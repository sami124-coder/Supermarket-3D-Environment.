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
    [Serializable] public class MaterialSpec { public string name; public float[] color, emission; public float roughness, metallic, emissionStrength, alpha; public bool transparent; }
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
    }

    /// <summary>Assembles the authored FBX, physical boundaries, lighting and player into an editable scene.</summary>
    [InitializeOnLoad]
    public static class SupermarketProject
    {
        const string ModelPath = "Assets/Environment/SipoSupermarket.fbx";
        const string DataPath = "Assets/Environment/scene-data.json";
        const string ScenePath = "Assets/Scenes/SipoSupermarket.unity";
        const string Marker = "Assets/Settings/scene-ready.json";
        static bool building;

        static SupermarketProject() { EditorApplication.delayCall += FirstImport; }
        static void FirstImport()
        {
            if (Application.isBatchMode || building || File.Exists(Marker)) return;
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
                ConfigurePipeline();
                var importer=AssetImporter.GetAtPath(ModelPath) as ModelImporter;
                if (importer == null) throw new FileNotFoundException("Import the supermarket FBX before building.");
                importer.globalScale=1;
                importer.useFileScale=true;
                importer.bakeAxisConversion=true;
                importer.importCameras=false;
                importer.importLights=false;
                importer.importAnimation=false;
                importer.addCollider=false;
                importer.isReadable=false;
                importer.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;
                importer.SaveAndReimport();
                var source=AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
                if (source == null) throw new InvalidDataException("The environment model did not import.");
                var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
                var root=new GameObject("SIPO | A little joy in every aisle");
                var model=(GameObject)PrefabUtility.InstantiatePrefab(source,root.transform);
                model.name="Architecture, licensed groceries and botanical garden";
                OrientModel(model.transform);
                var mats=new Dictionary<string,Material>(StringComparer.Ordinal);
                var shader=Shader.Find("Universal Render Pipeline/Lit");
                if (shader == null) throw new InvalidOperationException("Universal Render Pipeline/Lit shader is unavailable.");
                foreach (var m in spec.materials)
                {
                    string path="Assets/Materials/"+Safe(m.name)+".mat";
                    var material=AssetDatabase.LoadAssetAtPath<Material>(path);
                    if (material == null) { material=new Material(shader); AssetDatabase.CreateAsset(material,path); }
                    material.shader=shader; material.name=m.name; material.enableInstancing=true;
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
                    material.SetFloat("_Smoothness",1-m.roughness);
                    material.SetColor("_EmissionColor",C(m.emission)*m.emissionStrength);
                    if (m.emissionStrength>0) material.EnableKeyword("_EMISSION"); else material.DisableKeyword("_EMISSION");
                    material.globalIlluminationFlags=MaterialGlobalIlluminationFlags.BakedEmissive;
                    EditorUtility.SetDirty(material); mats[m.name]=material;
                }
                foreach (var renderer in model.GetComponentsInChildren<MeshRenderer>())
                {
                    renderer.sharedMaterials=renderer.sharedMaterials.Select(m => m != null && mats.TryGetValue(m.name,out var mapped) ? mapped : m).ToArray();
                    GameObjectUtility.SetStaticEditorFlags(renderer.gameObject,StaticEditorFlags.BatchingStatic|StaticEditorFlags.ReflectionProbeStatic);
                }
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
                RenderSettings.ambientSkyColor=new Color(.42f,.49f,.64f);
                RenderSettings.ambientEquatorColor=new Color(.38f,.32f,.24f);
                RenderSettings.ambientGroundColor=new Color(.15f,.19f,.28f);
                RenderSettings.ambientIntensity=1;
                RenderSettings.fog=false;
                RenderSettings.reflectionIntensity=.85f;
                var sun=Child("Soft exterior fill",lighting.transform).AddComponent<Light>();
                sun.type=LightType.Directional;sun.color=new Color(1,.86f,.69f);sun.intensity=.65f;
                sun.transform.rotation=Quaternion.Euler(65,-35,0);sun.shadows=LightShadows.Soft;RenderSettings.sun=sun;
                var probe=Child("Atrium reflections",lighting.transform).AddComponent<ReflectionProbe>();
                probe.transform.position=new Vector3(0,4,0);probe.size=new Vector3(49,15,45);
                probe.mode=ReflectionProbeMode.Realtime;probe.refreshMode=ReflectionProbeRefreshMode.OnAwake;
                probe.timeSlicingMode=ReflectionProbeTimeSlicingMode.IndividualFaces;probe.resolution=128;probe.boxProjection=true;
                probe.hdr=true;probe.farClipPlane=70;
                ConfigureVolume(lighting.transform);
                var player=SupermarketPlayerFactory.Create(root.transform,V(spec.spawn.position),spec.spawn.yaw);
                var camera=player.GetComponentInChildren<Camera>();
                camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.09f,.15f,.25f);
                var additional=camera.GetUniversalAdditionalCameraData();additional.renderPostProcessing=true;
                additional.antialiasing=AntialiasingMode.SubpixelMorphologicalAntiAliasing;
                player.GetComponent<SipoExplorer>().Configure(camera.transform,V(spec.spawn.position),spec.spawn.yaw,
                    spec.viewpoints.Select(v=>new SipoViewpoint {label=v.name,description=v.description,position=V(v.position),yaw=v.yaw,pitch=v.pitch}).ToArray(),
                    spec.departments.Select(d=>new SipoDepartmentZone {label=d.name,description="Discover something lovely.",bounds=new Bounds(V(d.position)+Vector3.up*2,V(d.size))}).ToArray());
                EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene(ScenePath,true)};
                PlayerSettings.companyName="Sipo";PlayerSettings.productName="Sipo Supermarket";
                PlayerSettings.colorSpace=ColorSpace.Linear;
                PlayerSettings.defaultScreenWidth=1600;PlayerSettings.defaultScreenHeight=1000;
                PlayerSettings.fullScreenMode=FullScreenMode.FullScreenWindow;
                QualitySettings.vSyncCount=1;
                EditorSceneManager.SaveScene(scene,ScenePath);
                AssetDatabase.SaveAssets();
                ValidateScene();
                File.WriteAllText(Marker,"{\"schemaVersion\":1,\"scene\":\""+ScenePath+"\"}\n");
                AssetDatabase.Refresh();
                Debug.Log("SIPO_SCENE_READY: " + ScenePath);
                if (SceneView.lastActiveSceneView != null)
                    SceneView.lastActiveSceneView.LookAt(new Vector3(0,5,0),Quaternion.Euler(12,180,0),24);
            }
            finally { building=false; }
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
        static void ConfigurePipeline()
        {
            const string rp="Assets/Settings/SipoURP.asset",rd="Assets/Settings/SipoRenderer.asset";
            var renderer=AssetDatabase.LoadAssetAtPath<UniversalRendererData>(rd);
            if (renderer==null) { renderer=ScriptableObject.CreateInstance<UniversalRendererData>();AssetDatabase.CreateAsset(renderer,rd); }
            renderer.renderingMode=RenderingMode.ForwardPlus;
            var pipeline=AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(rp);
            if (pipeline==null) { pipeline=UniversalRenderPipelineAsset.Create(renderer);AssetDatabase.CreateAsset(pipeline,rp); }
            pipeline.supportsHDR=true;pipeline.msaaSampleCount=4;pipeline.renderScale=1;pipeline.shadowDistance=45;
            pipeline.maxAdditionalLightsCount=8;
            var serialized=new SerializedObject(pipeline);
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
                var bloom=profile.Add<Bloom>(true);bloom.intensity.Override(.42f);bloom.threshold.Override(1.1f);bloom.scatter.Override(.65f);
                var tone=profile.Add<Tonemapping>(true);tone.mode.Override(TonemappingMode.ACES);
                var color=profile.Add<ColorAdjustments>(true);color.postExposure.Override(.65f);color.saturation.Override(8);
                var vignette=profile.Add<Vignette>(true);vignette.intensity.Override(.13f);vignette.smoothness.Override(.5f);
                foreach(var component in profile.components)AssetDatabase.AddObjectToAsset(component,profile);
                EditorUtility.SetDirty(profile);
            }
            var volume=Child("Sipo color and bloom",parent).AddComponent<Volume>();volume.isGlobal=true;volume.sharedProfile=profile;
        }
        [MenuItem("Sipo/Validate active supermarket scene")]
        public static void ValidateScene()
        {
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
