using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace Sipo.Editor
{
    [Serializable] public class MaterialSpec
    {
        public string name, baseMap, normalMap, metallicGlossMap;
        public float[] color, emission, textureScale;
        public float roughness, metallic, emissionStrength, alpha, normalScale=1;
        public bool transparent;
    }
    [Serializable] public class BoundsSpec { public float[] center, size; }
    [Serializable] public class LightSpec { public string name, type; public float[] position, rotation, color; public float intensity, range, spotAngle; }
    [Serializable] public class BoxSpec { public string name; public float[] position, size, rotation; }
    [Serializable] public class ViewSpec { public string name, description; public float[] position; public float yaw, pitch; }
    [Serializable] public class DepartmentSpec { public string name; public float[] position, size, color; }
    [Serializable] public class SceneSpec
    {
        public int schemaVersion;
        public MaterialSpec[] materials;
        public LightSpec[] lights;
        public BoxSpec[] colliders;
        public ViewSpec spawn;
        public ViewSpec[] viewpoints;
        public DepartmentSpec[] departments;
        public BoundsSpec environmentBounds;
        public string[] modelParts;
    }

    // Executed directly by the offline FBX material regression check as well.
    internal sealed class SupermarketMaterialNames
    {
        public const string ShaderName="Universal Render Pipeline/Lit";
        readonly HashSet<string> names;
        readonly string[] prefixes;
        public SupermarketMaterialNames(IEnumerable<string> materialNames,IEnumerable<string> modelPaths)
        {
            names=new HashSet<string>(materialNames,StringComparer.Ordinal);
            prefixes=modelPaths.Select(p=>Path.GetFileNameWithoutExtension(p)+"-").Distinct().ToArray();
        }
        public string Resolve(string importedName)
        {
            if(importedName!=null && names.Contains(importedName))return importedName;
            if(importedName!=null)
                foreach(string prefix in prefixes)
                    if(importedName.StartsWith(prefix,StringComparison.Ordinal))
                    {
                        string candidate=importedName.Substring(prefix.Length);
                        if(names.Contains(candidate))return candidate;
                    }
            throw new InvalidDataException("Unmapped supermarket material: '"+(importedName??"<null>")+"'.");
        }
        public static void RequireSlot(string context,string shaderName,bool expectedAsset)
        {
            if(!expectedAsset || shaderName!=ShaderName)
                throw new InvalidDataException(context+": expected the mapped Assets/Materials URP/Lit asset; shader='"+
                    (shaderName??"<missing>")+"', expected asset="+expectedAsset+".");
        }
    }

    /// <summary>Assembles the authored FBX, physical boundaries, lighting and player into an editable scene.</summary>
    [InitializeOnLoad]
    public static class SupermarketProject
    {
        const string ModelPath = "Assets/Environment/SipoSupermarket.fbx";
        const string MerchandisePath = "Assets/Environment/SipoMerchandise.fbx";
        const string DataPath = "Assets/Environment/scene-data.json";
        const string ScenePath = "Assets/Scenes/SipoSupermarket.unity";
        const string Marker = "Assets/Settings/scene-ready.json";
        static bool building;

        static SupermarketProject() { EditorApplication.delayCall += FirstImport; }
        static void FirstImport()
        {
            if (Application.isBatchMode || building || File.Exists(Marker) || File.Exists(ScenePath)) return;
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            { EditorApplication.delayCall += FirstImport; return; }
            if (!File.Exists(DataPath) || AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath) == null) return;
            if (SceneManager.GetActiveScene().isDirty) return;
            try { BuildScene(); }
            catch (Exception e) { Debug.LogException(e); }
        }
        static Vector3 V(float[] a) => a != null && a.Length == 3 ? new Vector3(a[0],a[1],a[2]) : Vector3.zero;
        static Color C(float[] a) => a != null && a.Length >= 3 ? new Color(a[0],a[1],a[2],1) : Color.white;
        static string Safe(string s) => string.Concat(s.Select(c => char.IsLetterOrDigit(c) || c == '_' || c == '-' ? c : '_'));
        static GameObject Child(string name, Transform parent)
        { var o=new GameObject(name); o.transform.SetParent(parent,false); return o; }

        [MenuItem("Sipo/Build supermarket scene")]
        public static void BuildScene()
        {
            if (building) return;
            if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            building=true;
            try
            {
                Directory.CreateDirectory("Assets/Settings");
                Directory.CreateDirectory("Assets/Materials");
                Directory.CreateDirectory("Assets/Scenes");
                AssetDatabase.Refresh();
                var spec=JsonUtility.FromJson<SceneSpec>(File.ReadAllText(DataPath));
                if (spec == null || spec.schemaVersion != 1 || spec.materials == null || spec.colliders == null)
                    throw new InvalidDataException("Unsupported or incomplete supermarket scene data.");
                var parts=ModelParts(spec);
                var mats=LoadMaterials(spec,true);
                // Retain the existing mesh import setup; remap BOTH parts before instantiation.
                foreach(var path in parts)
                {
                    var importer=AssetImporter.GetAtPath(path) as ModelImporter;
                    if(importer==null)throw new FileNotFoundException("Import every authored FBX part before building: "+path);
                    importer.globalScale=1;importer.useFileScale=true;importer.bakeAxisConversion=true;
                    importer.importCameras=false;importer.importLights=false;importer.importAnimation=false;
                    importer.addCollider=false;importer.isReadable=false;
                    importer.SaveAndReimport();
                }
                RemapModelMaterials(parts,mats);
                ConfigurePipeline();
                var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
                var root=new GameObject("SIPO | A little joy in every aisle");
                var model=Child("Complete premium retail environment",root.transform);
                foreach(var path in parts)
                {
                    var source=AssetDatabase.LoadAssetAtPath<GameObject>(path);
                    if(source==null)throw new InvalidDataException("Environment part did not import: "+path);
                    var instance=(GameObject)PrefabUtility.InstantiatePrefab(source,model.transform);
                    instance.name=Path.GetFileNameWithoutExtension(path);
                    OrientModel(instance.transform);
                }
                foreach(var renderer in model.GetComponentsInChildren<MeshRenderer>(true))
                    GameObjectUtility.SetStaticEditorFlags(renderer.gameObject,StaticEditorFlags.BatchingStatic|StaticEditorFlags.ReflectionProbeStatic);
                var boundaries=Child("Walkable floors, shelves and safety rails",root.transform);
                foreach (var s in spec.colliders)
                {
                    var o=Child(s.name,boundaries.transform); o.transform.localPosition=V(s.position);
                    o.transform.localRotation=Quaternion.Euler(V(s.rotation));
                    o.AddComponent<BoxCollider>().size=V(s.size); o.isStatic=true;
                }
                var lighting=Child("Warm architectural lighting",root.transform);
                int shadowLights=0;
                foreach (var s in spec.lights)
                {
                    var o=Child(s.name,lighting.transform);o.transform.position=V(s.position);
                    o.transform.rotation=Quaternion.Euler(V(s.rotation));
                    var l=o.AddComponent<Light>();l.type=s.type=="spot"?LightType.Spot:LightType.Point;
                    l.color=C(s.color);l.intensity=s.intensity*2;l.range=s.range;l.spotAngle=s.spotAngle;
                    l.bounceIntensity=1.4f;
                    l.shadows=s.name.Contains("Atrium") && shadowLights++<4?LightShadows.Soft:LightShadows.None;
                    l.shadowBias=.035f;l.shadowNormalBias=.2f;
                }
                RenderSettings.ambientMode=AmbientMode.Trilight;
                RenderSettings.ambientSkyColor=new Color(.30f,.37f,.51f);
                RenderSettings.ambientEquatorColor=new Color(.25f,.22f,.18f);
                RenderSettings.ambientGroundColor=new Color(.09f,.12f,.18f);
                RenderSettings.ambientIntensity=1;
                RenderSettings.fog=false;
                RenderSettings.reflectionIntensity=1;
                var sun=Child("Soft exterior fill",lighting.transform).AddComponent<Light>();
                sun.type=LightType.Directional;sun.color=new Color(1,.86f,.69f);sun.intensity=.45f;
                sun.transform.rotation=Quaternion.Euler(65,-35,0);sun.shadows=LightShadows.Soft;RenderSettings.sun=sun;
                ConfigureReflections(lighting.transform,spec.environmentBounds);
                ConfigureVolume(lighting.transform);
                var player=SupermarketPlayerFactory.Create(root.transform,V(spec.spawn.position),spec.spawn.yaw);
                var camera=player.GetComponentInChildren<Camera>();
                camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.09f,.15f,.25f);
                var additional=camera.GetUniversalAdditionalCameraData();additional.renderPostProcessing=true;
                additional.antialiasing=AntialiasingMode.SubpixelMorphologicalAntiAliasing;
                additional.antialiasingQuality=AntialiasingQuality.High;
                camera.allowHDR=true;
                player.GetComponent<SipoExplorer>().Configure(camera.transform,V(spec.spawn.position),spec.spawn.yaw,
                    spec.viewpoints.Select(v=>new SipoViewpoint {label=v.name,description=v.description,position=V(v.position),yaw=v.yaw,pitch=v.pitch}).ToArray(),
                    spec.departments.Select(d=>new SipoDepartmentZone {label=d.name,description="Discover something lovely.",bounds=new Bounds(V(d.position)+Vector3.up*2,V(d.size))}).ToArray());
                EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene(ScenePath,true)};
                PlayerSettings.companyName="Sipo";PlayerSettings.productName="Sipo Supermarket";
                PlayerSettings.colorSpace=ColorSpace.Linear;
                PlayerSettings.defaultScreenWidth=1600;PlayerSettings.defaultScreenHeight=1000;
                PlayerSettings.fullScreenMode=FullScreenMode.FullScreenWindow;
                QualitySettings.vSyncCount=1;
                ValidateScene(); // Do not overwrite the generated scene with an invalid mapping.
                if(!EditorSceneManager.SaveScene(scene,ScenePath))throw new IOException("Could not save "+ScenePath);
                AssetDatabase.SaveAssets();
                File.WriteAllText(Marker,"{\"schemaVersion\":1,\"scene\":\""+ScenePath+"\"}\n");
                AssetDatabase.Refresh();
                Debug.Log("SIPO_SCENE_READY: " + ScenePath);
                if (SceneView.lastActiveSceneView != null)
                    SceneView.lastActiveSceneView.LookAt(new Vector3(0,5,0),Quaternion.Euler(12,180,0),24);
            }
            finally { building=false; }
        }

        static SceneSpec ReadMaterialSpec()
        {
            var spec=JsonUtility.FromJson<SceneSpec>(File.ReadAllText(DataPath));
            if(spec==null || spec.schemaVersion!=1 || spec.materials==null)
                throw new InvalidDataException("Unsupported or incomplete supermarket material data.");
            return spec;
        }
        static string[] ModelParts(SceneSpec spec)
        {
            var parts=spec.modelParts!=null && spec.modelParts.Length>0
                ? spec.modelParts : new[]{ModelPath,MerchandisePath};
            if(!parts.Contains(ModelPath) || !parts.Contains(MerchandisePath) || parts.Distinct().Count()!=parts.Length)
                throw new InvalidDataException("Scene metadata must list both environment FBX parts exactly once. Update scene-data.json from the complete project.");
            return parts;
        }

        static Dictionary<string,Material> LoadMaterials(SceneSpec spec,bool createMissing)
        {
            var result=new Dictionary<string,Material>(StringComparer.Ordinal);
            foreach(var m in spec.materials)
            {
                string path="Assets/Materials/"+Safe(m.name)+".mat";
                var material=AssetDatabase.LoadAssetAtPath<Material>(path);
                if(material==null)
                {
                    if(!createMissing)throw new FileNotFoundException("Missing URP material: "+path+". Back up your scene, then use Sipo > Build supermarket scene to generate missing assets.");
                    var shader=Shader.Find(SupermarketMaterialNames.ShaderName);
                    if(shader==null)throw new InvalidOperationException("Universal Render Pipeline/Lit shader is unavailable.");
                    material=new Material(shader) {name=m.name,enableInstancing=true};
                    InitializeNewMaterial(material,m);
                    AssetDatabase.CreateAsset(material,path);
                }
                // Existing URP assets are authoritative: do not change properties, keywords, or names.
                SupermarketMaterialNames.RequireSlot(path,material.shader!=null?material.shader.name:null,true);
                result.Add(m.name,material);
            }
            return result;
        }
        static void InitializeNewMaterial(Material material,MaterialSpec m)
        {
            Color baseColor=C(m.color);baseColor.a=m.transparent?m.alpha:1;
            material.SetColor("_BaseColor",baseColor);
            material.SetFloat("_Surface",m.transparent?1:0);
            material.SetFloat("_SrcBlend",(float)(m.transparent?BlendMode.SrcAlpha:BlendMode.One));
            material.SetFloat("_DstBlend",(float)(m.transparent?BlendMode.OneMinusSrcAlpha:BlendMode.Zero));
            material.SetFloat("_ZWrite",m.transparent?0:1);
            if(m.transparent)material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");else material.DisableKeyword("_SURFACE_TYPE_TRANSPARENT");
            material.SetOverrideTag("RenderType",m.transparent?"Transparent":"Opaque");
            material.renderQueue=m.transparent?(int)RenderQueue.Transparent:(int)RenderQueue.Geometry;
            material.SetShaderPassEnabled("ShadowCaster",!m.transparent);
            material.SetFloat("_Metallic",m.metallic);
            ApplySurfaceMaps(material,m);
            material.SetColor("_EmissionColor",C(m.emission)*m.emissionStrength);
            if (m.emissionStrength>0) material.EnableKeyword("_EMISSION"); else material.DisableKeyword("_EMISSION");
            material.globalIlluminationFlags=MaterialGlobalIlluminationFlags.BakedEmissive;
        }
        static string[] SourceMaterialNames(ModelImporter importer)
        {
            // Same serialized identifiers used by Unity's ModelImporter material inspector.
            // The renderer display name can be prefixed; it is NOT the importer remap key.
            var serialized=new SerializedObject(importer);
            var sources=serialized.FindProperty("m_Materials");
            if(sources==null || !sources.isArray || sources.arraySize==0)
                throw new InvalidDataException("No source material identifiers in "+importer.assetPath);
            var names=new string[sources.arraySize];
            for(int i=0;i<names.Length;i++)
            {
                var name=sources.GetArrayElementAtIndex(i).FindPropertyRelative("name");
                if(name==null || string.IsNullOrEmpty(name.stringValue))
                    throw new InvalidDataException("Invalid source material identifier in "+importer.assetPath+" at "+i);
                names[i]=name.stringValue;
            }
            return names;
        }
        static void RemapModelMaterials(string[] parts,Dictionary<string,Material> mats)
        {
            var names=new SupermarketMaterialNames(mats.Keys,parts);
            var snapshots=mats.Values.Distinct().ToDictionary(m=>m,m=>EditorJsonUtility.ToJson(m));
            foreach(string path in parts)
            {
                var importer=AssetImporter.GetAtPath(path) as ModelImporter;
                if(importer==null)throw new FileNotFoundException("Missing environment model importer: "+path);
                // Only material settings change in the repair path, never geometry import settings.
                if(importer.materialImportMode!=ModelImporterMaterialImportMode.ImportStandard ||
                    importer.materialLocation!=ModelImporterMaterialLocation.InPrefab)
                {
                    importer.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;
                    importer.materialLocation=ModelImporterMaterialLocation.InPrefab;
                    importer.SaveAndReimport();
                }
                var sourceNames=SourceMaterialNames(importer);
                // Resolve all source names before writing this part's remap table; no silent fallback.
                var targets=sourceNames.Select(n=>mats[names.Resolve(n)]).ToArray();
                for(int i=0;i<sourceNames.Length;i++)
                    importer.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material),sourceNames[i]),targets[i]);
                importer.SaveAndReimport();
                ValidateModelMaterials(path,parts,mats);
            }
            foreach(var saved in snapshots)
                if(EditorJsonUtility.ToJson(saved.Key)!=saved.Value)
                    throw new InvalidDataException("Material properties changed during import: "+AssetDatabase.GetAssetPath(saved.Key));
            Debug.Log("SIPO_MATERIAL_PROPERTIES_PRESERVED: "+snapshots.Count+" material snapshots unchanged.");
        }
        static void ValidateModelMaterials(string path,string[] parts,Dictionary<string,Material> mats)
        {
            var importer=AssetImporter.GetAtPath(path) as ModelImporter;
            if(importer==null)throw new FileNotFoundException("Missing environment model importer: "+path);
            var names=new SupermarketMaterialNames(mats.Keys,parts);
            var remaps=importer.GetExternalObjectMap();
            foreach(string sourceName in SourceMaterialNames(importer))
            {
                var expected=mats[names.Resolve(sourceName)];
                var id=new AssetImporter.SourceAssetIdentifier(typeof(Material),sourceName);
                if(!remaps.TryGetValue(id,out var actual) || actual!=expected)
                    throw new InvalidDataException(path+": missing or incorrect importer remap for '"+sourceName+"'. Run Sipo > Repair active scene materials.");
            }
            var source=AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if(source==null)throw new InvalidDataException("Model did not import: "+path);
            ValidateRendererMaterials(source,mats,false);
        }
        static void ValidateRendererMaterials(GameObject root,Dictionary<string,Material> mats,bool comparePrefab)
        {
            var renderers=root.GetComponentsInChildren<MeshRenderer>(true);
            if(renderers.Length==0)throw new InvalidDataException("Environment renderers missing: "+root.name);
            var known=new HashSet<Material>(mats.Values);
            foreach(var renderer in renderers)
            {
                string context=root.name+"/"+AnimationUtility.CalculateTransformPath(renderer.transform,root.transform);
                var slots=renderer.sharedMaterials;
                if(slots.Length==0)throw new InvalidDataException(context+": empty material slots.");
                var source=comparePrefab?PrefabUtility.GetCorrespondingObjectFromSource(renderer):null;
                var expected=source!=null?source.sharedMaterials:null;
                if(comparePrefab && expected==null)
                    throw new InvalidDataException(context+": missing FBX prefab connection; regenerate a backed-up scene to validate slot correspondence.");
                if(expected!=null && slots.Length!=expected.Length)
                    throw new InvalidDataException(context+": material slot count differs from the FBX.");
                for(int slot=0;slot<slots.Length;slot++)
                {
                    var material=slots[slot];
                    bool correct=material!=null && known.Contains(material) && (expected==null || material==expected[slot]);
                    SupermarketMaterialNames.RequireSlot(context+" slot "+slot+" material '"+(material!=null?material.name:"<null>")+"'",
                        material!=null && material.shader!=null?material.shader.name:null,correct);
                }
            }
        }
        static List<GameObject> EnvironmentInstances(Scene scene,string[] parts)
        {
            var instances=scene.GetRootGameObjects().SelectMany(o=>o.GetComponentsInChildren<Transform>(true))
                .Select(t=>t.gameObject).Where(o=>PrefabUtility.IsAnyPrefabInstanceRoot(o) &&
                    parts.Contains(PrefabUtility.GetPrefabAssetPathOfNearestInstanceRoot(o))).ToList();
            foreach(string path in parts)
                if(!instances.Any(o=>PrefabUtility.GetPrefabAssetPathOfNearestInstanceRoot(o)==path))
                    throw new InvalidDataException("Active scene is missing a connected FBX instance: "+path+". Open the supermarket scene or regenerate a backed-up copy.");
            return instances;
        }
        [MenuItem("Sipo/Repair active scene materials")]
        public static void RepairActiveSceneMaterials()
        {
            var spec=ReadMaterialSpec();var parts=ModelParts(spec);var mats=LoadMaterials(spec,false);
            var scene=SceneManager.GetActiveScene();
            EnvironmentInstances(scene,parts); // Reject the wrong scene before editing importers.
            RemapModelMaterials(parts,mats);
            foreach(var root in EnvironmentInstances(scene,parts))
                foreach(var renderer in root.GetComponentsInChildren<MeshRenderer>(true))
                {
                    var source=PrefabUtility.GetCorrespondingObjectFromSource(renderer);
                    if(source==null)throw new InvalidDataException("Missing source renderer: "+renderer.name);
                    Undo.RecordObject(renderer,"Repair supermarket material slots");
                    renderer.sharedMaterials=source.sharedMaterials;
                    PrefabUtility.RecordPrefabInstancePropertyModifications(renderer);
                }
            EditorSceneManager.MarkSceneDirty(scene);
            ValidateEnvironmentMaterials();
            Debug.Log("SIPO_MATERIAL_REPAIR_PASSED: both FBX remaps and active scene slots verified; existing material properties preserved. Save the scene to keep the repair.");
        }
        [MenuItem("Sipo/Validate environment materials")]
        public static void ValidateEnvironmentMaterials()
        {
            var spec=ReadMaterialSpec();var parts=ModelParts(spec);var mats=LoadMaterials(spec,false);
            foreach(string path in parts)ValidateModelMaterials(path,parts,mats);
            var roots=EnvironmentInstances(SceneManager.GetActiveScene(),parts);
            foreach(var root in roots)ValidateRendererMaterials(root,mats,true);
            int renderers=roots.Sum(o=>o.GetComponentsInChildren<MeshRenderer>(true).Length);
            Debug.Log("SIPO_MATERIAL_VALIDATION_PASSED: "+parts.Length+" FBX parts, "+renderers+" environment MeshRenderers; all slots mapped to existing URP/Lit assets, including inactive objects.");
        }

        static void OrientModel(Transform model)
        {
            var anchors=model.GetComponentsInChildren<Transform>().ToDictionary(t=>t.name,t=>t);
            if (!anchors.TryGetValue("Anchor_Origin",out var origin) || !anchors.TryGetValue("Anchor_Up",out var up) ||
                !anchors.TryGetValue("Anchor_Back",out var back) || !anchors.TryGetValue("Anchor_Right",out var right))
                throw new InvalidDataException("The model is missing its coordinate-system anchors.");
            Vector3 u=(up.position-origin.position).normalized,b=(back.position-origin.position).normalized;
            model.rotation=Quaternion.Inverse(Quaternion.LookRotation(b,u))*model.rotation;
            float scale=Vector3.Distance(up.position,origin.position);
            if (scale<.00001f) throw new InvalidDataException("Degenerate model scale.");
            model.localScale/=scale;
            if (Vector3.Dot((right.position-origin.position).normalized,Vector3.right)<0)
                model.localScale=Vector3.Scale(model.localScale,new Vector3(-1,1,1));
            model.position-=origin.position;
        }
        static Texture2D SurfaceTexture(string path,bool normal=false,bool color=false)
        {
            if(string.IsNullOrWhiteSpace(path))return null;
            var importer=AssetImporter.GetAtPath(path) as TextureImporter;
            if(importer==null)throw new InvalidDataException("Missing authored surface texture: "+path);
            var type=normal?TextureImporterType.NormalMap:TextureImporterType.Default;
            // Packed smoothness lives in alpha. It must never be treated as
            // transparency or gamma-corrected during texture import.
            bool changed=importer.textureType!=type || importer.sRGBTexture!=color ||
                importer.alphaIsTransparency || !importer.mipmapEnabled ||
                importer.wrapMode!=TextureWrapMode.Repeat || importer.anisoLevel!=8 ||
                importer.textureCompression!=TextureImporterCompression.Uncompressed;
            if(changed)
            {
                importer.textureType=type;importer.sRGBTexture=color;
                importer.alphaSource=TextureImporterAlphaSource.FromInput;
                importer.alphaIsTransparency=false;importer.mipmapEnabled=true;
                importer.wrapMode=TextureWrapMode.Repeat;importer.anisoLevel=8;
                importer.textureCompression=TextureImporterCompression.Uncompressed;
                importer.SaveAndReimport();
            }
            var texture=AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            if(texture==null)throw new InvalidDataException("Surface texture did not import: "+path);
            return texture;
        }
        static void ApplySurfaceMaps(Material material,MaterialSpec spec)
        {
            var color=SurfaceTexture(spec.baseMap,color:true);
            var normal=SurfaceTexture(spec.normalMap,normal:true);
            var packed=SurfaceTexture(spec.metallicGlossMap);
            material.SetTexture("_BaseMap",color);
            material.SetTexture("_BumpMap",normal);
            material.SetTexture("_MetallicGlossMap",packed);
            material.SetFloat("_BumpScale",spec.normalScale);
            // URP multiplies the packed map's alpha by _Smoothness.
            material.SetFloat("_Smoothness",packed!=null?1:1-spec.roughness);
            material.SetFloat("_SmoothnessTextureChannel",0);
            material.SetFloat("_SpecularHighlights",1);
            material.SetFloat("_EnvironmentReflections",1);
            material.DisableKeyword("_SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A");
            if(normal!=null)material.EnableKeyword("_NORMALMAP");else material.DisableKeyword("_NORMALMAP");
            if(packed!=null)material.EnableKeyword("_METALLICSPECGLOSSMAP");else material.DisableKeyword("_METALLICSPECGLOSSMAP");
            var scale=spec.textureScale!=null && spec.textureScale.Length==2
                ?new Vector2(spec.textureScale[0],spec.textureScale[1]):Vector2.one;
            foreach(string property in new[]{"_BaseMap","_BumpMap","_MetallicGlossMap"})
            { material.SetTextureScale(property,scale);material.SetTextureOffset(property,Vector2.zero); }
        }
        static void ConfigureReflections(Transform parent,BoundsSpec spec)
        {
            var size=spec!=null?V(spec.size):new Vector3(49,15,58);
            var center=spec!=null?V(spec.center):new Vector3(0,7.5f,5);
            if(size.x<=0 || size.y<=0 || size.z<=0)throw new InvalidDataException("Invalid environment reflection bounds.");
            AddReflection("Whole market HDR reflection",parent,
                new Vector3(center.x,3.8f,center.z),new Bounds(center,size),512,0);
            // Local, overlapping volumes keep the two galleries and front/rear
            // product displays represented in the glossy floor and metalwork.
            foreach(int side in new[]{-1,1})
            {
                var position=new Vector3(center.x+side*size.x*.36f,size.y*.48f,center.z);
                AddReflection(side<0?"West mezzanine reflection":"East mezzanine reflection",parent,
                    position,new Bounds(position,new Vector3(size.x*.30f,size.y*.52f,size.z*.82f)),256,2);
                position=new Vector3(center.x,3.2f,center.z+side*size.z*.22f);
                AddReflection(side<0?"Rear department reflection":"Arrival court reflection",parent,
                    position,new Bounds(new Vector3(position.x,size.y*.36f,position.z),
                        new Vector3(size.x*.80f,size.y*.72f,size.z*.58f)),256,1);
            }
        }
        static void AddReflection(string name,Transform parent,Vector3 position,Bounds bounds,int resolution,int importance)
        {
            var probe=Child(name,parent).AddComponent<ReflectionProbe>();
            probe.transform.position=position;probe.center=bounds.center-position;probe.size=bounds.size;
            probe.mode=ReflectionProbeMode.Realtime;probe.refreshMode=ReflectionProbeRefreshMode.OnAwake;
            probe.timeSlicingMode=ReflectionProbeTimeSlicingMode.IndividualFaces;
            probe.resolution=resolution;probe.boxProjection=true;probe.hdr=true;
            probe.importance=importance;probe.blendDistance=4;
            probe.nearClipPlane=.15f;probe.farClipPlane=Mathf.Max(bounds.size.x,bounds.size.z)*1.5f;
            probe.clearFlags=ReflectionProbeClearFlags.SolidColor;
            probe.backgroundColor=new Color(.025f,.05f,.12f);
        }
        static void ConfigurePipeline()
        {
            const string rp="Assets/Settings/SipoURP.asset",rd="Assets/Settings/SipoRenderer.asset";
            var renderer=AssetDatabase.LoadAssetAtPath<UniversalRendererData>(rd);
            if (renderer==null) { renderer=ScriptableObject.CreateInstance<UniversalRendererData>();AssetDatabase.CreateAsset(renderer,rd); }
            renderer.renderingMode=RenderingMode.ForwardPlus;
            var pipeline=AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(rp);
            if (pipeline==null) { pipeline=UniversalRenderPipelineAsset.Create(renderer);AssetDatabase.CreateAsset(pipeline,rp); }
            pipeline.supportsHDR=true;pipeline.msaaSampleCount=4;pipeline.renderScale=1;pipeline.shadowDistance=75;
            pipeline.mainLightShadowmapResolution=4096;pipeline.additionalLightsShadowmapResolution=4096;
            pipeline.maxAdditionalLightsCount=8;
            var serialized=new SerializedObject(pipeline);
            serialized.FindProperty("m_ReflectionProbeBlending").boolValue=true;
            serialized.FindProperty("m_ReflectionProbeBoxProjection").boolValue=true;
            serialized.FindProperty("m_AdditionalLightsRenderingMode").intValue=(int)LightRenderingMode.PerPixel;
            serialized.FindProperty("m_AdditionalLightShadowsSupported").boolValue=true;
            serialized.ApplyModifiedPropertiesWithoutUndo();
            GraphicsSettings.defaultRenderPipeline=pipeline;QualitySettings.renderPipeline=pipeline;
            EditorUtility.SetDirty(renderer);EditorUtility.SetDirty(pipeline);
        }
        static void ConfigureVolume(Transform parent)
        {
            const string path="Assets/Settings/SipoAtmosphere.asset";
            var profile=AssetDatabase.LoadAssetAtPath<VolumeProfile>(path);
            if (profile==null)
            {
                profile=ScriptableObject.CreateInstance<VolumeProfile>();AssetDatabase.CreateAsset(profile,path);
            }
            // Rebuilding updates existing profiles as well as first imports.
            var bloom=VolumeEffect<Bloom>(profile);bloom.intensity.Override(.32f);bloom.threshold.Override(1.05f);bloom.scatter.Override(.68f);
            var tone=VolumeEffect<Tonemapping>(profile);tone.mode.Override(TonemappingMode.ACES);
            var color=VolumeEffect<ColorAdjustments>(profile);color.postExposure.Override(.15f);color.contrast.Override(14);color.saturation.Override(6);
            var vignette=VolumeEffect<Vignette>(profile);vignette.intensity.Override(.10f);vignette.smoothness.Override(.55f);
            foreach(var component in profile.components)EditorUtility.SetDirty(component);
            EditorUtility.SetDirty(profile);
            var volume=Child("Sipo color and bloom",parent).AddComponent<Volume>();volume.isGlobal=true;volume.sharedProfile=profile;
        }
        static T VolumeEffect<T>(VolumeProfile profile) where T:VolumeComponent
        {
            if(profile.TryGet<T>(out var effect))return effect;
            effect=profile.Add<T>(true);AssetDatabase.AddObjectToAsset(effect,profile);return effect;
        }
        [MenuItem("Sipo/Validate active supermarket scene")]
        public static void ValidateScene()
        {
            ValidateEnvironmentMaterials();
            var renderers=UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None);
            if(renderers.Length<30)throw new InvalidOperationException("Environment geometry missing.");
            if(UnityEngine.Object.FindObjectsByType<CharacterController>(FindObjectsSortMode.None).Length!=1)throw new InvalidOperationException("Expected one explorer.");
            if(UnityEngine.Object.FindObjectsByType<BoxCollider>(FindObjectsSortMode.None).Length<80)throw new InvalidOperationException("Walkable collision geometry missing.");
            foreach(var renderer in renderers)
                if(renderer.sharedMaterials.Any(m=>m==null || m.shader==null || m.shader.name=="Hidden/InternalErrorShader"))
                    throw new InvalidOperationException("Missing material on "+renderer.name);
            var feet=UnityEngine.Object.FindFirstObjectByType<SipoExplorer>().transform.position;
            Physics.SyncTransforms();
            if(!Physics.Raycast(feet+Vector3.up,Vector3.down,2))throw new InvalidOperationException("Explorer spawn has no ground support.");
            Debug.Log("SIPO_VALIDATION_PASSED: geometry, materials, player, colliders and spawn support.");
        }
        [MenuItem("Sipo/Build Linux player")]
        public static void BuildLinux()
        {
            if(!File.Exists(Marker))BuildScene();
            EditorSceneManager.OpenScene(ScenePath);ValidateScene();
            var result=BuildPipeline.BuildPlayer(new BuildPlayerOptions {scenes=new[]{ScenePath},locationPathName="Builds/Linux/Sipo.x86_64",target=BuildTarget.StandaloneLinux64,options=BuildOptions.None});
            if(result.summary.result!=BuildResult.Succeeded)throw new InvalidOperationException("Linux player build failed: "+result.summary.result);
        }
    }
}
