# Sipo Supermarket

A colorful, two-level supermarket built around a glowing celestial atrium. The environment follows the supplied reference's orange-and-blue palette, oversized circular canopy, suspended planets, welcoming central desk, lush planting and lively departmental signs.

![Grand atrium — Blender Cycles preview](Docs/Previews/01-grand-atrium.png)

**Major art redesign:** [Comparison, changes and remaining differences](Docs/ART_REDESIGN.md) · [All ten requested views](Docs/GALLERY.md)

**More views:** [Fresh garden](Docs/Previews/02-fresh-garden.png) · [Mezzanine and escalators](Docs/Previews/03-mezzanine.png) · [Grand entrance](Docs/Previews/04-grand-entrance.png)

If an embedded preview displays **"No image"**, use the [direct PNG links and complete 3D preview guide](Docs/PREVIEW_GUIDE.md). The guide also distinguishes the existing `.blend`/FBX assets from the Unity scene that still needs licensed assembly.

## Open in Unity

1. Install **Unity 6000.3.26f1 LTS** in Unity Hub and activate your eligible Unity license.
2. Add this repository folder as a project, then open it. URP **17.3.0** is bundled with this editor.
3. After scripts and assets import, the project assembles and opens `Assets/Scenes/SipoSupermarket.unity` automatically. If automatic assembly was deferred because another scene was dirty, use **Sipo → Build supermarket scene**.
4. Inspect the complete environment in **Scene view**. No Play mode is needed. The generated scene, materials, render settings, lights and colliders are ordinary editable Unity assets.

The first import creates the populated `.unity` scene from the included FBX and `scene-data.json`. The project does not require Blender to open in Unity. Rebuilding through the menu replaces the generated scene; save personal scene edits under a different name before doing so.

**Current validation:** C# compilation, asset integrity checks, FBX export/readback and offline scene rendering are checked independently of Unity activation. Unity project import, Play mode and player builds still require a licensed editor; the cloud editor currently exits with code **198**, reporting no valid license. The preview images are **Blender Cycles renders of the supplied 3D source**, not Unity screenshots. See [validation details](Docs/VALIDATION.md).

## Explore

| Control | Action |
| --- | --- |
| W A S D / arrow keys | Walk |
| Mouse | Look around |
| Shift | Walk faster |
| Escape | Release cursor / pause overlay |
| M | Open the directory and viewpoint map |
| H / F1 | Show controls |
| 1–5 | Visit the entrance, produce garden, atrium, gallery and bakery |
| Home | Return to the entrance |
| F2 | Hide the interface for a clean view |

The escalator treads are walkable stairs with handrail geometry. They are static scenic escalators; automatic passenger transport and tread animation are not implemented. Shopping, checkout transactions and NPCs are outside this environment's scope.

## Included environment

- A 48 × 44 metre market, exterior entrance portal and welcome paving.
- Two levels with a central atrium, mezzanine galleries and twin escalator flights.
- An orange illuminated oculus, star canopy, planets, clouds and an original orbit-bear mascots.
- Produce garden, bakery, snacks, frozen food, drinks, health and beauty, home, toys, a furnished upper-level kitchen and a colorful gym.
- Stocked shelving, pastry displays, an information desk, three checkout lanes and seven nested carts.
- Indoor trees, potted plants, trailing balcony greenery, glossy flowing cobalt/pearl/tangerine floor rings and brass inlays.
- URP Forward+ lighting, bloom, ACES tonemapping, reflection probe and first-person exploration UI.
- 36 retained CC0 grocery models, 27 types placed repeatedly in the scene, plus 17 retained CC0 furniture models, six now reused in the kitchen.
- Magenta lollipop sculptures, glazed doughnut arches, a rainbow drinks island, icy frozen motifs and a separate static first-person hand pose.

