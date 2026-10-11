using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Sipo.Rendering;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

namespace Sipo.Editor
{
    /// <summary>Presentation-only overlay. Never calls the scene builder or rewrites imported assets.</summary>
    public static class SipoCinematicLighting
    {
        public const string SettingsPath = "Assets/Settings/SipoCinematicLightingSettings.asset";
        const string ProfileOwnership = "SIPO_CINEMATIC_VOLUME_V1";
        static readonly string[] Models = {
            "Assets/Environment/SipoSupermarket.fbx", "Assets/Environment/SipoMerchandise.fbx"
        };
        [Serializable] public sealed class Layout
        {
            public int schemaVersion;
            public float lightIntensityMultiplier;
            public Lamp[] lights;
            public Probe[] reflections;
        }
        [Serializable] public sealed class Lamp
        {
            public string name, type;
            public float[] position, target, color;
            public float intensity, range, spotAngle;
            public bool shadow, bakeOnly;
        }
        [Serializable] public sealed class Probe
        {
            public string name;
            public float[] position, center, size;
            public int resolution, importance;
        }

        [MenuItem("Sipo/Select Cinematic Lighting Settings", false, 100)]
        public static void SelectSettings() => Selection.activeObject = Settings();

        [MenuItem("Sipo/Apply Cinematic Lighting to Active Scene", false, 101)]
        public static void Apply()
        {
            RequireEditMode();
            var scene = SceneManager.GetActiveScene();
            if (!scene.IsValid() || !scene.isLoaded || string.IsNullOrEmpty(scene.path))
                throw new InvalidOperationException("Save the existing supermarket scene (or a Save As copy) before applying cinematic lighting.");
            var settings = Settings(); settings.Validate();
            var layout = ReadLayout(settings);
            SupermarketProject.ValidateEnvironmentMaterials(); // Read-only; preserve the existing remapping fix.
            var roots = EnvironmentRoots(scene);
            var frame = CommonFrame(roots);
            if ((frame.lossyScale - Vector3.one).sqrMagnitude > .0001f)
                throw new InvalidOperationException("The supermarket's common parent must have unit world scale for the metre-based lighting preset. No geometry was changed.");
            var renderers = roots.SelectMany(r => r.GetComponentsInChildren<MeshRenderer>(true)).Distinct().ToArray();
            var cameras = Objects<Camera>(scene).Where(c => c.CompareTag("MainCamera") &&
                (c.GetComponent<UniversalAdditionalCameraData>() == null || c.GetComponent<UniversalAdditionalCameraData>().renderType == CameraRenderType.Base)).ToArray();
            if (cameras.Length == 0) throw new InvalidOperationException("The active scene needs a Base camera tagged MainCamera. Camera transforms and controls are never changed.");
            var source = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            if (source == null) throw new InvalidOperationException("Select the existing URP pipeline in Project Settings before applying this preset.");
            var state = FindState(scene);
            string sceneGuid = AssetDatabase.AssetPathToGUID(scene.path);
            if (state != null && state.sceneGuid != sceneGuid)
                throw new InvalidOperationException("This Save As copy contains another scene's cinematic rig. Restore Previous Lighting in this copy first, then apply again to create independent assets.");
            if (state != null && state.applied)
            {
                ValidateGeometry(state);
                if (state.qualityIndex != QualitySettings.GetQualityLevel() || QualitySettings.renderPipeline != state.appliedPipeline)
                    throw new InvalidOperationException("The quality level or pipeline changed after Apply. Restore Previous Lighting before applying to the new quality configuration.");
            }
            var beforeQuality = QualitySettings.renderPipeline;
            var beforeAmbient = CaptureAmbient();
            bool wasApplied = state != null && state.applied;
            Undo.IncrementCurrentGroup(); int undo = Undo.GetCurrentGroup();
            Undo.SetCurrentGroupName("Apply SIPO cinematic lighting");
            try
            {
                if (state == null)
                {
                    var rig = new GameObject("SIPO | Cinematic lighting (owned, reversible)");
                    SceneManager.MoveGameObjectToScene(rig, scene);
                    Undo.RegisterCreatedObjectUndo(rig, "Create cinematic rig");
                    Undo.SetTransformParent(rig.transform, frame, "Parent cinematic rig");
                    rig.transform.localPosition = Vector3.zero; rig.transform.localRotation = Quaternion.identity;
                    rig.transform.localScale = Vector3.one;
                    state = Undo.AddComponent<SipoCinematicLightingState>(rig);
                }
                Undo.RecordObject(state, "Remember cinematic restoration data");
                if (!wasApplied)
                {
                    state.sceneGuid = sceneGuid;
                    state.ownedFolder = "Assets/SipoCinematicGenerated/" + sceneGuid;
                    state.environmentFrame = frame;
                    state.qualityIndex = QualitySettings.GetQualityLevel();
                    state.previousPipeline = QualitySettings.renderPipeline;
                    state.originalDefaultPipeline = GraphicsSettings.defaultRenderPipeline;
                    CopyAmbient(beforeAmbient, state);
                    state.cameras.Clear(); state.previousLighting.Clear(); state.geometry.Clear();
                    foreach (var renderer in renderers)
                        state.geometry.Add(new SipoCinematicLightingState.RendererState {
                            renderer = renderer, mesh = renderer.GetComponent<MeshFilter>()?.sharedMesh,
                            materials = renderer.sharedMaterials,
                            relativeMatrix = frame.worldToLocalMatrix * renderer.transform.localToWorldMatrix
                        });
                }
                Undo.RecordObject(state.gameObject, "Enable cinematic rig");
                state.gameObject.SetActive(true);
                state.appliedPipeline = SipoCinematicPipeline.Configure(state.ownedFolder, source, settings);
                // Unity's current-quality override is project-wide, not scene-local. Restore records it explicitly.
                QualitySettings.renderPipeline = state.appliedPipeline;
                ConfigureOriginalLights(state, settings.replaceGeneratedLighting);
                ConfigureLights(state, layout, settings);
                ConfigureProbes(state, layout);
                ConfigureVolume(state, settings);
                ConfigureCameras(state, cameras);
                RenderSettings.ambientMode = AmbientMode.Trilight;
                RenderSettings.ambientSkyColor = settings.ambientSky;
                RenderSettings.ambientEquatorColor = settings.ambientEquator;
                RenderSettings.ambientGroundColor = settings.ambientGround;
                RenderSettings.ambientIntensity = settings.ambientIntensity;
                RenderSettings.reflectionIntensity = settings.reflectionIntensity;
                if (state.surfaces == null) state.surfaces = Undo.AddComponent<SipoCinematicSurfacePolish>(state.gameObject);
                Undo.RecordObject(state.surfaces, "Configure surface polish");
                state.surfaces.Restore(); state.surfaces.enabled = settings.polishSurfaces;
                if (settings.polishSurfaces) state.surfaces.Configure(renderers, settings.surfaces);
                state.settingsJson = EditorJsonUtility.ToJson(settings);
                state.layoutJson = settings.layout.text;
                state.reflectionsDirty = true;
                state.applied = true;
                EditorUtility.SetDirty(state);
                ValidateConfiguration(state, settings, false);
                EditorSceneManager.MarkSceneDirty(scene);
                Undo.CollapseUndoOperations(undo);
                Debug.Log("SIPO_CINEMATIC_APPLIED: " + layout.lights.Length + " lights, " + layout.lights.Count(l => l.shadow) +
                    " shadow spotlights. Original meshes and material assignments verified unchanged. Capture Cinematic Reflection Probes next; inspect the image locally and save the scene when satisfied. Reapply refreshes the rig; Restore Previous Lighting restores original settings.", state);
            }
            catch
            {
                if (state != null && state.surfaces != null) state.surfaces.Restore();
                Undo.RevertAllDownToGroup(undo);
                QualitySettings.renderPipeline = beforeQuality;
                RestoreAmbient(beforeAmbient);
                if (wasApplied && state != null && state.surfaces != null && state.surfaces.enabled) state.surfaces.Apply();
                throw;
            }
        }

