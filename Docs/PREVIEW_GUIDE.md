# Preview the complete grand retail hall

## Current renders

Use the direct PNG links if an embedded chat image says “No image”. The [gallery](GALLERY.md) displays every current view together.

| Requested view | Direct PNG |
| --- | --- |
| Central atrium | [Open](https://raw.githubusercontent.com/sami124-coder/Supermarket-3D-Environment./main/Docs/Previews/01-grand-atrium.png) |
| Bakery | [Open](https://raw.githubusercontent.com/sami124-coder/Supermarket-3D-Environment./main/Docs/Previews/05-bakery.png) |
| Frozen | [Open](https://raw.githubusercontent.com/sami124-coder/Supermarket-3D-Environment./main/Docs/Previews/08-frozen.png) |
| Drinks | [Open](https://raw.githubusercontent.com/sami124-coder/Supermarket-3D-Environment./main/Docs/Previews/07-drinks.png) |
| Snacks | [Open](https://raw.githubusercontent.com/sami124-coder/Supermarket-3D-Environment./main/Docs/Previews/06-snacks.png) |
| Fresh produce | [Open](https://raw.githubusercontent.com/sami124-coder/Supermarket-3D-Environment./main/Docs/Previews/02-fresh-garden.png) |
| Mezzanine / upper level | [Open](https://raw.githubusercontent.com/sami124-coder/Supermarket-3D-Environment./main/Docs/Previews/03-mezzanine.png) |
| First-person with static hands | [Open](https://raw.githubusercontent.com/sami124-coder/Supermarket-3D-Environment./main/Docs/Previews/12-first-person.png) |
| Flagship mascot close-up | [Open](https://raw.githubusercontent.com/sami124-coder/Supermarket-3D-Environment./main/Docs/Previews/13-mascot-detail.png) |

These are Blender Cycles renders of the actual 3D scene. Atrium is 1600 × 1000; the remaining current images are 1280 × 800. `Docs/Previews/manifest.json` records full PNG decoding, dimensions, opacity/nonblank checks, individual hashes and both source-file hashes. Previous-pass images live in `Docs/Previews/Archive` with separate provenance.

## Inspect both floors in Blender

1. Clone or download the complete repository. Keep **both** `ArtSource/SipoSupermarket.blend` and `ArtSource/SipoMerchandiseLibrary.blend` together. Also retain `Assets/Environment/Textures` at its repository path.
2. Open `ArtSource/SipoSupermarket.blend` in Blender 4.3.2 or a compatible newer version. The merchandise library loads automatically using its relative path. The complete environment is visible without running generation scripts.
3. Press **Home** to frame the scene. Orbit with the middle mouse, pan with Shift + middle mouse, and zoom with the wheel.
4. Press **Numpad 0** for the atrium camera. Select another numbered camera in the Outliner and use **View → Cameras → Set Active Object as Camera**. Thirteen cameras include optional kitchen, gym, checkout and entrance views as well as the nine current rendered subjects.
5. Use **Material Preview** for quick inspection or **Rendered** shading with scene lights/world for authored illumination.
6. Use **View → Navigation → Walk Navigation** for a Blender walkthrough. WASD and the mouse move/look; Esc exits. This requires no gameplay implementation.

The linked merchandise objects are editable in their library file. Open `SipoMerchandiseLibrary.blend` to edit them, then reload the main scene; for local edits instead, use Blender's supported Library Override workflow. The main scene's architecture, foliage and mascots remain directly editable.

The static hands are hidden from ordinary renders. `Tools/render_views.py --views=firstperson` unhides them for that camera. They are an optional unrigged art pose, not a camera controller or hand animation system.

## Actual Unity-ready files

| File | Contents |
| --- | --- |
| `Assets/Environment/SipoSupermarket.fbx` | Architecture, original mascots, foliage, themed fixtures and upper-floor geometry. |
| `Assets/Environment/SipoMerchandise.fbx` | Dense shelves, groceries, pastry/juice/candy/frozen merchandise. Both FBX files are required for the complete scene. |
| `Assets/Environment/FirstPersonHands.fbx` | Separate static sleeve/hand illustration pose; not attached by the scene builder. |
| `Assets/Environment/scene-data.json` | Both model-part paths, material/texture mappings, expanded bounds, lights, collision boxes, views and art counts. |
| `Assets/Environment/Textures/*.png` | Original linear porcelain normal and packed metallic/smoothness maps with Unity import metadata. |
| `Assets/ThirdParty/*/Models/*.fbx` | 53 separately reusable CC0 food/furniture models, with unchanged original sources and license records. |

The complete static environment totals approximately 8.01 million triangles. The two FBX parts and the two Blender files stay below GitHub's individual file limit.

## Assemble in Unity 6 URP

1. Activate Unity **6000.3.26f1** through your supported licensing route and open this repository. It pins **URP 17.3.0**.
2. Let assets/scripts import. On a fresh licensed import, the existing assembly code creates `Assets/Scenes/SipoSupermarket.unity`. For an already-imported project, use **Sipo → Build supermarket scene** to load the revised art and metadata. Save customized scenes under another name first: this command replaces the generated scene.
3. Inspect the environment in **Scene view**. The builder imports and aligns both FBX parts, applies URP/Lit materials and texture maps, expanded reflection probes, local lights, post-processing and the authored collision boxes. No Play mode is required for an environment review.

**Not yet created on this machine:** the populated `.unity` scene and generated `.mat`/URP settings assets. Unity activation is still unavailable, so native import, shader appearance, performance and a Unity walkthrough have not been tested. C# compilation, offline asset checks and independent FBX readback are recorded in [VALIDATION.md](VALIDATION.md).

Copying only the first FBX into another project omits merchandise. Copy both parts and the textures; remap their materials to URP/Lit or use the supplied metadata/editor workflow. FBX-only import does not recreate the lights, reflections, post-processing or collision boxes.

## Regenerate renders without regenerating geometry

```bash
bash Tools/install_render_tools.sh
blender -b ArtSource/SipoSupermarket.blend -t 5 --python-exit-code 1 \
  --python Tools/render_views.py -- --views=hero --samples=32 --percentage=100
blender -b ArtSource/SipoSupermarket.blend -t 5 --python-exit-code 1 \
  --python Tools/render_views.py -- \
  --views=bakery,frozen,drinks,snacks,produce,gallery,firstperson,mascot \
  --samples=32 --percentage=80
python3 Tools/validate_previews.py
```

Opening and exploring the saved `.blend` does not require the denoiser. The helper requires the installed official OIDN executable and Python PNG validation requires Pillow.
