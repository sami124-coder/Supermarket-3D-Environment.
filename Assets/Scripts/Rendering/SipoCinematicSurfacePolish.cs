using System;
using System.Collections.Generic;
using UnityEngine;

namespace Sipo.Rendering
{
    /// <summary>
    /// A reversible presentation layer over the original, mapped URP materials.
    /// No material, shader, keyword, texture, color, transparency or mesh asset is edited.
    /// MPBs are installed only on explicitly selected material slots, not every product.
    /// </summary>
    [ExecuteAlways, DisallowMultipleComponent]
    [AddComponentMenu("Sipo/Rendering/Cinematic Surface Polish")]
    public sealed class SipoCinematicSurfacePolish : MonoBehaviour
    {
        [Serializable]
        public sealed class SurfaceSettings
        {
            [Range(0, 1), Tooltip("Multiplier on the authored floor texture's smoothness alpha; 1 preserves its detail.")]
            public float floorSmoothness = 1;
            [Range(0, 1)] public float chromeSmoothness = .9f;
            [Range(0, 1)] public float goldSmoothness = .83f;
            [Range(0, 1)] public float chromeMetallic = .98f;
            [Range(0, 1)] public float goldMetallic = .86f;
            [Range(0, 1)] public float blueSmoothness = .74f;
            [Range(0, 1)] public float orangeSmoothness = .78f;
            [Range(0, 1), Tooltip("Only smoothness changes. The authored glass alpha, tint and blend mode are preserved.")]
            public float glassSmoothness = .94f;
            [Range(0, 3)] public float warmEmissionMultiplier = 1.25f;
            [Range(0, 3)] public float blueEmissionMultiplier = 1.1f;
            [Range(0, 3)] public float ceilingEmissionMultiplier = 1.1f;
            [Range(.1f, 4), Tooltip("Peak linear RGB ceiling for already-emissive white sign lettering, preserving hue.")]
            public float signEmissionCeiling = 1;
        }

        [SerializeField, Tooltip("Exact renderers belonging to the existing supermarket. No scene-wide material search.")]
        Renderer[] targets = Array.Empty<Renderer>();
        [SerializeField] SurfaceSettings settings = new SurfaceSettings();
        [SerializeField, HideInInspector] int ownershipToken;
        readonly List<Slot> activeSlots = new List<Slot>();

        const string LitShader = "Universal Render Pipeline/Lit";
        static readonly int Smoothness = Shader.PropertyToID("_Smoothness");
        static readonly int Metallic = Shader.PropertyToID("_Metallic");
        static readonly int Emission = Shader.PropertyToID("_EmissionColor");
        // Unused by the shader. Identifies our transient block across assembly reloads.
        static readonly int Owner = Shader.PropertyToID("_SipoCinematicSurfaceOwner");

        sealed class Slot
        {
            public Renderer renderer;
            public Material material;
            public int index;
            public bool smoothness, metallic, emission;
            public float smoothnessValue, metallicValue;
            public Color emissionValue;
        }

        public int AppliedSlotCount => activeSlots.Count;
        public SurfaceSettings Settings => settings;

        /// <summary>Call from the editor after Undo.RecordObject. Never clones/reassigns sharedMaterials.</summary>
        public void Configure(Renderer[] renderers, SurfaceSettings options)
        {
            Restore();
            targets = renderers == null ? Array.Empty<Renderer>() : (Renderer[])renderers.Clone();
            settings = options ?? new SurfaceSettings();
            if (isActiveAndEnabled) Apply();
        }

        void OnEnable()
        {
            try { Apply(); }
            catch (Exception error) { Debug.LogError("SIPO_SURFACE_POLISH_REFUSED: " + error.Message, this); }
        }

        void OnDisable() => Restore();
        void OnDestroy() => Restore();

        /// <summary>Explicit refresh, no Update loop and no automatic asset writes.</summary>
        [ContextMenu("Reapply surface polish")]
        public void Apply()
        {
            if (!isActiveAndEnabled) return;
            if (ownershipToken == 0) ownershipToken = (Guid.NewGuid().GetHashCode() & 0x007fffff) + 1;
            Restore();
            ValidateSettings();
            var pending = new List<Slot>();
            var seen = new HashSet<Renderer>();
            var block = new MaterialPropertyBlock();
            var global = new MaterialPropertyBlock();
            // Preflight every selected slot before changing any of them. An existing
            // unrelated MPB is a conflict, never something to erase or silently ignore.
            foreach (var renderer in targets)
            {
                if (renderer == null || !seen.Add(renderer)) continue;
                var materials = renderer.sharedMaterials;
                for (int index = 0; index < materials.Length; index++)
                {
                    var slot = MakeSlot(renderer, materials[index], index);
                    if (slot == null) continue;
                    renderer.GetPropertyBlock(global);
                    if (!global.isEmpty)
                        throw new InvalidOperationException(renderer.name + " has an existing renderer-wide property block; surface polish did not replace it.");
                    renderer.GetPropertyBlock(block, index);
                    if (!block.isEmpty && Math.Abs(block.GetInt(Owner)) != ownershipToken)
                        throw new InvalidOperationException(renderer.name + " slot " + index + " has an existing material property block; surface polish did not replace it.");
                    pending.Add(slot);
                }
            }
            foreach (var slot in pending)
            {
                slot.renderer.GetPropertyBlock(block, slot.index);
                if (slot.smoothness) block.SetFloat(Smoothness, slot.smoothnessValue);
                if (slot.metallic) block.SetFloat(Metallic, slot.metallicValue);
                if (slot.emission) block.SetColor(Emission, slot.emissionValue);
                block.SetInt(Owner, ownershipToken);
                slot.renderer.SetPropertyBlock(block, slot.index);
                activeSlots.Add(slot);
            }
        }