        [MenuItem("Sipo/Restore Previous Lighting", false, 104)]
        public static void Restore()
        {
            RequireEditMode();
            var state = RequiredState(false);
            if (!state.applied) { Debug.Log("SIPO cinematic lighting is already restored.", state); return; }
            Undo.IncrementCurrentGroup(); int undo = Undo.GetCurrentGroup(); Undo.SetCurrentGroupName("Restore previous SIPO lighting");
            Undo.RecordObject(state, "Restore lighting state");
            if (state.surfaces != null) state.surfaces.Restore();
            foreach (var item in state.previousLighting)
                if (item.component != null) { Undo.RecordObject(item.component, "Restore previous light"); item.component.enabled = item.enabled; RecordPrefab(item.component); }
            foreach (var item in state.cameras)
            {
                if (item.camera == null) continue;
                Undo.RecordObject(item.camera, "Restore camera HDR"); item.camera.allowHDR = item.hdr; RecordPrefab(item.camera);
                var data = item.camera.GetComponent<UniversalAdditionalCameraData>();
                if (data == null) continue;
                if (!item.hadAdditionalData) Undo.DestroyObjectImmediate(data);
                else
                {
                    Undo.RecordObject(data, "Restore camera effects");
                    data.renderPostProcessing = item.postProcessing; data.antialiasing = item.aa;
                    data.antialiasingQuality = item.aaQuality; data.dithering = item.dithering; data.stopNaN = item.stopNaN;
                    RecordPrefab(data);
                }
            }
            RestoreAmbient(state);
            if (QualitySettings.GetQualityLevel() == state.qualityIndex && QualitySettings.renderPipeline == state.appliedPipeline)
                QualitySettings.renderPipeline = state.previousPipeline;
            else Debug.LogWarning("The quality selection/pipeline was changed after Apply; Restore preserved that newer project choice. The previously used pipeline remains recorded on the rig.", state);
            Undo.RecordObject(state.gameObject, "Disable owned cinematic rig"); state.gameObject.SetActive(false);
            state.applied = false;
            // A copied scene can now apply with its own GUID; old generated assets are retained, never deleted.
            state.sceneGuid = AssetDatabase.AssetPathToGUID(SceneManager.GetActiveScene().path);
            EditorUtility.SetDirty(state); EditorSceneManager.MarkSceneDirty(SceneManager.GetActiveScene());
            Undo.CollapseUndoOperations(undo);
            Debug.Log("SIPO_CINEMATIC_RESTORED: original lights, camera presentation fields, ambient settings and applicable quality override restored. Owned rig disabled; no original objects/assets removed. Save to keep the restoration.", state);
        }

