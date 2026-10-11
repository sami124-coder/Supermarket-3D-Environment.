using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace Sipo.Editor
{
    [Serializable] public sealed class FreshProduceLightSpec
    {
        public string name, type;
        public float[] position, target, color;
        public float intensity, range, spotAngle;
        public bool shadow;
    }
    [Serializable] public sealed class FreshProduceReflectionSpec
    {
        public string name;
        public float[] position, center, size;
        public int resolution = 256;
    }
    [Serializable] public sealed class FreshProduceLibrarySpec
    {
        public string name;
        public string[] objectNames;
    }
    [Serializable] public sealed class FreshProduceLodSpec
    {
        public string name;
        public string[] lod0, lod1;
    }
    [Serializable] public sealed class FreshProduceSpec
    {
        public int schemaVersion;
        public string[] modelParts;
        public string libraryModel;
        public MaterialSpec[] materials;
        public BoundsSpec bounds;
        public float[] preferredPosition;
        public BoxSpec[] colliders;
        public FreshProduceLightSpec[] lights;
        public FreshProduceReflectionSpec[] reflections;
        public FreshProduceLibrarySpec[] libraryItems;
        public FreshProduceLodSpec[] lodGroups;
    }

    /// <summary>Installs only the new department. Does not rebuild the supermarket or configure gameplay.</summary>
    public static class SipoFreshProduceDepartment
    {
        const string Folder = "Assets/FreshProduce";
        const string DataPath = Folder + "/fresh-produce.json";
        const string PrefabPath = Folder + "/Prefabs/FreshProduceDepartment.prefab";
        const string Owner = "SIPO Fresh Produce v1";
        const string RootName = "SIPO | Premium Fresh Produce Department";
        const string ShaderName = "Universal Render Pipeline/Lit";

        static Vector3 V(float[] a) => new Vector3(a[0], a[1], a[2]);
        static Color C(float[] a) => new Color(a[0], a[1], a[2], 1);
        static string Safe(string s) => string.Concat(s.Select(c => char.IsLetterOrDigit(c) || c == '_' || c == '-' ? c : '_'));
        static bool Finite(float f) => !float.IsNaN(f) && !float.IsInfinity(f);
        static void Vector(float[] a, string context)
        {
            if (a == null || a.Length != 3 || a.Any(f => !Finite(f)))
                throw new InvalidDataException(context + " requires three finite values.");
        }
        static GameObject Child(string name, Transform parent)
        {
            var result = new GameObject(name); result.transform.SetParent(parent, false); return result;
        }
        static void RequireEditMode()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
                throw new InvalidOperationException("Fresh Produce installation and capture are available in Edit mode only.");
            if (PrefabStageUtility.GetCurrentPrefabStage() != null)
                throw new InvalidOperationException("Exit Prefab mode and open the intended supermarket scene first.");
        }
        static void RequireUrpRendering()
        {
            var pipeline = QualitySettings.renderPipeline != null ? QualitySettings.renderPipeline : GraphicsSettings.defaultRenderPipeline;
            if (!(pipeline is UniversalRenderPipelineAsset))
                throw new InvalidOperationException("The selected Quality level must use the existing SIPO URP pipeline. Select the correct URP asset first; Fresh Produce installation never replaces project pipeline settings.");
        }
        static FreshProduceSpec ReadSpec()
        {
            if (!File.Exists(DataPath)) throw new FileNotFoundException("Fresh Produce metadata is missing.", DataPath);
            var spec = JsonUtility.FromJson<FreshProduceSpec>(File.ReadAllText(DataPath));
            if (spec == null || spec.schemaVersion != 1 || spec.materials == null || spec.materials.Length == 0 ||
                spec.modelParts == null || spec.modelParts.Length == 0 || spec.bounds == null || spec.colliders == null ||
                spec.lights == null || spec.reflections == null)
                throw new InvalidDataException("Incomplete or unsupported Fresh Produce metadata.");
            Vector(spec.bounds.center, "Department bounds center"); Vector(spec.bounds.size, "Department bounds size");
            Vector(spec.preferredPosition, "Preferred placement");
            if (spec.bounds.size.Any(f => f <= 0)) throw new InvalidDataException("Department bounds must have positive size.");
            if (spec.materials.Any(m => m == null || string.IsNullOrWhiteSpace(m.name)) ||
                spec.materials.Select(m => m.name).Distinct(StringComparer.Ordinal).Count() != spec.materials.Length)
                throw new InvalidDataException("Material names must be present and unique.");
            foreach (var m in spec.materials)
            {
                Vector(m.color, m.name + " color"); Vector(m.emission, m.name + " emission");
                if (!Finite(m.roughness) || m.roughness < 0 || m.roughness > 1 || !Finite(m.metallic) ||
                    m.metallic < 0 || m.metallic > 1 || !Finite(m.emissionStrength) || m.emissionStrength < 0 ||
                    !Finite(m.alpha) || m.alpha < 0 || m.alpha > 1)
                    throw new InvalidDataException("Invalid material surface values: " + m.name);
            }
            foreach (string path in ModelPaths(spec))
                if (!path.StartsWith(Folder + "/Models/", StringComparison.Ordinal) || !path.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase) || !File.Exists(path))
                    throw new InvalidDataException("Fresh Produce model must exist under its own Models folder: " + path);
            foreach (var c in spec.colliders)
            {
                Vector(c.position, c.name + " position"); Vector(c.size, c.name + " size"); Vector(c.rotation, c.name + " rotation");
                if (c.size.Any(f => f <= 0)) throw new InvalidDataException("Invalid collider size: " + c.name);
            }
            if (spec.lights.Length > 7 || spec.lights.Count(l => l.shadow) > 1 || spec.lights.Any(l => l.shadow && l.type != "spot"))
                throw new InvalidDataException("Fresh Produce light budget is seven lights and one shadow-casting spotlight.");
            foreach (var l in spec.lights)
            {
                Vector(l.position, l.name + " position"); Vector(l.color, l.name + " color");
                if (l.type != "spot" && l.type != "point") throw new InvalidDataException("Unsupported light type: " + l.type);
                if (!Finite(l.intensity) || l.intensity < 0 || !Finite(l.range) || l.range <= 0)
                    throw new InvalidDataException("Invalid light intensity or range: " + l.name);
                if (l.type == "spot")
                {
                    Vector(l.target, l.name + " target");
                    if ((V(l.target) - V(l.position)).sqrMagnitude < .001f || !Finite(l.spotAngle) || l.spotAngle < 1 || l.spotAngle > 179)
                        throw new InvalidDataException("Invalid spotlight target/cone: " + l.name);
                }
            }
            if (spec.reflections.Length > 2) throw new InvalidDataException("Fresh Produce reflection budget is two probes.");
            foreach (var p in spec.reflections)
            {
                Vector(p.position, p.name + " position"); Vector(p.center, p.name + " center"); Vector(p.size, p.name + " size");
                if (p.size.Any(f => f <= 0) || (p.resolution != 128 && p.resolution != 256 && p.resolution != 512))
                    throw new InvalidDataException("Invalid reflection bounds/resolution: " + p.name);
            }
            return spec;
        }
        static string[] ModelPaths(FreshProduceSpec spec) => spec.modelParts.Concat(
            string.IsNullOrEmpty(spec.libraryModel) ? Array.Empty<string>() : new[] { spec.libraryModel }).Distinct().ToArray();
        static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            string parent = Path.GetDirectoryName(path).Replace('\\', '/'); EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
        }

        [MenuItem("Sipo/Install Fresh Produce Department", false, 200)]
        public static void Install()
        {
            RequireEditMode(); RequireUrpRendering(); var spec = ReadSpec(); var scene = SceneManager.GetActiveScene();
            if (!scene.IsValid() || !scene.isLoaded) throw new InvalidOperationException("Open a loaded scene before installation.");
            var existing = Instances(scene);
            if (existing.Count > 1) throw new InvalidOperationException("Multiple Fresh Produce prefab instances already exist. Installation stopped to avoid another duplicate.");
            if (existing.Count == 0 && scene.GetRootGameObjects().Any(o => o.name == RootName))
                throw new InvalidOperationException("An unpacked or disconnected Fresh Produce root already exists. Installation stopped to prevent a duplicate; preserve that customized root and reconnect or relocate it manually.");
            if (existing.Count == 1)
            {
                ValidateMaterials(spec, existing[0]); Frame(existing[0]);
                Debug.Log("SIPO_FRESH_PRODUCE_ALREADY_INSTALLED: existing instance preserved; no scene, material or prefab settings overwritten.", existing[0]);
                return;
            }
            var prefab = PreparePrefab(spec);
            var obstacles = SceneObstacles(scene, null);
            var localBounds = new Bounds(V(spec.bounds.center), V(spec.bounds.size));
            var preferred = V(spec.preferredPosition);
            var conflicts = Conflicts(localBounds, preferred, obstacles);
            Vector3 placement = preferred;
            if (conflicts.Count > 0)
            {
                // Conservative world AABB test intentionally prefers a safe staging position over moving original geometry.
                float maximumX = obstacles.Max(o => o.bounds.max.x);
                placement = new Vector3(maximumX + 4 - localBounds.min.x, 0, preferred.z);
                if (Conflicts(localBounds, placement, obstacles).Count != 0)
                    throw new InvalidOperationException("Could not find a conflict-free staging position. No scene objects changed.");
                Debug.LogWarning("SIPO_FRESH_PRODUCE_PLACEMENT_CONFLICT: preferred placement " + preferred +
                    " overlaps " + conflicts.Count + " existing renderer/collider bounds (" +
                    string.Join(", ", conflicts.Take(5).Select(o => o.name)) + "). Installing the self-contained module at safe staging position " +
                    placement + " outside the current scene geometry. No original objects are moved or removed. Use Frame Fresh Produce Department, then relocate the module after checking clearance; no player teleport/control changes are made.");
            }
            Undo.IncrementCurrentGroup(); int group = Undo.GetCurrentGroup(); Undo.SetCurrentGroupName("Install Fresh Produce Department");
            GameObject instance = null;
            try
            {
                instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab, scene);
                Undo.RegisterCreatedObjectUndo(instance, "Install Fresh Produce Department");
                instance.transform.position = placement;
                PrefabUtility.RecordPrefabInstancePropertyModifications(instance.transform);
                ValidateMaterials(spec, instance);
                ValidateInstalled(spec, instance, false);
                EditorSceneManager.MarkSceneDirty(scene); Frame(instance); Undo.CollapseUndoOperations(group);
                Debug.Log("SIPO_FRESH_PRODUCE_INSTALLED: editable connected prefab, collision floor/display boundaries, seven or fewer lights and two or fewer on-demand reflection probes. Original scene objects, materials, pipeline settings and player controls are unchanged. Capture Fresh Produce Reflections next, inspect the scene, then save it manually.", instance);
            }
            catch { Undo.RevertAllDownToGroup(group); throw; }
        }

        [MenuItem("Sipo/Build Fresh Produce Prefab Library", false, 201)]
        public static void BuildPrefabLibrary()
        {
            RequireEditMode(); var spec = ReadSpec(); PreparePrefab(spec);
            Debug.Log("SIPO_FRESH_PRODUCE_PREFABS_READY: " + PrefabPath + "; reusable products, plants and fixtures are in Assets/FreshProduce/Prefabs/Library. Existing prefab assets are preserved.");
        }
        static GameObject PreparePrefab(FreshProduceSpec spec)
        {
            EnsureFolder(Folder + "/Materials"); EnsureFolder(Folder + "/Prefabs/Library");
            var materials = LoadMaterials(spec, true); RemapModels(spec, materials);
            BuildLibrary(spec);
            var existing = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
            if (existing != null)
            {
                RequireOwned(PrefabPath); ValidateRendererMaterials(existing, materials);
                return existing; // Local manual prefab customizations are authoritative.
            }
            if (File.Exists(PrefabPath)) throw new InvalidOperationException("Unrecognized asset occupies " + PrefabPath);
            var preview = EditorSceneManager.NewPreviewScene();
            GameObject root = null;
            try
            {
                root = new GameObject(RootName); SceneManager.MoveGameObjectToScene(root, preview);
                var model = Child("Editable authored department", root.transform);
                foreach (string path in spec.modelParts)
                {
                    var instance = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(path), model.transform);
                    OrientModel(instance.transform);
                }
                foreach (var renderer in model.GetComponentsInChildren<MeshRenderer>(true))
                {
                    // Instanced library assets remain instanced; reflection eligibility does not force mesh duplication.
                    GameObjectUtility.SetStaticEditorFlags(renderer.gameObject, StaticEditorFlags.ReflectionProbeStatic);
                    renderer.reflectionProbeUsage = ReflectionProbeUsage.BlendProbes;
                }
                InstallLods(model.transform, spec);
                var collisions = Child("Walkable floor and display boundaries", root.transform);
                foreach (var c in spec.colliders)
                {
                    var go = Child(c.name, collisions.transform); go.transform.localPosition = V(c.position);
                    go.transform.localRotation = Quaternion.Euler(V(c.rotation)); go.AddComponent<BoxCollider>().size = V(c.size);
                }
                var lighting = Child("Department lighting | no global settings", root.transform);
                foreach (var l in spec.lights)
                {
                    var go = Child(l.name, lighting.transform); go.transform.localPosition = V(l.position);
                    var light = go.AddComponent<Light>(); light.type = l.type == "spot" ? LightType.Spot : LightType.Point;
                    if (l.type == "spot") go.transform.localRotation = Quaternion.LookRotation(V(l.target) - V(l.position));
                    light.color = C(l.color); light.intensity = l.intensity; light.range = l.range;
                    light.spotAngle = l.spotAngle; light.innerSpotAngle = l.spotAngle * .68f;
                    light.lightmapBakeType = LightmapBakeType.Realtime;
                    light.shadows = l.shadow ? LightShadows.Soft : LightShadows.None;
                    light.shadowBias = .035f; light.shadowNormalBias = .15f;
                }
                foreach (var p in spec.reflections)
                {
                    var go = Child(p.name, lighting.transform); go.transform.localPosition = V(p.position);
                    var probe = go.AddComponent<ReflectionProbe>(); probe.mode = ReflectionProbeMode.Baked;
                    probe.refreshMode = ReflectionProbeRefreshMode.ViaScripting; probe.hdr = true;
                    probe.boxProjection = true; probe.resolution = p.resolution; probe.size = V(p.size);
                    probe.center = V(p.center) - V(p.position); probe.importance = 4;
                    probe.blendDistance = 2; probe.nearClipPlane = .2f; probe.farClipPlane = 70;
                    probe.clearFlags = ReflectionProbeClearFlags.Skybox;
                }
                ValidateRendererMaterials(root, materials);
                var prefab = PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
                if (prefab == null) throw new IOException("Failed to create Fresh Produce prefab.");
                TagOwned(PrefabPath); AssetDatabase.SaveAssets(); return prefab;
            }
            finally { EditorSceneManager.ClosePreviewScene(preview); }
        }
        static void OrientModel(Transform model)
        {
            var anchors = model.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Anchor_", StringComparison.Ordinal)).ToDictionary(t => t.name);
            foreach (string name in new[] { "Anchor_Origin", "Anchor_Up", "Anchor_Back", "Anchor_Right" })
                if (!anchors.ContainsKey(name)) throw new InvalidDataException("Missing FBX coordinate anchor: " + model.name + "/" + name);
            var origin = anchors["Anchor_Origin"]; var up = anchors["Anchor_Up"]; var back = anchors["Anchor_Back"]; var right = anchors["Anchor_Right"];
            float scale = Vector3.Distance(up.position, origin.position);
            if (scale < .00001f) throw new InvalidDataException("Degenerate model anchors: " + model.name);
            model.rotation = Quaternion.Inverse(Quaternion.LookRotation((back.position - origin.position).normalized, (up.position - origin.position).normalized)) * model.rotation;
            model.localScale /= scale;
            if (Vector3.Dot((right.position - origin.position).normalized, Vector3.right) < 0)
                model.localScale = Vector3.Scale(model.localScale, new Vector3(-1, 1, 1));
            model.position -= origin.position;
        }
        static void InstallLods(Transform model, FreshProduceSpec spec)
        {
            if (spec.lodGroups == null) return;
            // Unity can synthesize LODGroups from the FBX _LOD0/_LOD1 names.
            // Replace only those components on this new preview-scene instance;
            // the source FBX and any installed/customized scene remain untouched.
            // Otherwise two groups can compete for the same renderers.
            foreach (var importedGroup in model.GetComponentsInChildren<LODGroup>(true))
                UnityEngine.Object.DestroyImmediate(importedGroup);
            var all = model.GetComponentsInChildren<Renderer>(true);
            var claimed = new HashSet<Renderer>();
            foreach (var group in spec.lodGroups)
            {
                var high = NamedRenderers(all, group.lod0); var low = NamedRenderers(all, group.lod1);
                if (high.Concat(low).Any(r => !claimed.Add(r))) throw new InvalidDataException("Renderer belongs to multiple LOD levels/groups: " + group.name);
                // Blender hides the alternate meshes only for source previews. LODGroup
                // must own visibility after Unity import, including originally hidden FBX nodes.
                foreach (var renderer in high.Concat(low))
                {
                    renderer.gameObject.SetActive(true);
                    renderer.enabled = true;
                }
                var owner = Child(group.name + " | LOD", model).AddComponent<LODGroup>();
                owner.SetLODs(new[] { new LOD(.14f, high), new LOD(.012f, low) });
                owner.fadeMode = LODFadeMode.None; owner.RecalculateBounds();
            }
        }
        static Renderer[] NamedRenderers(Renderer[] all, string[] names)
        {
            if (names == null || names.Length == 0) throw new InvalidDataException("LOD level has no renderer names.");
            return names.Select(name =>
            {
                var matches = all.Where(r => r.name == name).ToArray();
                if (matches.Length != 1) throw new InvalidDataException("Expected exactly one renderer for LOD object " + name);
                return matches[0];
            }).ToArray();
        }

        static Dictionary<string, Material> LoadMaterials(FreshProduceSpec spec, bool create)
        {
            var result = new Dictionary<string, Material>(StringComparer.Ordinal);
            foreach (var m in spec.materials)
            {
                string path = Folder + "/Materials/" + Safe(m.name) + ".mat";
                // Existing supermarket materials can be reused verbatim; never repair/reinitialize them here.
                var material = AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/" + Safe(m.name) + ".mat") ?? AssetDatabase.LoadAssetAtPath<Material>(path);
                if (material == null)
                {
                    if (!create) throw new FileNotFoundException("Missing Fresh Produce material: " + path);
                    var shader = Shader.Find(ShaderName);
                    if (shader == null) throw new InvalidOperationException("URP/Lit shader is unavailable. Install URP 17.3.0 before building the module.");
                    material = new Material(shader) { name = m.name, enableInstancing = true };
                    InitializeMaterial(material, m); AssetDatabase.CreateAsset(material, path); TagOwned(path);
                }
                SupermarketMaterialNames.RequireSlot(path, material.shader != null ? material.shader.name : null, true);
                result.Add(m.name, material);
            }
            return result;
        }
        static Texture2D Texture(string path, bool normal = false, bool color = false)
        {
            if (string.IsNullOrWhiteSpace(path)) return null;
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer == null) throw new FileNotFoundException("Missing Fresh Produce surface texture: " + path);
            // Existing shared project textures remain untouched. Authored new maps are explicitly imported in the right color space.
            if (path.StartsWith(Folder + "/", StringComparison.Ordinal))
            {
                var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                if (importer.textureType != type || importer.sRGBTexture != color || importer.alphaIsTransparency || !importer.mipmapEnabled ||
                    importer.alphaSource != TextureImporterAlphaSource.FromInput || importer.wrapMode != TextureWrapMode.Repeat || importer.anisoLevel != 4)
                {
                    importer.textureType = type; importer.sRGBTexture = color; importer.alphaIsTransparency = false;
                    importer.alphaSource = TextureImporterAlphaSource.FromInput; importer.mipmapEnabled = true;
                    importer.wrapMode = TextureWrapMode.Repeat; importer.anisoLevel = 4; importer.SaveAndReimport();
                }
            }
            var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            if (texture == null) throw new InvalidDataException("Fresh Produce texture did not import: " + path);
            return texture;
        }
        static void InitializeMaterial(Material material, MaterialSpec m)
        {
            Color color = C(m.color); color.a = m.transparent ? m.alpha : 1;
            material.SetColor("_BaseColor", color); material.SetFloat("_Surface", m.transparent ? 1 : 0);
            material.SetFloat("_SrcBlend", (float)(m.transparent ? BlendMode.SrcAlpha : BlendMode.One));
            material.SetFloat("_DstBlend", (float)(m.transparent ? BlendMode.OneMinusSrcAlpha : BlendMode.Zero));
            material.SetFloat("_ZWrite", m.transparent ? 0 : 1);
            if (m.transparent) material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            material.SetOverrideTag("RenderType", m.transparent ? "Transparent" : "Opaque");
            material.renderQueue = m.transparent ? (int)RenderQueue.Transparent : (int)RenderQueue.Geometry;
            material.SetShaderPassEnabled("ShadowCaster", !m.transparent);
            material.SetFloat("_Metallic", m.metallic);
            var baseMap = Texture(m.baseMap, color: true); var normal = Texture(m.normalMap, normal: true); var packed = Texture(m.metallicGlossMap);
            material.SetTexture("_BaseMap", baseMap); material.SetTexture("_BumpMap", normal); material.SetTexture("_MetallicGlossMap", packed);
            material.SetFloat("_BumpScale", m.normalScale); material.SetFloat("_Smoothness", packed != null ? 1 : 1 - m.roughness);
            material.SetFloat("_SmoothnessTextureChannel", 0); material.SetFloat("_SpecularHighlights", 1); material.SetFloat("_EnvironmentReflections", 1);
            material.DisableKeyword("_SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A");
            if (normal != null) material.EnableKeyword("_NORMALMAP");
            if (packed != null) material.EnableKeyword("_METALLICSPECGLOSSMAP");
            if (m.textureScale != null && m.textureScale.Length == 2)
                foreach (string property in new[] { "_BaseMap", "_BumpMap", "_MetallicGlossMap" })
                    material.SetTextureScale(property, new Vector2(m.textureScale[0], m.textureScale[1]));
            material.SetColor("_EmissionColor", C(m.emission) * m.emissionStrength);
            if (m.emissionStrength > 0) material.EnableKeyword("_EMISSION");
            material.globalIlluminationFlags = MaterialGlobalIlluminationFlags.BakedEmissive;
        }
        static string[] SourceNames(ModelImporter importer)
        {
            var sources = new SerializedObject(importer).FindProperty("m_Materials");
            if (sources == null || !sources.isArray || sources.arraySize == 0)
                throw new InvalidDataException("No source material identifiers in " + importer.assetPath);
            var names = new string[sources.arraySize];
            for (int i = 0; i < names.Length; i++)
            {
                var value = sources.GetArrayElementAtIndex(i).FindPropertyRelative("name");
                if (value == null || string.IsNullOrEmpty(value.stringValue)) throw new InvalidDataException("Invalid source material identifier in " + importer.assetPath);
                names[i] = value.stringValue;
            }
            return names;
        }
        static void RemapModels(FreshProduceSpec spec, Dictionary<string, Material> materials)
        {
            var paths = ModelPaths(spec); var resolver = new SupermarketMaterialNames(materials.Keys, paths);
            var snapshots = materials.Values.Distinct().ToDictionary(m => m, EditorJsonUtility.ToJson);
            var sourceNames = new Dictionary<string, string[]>();
            foreach (string path in paths)
            {
                var importer = AssetImporter.GetAtPath(path) as ModelImporter;
                if (importer == null) throw new FileNotFoundException("Fresh Produce model importer is missing: " + path);
                if (importer.materialImportMode != ModelImporterMaterialImportMode.ImportStandard || importer.materialLocation != ModelImporterMaterialLocation.InPrefab)
                {
                    importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
                    importer.materialLocation = ModelImporterMaterialLocation.InPrefab; importer.SaveAndReimport();
                }
                sourceNames[path] = SourceNames(importer);
                foreach (string name in sourceNames[path]) resolver.Resolve(name); // All parts must resolve before any remap table writes.
            }
            foreach (string path in paths)
            {
                var importer = (ModelImporter)AssetImporter.GetAtPath(path);
                foreach (string name in sourceNames[path])
                    importer.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), name), materials[resolver.Resolve(name)]);
                importer.SaveAndReimport();
            }
            foreach (var pair in snapshots)
                if (EditorJsonUtility.ToJson(pair.Key) != pair.Value) throw new InvalidDataException("Material changed during import: " + pair.Key.name);
            ValidateModels(spec, materials);
        }
        static void ValidateModels(FreshProduceSpec spec, Dictionary<string, Material> materials)
        {
            var paths = ModelPaths(spec); var resolver = new SupermarketMaterialNames(materials.Keys, paths);
            foreach (string path in paths)
            {
                var importer = AssetImporter.GetAtPath(path) as ModelImporter;
                if (importer == null) throw new FileNotFoundException("Missing model importer: " + path);
                var remaps = importer.GetExternalObjectMap();
                foreach (string name in SourceNames(importer))
                {
                    var expected = materials[resolver.Resolve(name)];
                    if (!remaps.TryGetValue(new AssetImporter.SourceAssetIdentifier(typeof(Material), name), out var actual) || actual != expected)
                        throw new InvalidDataException(path + ": unmapped or incorrect source material '" + name + "'. Use Build Fresh Produce Prefab Library.");
                }
                var asset = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (asset == null) throw new InvalidDataException("Missing imported model: " + path);
                ValidateRendererMaterials(asset, materials);
            }
        }
        static void ValidateRendererMaterials(GameObject root, Dictionary<string, Material> materials)
        {
            var known = new HashSet<Material>(materials.Values); var renderers = root.GetComponentsInChildren<MeshRenderer>(true);
            if (renderers.Length == 0) throw new InvalidDataException("No mesh renderers in " + root.name);
            foreach (var renderer in renderers)
            {
                var filter = renderer.GetComponent<MeshFilter>();
                if (filter == null || filter.sharedMesh == null || renderer.sharedMaterials.Length != filter.sharedMesh.subMeshCount)
                    throw new InvalidDataException("Missing mesh or submesh/material slot mismatch: " + renderer.name);
                foreach (var material in renderer.sharedMaterials)
                    SupermarketMaterialNames.RequireSlot(root.name + "/" + renderer.name,
                        material != null && material.shader != null ? material.shader.name : null, material != null && known.Contains(material));
            }
        }
        static void ValidateMaterials(FreshProduceSpec spec, GameObject root)
        {
            var materials = LoadMaterials(spec, false); ValidateModels(spec, materials); ValidateRendererMaterials(root, materials);
        }
        static void BuildLibrary(FreshProduceSpec spec)
        {
            if (spec.libraryItems == null || spec.libraryItems.Length == 0) return;
            if (string.IsNullOrEmpty(spec.libraryModel)) throw new InvalidDataException("Library items require a library FBX.");
            var preview = EditorSceneManager.NewPreviewScene();
            try
            {
                var source = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(spec.libraryModel), preview);
                OrientModel(source.transform);
                foreach (var item in spec.libraryItems)
                {
                    string path = Folder + "/Prefabs/Library/" + Safe(item.name) + ".prefab";
                    if (AssetDatabase.LoadAssetAtPath<GameObject>(path) != null) { RequireOwned(path); continue; }
                    var asset = new GameObject(item.name); SceneManager.MoveGameObjectToScene(asset, preview);
                    try
                    {
                        foreach (string name in item.objectNames)
                        {
                            var objects = source.GetComponentsInChildren<Transform>(true).Where(t => t.name == name).ToArray();
                            if (objects.Length != 1) throw new InvalidDataException("Library item must name exactly one authored object: " + name);
                            var original = objects[0]; var clone = UnityEngine.Object.Instantiate(original.gameObject, asset.transform);
                            clone.name = original.name;
                            // Preserve anchor-corrected handedness as well as rotation/scale.
                            var matrix = original.localToWorldMatrix;
                            Vector3 x = matrix.GetColumn(0), y = matrix.GetColumn(1), z = matrix.GetColumn(2);
                            float sign = Vector3.Dot(Vector3.Cross(x, y), z) < 0 ? -1 : 1;
                            clone.transform.SetPositionAndRotation(matrix.GetColumn(3), Quaternion.LookRotation(z.normalized, y.normalized));
                            clone.transform.localScale = new Vector3(x.magnitude * sign, y.magnitude, z.magnitude);
                        }
                        var renderers = asset.GetComponentsInChildren<Renderer>(true);
                        if (renderers.Length == 0) throw new InvalidDataException("Empty reusable library item: " + item.name);
                        var bounds = renderers[0].bounds; foreach (var r in renderers.Skip(1)) bounds.Encapsulate(r.bounds);
                        Vector3 pivot = new Vector3(bounds.center.x, bounds.min.y, bounds.center.z);
                        foreach (Transform child in asset.transform) child.localPosition -= pivot;
                        if (PrefabUtility.SaveAsPrefabAsset(asset, path) == null) throw new IOException("Failed to create reusable prefab " + path);
                        TagOwned(path);
                    }
                    finally { UnityEngine.Object.DestroyImmediate(asset); }
                }
            }
            finally { EditorSceneManager.ClosePreviewScene(preview); }
        }
        static void TagOwned(string path)
        {
            var importer = AssetImporter.GetAtPath(path);
            if (importer == null) throw new InvalidDataException("Missing asset importer: " + path);
            importer.userData = Owner; AssetDatabase.WriteImportSettingsIfDirty(path);
        }
        static void RequireOwned(string path)
        {
            string ownership = AssetImporter.GetAtPath(path)?.userData;
            if (ownership != Owner && (ownership == null || !ownership.StartsWith(Owner + "|", StringComparison.Ordinal)))
                throw new InvalidOperationException("Refusing to overwrite or assume ownership of an unrelated asset: " + path);
        }
        static List<GameObject> Instances(Scene scene) => scene.GetRootGameObjects()
            .SelectMany(o => o.GetComponentsInChildren<Transform>(true)).Select(t => t.gameObject)
            .Where(o => PrefabUtility.IsAnyPrefabInstanceRoot(o) && PrefabUtility.GetPrefabAssetPathOfNearestInstanceRoot(o) == PrefabPath).ToList();
        static GameObject RequiredInstance()
        {
            var instances = Instances(SceneManager.GetActiveScene());
            if (instances.Count != 1) throw new InvalidOperationException("Expected one Fresh Produce Department prefab in the active scene; found " + instances.Count + ". Install the module or select the appropriate scene.");
            return instances[0];
        }
        struct Obstacle { public string name; public Bounds bounds; }
        static List<Obstacle> SceneObstacles(Scene scene, GameObject except)
        {
            var result = new List<Obstacle>();
            foreach (var root in scene.GetRootGameObjects())
            {
                foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true))
                    if (r.enabled && r.gameObject.activeInHierarchy && (except == null || !r.transform.IsChildOf(except.transform)))
                        result.Add(new Obstacle { name = r.name, bounds = r.bounds });
                foreach (var c in root.GetComponentsInChildren<Collider>(true))
                    if (c.enabled && c.gameObject.activeInHierarchy && !c.isTrigger && (except == null || !c.transform.IsChildOf(except.transform)))
                        result.Add(new Obstacle { name = c.name, bounds = c.bounds });
            }
            return result;
        }
        static List<Obstacle> Conflicts(Bounds localBounds, Vector3 position, List<Obstacle> obstacles)
        {
            var volume = new Bounds(localBounds.center + position, localBounds.size);
            volume.Expand(.1f); return obstacles.Where(o => volume.Intersects(o.bounds)).ToList();
        }
        [MenuItem("Sipo/Frame Fresh Produce Department", false, 202)]
        public static void FrameDepartment() { RequireEditMode(); Frame(RequiredInstance()); }
        static void Frame(GameObject root)
        {
            Selection.activeGameObject = root;
            var view = SceneView.lastActiveSceneView;
            if (view != null) { view.FrameSelected(); view.Focus(); }
        }
        [MenuItem("Sipo/Validate Fresh Produce Department", false, 204)]
        public static void Validate()
        {
            RequireEditMode(); RequireUrpRendering(); var spec = ReadSpec(); var root = RequiredInstance();
            ValidateMaterials(spec, root); ValidateInstalled(spec, root, true);
            Debug.Log("SIPO_FRESH_PRODUCE_VALIDATED: both FBX importer maps, all active/inactive material slots, URP/Lit shaders, colliders, LODs, light budget, HDR reflection captures and placement checked. This validates configuration; visually inspect the scene in the licensed Unity Editor.", root);
        }
        static void ValidateInstalled(FreshProduceSpec spec, GameObject root, bool requireCaptures)
        {
            var lights = root.GetComponentsInChildren<Light>(true);
            if (lights.Length != spec.lights.Length || lights.Count(l => l.shadows != LightShadows.None) > 1)
                throw new InvalidDataException("Fresh Produce light count/shadow budget differs from metadata.");
            if (root.GetComponentsInChildren<BoxCollider>(true).Length != spec.colliders.Length)
                throw new InvalidDataException("Fresh Produce collision boundaries are missing or duplicated.");
            var lodGroups = root.GetComponentsInChildren<LODGroup>(true);
            if (lodGroups.Length != (spec.lodGroups?.Length ?? 0))
                throw new InvalidDataException("Fresh Produce LOD groups are missing or duplicated.");
            var lodRenderers = root.GetComponentsInChildren<Renderer>(true);
            foreach (var authored in spec.lodGroups ?? Array.Empty<FreshProduceLodSpec>())
            {
                string name = authored.name + " | LOD";
                var matches = lodGroups.Where(g => g.name == name).ToArray();
                if (matches.Length != 1)
                    throw new InvalidDataException("Expected exactly one authored Fresh Produce LOD group: " + name);
                var group = matches[0];
                if (!group.enabled || !group.gameObject.activeInHierarchy)
                    throw new InvalidDataException("Fresh Produce LOD group is disabled or inactive: " + name);
                var levels = group.GetLODs();
                if (levels.Length != 2)
                    throw new InvalidDataException("Fresh Produce LOD group must retain its high and low levels: " + name);
                var expectedLevels = new[] { NamedRenderers(lodRenderers, authored.lod0), NamedRenderers(lodRenderers, authored.lod1) };
                for (int i = 0; i < levels.Length; i++)
                {
                    var assigned = levels[i].renderers;
                    var expected = expectedLevels[i];
                    if (assigned == null || assigned.Length != expected.Length || !new HashSet<Renderer>(expected).SetEquals(assigned))
                        throw new InvalidDataException("Fresh Produce LOD renderer assignments differ from the authored level: " + name + " / " + i);
                    // LODGroup controls render-time visibility. Check hierarchy activity,
                    // never Renderer.enabled or isVisible, which can reflect the current LOD.
                    if (expected.Any(r => !r.gameObject.activeInHierarchy))
                        throw new InvalidDataException("Fresh Produce LOD mesh GameObject is inactive: " + name + " / " + i);
                }
            }
            var probes = root.GetComponentsInChildren<ReflectionProbe>(true);
            if (probes.Length != spec.reflections.Length) throw new InvalidDataException("Fresh Produce reflection probe count differs from metadata.");
            foreach (var probe in probes)
            {
                if (!probe.hdr || !probe.boxProjection || probe.mode == ReflectionProbeMode.Realtime)
                    throw new InvalidDataException("Fresh Produce probe requires HDR, box projection and on-demand capture: " + probe.name);
                if (requireCaptures && (probe.mode != ReflectionProbeMode.Custom || probe.customBakedTexture == null || probe.customBakedTexture.dimension != TextureDimension.Cube))
                    throw new InvalidOperationException("Fresh Produce reflections have not been captured. Run Sipo > Capture Fresh Produce Reflections first.");
                if (requireCaptures && AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(probe.customBakedTexture))?.userData != Owner + "|" + CaptureFingerprint(root))
                    throw new InvalidOperationException("Fresh Produce reflection capture is stale after relocation or local light changes. Recapture Fresh Produce Reflections.");
            }
            // Rotation/scale are permitted for manual placement; use the transformed eight corners of the metadata volume.
            var b = new Bounds(V(spec.bounds.center), V(spec.bounds.size));
            var world = new Bounds(root.transform.TransformPoint(b.min), Vector3.zero);
            foreach (int x in new[] { 0, 1 }) foreach (int y in new[] { 0, 1 }) foreach (int z in new[] { 0, 1 })
                world.Encapsulate(root.transform.TransformPoint(new Vector3(x == 0 ? b.min.x : b.max.x, y == 0 ? b.min.y : b.max.y, z == 0 ? b.min.z : b.max.z)));
            var permitted = world; permitted.Expand(.2f);
            foreach (var renderer in root.GetComponentsInChildren<MeshRenderer>(true))
                if (!permitted.Contains(renderer.bounds.min) || !permitted.Contains(renderer.bounds.max))
                    throw new InvalidDataException("Authored geometry exceeds declared department bounds: " + renderer.name + ". Update module bounds before relying on placement safety.");
            var conflicts = SceneObstacles(root.scene, root).Where(o => world.Intersects(o.bounds)).ToList();
            if (conflicts.Count > 0) throw new InvalidOperationException("Fresh Produce placement overlaps " + conflicts.Count +
                " existing renderer/collider bounds. Move the module to clear space; original geometry must not be deleted automatically. First overlaps: " + string.Join(", ", conflicts.Take(5).Select(o => o.name)));
        }
        [MenuItem("Sipo/Capture Fresh Produce Reflections", false, 203)]
        public static void CaptureReflections()
        {
            RequireEditMode(); RequireUrpRendering(); var root = RequiredInstance(); var spec = ReadSpec();
            ValidateMaterials(spec, root); ValidateInstalled(spec, root, false);
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null)
                throw new InvalidOperationException("Reflection capture requires a licensed Unity Editor with an active graphics device.");
            if (string.IsNullOrEmpty(root.scene.path)) throw new InvalidOperationException("Save the scene under a unique name before capturing scene-specific reflection textures.");
            string folder = Folder + "/Reflections/" + AssetDatabase.AssetPathToGUID(root.scene.path);
            EnsureFolder(folder); var probes = root.GetComponentsInChildren<ReflectionProbe>(true);
            try
            {
                for (int i = 0; i < probes.Length; i++)
                {
                    var probe = probes[i]; string path = folder + "/FreshProduce-" + i.ToString("00") + ".exr";
                    if (File.Exists(path)) RequireOwned(path);
                    EditorUtility.DisplayProgressBar("Fresh Produce HDR reflections", probe.name, (float)i / probes.Length);
                    Undo.RecordObject(probe, "Capture Fresh Produce reflections"); var oldMode = probe.mode;
                    try
                    {
                        probe.mode = ReflectionProbeMode.Baked;
                        if (!Lightmapping.BakeReflectionProbe(probe, path)) throw new InvalidOperationException("Reflection capture failed: " + probe.name);
                        AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
                        var importer = AssetImporter.GetAtPath(path) as TextureImporter;
                        if (importer == null) throw new InvalidDataException("Missing reflection texture importer: " + path);
                        importer.userData = Owner + "|" + CaptureFingerprint(root); importer.textureShape = TextureImporterShape.TextureCube;
                        importer.generateCubemap = TextureImporterGenerateCubemap.AutoCubemap; importer.sRGBTexture = false;
                        importer.mipmapEnabled = true; importer.textureCompression = TextureImporterCompression.Uncompressed; importer.SaveAndReimport();
                        var texture = AssetDatabase.LoadAssetAtPath<Texture>(path);
                        if (texture == null || texture.dimension != TextureDimension.Cube) throw new InvalidDataException("Reflection did not import as an HDR cubemap: " + path);
                        probe.customBakedTexture = texture; probe.mode = ReflectionProbeMode.Custom;
                        PrefabUtility.RecordPrefabInstancePropertyModifications(probe); EditorUtility.SetDirty(probe);
                    }
                    catch { probe.mode = oldMode; throw; }
                }
                EditorSceneManager.MarkSceneDirty(root.scene); AssetDatabase.SaveAssets();
                ValidateInstalled(spec, root, true);
                Debug.Log("SIPO_FRESH_PRODUCE_REFLECTIONS_CAPTURED: persistent scene-specific HDR cubemaps captured once. Recapture after relocating the module or changing nearby lighting/geometry. Save the scene manually.", root);
            }
            finally { EditorUtility.ClearProgressBar(); }
        }
        static string CaptureFingerprint(GameObject root)
        {
            // Persist a stable placement/local-light signature across scene reloads. Nearby scene edits still require manual recapture.
            var data = new StringBuilder();
            Action<float> number = f => data.Append(f.ToString("F5", CultureInfo.InvariantCulture)).Append(';');
            Action<Transform> transform = t => { var matrix = t.localToWorldMatrix; for (int i = 0; i < 16; i++) number(matrix[i]); };
            transform(root.transform);
            foreach (var light in root.GetComponentsInChildren<Light>(true))
            {
                data.Append(light.name).Append(light.enabled).Append(light.gameObject.activeInHierarchy); transform(light.transform);
                number(light.intensity); number(light.range); number(light.spotAngle); number(light.innerSpotAngle);
                number(light.color.r); number(light.color.g); number(light.color.b);
            }
            foreach (var probe in root.GetComponentsInChildren<ReflectionProbe>(true))
            {
                data.Append(probe.name); transform(probe.transform);
                number(probe.center.x); number(probe.center.y); number(probe.center.z);
                number(probe.size.x); number(probe.size.y); number(probe.size.z); number(probe.resolution);
            }
            using (var hash = SHA256.Create())
                return BitConverter.ToString(hash.ComputeHash(Encoding.UTF8.GetBytes(data.ToString()))).Replace("-", "");
        }
    }
}
