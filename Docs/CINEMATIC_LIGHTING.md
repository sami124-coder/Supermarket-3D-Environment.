# Cinematic lighting for Unity 6.3 URP

This optional visual treatment lights the existing two-floor SIPO environment with warm retail pools, cool atrium fill, orange ring accents, a dedicated mascot portrait light, and local HDR reflections. It targets Unity **6000.3.26f1 / URP 17.3.0**. The environment FBXs, their importers, the corrected material mappings, original material assets, layout, and gameplay remain unchanged.

The supplied reference calls for luminous rings, readable signs, rich orange/cobalt separation, polished floors, and clear merchandise. The previous setup mostly used broad point lights, including several expensive point-light shadows. The new layout gives reception, shelves, balconies, storefronts, escalators, ceiling, and ornaments their own directed illumination. A second screenshot of the current Unity appearance was not available in this task, so the comparison is based on the supplied ideal reference and inspected project configuration.

**The final appearance has not been rendered or visually verified in native Unity here.** The installed editor cannot activate its license in the cloud and exits with code 198. Compilation against the actual Unity/URP APIs, spatial configuration checks, and material-mapping checks are separate from a local rendered review.

## Apply to an existing local scene

1. Back up or commit your local project, including customized scenes, material assets, and `.meta` files. Pull the repository update without discarding local changes. Resolve any Git conflicts before opening Unity.
2. Open the project in Unity 6000.3.26f1 and wait for compilation. Open your existing customized supermarket scene. Save it first; using **File → Save As** to create a separate lighting review scene gives you an independent comparison copy.
3. Run **Sipo → Validate environment materials**. Correct any mapping failures using the existing [material repair procedure](MATERIAL_REPAIR.md) before applying lighting. The cinematic command expects the established URP materials; it does not repair materials by replacing their settings.
4. Run **Sipo → Apply Cinematic Lighting to Active Scene**. This edits the active scene in memory and marks it dirty; it does not save over your scene file. It creates assets owned by the lighting configuration and assigns an owned pipeline copy to the current Quality level, as described below.
5. Run **Sipo → Capture Cinematic Reflection Probes**. Let the six cubemap captures finish. Recapture after changing the environment, lighting, emission, or surface polish so the reflective floor and metalwork show the updated surroundings.
6. Run **Sipo → Validate Cinematic Lighting**. Treat a failed validation as a problem to resolve before accepting the result. Also rerun **Sipo → Validate environment materials** to confirm the original mapping remains valid.
7. Review the Game view and both floors: reception, mascot, produce, bakery, snacks, drinks, frozen, kitchen, gym, upper storefronts, checkout, and escalators. Enable Scene-view lighting and effects when using the Scene view. Check signs at first-person height, glass against bright backgrounds, dark corners, and reflective floors while moving the camera.
8. Tune the configuration if necessary, reapply, recapture reflections, and validate again. Save the reviewed scene when satisfied. Commit the scene and generated assets together if sharing the result.

**Do not run “Build supermarket scene” for this upgrade.** The dedicated lighting command works on your existing scene and does not regenerate or replace its environment.

## Controls and ownership

Use **Sipo → Select Cinematic Lighting Settings** to select `Assets/Settings/SipoCinematicLightingSettings.asset`. Edit the Inspector settings, then reapply to update the owned lighting configuration. The JSON layout at [`Assets/Settings/SipoCinematicLighting.json`](../Assets/Settings/SipoCinematicLighting.json) controls individual light names, positions, targets, colors, intensities, ranges, cone angles, shadow flags, and reflection volumes.

| Control | Purpose and tuning guidance |
| --- | --- |
| Light intensity multiplier | Changes the rig's illumination without recoloring authored materials. Adjust this before increasing exposure to rescue an underlit area. Individual department lights are also editable in the JSON. |
| Warm/cool light colors | Warm near-white merchandise keys retain food and package colors; orange and cobalt are reserved for accents and atmosphere. Light colors are authored as sRGB triples. |
| Ambient fill and reflections | Supports readability between direct-light pools. Avoid lifting the ambient contribution so far that shadows and material contrast disappear. |
| HDR, tonemapping, post exposure | Uses URP HDR rendering, tonemapping, and the supported `ColorAdjustments.postExposure` control. This is a fixed exposure adjustment, not HDRP's Exposure component or automatic eye adaptation. |
| Bloom | Gives existing emissive rings and ornaments a restrained glow. Lower intensity or raise threshold if text or bright edges become difficult to read. |
| White balance, contrast, saturation | Provides final color tuning after light balance and exposure are correct. The lighting does not recolor the underlying material assets. |
| Ambient occlusion | Optional URP Screen Space Ambient Occlusion, with half-resolution processing and a moderate sample count. It adds contact depth around products, fixtures, and architectural edges. It is not global illumination. |
| Anti-aliasing | The default is high-quality camera SMAA with MSAA disabled (1 sample); optional 2/4/8-sample MSAA is configurable. Review fine railings and signs at the intended output resolution. |
| Surface polish | Reversible selected-slot overrides for floor, orange/blue enamel, chrome, gold, glass, existing emission, and sign emission. Disable this option to retain the original surface response. |

