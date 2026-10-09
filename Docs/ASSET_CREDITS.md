# Asset provenance

The supermarket reuses Kenney models under **Creative Commons Zero 1.0 (CC0)**. The original license notices are retained beside each pack. CC0 permits redistribution and commercial use. No paid Asset Store content or assets of uncertain origin are included.

| Content | Creator / original pack | Retained licensed distribution |
| --- | --- | --- |
| 36 groceries, fruits, vegetables, bakery items, containers and fish | [Kenney Food Kit 1.2](https://kenney.nl/assets/food-kit) | [nrsharip/threejs-food-kit](https://github.com/nrsharip/threejs-food-kit/tree/5d9498cedad3601af796b069213a4f5044ae2525/assets/3d/foodKit_v1.2), commit `5d9498cedad3601af796b069213a4f5044ae2525` |
| 17 optional furniture, appliance and plant models | [Kenney Furniture Kit 2.0](https://kenney.nl/assets/furniture-kit) | [mr-akashdesai/kitchen-kreation](https://github.com/mr-akashdesai/kitchen-kreation/tree/c80ccdad05628feef41ac7053161731b5c25d5a1/models), commit `c80ccdad05628feef41ac7053161731b5c25d5a1` |

`Assets/ThirdParty/*/manifest.json` records each original file's SHA-256, its retained source path, Unity-native FBX path and measured dimensions. The original files are unchanged. FBX conversions reduce the food materials' metallic value to zero and use roughness 0.42. The supermarket places and batches copies of these models; it does not reconstruct the food from primitives. The optional furniture models are supplied for further dressing, separate from the custom architectural fixtures.

The CC0 legal text is at <https://creativecommons.org/publicdomain/zero/1.0/>. The included original `LICENSE.txt` files identify Kenney and explicitly permit personal, educational and commercial use.

Architecture, original sun mascot, carts, fixtures, lighting, planting arrangements, scene-generation code and exploration code were created for this project. The supplied reference guides composition and art direction; it is not distributed as a texture or model.

Signage uses outlines from **DejaVu Sans Condensed Bold** and **DejaVu Sans Bold Oblique**, converted to mesh geometry. The font's redistribution notice is retained in `Docs/Licenses/DejaVu.txt`. Source regeneration expects the DejaVu fonts installed at their standard Debian paths; the exported model has no font dependency.

Unity and the Universal Render Pipeline retain their own licenses. The editor installation is outside this repository and is not redistributed with the project.
