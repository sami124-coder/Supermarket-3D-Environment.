# Asset provenance

The supermarket reuses Kenney models under **Creative Commons Zero 1.0 (CC0)**. The original license notices are retained beside each pack. CC0 permits redistribution and commercial use. No paid Asset Store content or assets of uncertain origin are included.

| Content | Creator / original pack | Retained licensed distribution |
| --- | --- | --- |
| 36 groceries, fruits, vegetables, bakery items, containers and fish | [Kenney Food Kit 1.2](https://kenney.nl/assets/food-kit) | [nrsharip/threejs-food-kit](https://github.com/nrsharip/threejs-food-kit/tree/5d9498cedad3601af796b069213a4f5044ae2525/assets/3d/foodKit_v1.2), commit `5d9498cedad3601af796b069213a4f5044ae2525` |
| 17 furniture, appliance and plant models | [Kenney Furniture Kit 2.0](https://kenney.nl/assets/furniture-kit) | [mr-akashdesai/kitchen-kreation](https://github.com/mr-akashdesai/kitchen-kreation/tree/c80ccdad05628feef41ac7053161731b5c25d5a1/models), commit `c80ccdad05628feef41ac7053161731b5c25d5a1` |

`Assets/ThirdParty/*/manifest.json` records each original file's SHA-256, its retained source path, Unity-native FBX path and measured dimensions. The original files are unchanged. FBX conversions reduce the food materials' metallic value to zero and use roughness 0.42. The supermarket places and batches copies of these models; it does not reconstruct the food from primitives. The visual redesign applies a stronger contrast curve to the placed materials for richer confectionery colors; original source files and standalone conversions are unchanged. The redesigned kitchen reuses six retained Furniture Kit models: kitchenFridgeLarge, kitchenCabinetDrawer, kitchenSink, kitchenCabinet, kitchenCoffeeMachine and toaster. Original source files remain unchanged. Other furniture models remain available for further dressing.

The CC0 legal text is at <https://creativecommons.org/publicdomain/zero/1.0/>. The included original `LICENSE.txt` files identify Kenney and explicitly permit personal, educational and commercial use.

Architecture, original orbit-bear mascots, static first-person hands, candy sculptures and gym equipment, carts, fixtures, lighting, planting arrangements, scene-generation code and exploration code were created for this project. The supplied reference guides composition and art direction; it is not distributed as a texture or model.

Signage uses outlines from **DejaVu Sans Condensed Bold** and **DejaVu Sans Bold Oblique**, converted to mesh geometry. The font's redistribution notice is retained in `Docs/Licenses/DejaVu.txt`. Source regeneration expects the DejaVu fonts installed at their standard Debian paths; the exported model has no font dependency.

Unity and the Universal Render Pipeline retain their own licenses. The editor installation is outside this repository and is not redistributed with the project.

The grand retail hall pass also instances retained tableRound, chairRounded and other furniture into upper boutiques and lounges. Its 1024px porcelain data maps are original procedural project textures. Label graphics, detailed Orbit Club mascot sculptures, shaped leaf meshes, awnings, windows and café/gym dressings are original project geometry. The retained CC0 distribution files and original notices remain unchanged.

## Additive Fresh Produce Department

`ArtSource/SipoFreshProduce.blend` and `Tools/build_fresh_produce.py` create a separate department; the original supermarket Blender files and both environment FBXs remain unchanged. New produce-display fixtures, emerald sign architecture, crates, lettering, decorative icons, foliage arrangements, lighting layout, and procedural surface textures are original project work. The hero apple, orange, pepper, and pear meshes are original project models. The department reuses a copy of the project's original Orbit Club garden mascot, retaining its existing design and materials.

The department also reuses the retained **Kenney Food Kit 1.2 (CC0)** models for banana, broccoli, carrot, grapes, pineapple, cabbage, lemon, watermelon, eggplant, corn, tomato, soda bottle, and fish. These are copies of the already documented source files under `Assets/ThirdParty/KenneyFoodKit/Source/`; the original source and license notices are preserved. `Assets/ThirdParty/KenneyFoodKit/manifest.json` records the retained distributions and hashes. The pack and distribution links in the table above apply to this department as well. No newly downloaded third-party model is required by this module.

All thirteen types are included in the reusable source library. Watermelon, eggplant, and corn are library-only options in this composition; the other ten licensed types are placed in the department.

Sign lettering is exported as geometry from the existing DejaVu font family; the retained notice is `Docs/Licenses/DejaVu.txt`. The user-supplied reference guides architecture, color, density, and composition; it is not redistributed as a texture or used as a flat replacement for the modeled environment.