        [MenuItem("Sipo/Capture Cinematic Reflection Probes", false, 102)]
        public static void CaptureReflections()
        {
            RequireEditMode();
            var state = RequiredState(true);
            var settings = AppliedSettings(state);
            try { ValidateConfiguration(state, settings, false); }
            finally { DestroySnapshot(settings); }
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null)
                throw new InvalidOperationException("Reflection capture requires the licensed Unity Editor with an active graphics device. A -nographics session cannot capture the environment.");
            try
            {
                for (int i = 0; i < state.probes.Count; i++)
                {
                    var probe = state.probes[i]; if (probe == null || !probe.enabled) continue;
                    EditorUtility.DisplayProgressBar("SIPO cinematic reflections", probe.name, (float)i / state.probes.Count);
                    string path = state.ownedFolder + "/Reflection-" + i.ToString("00") + ".exr";
                    if (File.Exists(path) && AssetImporter.GetAtPath(path)?.userData != ProfileOwnership)
                        throw new InvalidOperationException("Refusing to replace an unowned reflection texture: " + path);
                    Undo.RecordObject(probe, "Capture cinematic reflection");
                    var oldMode = probe.mode;
                    try
                    {
                        probe.mode = ReflectionProbeMode.Baked;
                        if (!Lightmapping.BakeReflectionProbe(probe, path)) throw new InvalidOperationException("Reflection capture failed: " + probe.name);
                        AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
                        var importer = AssetImporter.GetAtPath(path) as TextureImporter;
                        if (importer == null) throw new InvalidOperationException("Missing reflection texture importer: " + path);
                        importer.userData = ProfileOwnership;
                        importer.textureShape = TextureImporterShape.TextureCube;
                        importer.generateCubemap = TextureImporterGenerateCubemap.AutoCubemap;
                        importer.sRGBTexture = false; importer.mipmapEnabled = true;
                        importer.textureCompression = TextureImporterCompression.Uncompressed;
                        importer.SaveAndReimport();
                        var texture = AssetDatabase.LoadAssetAtPath<Texture>(path);
                        if (texture == null || texture.dimension != TextureDimension.Cube)
                            throw new InvalidOperationException("The captured EXR did not import as an HDR cubemap: " + path);
                        probe.customBakedTexture = texture; probe.mode = ReflectionProbeMode.Custom;
                        EditorUtility.SetDirty(probe);
                    }
                    catch { probe.mode = oldMode; throw; }
                }
                Undo.RecordObject(state, "Remember reflection capture status");
                state.reflectionsDirty = false;
                EditorUtility.SetDirty(state);
                EditorSceneManager.MarkSceneDirty(SceneManager.GetActiveScene());
                settings = AppliedSettings(state);
                try { ValidateConfiguration(state, settings, true); }
                finally { DestroySnapshot(settings); }
                Debug.Log("SIPO_CINEMATIC_REFLECTIONS_CAPTURED: six view directions per probe captured once into persistent HDR cubemaps. Recapture after scene, light or surface changes; no per-frame probe rendering.", state);
            }
            finally { EditorUtility.ClearProgressBar(); }
        }