The intensity values in the JSON are assigned directly, with the configurable multiplier. They are calibrated as a starting point for the actual 6–14 metre light throws; they do not repeat the previous builder's unconditional `intensity * 2` conversion. Local rendering is needed to judge their final appearance.

Generated pipeline, renderer, volume-profile, and reflection assets live under `Assets/SipoCinematicGenerated/<sceneGuid>/`. Existing renderer features and renderer slots are copied into the owned configuration. Original pipeline/renderer/profile assets and their `.meta` files are preserved. Reapplying updates this scene's owned assets and rig instead of accumulating duplicate lighting rigs.

**A Quality render-pipeline override is project-wide for that Quality level.** Unity does not provide a scene-local pipeline assignment. Applying the treatment changes the active Quality level's pipeline reference; another scene opened under that level will use that pipeline until it is restored. Other Quality levels and the Graphics default pipeline are not changed by this command. Review the selected Quality level when testing a build.

## Lighting and reflection budget

The supplied layout contains **36 real-time lights: 30 spotlights and six point fills**. Exactly **three spotlights cast real-time shadows**. The other lights supply merchandise illumination, ceiling color, and architectural fill without additional shadow-map faces. Existing generated illumination is disabled reversibly so the old rig does not double the new rig's light contribution; user-authored objects are not removed.

Forward+ handles the overlapping local lights. Additional-light shadows use a bounded atlas. Optional SSAO uses depth reconstruction rather than requiring a full normal prepass. Profiling remains necessary for the approximately eight-million-triangle environment; the upgrade does not simplify its meshes or products.

The six reflection probes use **one 512-pixel cubemap and five 256-pixel cubemaps**, with HDR capture, blending, and box projection. Their influence volumes cover the atrium, rear retail departments, both upper galleries, produce, and drinks/checkout. Captures happen on demand in the Editor; they do not rerender six views every frame. Uncompressed RGBAHalf cubemap storage with mipmaps is approximately 36 MiB in total, before any atlas duplication or platform compression.

These static cubemaps provide attractive, economical reflections. Box projection reduces some indoor parallax error, but a cubemap cannot reproduce an exact mirror reflection for every viewpoint or show moving objects accurately. No HDRP-only reflection system, ray tracing, or screen-space reflections are assumed or installed.

## Material preservation and polish

The existing `Assets/Materials/` assets remain the renderer's shared materials. The original FBX remaps remain in place for both environment parts. The treatment does not substitute Standard shaders, change material keywords or blend modes, rewrite textures, or overwrite authored base colors, transparency, texture tiling, or normal/metallic maps.

Optional polish uses `MaterialPropertyBlock` overrides only on selected `SIPO_` material slots:

- Floor smoothness respects the authored metallic/smoothness texture and its detail.
- Orange/blue surfaces, chrome, and gold receive controlled highlights; texture-encoded metallic detail remains authoritative.
- Glass receives a smoothness adjustment while retaining its original tint, alpha, and transparency mode. This does not add physical refraction or solve all transparent-object sorting limitations.
- Already-emissive warm rings, blue elements, and the planetarium receive restrained emission multipliers. White sign emission is capped separately to protect text readability.

An existing unrelated material property block is treated as a conflict rather than silently overwritten. Disable surface polish when another system owns the same renderer properties.

Property blocks can prevent affected draws from using the SRP Batcher. They also do not turn mesh emission into baked indirect lighting. Profile the polished scene locally and compare with polish disabled if CPU rendering cost is significant. The overrides are applied without a per-frame update loop and do not alter imported geometry.

