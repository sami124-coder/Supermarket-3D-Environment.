# Preview the existing supermarket

## Open the images directly

These links open the PNG bytes rather than an embedded chat preview. If a chat displays "No image", use the direct link or download the file from GitHub.

| View | Direct PNG | Resolution |
| --- | --- | --- |
| Grand atrium | [Open image](https://raw.githubusercontent.com/sami124-coder/Supermarket-3D-Environment./main/Docs/Previews/01-grand-atrium.png) | 1600 × 1000 |
| Fresh garden | [Open image](https://raw.githubusercontent.com/sami124-coder/Supermarket-3D-Environment./main/Docs/Previews/02-fresh-garden.png) | 1280 × 800 |
| Mezzanine and escalators | [Open image](https://raw.githubusercontent.com/sami124-coder/Supermarket-3D-Environment./main/Docs/Previews/03-mezzanine.png) | 1280 × 800 |
| Grand entrance | [Open image](https://raw.githubusercontent.com/sami124-coder/Supermarket-3D-Environment./main/Docs/Previews/04-grand-entrance.png) | 1280 × 800 |

`Docs/Previews/manifest.json` records the decoded format, dimensions, byte size and SHA-256 of every preview. These are conventional Blender renders of the supplied environment, not screenshots from Unity.

## Inspect the complete 3D environment in Blender

1. Download or clone [the repository](https://github.com/sami124-coder/Supermarket-3D-Environment.).
2. Open **`ArtSource/SipoSupermarket.blend`** in Blender 4.3.2 or a compatible newer version.
3. In the 3D Viewport, press **Home** to frame the environment. Orbit with the middle mouse button; pan with Shift + middle mouse; zoom with the wheel. This lets you inspect both floors, the entrance, stocked aisles, checkouts, carts and the suspended ceiling installation.
4. Press **Numpad 0** for the saved atrium camera. The Outliner contains four named cameras: `01 Grand atrium`, `02 Fresh garden`, `03 Mezzanine`, and `04 Grand entrance`. Select a camera and use **View → Cameras → Set Active Object as Camera** to switch views.
5. Use **Material Preview** for fast inspection of the colors. For the authored illumination, use **Rendered** viewport shading with scene lights/world, or render the camera with **F12**. Interactive rendering speed depends on your machine; the supplied PNGs are already finished.
6. For a walkthrough without Unity or gameplay, use Blender's **View → Navigation → Walk Navigation**. Use WASD and the mouse to move and look around; Esc exits. Solid or Material Preview shading is faster for navigation than CPU-rendered shading.

Opening or navigating this file does not rebuild the supermarket. Blender does not require Unity activation. Built-in Blender denoising is disabled for compatibility with this cloud image; the supplied final PNGs use the separate verified OIDN render helper.

## Actual 3D files included

| File | What it contains |
| --- | --- |
| `ArtSource/SipoSupermarket.blend` | Complete editable scene, 166 spatial mesh batches, 29 local lights, materials and four preview cameras. |
| `Assets/Environment/SipoSupermarket.fbx` | Complete static environment geometry and materials, plus coordinate markers. Approximately 966k triangles. Imports natively in Unity. Cameras, light objects and physics are not embedded in this FBX. |
| `Assets/Environment/scene-data.json` | URP material properties, transparent glazing, 29 local-light definitions, 116 collision boxes and existing view/department definitions. It is data, not a standalone Unity scene. |
| `Assets/ThirdParty/KenneyFoodKit/Models/*.fbx` | 36 separately reusable, converted CC0 food models; original GLB sources and license included. |
| `Assets/ThirdParty/KenneyFurnitureKit/Models/*.fbx` | 17 separately reusable CC0 furniture, appliance and plant models; original sources and license included. |

The `.blend` and full-environment FBX have both been opened successfully in Blender. An independent FBX readback confirms mesh count, coordinate markers, materials and metre-scale bounds. Third-party source hashes are recorded in each pack's manifest.

**Not yet created:** `Assets/Scenes/SipoSupermarket.unity` and the generated Unity `.mat`/URP settings assets. There is no completed Unity player build. The current machine's Unity activation blocker prevented those operations.

## What is ready for Unity 6 URP

The geometry, licensed reusable models, material/lighting/collision metadata and editor assembly code are present. The project pins **Unity 6000.3.26f1** and **URP 17.3.0**. The C# sources compile against that editor's assemblies, but Unity asset import, shader execution and scene appearance have not been validated in a licensed editor.

To inspect the existing project in Unity:

1. Activate Unity through your supported licensing route and open this repository in Unity Hub using the pinned editor version.
2. Let scripts and assets import. The existing editor code assembles the supplied FBX and metadata into `Assets/Scenes/SipoSupermarket.unity` on first import. If automatic assembly is deferred, use **Sipo → Build supermarket scene**. This assembles the existing assets; it does not regenerate the model from scratch.
3. Inspect the resulting environment in **Scene view**. No Play mode or gameplay is required to view it. The generated scene contains separate environment, lighting and collision roots; the pre-existing explorer can be disabled when using the scene solely as an environment.

For integration into another Unity 6 URP project, the FBX and individual licensed models can be imported directly as static assets. Remap their materials to **Universal Render Pipeline/Lit**, including transparent glazing. An FBX-only import does **not** recreate the authored lights, collision boxes, reflection probe or post-processing; apply the supplied metadata/editor workflow for those. The existing scene builder expects the repository's asset paths, so copying only the FBX does not activate that workflow.

No scene reconstruction or gameplay implementation was performed as part of this preview verification.