        [MenuItem("Sipo/Validate Cinematic Lighting", false, 103)]
        public static void Validate()
        {
            RequireEditMode(); var state = RequiredState(true);
            var settings = AppliedSettings(state);
            try { ValidateConfiguration(state, settings, true); }
            finally { DestroySnapshot(settings); }
            Debug.Log("SIPO_CINEMATIC_VALIDATION_PASSED: mapped URP materials, mesh references/transforms, pipeline, effects, cameras, light budgets and captured reflection cubemaps verified. This validates configuration, not the final rendered appearance.", state);
        }

        static void ValidateConfiguration(SipoCinematicLightingState state, SipoCinematicLightingSettings settings, bool requireCaptures)
        {
            settings.Validate(); SupermarketProject.ValidateEnvironmentMaterials(); ValidateGeometry(state);
            if (QualitySettings.GetQualityLevel() != state.qualityIndex || QualitySettings.renderPipeline != state.appliedPipeline)
                throw new InvalidOperationException("The cinematic pipeline is not selected for the current quality level.");
            if (GraphicsSettings.defaultRenderPipeline != state.originalDefaultPipeline)
                throw new InvalidOperationException("The project default pipeline changed since Apply. Restore/reapply after confirming the intended pipeline.");
            SipoCinematicPipeline.Validate((UniversalRenderPipelineAsset)state.appliedPipeline, settings);
            var layout = ReadLayout(settings);
            var lamps = state.lights.Where(l => l != null && l.enabled).ToArray();
            if (lamps.Length != layout.lights.Length || lamps.Count(l => l.shadows != LightShadows.None) > 3 ||
                lamps.Any(l => l.lightmapBakeType != LightmapBakeType.Realtime || (l.shadows != LightShadows.None && l.type != LightType.Spot)))
                throw new InvalidOperationException("Cinematic light count/type/shadow budget differs from the applied recipe.");
            foreach (var entry in layout.lights)
            {
                var light = lamps.SingleOrDefault(l => l.name == entry.name);
                if (light == null || light.type != (entry.type == "spot" ? LightType.Spot : LightType.Point) ||
                    (light.transform.localPosition - V(entry.position)).sqrMagnitude > .0001f ||
                    !Mathf.Approximately(light.intensity, entry.intensity * layout.lightIntensityMultiplier * settings.lightIntensityMultiplier) ||
                    !Mathf.Approximately(light.range, entry.range) || light.color != C(entry.color) ||
                    (light.shadows != LightShadows.None) != entry.shadow)
                    throw new InvalidOperationException("Light differs from the applied recipe: " + entry.name + ". Edit the settings/JSON and reapply to keep validation repeatable.");
            }
            var probes = state.probes.Where(p => p != null && p.enabled).ToArray();
            if (probes.Length != layout.reflections.Length || probes.Any(p => !p.hdr || !p.boxProjection || p.mode == ReflectionProbeMode.Realtime || p.refreshMode == ReflectionProbeRefreshMode.EveryFrame))
                throw new InvalidOperationException("Cinematic reflection probe configuration is incomplete or rendering continuously.");
            foreach (var entry in layout.reflections)
            {
                var probe = probes.SingleOrDefault(p => p.name == entry.name);
                if (probe == null || probe.resolution != entry.resolution || probe.importance != entry.importance ||
                    (probe.transform.localPosition - V(entry.position)).sqrMagnitude > .0001f ||
                    (probe.size - V(entry.size)).sqrMagnitude > .0001f ||
                    (probe.center - (V(entry.center) - V(entry.position))).sqrMagnitude > .0001f)
                    throw new InvalidOperationException("Reflection volume differs from the applied recipe: " + entry.name);
            }
            int pending = probes.Count(p => p.mode != ReflectionProbeMode.Custom || p.customBakedTexture == null || p.customBakedTexture.dimension != TextureDimension.Cube);
            if (state.reflectionsDirty && requireCaptures) throw new InvalidOperationException("Reflection captures are stale after Apply. Run Sipo > Capture Cinematic Reflection Probes to refresh them.");
            if (pending > 0 && requireCaptures) throw new InvalidOperationException(pending + " reflection captures are missing. Run Sipo > Capture Cinematic Reflection Probes before claiming validation complete.");
            if (pending > 0) Debug.LogWarning(pending + " cinematic reflection captures are pending. Glossy floors and metals require Capture Cinematic Reflection Probes.", state);
            if (state.volume == null || !state.volume.enabled || !state.volume.isGlobal || state.volume.sharedProfile == null ||
                !state.volume.sharedProfile.TryGet<Bloom>(out var bloom) || !bloom.active ||
                !Mathf.Approximately(bloom.intensity.value, settings.bloomIntensity) || !Mathf.Approximately(bloom.threshold.value, settings.bloomThreshold) ||
                !state.volume.sharedProfile.TryGet<Tonemapping>(out var tone) || tone.mode.value != settings.tonemapping ||
                !state.volume.sharedProfile.TryGet<ColorAdjustments>(out var color) || !Mathf.Approximately(color.postExposure.value, settings.postExposure))
                throw new InvalidOperationException("The owned post-processing volume is missing or differs from the applied settings.");
            foreach (var item in state.cameras)
            {
                if (item.camera == null) throw new InvalidOperationException("A configured camera was removed.");
                var data = item.camera.GetComponent<UniversalAdditionalCameraData>();
                if (!item.camera.allowHDR || data == null || !data.renderPostProcessing || data.antialiasing != AntialiasingMode.SubpixelMorphologicalAntiAliasing)
                    throw new InvalidOperationException("Camera HDR, post-processing or SMAA is disabled: " + item.camera.name);
                if ((data.volumeLayerMask.value & (1 << state.gameObject.layer)) == 0)
                    throw new InvalidOperationException("The camera's volume mask excludes the cinematic volume layer: " + item.camera.name);
            }
            if (settings.polishSurfaces && (state.surfaces == null || !state.surfaces.enabled || !state.surfaces.ValidateApplied(out _)))
                throw new InvalidOperationException("Surface polish validation failed; check Console and existing renderer property blocks.");
            if (settings.replaceGeneratedLighting && state.previousLighting.Any(item => item.component != null && item.component.enabled))
                throw new InvalidOperationException("An original generated light/probe/volume was re-enabled and would double the cinematic treatment. Reapply or disable replacement in the settings.");
            int extraShadows = Objects<Light>(SceneManager.GetActiveScene()).Count(l => l.isActiveAndEnabled && l.shadows != LightShadows.None && !state.lights.Contains(l));
            if (extraShadows > 0) Debug.LogWarning(extraShadows + " custom/original shadow-casting lights remain enabled. The owned rig budget is three spots; inspect total scene cost locally.", state);
        }

