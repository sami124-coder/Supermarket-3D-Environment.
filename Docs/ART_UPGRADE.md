# Grand retail hall — ambitious art upgrade

The existing Sipo project has been expanded and redressed around the reference's dense orange/cobalt retail fantasy. This pass changes environment art, visual import settings and scene metadata. Runtime gameplay scripts are unchanged.

## What improved

| Area | Previous pass | Current art |
| --- | --- | --- |
| Scale | 49 × 45m foundation, 28m clear atrium, 5.8m mezzanine, 13m ceiling | 69.58 × 63.9m foundation, 39.76m clear atrium, 7.25m mezzanine, 16.25m ceiling. Floor area approximately doubles. Human props and coherent decorative groups retain their local proportions. |
| Reception | Solid round counter filling much of the foreground | Human-height open crescent, ivory worktop, brass fluting, fine illuminated bands, visitor leaflets, terminals and a seated mascot; longer clear approach. |
| Planetarium | Flat midnight disc, one dominant ring, sparse ornaments | Vaulted cobalt starfield, hundreds of modelled stars, additional orbital rail/jewels, layered striped planets, Saturn rings, sculpted clouds and hanging five-pointed stars. Roof framing sits above the dome. |
| Flagship character | Primitive bear with simple spherical eyes and limbs | Five original Orbit Club sculptures: sculpted cheek/jaw surfaces, recessed ears, iris fibers, eyelids, brows, muzzle and smile, tailored sleeves, padded paws, molded boots, stitch details, zipper teeth and themed accessories. Includes a dedicated close-up render. |
| Merchandise | Repeated sparse front rows | 1,667 additional licensed groceries, 225 original packaged items, 33 stocked displays and 26 pastry trays. Multirow shelf stock, dividers, price cards, label graphics, glaze variety and shaped display stands. |
| Bakery | A few cakes and pastries | Dense glass-front pastry vitrine, baguette stand, celebration-cake columns, macaron tower, oversized glazed doughnuts and detailed chef mascot. |
| Frozen | Plain island and basic crystal cylinders | Stocked glazed cabinets, retail cartons, cold cabinet detail, two full glass-door freezer towers, pointed crystals and snowflake ornaments. |
| Drinks / candy | Sparse circular towers | Labelled juice bottles/cartons, color bands and detailed stepped displays; candy jars, loose sweets, gift cartons and giant bonbons alongside spiral lollipops. |
| Produce / gardens | Ellipsoid leaf blobs | Sorted fruit abundance, harvest-crate satellites, orchard branches, 10,739 curved leaves with midribs, 156 flowers and 83 botanical assemblies. Cascading balcony gardens keep the bakery frontage open. |
| Upper floor | Flat repeated signs and generic shelves | Five deep dimensional boutiques: HOME STUDIO, LITTLE WONDERS, SUNSHINE CAFÉ, PLAY PLANET and BOTANICA. Brass arches, striped/scalloped awnings, lit cabinets, window vignettes, café servery, furnished lounges and richer promenade rails. Kitchen dressing and static gym cycles/storage are added. |
| Surface / lighting | Solid colors, broad washes, small reflection probe | Original 1024px porcelain normal and packed metallic/smoothness maps, explicit floor UVs, local retail light pools, cool canopy uplights, higher-resolution overlapping Unity reflection probes and updated visual post-processing. |

## Updated models, materials and sources

- `Assets/Environment/SipoSupermarket.fbx`: architecture, themed fixtures, mascots, foliage and mezzanine geometry.
- `Assets/Environment/SipoMerchandise.fbx`: the dense product/merchandising geometry. **Both FBXs form the complete environment**; the first file alone is incomplete.
- `ArtSource/SipoSupermarket.blend`: complete scene, lights and thirteen cameras, with merchandise linked from `ArtSource/SipoMerchandiseLibrary.blend`. Keep both files together; opening the main file shows the complete scene.
- `Assets/Environment/FirstPersonHands.fbx`: separate static illustration pose, updated for the current camera. It remains unrigged and is excluded from the two environment FBXs.
- `Assets/Environment/Textures/`: original porcelain micro-normal and three metallic/smoothness maps. Maps and Unity `.meta` files are included; no external texture license is required.
- `Assets/Environment/scene-data.json`: both model paths, material maps, expanded bounds, lighting/collision/view metadata and recorded art counts.
- `Assets/Editor/SupermarketProject.cs`: imports both FBX parts, remaps surface maps to URP/Lit, and configures reflection coverage and visual post-processing.
- `Tools/premium_*.py`, `Tools/expand_retail_hall.py`, `Tools/export_premium_environment.py`, `Tools/link_merchandise_source.py`: reproducible specialist art and portable source/export packaging.

The retained Kenney CC0 source files are unchanged. More of the retained groceries and furniture are reused in the new boutiques and lounges. Fonts remain mesh outlines from the licensed DejaVu family. All newly authored labels, character sculptures, leaf meshes and fixtures are original project art.

## What still differs from the reference

The building, floor ribbons, branding and mascot are an original interpretation rather than an exact reconstruction. The floor uses broad circular ribbons, while the reference mixes smaller tiles and colorful arcs. Packaging lacks the reference's illustrated label density and many tiny architectural details. Peripheral walls and overhead planting are still less layered than the reference. Plants and food retain a deliberately stylized treatment. The mascot's silhouette and prominent eye treatment differ from the reference's softer character finish. Characters are static sculptures with detailed surfaces; they have no production rig, facial animation or simulated fur.

These previews use Cycles light transport, HDR denoising and AgX. Unity URP still requires licensed import, lighting/reflection tuning and platform profiling; matching Unity appearance and performance have not been established on this machine. The dense static model contains roughly **8.01 million triangles** and needs target-specific LOD/optimization work for mobile, VR or constrained desktop hardware. The user-requested fidelity takes priority in this art delivery.

## Review the environment

The [current gallery](GALLERY.md) contains the eight requested subjects plus the mascot close-up. The [preview guide](PREVIEW_GUIDE.md) explains complete Blender inspection and Unity assembly. Older entrance/kitchen/gym/checkout renders are retained under `Docs/Previews/Archive` and explicitly marked as previous-pass images.
