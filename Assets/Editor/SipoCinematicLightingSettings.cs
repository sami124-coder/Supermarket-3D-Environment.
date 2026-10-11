using System;
using Sipo.Rendering;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Sipo.Editor
{
    /// <summary>Editable inputs for the opt-in cinematic lighting command; contains no scene references.</summary>
    [CreateAssetMenu(menuName = "Sipo/Cinematic Lighting Settings", fileName = "SipoCinematicLightingSettings")]
    public sealed class SipoCinematicLightingSettings : ScriptableObject
    {
        [Header("Existing environment")]
        [Tooltip("SipoCinematicLighting.json: light placement and reflection volumes in the existing environment's metre-based coordinates.")]
        public TextAsset layout;
        [Range(0, 4), Tooltip("Scales the generated cinematic rig lights without editing authored light assets.")]
        public float lightIntensityMultiplier = 1;
        [Tooltip("Temporarily disables the original generated supermarket lighting while this rig is applied. Custom lights are preserved.")]
        public bool replaceGeneratedLighting = true;
        [Tooltip("Apply reversible surface overrides. Disable to retain SRP Batcher eligibility for all mapped materials.")]
        public bool polishSurfaces = true;
        public SipoCinematicSurfacePolish.SurfaceSettings surfaces = new SipoCinematicSurfacePolish.SurfaceSettings();

        [Header("URP renderer quality")]
        [Tooltip("Optional URP screen-space ambient occlusion. This is not HDRP ambient occlusion or ray tracing.")]
        public bool enableAmbientOcclusion = true;
        [Range(0, 1)] public float aoIntensity = .32f;
        [Range(.05f, 2)] public float aoRadius = .35f;
        [Tooltip("Supported values: 1 (disabled), 2, 4, 8. The default uses camera anti-aliasing without MSAA.")]
        public int msaaSamples = 1;
        [Tooltip("Supported shadow atlas sizes: 512, 1024, 2048 or 4096 pixels.")]
        public int shadowAtlasResolution = 2048;
        [Range(1, 200)] public float shadowDistance = 65;

        [Header("Warm / cool ambient balance")]
        public Color ambientSky = new Color(.34f, .43f, .62f, 1);
        public Color ambientEquator = new Color(.36f, .31f, .25f, 1);
        public Color ambientGround = new Color(.16f, .21f, .31f, 1);
        [Range(0, 4)] public float ambientIntensity = 1;
        [Range(0, 4)] public float reflectionIntensity = 1;

        [Header("URP post-processing")]
        public TonemappingMode tonemapping = TonemappingMode.ACES;
        [Range(-5, 5), Tooltip("URP Color Adjustments post-exposure in EV; manual exposure, not HDRP automatic exposure.")]
        public float postExposure = .25f;
        [Range(0, 2)] public float bloomIntensity = .24f;
        [Range(0, 8)] public float bloomThreshold = 1.2f;
        [Range(0, 1)] public float bloomScatter = .6f;
        [Range(-100, 100)] public float contrast = 7;
        [Range(-100, 100)] public float saturation = 6;
        [Range(-100, 100)] public float temperature = 4;
        [Range(-100, 100)] public float tint;
        [Range(0, .5f)] public float vignetteIntensity = .055f;

        /// <summary>Fail before touching the active scene if settings are invalid or unsupported.</summary>
        public void Validate()
        {
            SipoCinematicLighting.ReadLayout(this);

            Between(nameof(lightIntensityMultiplier), lightIntensityMultiplier, 0, 4);
            Between(nameof(aoIntensity), aoIntensity, 0, 1);
            Between(nameof(aoRadius), aoRadius, .05f, 2);
            if (msaaSamples != 1 && msaaSamples != 2 && msaaSamples != 4 && msaaSamples != 8)
                throw new InvalidOperationException("MSAA samples must be 1, 2, 4 or 8.");
            if (shadowAtlasResolution != 512 && shadowAtlasResolution != 1024 && shadowAtlasResolution != 2048 &&
                shadowAtlasResolution != 4096)
                throw new InvalidOperationException("Shadow atlas resolution must be 512, 1024, 2048 or 4096.");
            Between(nameof(shadowDistance), shadowDistance, 1, 200);
            ValidateColor(nameof(ambientSky), ambientSky);
            ValidateColor(nameof(ambientEquator), ambientEquator);
            ValidateColor(nameof(ambientGround), ambientGround);
            Between(nameof(ambientIntensity), ambientIntensity, 0, 4);
            Between(nameof(reflectionIntensity), reflectionIntensity, 0, 4);
            if (tonemapping != TonemappingMode.None && tonemapping != TonemappingMode.Neutral && tonemapping != TonemappingMode.ACES)
                throw new InvalidOperationException("Use a supported URP tonemapping mode: None, Neutral or ACES.");
            Between(nameof(postExposure), postExposure, -5, 5);
            Between(nameof(bloomIntensity), bloomIntensity, 0, 2);
            Between(nameof(bloomThreshold), bloomThreshold, 0, 8);
            Between(nameof(bloomScatter), bloomScatter, 0, 1);
            Between(nameof(contrast), contrast, -100, 100);
            Between(nameof(saturation), saturation, -100, 100);
            Between(nameof(temperature), temperature, -100, 100);
            Between(nameof(tint), tint, -100, 100);
            Between(nameof(vignetteIntensity), vignetteIntensity, 0, .5f);

            if (surfaces == null) throw new InvalidOperationException("Cinematic surface settings are missing.");
            Between("surfaces.floorSmoothness", surfaces.floorSmoothness, 0, 1);
            Between("surfaces.chromeSmoothness", surfaces.chromeSmoothness, 0, 1);
            Between("surfaces.goldSmoothness", surfaces.goldSmoothness, 0, 1);
            Between("surfaces.chromeMetallic", surfaces.chromeMetallic, 0, 1);
            Between("surfaces.goldMetallic", surfaces.goldMetallic, 0, 1);
            Between("surfaces.blueSmoothness", surfaces.blueSmoothness, 0, 1);
            Between("surfaces.orangeSmoothness", surfaces.orangeSmoothness, 0, 1);
            Between("surfaces.glassSmoothness", surfaces.glassSmoothness, 0, 1);
            Between("surfaces.warmEmissionMultiplier", surfaces.warmEmissionMultiplier, 0, 3);
            Between("surfaces.blueEmissionMultiplier", surfaces.blueEmissionMultiplier, 0, 3);
            Between("surfaces.ceilingEmissionMultiplier", surfaces.ceilingEmissionMultiplier, 0, 3);
            Between("surfaces.signEmissionCeiling", surfaces.signEmissionCeiling, .1f, 4);
        }

        static void Between(string name, float value, float minimum, float maximum)
        {
            if (float.IsNaN(value) || float.IsInfinity(value) || value < minimum || value > maximum)
                throw new InvalidOperationException(name + " must be finite and between " + minimum + " and " + maximum + ".");
        }

        static void ValidateColor(string name, Color value)
        {
            Between(name + ".r", value.r, 0, 1);
            Between(name + ".g", value.g, 0, 1);
            Between(name + ".b", value.b, 0, 1);
            Between(name + ".a", value.a, 0, 1);
        }
    }
}