        static void ConfigureOriginalLights(SipoCinematicLightingState state, bool replace)
        {
            // Exact generated group only: custom lights elsewhere remain untouched.
            var group = state.environmentFrame.root.GetComponentsInChildren<Transform>(true)
                .FirstOrDefault(t => t.name == "Warm architectural lighting");
            if (group == null) { Debug.LogWarning("Original generated lighting group not found. Existing custom lights/volumes remain untouched; inspect for overlapping illumination.", state); return; }
            var behaviours = group.GetComponentsInChildren<Behaviour>(true).Where(b => b is Light || b is ReflectionProbe || b is Volume);
            foreach (var behaviour in behaviours)
            {
                var previous = state.previousLighting.FirstOrDefault(s => s.component == behaviour);
                if (previous == null) { previous = new SipoCinematicLightingState.BehaviourState { component = behaviour, enabled = behaviour.enabled }; state.previousLighting.Add(previous); }
                Undo.RecordObject(behaviour, "Set original generated lighting participation");
                behaviour.enabled = replace ? false : previous.enabled; RecordPrefab(behaviour);
            }
        }

        static void ConfigureLights(SipoCinematicLightingState state, Layout layout, SipoCinematicLightingSettings settings)
        {
            foreach (var old in state.lights.Where(l => l != null)) { Undo.RecordObject(old, "Refresh owned light"); old.enabled = false; }
            foreach (var entry in layout.lights)
            {
                var light = state.lights.FirstOrDefault(l => l != null && l.name == entry.name);
                if (light == null) { light = Undo.AddComponent<Light>(Child(entry.name, state.transform)); state.lights.Add(light); }
                Undo.RecordObject(light, "Tune cinematic light"); Undo.RecordObject(light.transform, "Position cinematic light");
                light.transform.localPosition = V(entry.position);
                light.transform.localRotation = Quaternion.LookRotation(V(entry.target) - V(entry.position));
                light.type = entry.type == "spot" ? LightType.Spot : LightType.Point;
                light.color = C(entry.color); light.intensity = entry.intensity * layout.lightIntensityMultiplier * settings.lightIntensityMultiplier;
                light.range = entry.range; light.spotAngle = entry.spotAngle; light.innerSpotAngle = entry.spotAngle * .65f;
                light.lightmapBakeType = LightmapBakeType.Realtime;
                light.shadows = entry.shadow ? LightShadows.Soft : LightShadows.None;
                light.shadowStrength = .75f; light.shadowBias = .04f; light.shadowNormalBias = .2f;
                light.bounceIntensity = 1; light.enabled = true;
            }
        }

