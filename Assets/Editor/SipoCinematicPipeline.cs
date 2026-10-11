using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Sipo.Editor
{
    /// <summary>Owns renderer copies, never the project's existing render pipeline assets.</summary>
    internal static class SipoCinematicPipeline
    {
        const string Ownership = "SIPO_CINEMATIC_PIPELINE_V1";
        const string PipelineFile = "CinematicURP.asset";

        public static UniversalRenderPipelineAsset Configure(string ownedFolder,
            UniversalRenderPipelineAsset source, SipoCinematicLightingSettings settings)
        {
            RequireSettings(settings);
            if (source == null) throw new InvalidOperationException("An active Universal Render Pipeline asset is required.");
            if (string.IsNullOrWhiteSpace(ownedFolder) || !ownedFolder.StartsWith("Assets/", StringComparison.Ordinal)
                || ownedFolder.Split('/').Any(p => p == ".." || p == ".") || ownedFolder.Contains('\\'))
                throw new ArgumentException("The cinematic asset folder must be a project Assets subfolder.", nameof(ownedFolder));
            ownedFolder = ownedFolder.TrimEnd('/');
            var sourceState = new SerializedObject(source);
            var sourceRenderers = Required(sourceState, "m_RendererDataList");
            int defaultIndex = Required(sourceState, "m_DefaultRendererIndex").intValue;
            if (defaultIndex < 0 || defaultIndex >= sourceRenderers.arraySize
                || !(sourceRenderers.GetArrayElementAtIndex(defaultIndex).objectReferenceValue is UniversalRendererData))
                throw new InvalidOperationException("The active default renderer must be a Universal Renderer. Custom alternate renderer slots are preserved.");

            EnsureFolder(ownedFolder);
            string pipelinePath = ownedFolder + "/" + PipelineFile;
            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(pipelinePath);
            if (pipeline == null)
            {
                PreflightSource(source, ownedFolder);
                // Copying the asset preserves all original quality choices and renderer indices.
                pipeline = CopyOwnedAsset<UniversalRenderPipelineAsset>(source, pipelinePath);
                var copies = new Dictionary<ScriptableRendererData, ScriptableRendererData>();
                var pipelineState = new SerializedObject(pipeline);
                var rendererSlots = Required(pipelineState, "m_RendererDataList");
                for (int i = 0; i < sourceRenderers.arraySize; i++)
                {
                    var original = sourceRenderers.GetArrayElementAtIndex(i).objectReferenceValue as ScriptableRendererData;
                    if (original == null) continue; // Preserve intentionally empty slots.
                    if (!copies.TryGetValue(original, out var copy))
                    {
                        string rendererPath = ownedFolder + "/CinematicRenderer-" + i + ".asset";
                        copy = CopyOwnedAsset<ScriptableRendererData>(original, rendererPath);
                        MakeFeaturesOwned(copy);
                        copies.Add(original, copy);
                    }
                    rendererSlots.GetArrayElementAtIndex(i).objectReferenceValue = copy;
                }
                pipelineState.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(pipeline);
            }
            else
            {
                RequireOwned(pipeline, ownedFolder);
                foreach (var renderer in ReadRenderers(pipeline).Where(r => r != null).Distinct())
                {
                    RequireOwned(renderer, ownedFolder);
                    RequireFeaturesValid(renderer);
                }
            }

            // Reapply only our explicitly documented settings; never recopy customized clones.
            pipeline.supportsHDR = true;
            pipeline.colorGradingMode = ColorGradingMode.HighDynamicRange;
            pipeline.colorGradingLutSize = 32;
            pipeline.msaaSampleCount = settings.msaaSamples;
            pipeline.shadowDistance = settings.shadowDistance;
            pipeline.additionalLightsShadowmapResolution = settings.shadowAtlasResolution;
            var state = new SerializedObject(pipeline);
            SetInt(state, "m_MainLightRenderingMode", (int)LightRenderingMode.PerPixel);
            SetBool(state, "m_MainLightShadowsSupported", false);
            SetInt(state, "m_AdditionalLightsRenderingMode", (int)LightRenderingMode.PerPixel);
            SetBool(state, "m_AdditionalLightShadowsSupported", true);
            SetBool(state, "m_AnyShadowsSupported", true);
            SetBool(state, "m_SoftShadowsSupported", true);
            SetBool(state, "m_ReflectionProbeBlending", true);
            SetBool(state, "m_ReflectionProbeBoxProjection", true);
            SetBool(state, "m_ReflectionProbeAtlas", true);
            state.ApplyModifiedPropertiesWithoutUndo();

            foreach (var renderer in ReadRenderers(pipeline).Where(r => r != null).Distinct())
            {
                RequireOwned(renderer, ownedFolder);
                MakeFeaturesOwned(renderer);
                if (renderer is UniversalRendererData universal)
                {
                    universal.renderingMode = RenderingMode.ForwardPlus;
                    ConfigureAmbientOcclusion(universal, settings);
                }
                renderer.SetDirty();
                EditorUtility.SetDirty(renderer);
                AssetDatabase.SaveAssetIfDirty(renderer);
            }
            EditorUtility.SetDirty(pipeline);
            AssetDatabase.SaveAssetIfDirty(pipeline);
            Validate(pipeline, settings);
            return pipeline;
        }

        public static void Validate(UniversalRenderPipelineAsset pipeline, SipoCinematicLightingSettings settings)
        {
            RequireSettings(settings);
            if (pipeline == null) throw new InvalidOperationException("The cinematic pipeline is missing.");
            string folder = Path.GetDirectoryName(AssetDatabase.GetAssetPath(pipeline))?.Replace('\\', '/');
            RequireOwned(pipeline, folder);
            if (!pipeline.supportsHDR || pipeline.colorGradingMode != ColorGradingMode.HighDynamicRange || pipeline.colorGradingLutSize != 32
                || pipeline.msaaSampleCount != settings.msaaSamples
                || !Mathf.Approximately(pipeline.shadowDistance, settings.shadowDistance)
                || pipeline.additionalLightsShadowmapResolution != settings.shadowAtlasResolution
                || pipeline.supportsMainLightShadows || !pipeline.supportsAdditionalLightShadows
                || pipeline.mainLightRenderingMode != LightRenderingMode.PerPixel
                || pipeline.additionalLightsRenderingMode != LightRenderingMode.PerPixel
                || !pipeline.supportsSoftShadows || !pipeline.reflectionProbeBlending
                || !pipeline.reflectionProbeBoxProjection || !pipeline.reflectionProbeAtlas)
                throw new InvalidOperationException("Cinematic URP HDR, lights, shadows, antialiasing or reflection settings do not match the configuration.");
            var renderers = ReadRenderers(pipeline);
            int defaultIndex = Required(new SerializedObject(pipeline), "m_DefaultRendererIndex").intValue;
            if (defaultIndex < 0 || defaultIndex >= renderers.Length || !(renderers[defaultIndex] is UniversalRendererData))
                throw new InvalidOperationException("The cinematic default renderer is missing or incompatible.");
            foreach (var renderer in renderers.Where(r => r != null).Distinct())
            {
                RequireOwned(renderer, folder);
                foreach (var feature in renderer.rendererFeatures)
                {
                    if (feature == null) throw new InvalidOperationException("Missing renderer feature on " + renderer.name + ".");
                    if (AssetDatabase.GetAssetPath(feature) != AssetDatabase.GetAssetPath(renderer))
                        throw new InvalidOperationException("Renderer feature is not an owned subasset: " + feature.name + ".");
                }
                var featureMap = Required(new SerializedObject(renderer), "m_RendererFeatureMap");
                if (featureMap.arraySize != renderer.rendererFeatures.Count)
                    throw new InvalidOperationException("The cinematic renderer feature recovery map is incomplete.");
                for (int i = 0; i < featureMap.arraySize; i++)
                    if (!AssetDatabase.TryGetGUIDAndLocalFileIdentifier(renderer.rendererFeatures[i], out string guid, out long id)
                        || featureMap.GetArrayElementAtIndex(i).longValue != id)
                        throw new InvalidOperationException("The cinematic renderer feature recovery map has an incorrect subasset ID.");
                if (!(renderer is UniversalRendererData universal)) continue;
                if (universal.renderingMode != RenderingMode.ForwardPlus)
                    throw new InvalidOperationException("The cinematic Universal Renderer must use Forward+.");
                var features = universal.rendererFeatures.OfType<ScreenSpaceAmbientOcclusion>().ToArray();
                if (features.Length > 1 || (settings.enableAmbientOcclusion && features.Length != 1))
                    throw new InvalidOperationException("Expected one SSAO feature per cinematic Universal Renderer when enabled.");
                if (features.Length == 0) continue;
                var ao = features[0];
                if (ao.isActive != settings.enableAmbientOcclusion)
                    throw new InvalidOperationException("The cinematic SSAO enabled state does not match the configuration.");
                if (!settings.enableAmbientOcclusion) continue;
                var aoState = new SerializedObject(ao);
                if (!Mathf.Approximately(Required(aoState, "m_Settings.Intensity").floatValue, settings.aoIntensity)
                    || !Mathf.Approximately(Required(aoState, "m_Settings.Radius").floatValue, settings.aoRadius)
                    || !Required(aoState, "m_Settings.Downsample").boolValue
                    || Required(aoState, "m_Settings.AfterOpaque").boolValue
                    || Required(aoState, "m_Settings.Source").intValue != 0
                    || Required(aoState, "m_Settings.Samples").intValue != 1
                    || Required(aoState, "m_Settings.NormalSamples").intValue != 1
                    || Required(aoState, "m_Settings.BlurQuality").intValue != 1
                    || Required(aoState, "m_Settings.AOMethod").intValue != 1
                    || Required(aoState, "m_Settings.SampleCount").intValue != -1
                    || !Mathf.Approximately(Required(aoState, "m_Settings.DirectLightingStrength").floatValue, .12f)
                    || !Mathf.Approximately(Required(aoState, "m_Settings.Falloff").floatValue, settings.shadowDistance))
                    throw new InvalidOperationException("The cinematic SSAO settings do not match the configuration.");
            }
        }

        static void ConfigureAmbientOcclusion(UniversalRendererData renderer, SipoCinematicLightingSettings settings)
        {
            var features = renderer.rendererFeatures.OfType<ScreenSpaceAmbientOcclusion>().ToArray();
            if (features.Length > 1) throw new InvalidOperationException("Multiple existing SSAO features on " + renderer.name + "; remove the duplicate before applying cinematic lighting.");
            var ao = features.FirstOrDefault();
            if (ao == null && !settings.enableAmbientOcclusion) return;
            if (ao == null)
            {
                ao = ScriptableObject.CreateInstance<ScreenSpaceAmbientOcclusion>();
                ao.name = "Sipo Cinematic Ambient Occlusion";
                AssetDatabase.AddObjectToAsset(ao, renderer);
                renderer.rendererFeatures.Add(ao);
            }
            if (AssetDatabase.GetAssetPath(ao) != AssetDatabase.GetAssetPath(renderer))
                throw new InvalidOperationException("Refusing to edit an external SSAO feature.");
            ao.SetActive(settings.enableAmbientOcclusion);
            if (settings.enableAmbientOcclusion)
            {
                // URP 17.3's feature is public; its settings class is internal.
                // Guarded serialized paths intentionally fail loudly on an incompatible upgrade.
                var state = new SerializedObject(ao);
                SetFloat(state, "m_Settings.Intensity", settings.aoIntensity);
                SetFloat(state, "m_Settings.Radius", settings.aoRadius);
                SetFloat(state, "m_Settings.DirectLightingStrength", .12f);
                SetFloat(state, "m_Settings.Falloff", settings.shadowDistance);
                SetBool(state, "m_Settings.Downsample", true);
                SetBool(state, "m_Settings.AfterOpaque", false);
                SetInt(state, "m_Settings.Source", 0); // Depth reconstruction avoids the normal prepass.
                SetInt(state, "m_Settings.NormalSamples", 1);
                SetInt(state, "m_Settings.Samples", 1); // Medium: eight samples.
                SetInt(state, "m_Settings.BlurQuality", 1);
                SetInt(state, "m_Settings.AOMethod", 1); // Stable interleaved gradient noise with SMAA.
                SetInt(state, "m_Settings.SampleCount", -1); // Disable legacy migration overriding Samples.
                state.ApplyModifiedPropertiesWithoutUndo();
            }
            EditorUtility.SetDirty(ao);
            SynchronizeFeatureMap(renderer);
        }

        static void MakeFeaturesOwned(ScriptableRendererData renderer)
        {
            string path = AssetDatabase.GetAssetPath(renderer);
            var remap = new Dictionary<UnityEngine.Object, UnityEngine.Object>();
            for (int i = 0; i < renderer.rendererFeatures.Count; i++)
            {
                var feature = renderer.rendererFeatures[i];
                if (feature == null) throw new InvalidOperationException("Missing source renderer feature on " + renderer.name + ".");
                if (AssetDatabase.GetAssetPath(feature) == path) continue;
                if (!remap.TryGetValue(feature, out var copy))
                {
                    copy = UnityEngine.Object.Instantiate(feature);
                    copy.name = feature.name;
                    AssetDatabase.AddObjectToAsset(copy, renderer);
                    remap.Add(feature, copy);
                }
                renderer.rendererFeatures[i] = (ScriptableRendererFeature)copy;
            }
            // Preserve references from features AND their owned configuration subassets
            // when externally shared features were copied. External resources stay untouched.
            foreach (var feature in AssetDatabase.LoadAllAssetsAtPath(path).OfType<ScriptableObject>())
            {
                var state = new SerializedObject(feature);
                var property = state.GetIterator();
                while (property.Next(true))
                    if (property.propertyType == SerializedPropertyType.ObjectReference
                        && property.objectReferenceValue != null
                        && remap.TryGetValue(property.objectReferenceValue, out var copy))
                        property.objectReferenceValue = copy;
                state.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(feature);
            }
            SynchronizeFeatureMap(renderer);
        }

        static void SynchronizeFeatureMap(ScriptableRendererData renderer)
        {
            EditorUtility.SetDirty(renderer);
            AssetDatabase.SaveAssetIfDirty(renderer);
            var state = new SerializedObject(renderer);
            var map = Required(state, "m_RendererFeatureMap");
            map.arraySize = renderer.rendererFeatures.Count;
            for (int i = 0; i < map.arraySize; i++)
            {
                if (!AssetDatabase.TryGetGUIDAndLocalFileIdentifier(renderer.rendererFeatures[i], out string guid, out long id))
                    throw new InvalidOperationException("Could not identify owned renderer feature " + renderer.rendererFeatures[i].name + ".");
                map.GetArrayElementAtIndex(i).longValue = id;
            }
            state.ApplyModifiedPropertiesWithoutUndo();
            renderer.SetDirty();
            EditorUtility.SetDirty(renderer);
        }

        static ScriptableRendererData[] ReadRenderers(UniversalRenderPipelineAsset pipeline)
        {
            var array = Required(new SerializedObject(pipeline), "m_RendererDataList");
            var result = new ScriptableRendererData[array.arraySize];
            for (int i = 0; i < result.Length; i++) result[i] = array.GetArrayElementAtIndex(i).objectReferenceValue as ScriptableRendererData;
            return result;
        }

        static T CopyOwnedAsset<T>(T source, string path) where T : UnityEngine.Object
        {
            RequireVacant(path);
            string originalPath = AssetDatabase.GetAssetPath(source);
            if (string.IsNullOrEmpty(originalPath) || !AssetDatabase.CopyAsset(originalPath, path))
                throw new IOException("Could not copy rendering asset " + originalPath + " to " + path + ".");
            var copy = AssetDatabase.LoadAssetAtPath<T>(path);
            if (copy == null) throw new IOException("The copied rendering asset did not import: " + path + ".");
            var importer = AssetImporter.GetAtPath(path);
            if (importer == null) throw new IOException("The copied rendering asset has no importer: " + path + ".");
            // Retain any third-party import metadata on the copy as well.
            importer.userData = Ownership + (string.IsNullOrEmpty(importer.userData) ? "" : "\n" + importer.userData);
            AssetDatabase.WriteImportSettingsIfDirty(path);
            CopyCurrentSerializedState(source, copy, originalPath, path);
            return copy;
        }

        static void CopyCurrentSerializedState(UnityEngine.Object source, UnityEngine.Object copy, string originalPath, string copyPath)
        {
            // CopyAsset preserves the asset file and subassets, while CopySerialized includes
            // current Inspector edits that have not yet been saved. Remap references back to
            // copied subassets so current feature/resource settings never point at originals.
            var remap = new Dictionary<UnityEngine.Object, UnityEngine.Object> { [source] = copy };
            var copiedById = new Dictionary<long, UnityEngine.Object>();
            foreach (var item in AssetDatabase.LoadAllAssetsAtPath(copyPath))
                if (item != null && AssetDatabase.TryGetGUIDAndLocalFileIdentifier(item, out string guid, out long id)) copiedById[id] = item;
            foreach (var item in AssetDatabase.LoadAllAssetsAtPath(originalPath))
            {
                if (item == null || item == source) continue;
                if (!AssetDatabase.TryGetGUIDAndLocalFileIdentifier(item, out string guid, out long id))
                    throw new InvalidOperationException("Could not identify source rendering subasset " + item.name + ".");
                if (copiedById.TryGetValue(id, out var counterpart) && counterpart.GetType() == item.GetType())
                    remap[item] = counterpart;
                else if (item is ScriptableObject)
                {
                    counterpart = UnityEngine.Object.Instantiate(item);
                    counterpart.name = item.name;
                    AssetDatabase.AddObjectToAsset(counterpart, copy);
                    remap[item] = counterpart;
                }
                else throw new InvalidOperationException("Could not preserve rendering resource subasset " + item.name + ".");
            }
            foreach (var pair in remap)
            {
                if (!(pair.Key is ScriptableObject)) continue;
                EditorUtility.CopySerialized(pair.Key, pair.Value);
                var state = new SerializedObject(pair.Value);
                var property = state.GetIterator();
                while (property.Next(true))
                    if (property.propertyType == SerializedPropertyType.ObjectReference
                        && property.objectReferenceValue != null
                        && remap.TryGetValue(property.objectReferenceValue, out var replacement))
                        property.objectReferenceValue = replacement;
                state.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(pair.Value);
            }
            AssetDatabase.SaveAssetIfDirty(copy);
        }

        static void PreflightSource(UniversalRenderPipelineAsset source, string folder)
        {
            RequireVacant(folder + "/" + PipelineFile);
            var seen = new HashSet<ScriptableRendererData>();
            var renderers = ReadRenderers(source);
            for (int i = 0; i < renderers.Length; i++)
            {
                var renderer = renderers[i];
                if (renderer == null || !seen.Add(renderer)) continue;
                RequireVacant(folder + "/CinematicRenderer-" + i + ".asset");
                if (string.IsNullOrEmpty(AssetDatabase.GetAssetPath(renderer)))
                    throw new InvalidOperationException("Source renderers must be persistent assets before applying cinematic lighting.");
                RequireFeaturesValid(renderer);
            }
        }

        static void RequireFeaturesValid(ScriptableRendererData renderer)
        {
            if (renderer.rendererFeatures.Any(feature => feature == null))
                throw new InvalidOperationException("Missing source renderer feature on " + renderer.name + ".");
            if (renderer.rendererFeatures.OfType<ScreenSpaceAmbientOcclusion>().Count() > 1)
                throw new InvalidOperationException("Multiple source SSAO features on " + renderer.name + ". Resolve this duplicate before applying cinematic lighting.");
            Required(new SerializedObject(renderer), "m_RendererFeatureMap");
        }

        static void RequireVacant(string path)
        {
            if (AssetDatabase.LoadMainAssetAtPath(path) != null || File.Exists(path) || File.Exists(path + ".meta"))
                throw new IOException("Refusing to overwrite an existing asset: " + path + ".");
        }

        static void RequireOwned(UnityEngine.Object asset, string folder)
        {
            string path = AssetDatabase.GetAssetPath(asset);
            string marker = AssetImporter.GetAtPath(path)?.userData;
            if (string.IsNullOrEmpty(folder) || string.IsNullOrEmpty(path)
                || Path.GetDirectoryName(path)?.Replace('\\', '/') != folder
                || !(marker == Ownership || (marker != null && marker.StartsWith(Ownership + "\n", StringComparison.Ordinal))))
                throw new InvalidOperationException("Refusing to modify an asset outside this scene's owned cinematic configuration: " + path + ".");
        }

        static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            int slash = path.LastIndexOf('/');
            if (slash < 0) throw new ArgumentException("Invalid Assets folder: " + path + ".");
            EnsureFolder(path.Substring(0, slash));
            if (string.IsNullOrEmpty(AssetDatabase.CreateFolder(path.Substring(0, slash), path.Substring(slash + 1))))
                throw new IOException("Could not create cinematic asset folder " + path + ".");
        }

        static void RequireSettings(SipoCinematicLightingSettings settings)
        {
            if (settings == null) throw new ArgumentNullException(nameof(settings));
            if (settings.msaaSamples != 1 && settings.msaaSamples != 2 && settings.msaaSamples != 4 && settings.msaaSamples != 8)
                throw new ArgumentException("URP MSAA must be 1, 2, 4 or 8 samples.");
            if (settings.shadowAtlasResolution < 256 || settings.shadowAtlasResolution > 4096
                || !Mathf.IsPowerOfTwo(settings.shadowAtlasResolution))
                throw new ArgumentException("Additional-light shadow atlas resolution must be a power of two from 256 to 4096.");
            if (float.IsNaN(settings.shadowDistance) || float.IsInfinity(settings.shadowDistance) || settings.shadowDistance <= 0
                || float.IsNaN(settings.aoIntensity) || float.IsInfinity(settings.aoIntensity) || settings.aoIntensity < 0
                || float.IsNaN(settings.aoRadius) || float.IsInfinity(settings.aoRadius) || settings.aoRadius <= 0)
                throw new ArgumentException("Cinematic lighting distances and AO settings must be finite and non-negative; distances must be positive.");
        }

        static SerializedProperty Required(SerializedObject state, string path)
        {
            return state.FindProperty(path) ?? throw new NotSupportedException("URP 17.3 property missing: " + state.targetObject.GetType().Name + "." + path + ".");
        }
        static void SetBool(SerializedObject state, string path, bool value) { Required(state, path).boolValue = value; }
        static void SetInt(SerializedObject state, string path, int value) { Required(state, path).intValue = value; }
        static void SetFloat(SerializedObject state, string path, float value) { Required(state, path).floatValue = value; }
    }
}
