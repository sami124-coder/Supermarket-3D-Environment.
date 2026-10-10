# Fantasy supermarket — visual redesign

This art pass revises the existing supermarket. The building footprint, two floors, mezzanine circulation, escalators, asset provenance and Unity integration are retained. No gameplay or mechanics were added or changed.

## Comparison with the supplied reference

The previous version had a recognizable orange halo and two-floor layout, but the cream/blue checkerboard, small flat signs, repeated straight shelves and sparse centerpieces made it feel like a conventional shop. The reference has much stronger circular rhythms, character-led branding, saturated departmental landmarks, layered greenery and decorative spectacle.

| Area | Implemented visual change |
| --- | --- |
| Central atrium | Flowing cobalt, pearl and tangerine floor rings; glossy low-roughness enamel; lobed luminous Sipo brand silhouette; giant original orbit-bear mascot and small welcome-desk character; brighter blue star canopy; richer balcony vines. Existing huge orange oculus, planets, clouds, welcome desk and open two-story volume retained. |
| Fresh produce | Larger illuminated green garden crown, tiered CC0 fruit abundance with richer placed-copy colors, flower ornaments and elevated green mascot around the existing central tree. |
| Bakery | Orange halo, giant strawberry-glazed doughnuts with sprinkles, tiered birthday cakes, chef bear and cleared display frontage. |
| Snacks | Magenta circular island and halo; three enormous spiral lollipops; rings of pastries and candy-colored accents. |
| Drinks | Orange circular bar with three stepped rings of licensed bottles, rainbow label sleeves, giant orange fruit and straw. |
| Frozen | Cobalt halo, cyan freezer island, glazed lids, faceted ice pillars and suspended luminous snowflakes. |
| Kitchen | Upper west gallery: teal feature wall with KITCHEN lettering, orange cooking island and extractor, visible copper cookware and induction rings, six reused CC0 cabinet/appliance models. |
| Gym | Upper east gallery: purple GYM feature wall, turquoise/orange static treadmills, pink dumbbells, yoga mat and oversized yellow exercise ball. |
| Checkout | Teal illuminated crown, clear CHECKOUT lettering, cashier mascot, groceries on belts and glowing trim. Middle counter moved clear of a structural column. |
| First person | A 1.7-metre eye-height camera and separate modelled sleeve/hand pose. Hands are a static illustration asset, not rigged or connected to controls. |

## Updated deliverables

- `ArtSource/SipoSupermarket.blend`: complete revised scene, 12 named cameras, actual geometry and authored offline lighting. The first-person hand objects are tagged `preview_hands` and hidden from other renders.
- `Assets/Environment/SipoSupermarket.fbx`: updated full static environment; excludes the preview hands.
- `Assets/Environment/FirstPersonHands.fbx`: separate static art pose in camera-local coordinates; does not attach itself to a Unity camera. Remap its materials to URP/Lit if using it independently.
- `Assets/Environment/scene-data.json`: current material definitions, lighting, collision boxes and department metadata.
- `Tools/build_supermarket.py`, `Tools/redesign_art.py`, `Tools/preview_hands.py`: reproducible art authoring/export pipeline using the retained asset sources.
- `Tools/render_views.py`, `Tools/validate_previews.py`: all camera render selections and full PNG validation.
- All twelve `Docs/Previews/*.png` images, including the ten requested subjects plus mezzanine and entrance views.

The runtime C# files and gameplay systems were not modified. Existing FBX GUIDs are preserved. The original licensed asset files are unchanged.

## What still differs from the reference

This is a stylized, modelled environment rather than a pixel-identical reconstruction. It has lower product/foliage density, simpler plant silhouettes, simpler packaging without illustrated brand labels, less elaborate animal anatomy and fewer fine architectural details than the reference. Its original bear mascot and dimensional cloud-shaped sign differ from the reference's character and logo treatment. The new hands are an unrigged, simplified static pose.

The Cycles previews use offline reflections, light transport and denoising. Unity URP needs a licensed import and a lighting/reflection tuning pass to establish equivalent appearance; these images do not demonstrate Unity performance or parity. The scene is intended for desktop and still needs runtime profiling, LODs and production optimization for a target platform.

## Preview and integration

Use the [complete gallery and preview guide](PREVIEW_GUIDE.md). Open the saved `.blend` to inspect both floors immediately; regeneration is unnecessary. In Unity, use the existing **Sipo → Build supermarket scene** menu after licensed import to assemble the updated FBX and metadata. Save customized scenes before running that command because it replaces the generated scene. Inspect Scene view without entering Play mode.