        /// <summary>
        /// Restore ONLY properties still owned by us to current shared-material values.
        /// Never clear an entire block: another tool may have added unrelated keys.
        /// Unity cannot remove individual MPB keys, so inert baseline overrides remain
        /// until the scene is reloaded. No overrides are saved into material assets.
        /// </summary>
        public void Restore()
        {
            var block = new MaterialPropertyBlock();
            foreach (var slot in activeSlots)
            {
                if (slot.renderer == null || slot.material == null) continue;
                var materials = slot.renderer.sharedMaterials;
                if (slot.index >= materials.Length || materials[slot.index] != slot.material) continue;
                slot.renderer.GetPropertyBlock(block, slot.index);
                if (block.GetInt(Owner) != ownershipToken) continue;
                // Respect edits made by another tool after Apply, even on owned keys.
                if (slot.smoothness && Mathf.Approximately(block.GetFloat(Smoothness), slot.smoothnessValue))
                    block.SetFloat(Smoothness, slot.material.GetFloat(Smoothness));
                if (slot.metallic && Mathf.Approximately(block.GetFloat(Metallic), slot.metallicValue))
                    block.SetFloat(Metallic, slot.material.GetFloat(Metallic));
                if (slot.emission && Close(block.GetColor(Emission), slot.emissionValue))
                    block.SetColor(Emission, slot.material.GetColor(Emission));
                block.SetInt(Owner, -ownershipToken);
                slot.renderer.SetPropertyBlock(block, slot.index);
            }
            activeSlots.Clear();
        }

        public bool ValidateApplied(out string report)
        {
            try
            {
                ValidateSettings();
                if (!isActiveAndEnabled) throw new InvalidOperationException("Surface polish component is disabled.");
                int expected = 0;
                var seen = new HashSet<Renderer>();
                foreach (var renderer in targets)
                {
                    if (renderer == null || !seen.Add(renderer)) continue;
                    var materials = renderer.sharedMaterials;
                    for (int i = 0; i < materials.Length; i++)
                        if (MakeSlot(renderer, materials[i], i) != null) expected++;
                }
                if (expected == 0 || expected != activeSlots.Count)
                    throw new InvalidOperationException("Expected " + expected + " polished slots, found " + activeSlots.Count + ". Reapply after changing targets or materials.");
                var block = new MaterialPropertyBlock();
                foreach (var slot in activeSlots)
                {
                    var materials = slot.renderer.sharedMaterials;
                    if (slot.index >= materials.Length || materials[slot.index] != slot.material)
                        throw new InvalidOperationException("Shared material reference changed on " + slot.renderer.name + ".");
                    RequireLit(slot.material);
                    var configured = MakeSlot(slot.renderer, slot.material, slot.index);
                    if (configured == null || configured.smoothness != slot.smoothness || configured.metallic != slot.metallic ||
                        configured.emission != slot.emission ||
                        (slot.smoothness && !Mathf.Approximately(configured.smoothnessValue, slot.smoothnessValue)) ||
                        (slot.metallic && !Mathf.Approximately(configured.metallicValue, slot.metallicValue)) ||
                        (slot.emission && !Close(configured.emissionValue, slot.emissionValue)))
                        throw new InvalidOperationException("Surface settings or material emission changed since Apply; reapply on " + slot.renderer.name + ".");
                    slot.renderer.GetPropertyBlock(block, slot.index);
                    if (block.GetInt(Owner) != ownershipToken ||
                        (slot.smoothness && !Mathf.Approximately(block.GetFloat(Smoothness), slot.smoothnessValue)) ||
                        (slot.metallic && !Mathf.Approximately(block.GetFloat(Metallic), slot.metallicValue)) ||
                        (slot.emission && !Close(block.GetColor(Emission), slot.emissionValue)))
                        throw new InvalidOperationException("Missing or changed surface override on " + slot.renderer.name + " slot " + slot.index + ".");
                }
                report = "SIPO_SURFACE_POLISH_VALIDATED: " + activeSlots.Count + " selected URP/Lit slots; shared material references preserved.";
                return true;
            }
            catch (Exception error) { report = "SIPO_SURFACE_POLISH_INVALID: " + error.Message; return false; }
        }