Default post settings are ACES, +0.25 EV, bloom 0.24 with threshold 1.2/scatter 0.6, contrast +7, saturation +6, white-balance temperature +4, and a subtle 0.055 vignette. The additional-light shadow atlas is 2048 pixels with a 65-metre shadow distance. These are adjustable starting values, not a locally rendered calibration.

## Restore and safe iteration

Run **Sipo → Restore Previous Lighting** to restore the recorded ambient/render settings, affected camera rendering settings, original Quality pipeline reference, and enabled states of the previous generated lights. It disables the owned rig; original shelves, decorations, light objects, and environment objects are not removed. The generated assets are retained for safe reuse.

Use the explicit Restore command rather than relying on Ctrl+Z: Unity Undo does not fully restore project-wide pipeline settings or generated asset files. A later quality-level/pipeline selection is preserved by Restore instead of overwritten; return to the original Quality level and select its recorded prior pipeline manually if you changed levels after Apply.

Apply requires one connected instance of each existing FBX under a common parent with unit world scale, and a Base camera tagged MainCamera whose Volume Mask includes the rig layer (Default). The rig follows that common parent; camera positions and controls stay unchanged. If you make a Save As copy after applying, restore the treatment in that copy before applying again to create independent generated assets.

Reapplying marks reflection captures stale. Validation requires recapture even when older cubemaps still exist. Geometry or material edits made after Apply are reported by validation; restore/reapply after reviewing intentional edits.

Keep the generated assets with the saved scene. They are deliberately separate from your original configuration. Do not delete their folder while a scene or Quality setting still references them. Restore the treatment first if you want to return to the original configuration.

Surface-polish restoration returns the owned properties to the shared material's values while preserving unrelated overrides added by other tools. Unity cannot remove individual keys from a property block, so inert baseline overrides can remain until the scene is reloaded. Restore, save, and reopen the scene to fully clear these transient blocks before judging SRP Batcher eligibility or making further material edits.

The restore operation uses the recorded baseline. Restore first before independently changing settings that the cinematic treatment owns; otherwise those edits can be replaced when restoring or reapplying.

## Optional local baked lighting

The default rig uses real-time lights because the supplied environment does not have a validated lightmap UV2/Contribute GI setup. Applying the treatment does not enable static GI, regenerate mesh UVs, alter FBX importers, or launch a light bake. Baking is optional and requires a separate, deliberate local preparation pass.

For a production bake, work in a separate scene and project/asset copy. Audit or generate non-overlapping lightmap UVs on that copy, select static surfaces that should contribute GI, choose suitable lightmap density, and configure supported Unity Lighting Settings. Avoid lightmapping every tiny grocery at the same density as visible architecture. Once that copy has valid GI preparation, convert appropriate fixture lights to Baked or Mixed and bake in the licensed Unity editor. Keep a small number of useful real-time shadow lights and validate mixed-light behavior in the intended URP build.

Emission applied through property blocks is a presentation effect and is not a substitute for bakeable emissive materials or baked light sources. Use deliberately authored bake inputs in that separate copy if indirect ring glow is required. Recapture reflection cubemaps after a successful bake. No bake result is included or claimed by this change.

## Validation and remaining visual work

Run the repository checks from its root:

```bash
python Tools/check_csharp.py
python Tools/validate_cinematic_lighting_layout.py
python Tools/validate_cinematic_configuration.py
python Tools/validate_material_mapping.py
```

The layout audit checks the real-time shadow budget, finite colors/positions, target ranges, spot-cone coverage at 24 landmarks, and reflection influence coverage on both floors. It cannot evaluate geometry occlusion, bloom, exposure, material appearance, or a finished image. The local **Validate Cinematic Lighting** and material validation commands inspect the instantiated Unity configuration; they should be followed by the Game-view review described above.

The reference remains a visual target. This change strengthens lighting composition and surface presentation while keeping the existing geometry intact. It does not create missing reference detail, simulate volumetric light shafts, add fully dynamic mirror reflections, or guarantee an identical image. Final light balance, exposure, transparent sorting, probe capture quality, and frame time must be checked in an activated Unity editor on the target hardware.

Recorded cloud check results are in [CINEMATIC_VALIDATION.json](CINEMATIC_VALIDATION.json). The C# compile covers the real APIs; the configuration audit also checks the serialized field names against installed URP 17.3 source. Native Apply/reapply/Restore execution, asset import, and reflection capture still require local validation.
