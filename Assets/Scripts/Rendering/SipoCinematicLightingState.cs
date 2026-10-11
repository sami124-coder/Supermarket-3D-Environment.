using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Sipo.Rendering
{
    // Serialized restoration data only. No player controls, Update loop or lighting automation.
    [DisallowMultipleComponent, AddComponentMenu("")]
    public sealed class SipoCinematicLightingState : MonoBehaviour
    {
        [Serializable] public sealed class CameraState
        {
            public Camera camera;
            public bool hdr, hadAdditionalData, postProcessing, dithering, stopNaN;
            public AntialiasingMode aa;
            public AntialiasingQuality aaQuality;
        }
        [Serializable] public sealed class BehaviourState
        {
            public Behaviour component;
            public bool enabled;
        }
        [Serializable] public sealed class RendererState
        {
            public MeshRenderer renderer;
            public Mesh mesh;
            public Material[] materials;
            public Matrix4x4 relativeMatrix;
        }
        [HideInInspector] public bool applied, reflectionsDirty;
        [HideInInspector] public string sceneGuid, ownedFolder, settingsJson, layoutJson;
        [HideInInspector] public int qualityIndex;
        [HideInInspector] public RenderPipelineAsset previousPipeline, originalDefaultPipeline, appliedPipeline;
        [HideInInspector] public AmbientMode ambientMode;
        [HideInInspector] public Color ambientSky, ambientEquator, ambientGround;
        [HideInInspector] public float ambientIntensity, reflectionIntensity;
        [HideInInspector] public Transform environmentFrame;
        [HideInInspector] public List<CameraState> cameras = new List<CameraState>();
        [HideInInspector] public List<BehaviourState> previousLighting = new List<BehaviourState>();
        [HideInInspector] public List<RendererState> geometry = new List<RendererState>();
        [HideInInspector] public List<Light> lights = new List<Light>();
        [HideInInspector] public List<ReflectionProbe> probes = new List<ReflectionProbe>();
        [HideInInspector] public Volume volume;
        [HideInInspector] public SipoCinematicSurfacePolish surfaces;
    }
}