        static void ConfigureProbes(SipoCinematicLightingState state, Layout layout)
        {
            foreach (var old in state.probes.Where(p => p != null)) { Undo.RecordObject(old, "Refresh owned probe"); old.enabled = false; }
            foreach (var entry in layout.reflections)
            {
                var probe = state.probes.FirstOrDefault(p => p != null && p.name == entry.name);
                if (probe == null) { probe = Undo.AddComponent<ReflectionProbe>(Child(entry.name, state.transform)); state.probes.Add(probe); }
                Undo.RecordObject(probe, "Tune cinematic probe"); Undo.RecordObject(probe.transform, "Position cinematic probe");
                probe.transform.localPosition = V(entry.position); probe.transform.localRotation = Quaternion.identity;
                probe.center = V(entry.center) - V(entry.position); probe.size = V(entry.size);
                probe.resolution = entry.resolution; probe.importance = entry.importance;
                probe.hdr = true; probe.boxProjection = true; probe.blendDistance = 3;
                probe.nearClipPlane = .15f; probe.farClipPlane = 100;
                probe.mode = probe.customBakedTexture != null ? ReflectionProbeMode.Custom : ReflectionProbeMode.Baked;
                probe.refreshMode = ReflectionProbeRefreshMode.ViaScripting;
                probe.clearFlags = ReflectionProbeClearFlags.Skybox;
                probe.intensity = 1; probe.enabled = true;
            }
        }

        static void ConfigureCameras(SipoCinematicLightingState state, Camera[] cameras)
        {
            foreach (var camera in cameras)
            {
                var data = camera.GetComponent<UniversalAdditionalCameraData>();
                if (data != null && (data.volumeLayerMask.value & (1 << state.gameObject.layer)) == 0)
                    throw new InvalidOperationException("The MainCamera volume mask excludes Default. Include the cinematic rig layer in the camera's Volume Mask, then Apply again.");
                if (!state.cameras.Any(c => c.camera == camera)) state.cameras.Add(new SipoCinematicLightingState.CameraState {
                    camera = camera, hdr = camera.allowHDR, hadAdditionalData = data != null,
                    postProcessing = data != null && data.renderPostProcessing,
                    aa = data != null ? data.antialiasing : AntialiasingMode.None,
                    aaQuality = data != null ? data.antialiasingQuality : AntialiasingQuality.High,
                    dithering = data != null && data.dithering, stopNaN = data != null && data.stopNaN
                });
                if (data == null) data = Undo.AddComponent<UniversalAdditionalCameraData>(camera.gameObject);
                Undo.RecordObject(camera, "Enable camera HDR"); Undo.RecordObject(data, "Tune camera effects");
                camera.allowHDR = true; data.renderPostProcessing = true;
                data.antialiasing = AntialiasingMode.SubpixelMorphologicalAntiAliasing;
                data.antialiasingQuality = AntialiasingQuality.High; data.dithering = true; data.stopNaN = true;
                RecordPrefab(camera); RecordPrefab(data);
            }
        }

        static void ConfigureVolume(SipoCinematicLightingState state, SipoCinematicLightingSettings settings)
        {
            string path = state.ownedFolder + "/CinematicVolume.asset";
            var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(path);
            if (profile == null)
            {
                if (File.Exists(path)) throw new InvalidOperationException("Refusing to overwrite unrelated asset: " + path);
                profile = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(profile, path);
                var importer = AssetImporter.GetAtPath(path); importer.userData = ProfileOwnership; importer.SaveAndReimport();
            }
            if (AssetImporter.GetAtPath(path).userData != ProfileOwnership) throw new InvalidOperationException("Volume asset is not owned by the cinematic tool: " + path);
            var tone = Effect<Tonemapping>(profile); tone.mode.Override(settings.tonemapping);
            var bloom = Effect<Bloom>(profile); bloom.intensity.Override(settings.bloomIntensity);
            bloom.threshold.Override(settings.bloomThreshold); bloom.scatter.Override(settings.bloomScatter);
            bloom.clamp.Override(8); bloom.highQualityFiltering.Override(true);
            var color = Effect<ColorAdjustments>(profile); color.postExposure.Override(settings.postExposure);
            color.contrast.Override(settings.contrast); color.saturation.Override(settings.saturation);
            color.colorFilter.Override(Color.white);
            var white = Effect<WhiteBalance>(profile); white.temperature.Override(settings.temperature); white.tint.Override(settings.tint);
            var vignette = Effect<Vignette>(profile); vignette.intensity.Override(settings.vignetteIntensity); vignette.smoothness.Override(.4f);
            EditorUtility.SetDirty(profile); AssetDatabase.SaveAssetIfDirty(profile);
            if (state.volume == null) state.volume = Undo.AddComponent<Volume>(state.gameObject);
            Undo.RecordObject(state.volume, "Tune cinematic volume");
            state.volume.isGlobal = true; state.volume.priority = 30; state.volume.weight = 1;
            state.volume.sharedProfile = profile; state.volume.enabled = true;
        }
        static T Effect<T>(VolumeProfile profile) where T : VolumeComponent
        {
            if (!profile.TryGet<T>(out var effect)) { effect = profile.Add<T>(true); AssetDatabase.AddObjectToAsset(effect, profile); }
            Undo.RecordObject(effect, "Tune cinematic post processing"); effect.active = true; EditorUtility.SetDirty(effect); return effect;
        }