        Slot MakeSlot(Renderer renderer, Material material, int index)
        {
            if (material == null || !material.name.StartsWith("SIPO_", StringComparison.Ordinal)) return null;
            var slot = new Slot { renderer = renderer, material = material, index = index };
            // Exact names only. In particular, do not polish mascot fabric, food,
            // foliage, arbitrary imported products or material-name prefixes.
            switch (material.name)
            {
                case "SIPO_FloorCobalt": case "SIPO_FloorPearl": case "SIPO_FloorTangerine":
                    slot.smoothness = true; slot.smoothnessValue = settings.floorSmoothness; break;
                case "SIPO_Chrome":
                    slot.smoothness = slot.metallic = true;
                    slot.smoothnessValue = settings.chromeSmoothness; slot.metallicValue = settings.chromeMetallic; break;
                case "SIPO_Gold":
                    slot.smoothness = slot.metallic = true;
                    slot.smoothnessValue = settings.goldSmoothness; slot.metallicValue = settings.goldMetallic; break;
                case "SIPO_Blue": case "SIPO_Navy":
                    slot.smoothness = true; slot.smoothnessValue = settings.blueSmoothness; break;
                case "SIPO_Orange": case "SIPO_ReceptionOrange":
                    slot.smoothness = true; slot.smoothnessValue = settings.orangeSmoothness; break;
                case "SIPO_Glass":
                    slot.smoothness = true; slot.smoothnessValue = settings.glassSmoothness; break;
                case "SIPO_WarmLight":
                    SetEmission(slot, settings.warmEmissionMultiplier); break;
                case "SIPO_BlueLight":
                    SetEmission(slot, settings.blueEmissionMultiplier); break;
                case "SIPO_Night": case "SIPO_CelestialInk":
                case "SIPO_PlanetariumBlue0": case "SIPO_PlanetariumBlue1": case "SIPO_PlanetariumBlue2":
                case "SIPO_PlanetariumBlue3": case "SIPO_PlanetariumBlue4": case "SIPO_PlanetariumBlue5": case "SIPO_PlanetariumBlue6":
                    SetEmission(slot, settings.ceilingEmissionMultiplier); break;
                case "SIPO_SignWhite":
                    SetEmission(slot, 1);
                    if (slot.emission && slot.emissionValue.maxColorComponent > settings.signEmissionCeiling)
                    {
                        float alpha = slot.emissionValue.a;
                        slot.emissionValue *= settings.signEmissionCeiling / slot.emissionValue.maxColorComponent;
                        slot.emissionValue.a = alpha;
                    }
                    break;
            }
            if (!slot.smoothness && !slot.metallic && !slot.emission) return null;
            RequireLit(material);
            // Metallic is encoded by the authored map when present. Do not flatten it.
            if (slot.metallic && material.GetTexture("_MetallicGlossMap") != null) slot.metallic = false;
            return slot;
        }

        static void SetEmission(Slot slot, float multiplier)
        {
            var material = slot.material;
            if (!material.IsKeywordEnabled("_EMISSION") || !material.HasProperty(Emission)) return;
            Color original = material.GetColor(Emission);
            if (original.maxColorComponent <= 0) return;
            slot.emission = true;
            slot.emissionValue = original * multiplier;
            slot.emissionValue.a = original.a;
        }

        static void RequireLit(Material material)
        {
            if (material.shader == null || material.shader.name != LitShader ||
                !material.HasProperty(Smoothness) || !material.HasProperty(Metallic))
                throw new InvalidOperationException("Expected the existing URP/Lit asset for " + material.name + "; repair environment material mappings first.");
        }

        void ValidateSettings()
        {
            if (settings == null) throw new InvalidOperationException("Surface settings are missing.");
            foreach (float value in new[] { settings.floorSmoothness, settings.chromeSmoothness,
                settings.goldSmoothness, settings.chromeMetallic, settings.goldMetallic, settings.blueSmoothness,
                settings.orangeSmoothness, settings.glassSmoothness })
                if (float.IsNaN(value) || value < 0 || value > 1)
                    throw new InvalidOperationException("Smoothness and metallic settings must be finite values from 0 to 1.");
            foreach (float value in new[] { settings.warmEmissionMultiplier, settings.blueEmissionMultiplier, settings.ceilingEmissionMultiplier })
                if (float.IsNaN(value) || value < 0 || value > 3)
                    throw new InvalidOperationException("Emission multipliers must be finite values from 0 to 3.");
            if (float.IsNaN(settings.signEmissionCeiling) || settings.signEmissionCeiling < .1f || settings.signEmissionCeiling > 4)
                throw new InvalidOperationException("Sign emission ceiling must be a finite value from 0.1 to 4.");
        }

        static bool Close(Color a, Color b) => Mathf.Approximately(a.r, b.r) && Mathf.Approximately(a.g, b.g) &&
            Mathf.Approximately(a.b, b.b) && Mathf.Approximately(a.a, b.a);
    }
}