The static environment is grouped into **194 spatial mesh batches**, **1,462,868 triangles**, with **39 local lights** and **118 collision volumes**. Individual reusable models are retained separately for editing. This is a desktop-oriented scene; mobile or VR deployment needs profiling and a separate optimization pass.

## Reused assets and licenses

The scene reuses **Kenney Food Kit 1.2**, under **CC0**. Original source assets, FBX conversions, original license files and SHA-256 manifests are included. Kenney Furniture Kit 2.0 supplies the kitchen appliances and cabinets. See [asset credits and provenance](Docs/ASSET_CREDITS.md).

## Files

| Path | Purpose |
| --- | --- |
| `Assets/Environment/SipoSupermarket.fbx` | Complete authored environment, imported natively by Unity |
| `Assets/Environment/scene-data.json` | Material, lighting, collider and viewpoint definitions |
| `Assets/Editor/SupermarketProject.cs` | Scene assembly, URP setup, validation and Linux build menus |
| `Assets/Scripts/Runtime/` | Explorer, map, interface and player factory |
| `Assets/ThirdParty/` | Licensed, reusable source models and FBX conversions |
| `ArtSource/SipoSupermarket.blend` | Editable Blender scene, including preview cameras and lighting |
| `Tools/build_supermarket.py`, `Tools/redesign_art.py` | Existing layout and major visual art pass using retained CC0 assets |
| `Assets/Environment/FirstPersonHands.fbx` | Separate unrigged preview pose, without gameplay behavior |
| `Docs/Previews/` | Offline render evidence |

## Rebuild and validate

From the repository root, with Blender 4.3.2 and DejaVu fonts installed (PNG validation also requires Python Pillow, available as `python3-pil`):

```bash
# Install the checksum-verified render denoiser outside the repository.
bash Tools/install_render_tools.sh

# Rebuild geometry, metadata and editable Blender source; optionally render the hero view.
blender --background --threads 5 --python-exit-code 1 --python Tools/build_supermarket.py -- --render

# Recreate standalone reusable FBX models from their unchanged licensed source files.
blender --background --python-exit-code 1 --python Tools/convert_assets.py

# Check hashes, exports and grounded, obstacle-free viewpoints.
python3 Tools/validate_assets.py

# Check C# against the installed Unity assemblies, without claiming a Play-mode test.
python3 Tools/check_csharp.py --editor /workspace/tools/unity/6000.3.26f1/Editor

# Render other authored views without rebuilding geometry.
blender -b ArtSource/SipoSupermarket.blend -t 5 --python-exit-code 1 \
  --python Tools/render_views.py -- --views=produce,bakery,snacks,drinks,frozen,kitchen,gym,checkout,firstperson,gallery,entrance --samples=24 --percentage=80
```

The source generator overwrites only its documented generated model, metadata, `.blend` and preview outputs. Exported lettering is mesh geometry and needs no installed fonts at runtime.

The preview pipeline uses Cycles, linear HDR buffers, Open Image Denoise 2.5.1 and AgX color management. The denoiser is obtained from the official RenderKit release and checked against its published SHA-256. It is a render-processing tool outside the Unity project; Unity has no dependency on it.

With an activated editor, run these from the repository root:

```bash
/workspace/tools/unity-editor -batchmode -nographics -projectPath "$PWD" \
  -executeMethod Sipo.Editor.SupermarketProject.BuildScene -quit -logFile /tmp/sipo-import.log

/workspace/tools/unity-editor -batchmode -nographics -projectPath "$PWD" \
  -executeMethod Sipo.Editor.SupermarketProject.BuildLinux -quit -logFile /tmp/sipo-build.log
```

Successful scene assembly logs `SIPO_VALIDATION_PASSED` and `SIPO_SCENE_READY`. The Linux player is written to `Builds/Linux/Sipo.x86_64`. Those commands are provided for licensed validation; they have not passed on this unactivated machine.

Each cloud task is already isolated. Use this checkout directly; creating an additional Git worktree is unnecessary.