        static void ValidateGeometry(SipoCinematicLightingState state)
        {
            if (state.environmentFrame == null || state.geometry.Count == 0) throw new InvalidOperationException("Missing environment preservation snapshot.");
            foreach (var saved in state.geometry)
            {
                if (saved.renderer == null || saved.renderer.GetComponent<MeshFilter>()?.sharedMesh != saved.mesh ||
                    !saved.renderer.sharedMaterials.SequenceEqual(saved.materials))
                    throw new InvalidOperationException("An original renderer, mesh or material assignment changed since Apply. Restore/reapply after reviewing your intended edits.");
                var now = state.environmentFrame.worldToLocalMatrix * saved.renderer.transform.localToWorldMatrix;
                for (int i = 0; i < 16; i++) if (Mathf.Abs(now[i] - saved.relativeMatrix[i]) > .001f)
                    throw new InvalidOperationException("An original environment transform changed since Apply: " + saved.renderer.name);
            }
        }
        internal static Layout ReadLayout(SipoCinematicLightingSettings settings)
        {
            if (settings.layout == null) throw new InvalidOperationException("The lighting settings need the supplied layout JSON.");
            var layout = JsonUtility.FromJson<Layout>(settings.layout.text);
            if (layout == null || layout.schemaVersion != 1 || layout.lights == null || layout.reflections == null ||
                layout.lights.Length == 0 || layout.lights.Length > 40 || layout.reflections.Length == 0 || layout.reflections.Length > 6 ||
                !Finite(layout.lightIntensityMultiplier) || layout.lightIntensityMultiplier <= 0 || layout.lightIntensityMultiplier > 4 ||
                layout.lights.Select(l => l.name).Distinct().Count() != layout.lights.Length || layout.reflections.Select(p => p.name).Distinct().Count() != layout.reflections.Length ||
                layout.lights.Count(l => l.shadow) > 3)
                throw new InvalidDataException("Invalid cinematic layout schema, names or light/probe budget.");
            foreach (var l in layout.lights)
            {
                var position = V(l.position); var target = V(l.target); var color = V(l.color);
                if (string.IsNullOrWhiteSpace(l.name) || (l.type != "point" && l.type != "spot") || l.bakeOnly ||
                    (l.shadow && l.type != "spot") || !Finite(l.intensity) || l.intensity <= 0 || l.intensity > 250 ||
                    !Finite(l.range) || l.range <= 0 || l.range > 35 || !Finite(l.spotAngle) || l.spotAngle <= 1 || l.spotAngle >= 150 ||
                    color.x < 0 || color.y < 0 || color.z < 0 || color.x > 1 || color.y > 1 || color.z > 1 ||
                    Vector3.Distance(position, target) < .1f || Vector3.Distance(position, target) >= l.range)
                    throw new InvalidDataException("Invalid light/target or unsupported bake-only light: " + l.name);
            }
            foreach (var p in layout.reflections)
            {
                V(p.position); V(p.center); var size = V(p.size);
                if (string.IsNullOrWhiteSpace(p.name) || size.x <= 0 || size.y <= 0 || size.z <= 0 || (p.resolution != 128 && p.resolution != 256 && p.resolution != 512))
                    throw new InvalidDataException("Invalid reflection probe: " + p.name);
            }
            return layout;
        }
        static SipoCinematicLightingSettings Settings() => AssetDatabase.LoadAssetAtPath<SipoCinematicLightingSettings>(SettingsPath)
            ?? throw new FileNotFoundException("Missing cinematic settings asset: " + SettingsPath);
        static SipoCinematicLightingSettings AppliedSettings(SipoCinematicLightingState state)
        {
            var settings = ScriptableObject.CreateInstance<SipoCinematicLightingSettings>();
            EditorJsonUtility.FromJsonOverwrite(state.settingsJson, settings);
            // Persist the applied recipe by value; current project settings can be edited independently.
            settings.layout = new TextAsset(state.layoutJson);
            return settings;
        }
        static void DestroySnapshot(SipoCinematicLightingSettings settings)
        {
            Object.DestroyImmediate(settings.layout); Object.DestroyImmediate(settings);
        }
        static GameObject[] EnvironmentRoots(Scene scene)
        {
            var roots = Objects<Transform>(scene).Select(t => t.gameObject).Where(o => PrefabUtility.IsAnyPrefabInstanceRoot(o) && Models.Contains(PrefabUtility.GetPrefabAssetPathOfNearestInstanceRoot(o))).ToArray();
            if (Models.Any(p => roots.Count(o => PrefabUtility.GetPrefabAssetPathOfNearestInstanceRoot(o) == p) != 1))
                throw new InvalidOperationException("Apply requires exactly one connected instance of each supermarket FBX in the active scene.");
            return roots;
        }
        static Transform CommonFrame(GameObject[] roots)
        {
            for (var parent = roots[0].transform.parent; parent != null; parent = parent.parent)
                if (roots.All(r => r.transform.IsChildOf(parent))) return parent;
            throw new InvalidOperationException("Both FBX instances must share their existing environment parent. The tool will not move geometry.");
        }
        static IEnumerable<T> Objects<T>(Scene scene) where T : Component => scene.GetRootGameObjects().SelectMany(r => r.GetComponentsInChildren<T>(true));
        static SipoCinematicLightingState FindState(Scene scene)
        {
            var states = Objects<SipoCinematicLightingState>(scene).ToArray();
            if (states.Length > 1) throw new InvalidOperationException("Multiple cinematic rigs found in this scene. Restore/remove only the unintended duplicate before applying.");
            return states.SingleOrDefault();
        }
        static SipoCinematicLightingState RequiredState(bool applied)
        {
            var state = FindState(SceneManager.GetActiveScene());
            if (state == null || (applied && !state.applied)) throw new InvalidOperationException("Apply cinematic lighting to this active scene first.");
            return state;
        }
        static void RequireEditMode()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode) throw new InvalidOperationException("Cinematic configuration commands run in Edit Mode only.");
        }
        static GameObject Child(string name, Transform parent)
        {
            var child = new GameObject(name); Undo.RegisterCreatedObjectUndo(child, "Create cinematic fixture");
            Undo.SetTransformParent(child.transform, parent, "Parent cinematic fixture");
            child.transform.localPosition = Vector3.zero; child.transform.localRotation = Quaternion.identity; child.transform.localScale = Vector3.one;
            return child;
        }
        static void RecordPrefab(Object obj) { if (PrefabUtility.IsPartOfPrefabInstance(obj)) PrefabUtility.RecordPrefabInstancePropertyModifications(obj); }
        static bool Finite(float value) => !float.IsNaN(value) && !float.IsInfinity(value);
        static Vector3 V(float[] a)
        {
            if (a == null || a.Length != 3 || a.Any(v => !Finite(v))) throw new InvalidDataException("Expected three finite layout coordinates.");
            return new Vector3(a[0], a[1], a[2]);
        }
        static Color C(float[] a) { var v = V(a); return new Color(v.x, v.y, v.z, 1); }
        sealed class AmbientSnapshot
        {
            public AmbientMode mode; public Color sky, equator, ground; public float intensity, reflections;
        }
        static AmbientSnapshot CaptureAmbient() => new AmbientSnapshot { mode = RenderSettings.ambientMode, sky = RenderSettings.ambientSkyColor, equator = RenderSettings.ambientEquatorColor, ground = RenderSettings.ambientGroundColor, intensity = RenderSettings.ambientIntensity, reflections = RenderSettings.reflectionIntensity };
        static void CopyAmbient(AmbientSnapshot source, SipoCinematicLightingState state)
        {
            state.ambientMode = source.mode; state.ambientSky = source.sky; state.ambientEquator = source.equator; state.ambientGround = source.ground; state.ambientIntensity = source.intensity; state.reflectionIntensity = source.reflections;
        }
        static void RestoreAmbient(SipoCinematicLightingState s) => RestoreAmbient(new AmbientSnapshot { mode = s.ambientMode, sky = s.ambientSky, equator = s.ambientEquator, ground = s.ambientGround, intensity = s.ambientIntensity, reflections = s.reflectionIntensity });
        static void RestoreAmbient(AmbientSnapshot s)
        {
            RenderSettings.ambientMode = s.mode; RenderSettings.ambientSkyColor = s.sky; RenderSettings.ambientEquatorColor = s.equator; RenderSettings.ambientGroundColor = s.ground; RenderSettings.ambientIntensity = s.intensity; RenderSettings.reflectionIntensity = s.reflections;
        }
    }
}
