# Validation record

## Passed

- Installed **Unity 6000.3.26f1** from official Unity HTTPS release metadata. Checked the downloaded archive against the official published integrity value and byte count before extracting. The editor's `-version` command succeeds; all inspected shared-library dependencies resolve.
- Re-ran the installation script against the retained installation successfully. Workspace-local XDG configuration/cache/data paths remove the original read-only home-directory errors.
- Compiled all project C# sources with the editor's bundled Roslyn compiler against the actual UnityEngine, UnityEditor and URP template assemblies. `Tools/check_csharp.py` exits 0 with no compiler errors. This validates C# syntax and API compatibility, not native engine execution.
- Verified SHA-256 hashes for all 53 retained CC0 source models, original license notices and standalone FBX conversions.
- Generated the full environment FBX and editable `.blend` source. The export has 166 spatial mesh batches, 965,583 triangles, 23 reused grocery model types, 29 authored local lights and 116 collision volumes.
- Independently re-imported the exported FBX in a clean Blender process. Verified all 166 meshes, material mappings, coordinate markers and metric bounds. Bounds in Blender coordinates are approximately `(-24.5, -32.0, -0.44)` to `(24.5, 22.5, 13.14)` metres, including the exterior paving.
- Checked the initial spawn and all five scenic viewpoints for floor support and clearance from authored collision boxes. Corrected the bakery viewpoint that initially intersected a stocked shelf.
- Verified the Open Image Denoise 2.5.1 archive against the SHA-256 published on its official RenderKit GitHub release: `743c3e2aff8c220d5d70fe6cb970fb3d36f2702d2693c61d1d148e404cf37cd6`.
- Rendered and visually inspected the grand atrium (1600 × 1000), mezzanine (1280 × 800) and entrance (1280 × 800). All three use actual scene geometry, Cycles, 24 samples and an HDR denoising pass. Corrected the entrance glazing to use transmission in the source and transparent materials in Unity; C# compilation and FBX readback passed again after that change.

## Unity activation blocker

An isolated scratch project creation attempt with `-batchmode -nographics -createProject` exits **198** and reports:

> No valid Unity Editor license found. Please activate your license.

The result remains the same with writable XDG paths. No credentials were requested in chat, stored in the repository, fabricated or used to bypass activation. Unity Personal uses Unity Hub sign-in; organization licensing must follow its supported route.

Because this prerequisite is unresolved, the following have **not run successfully**:

- Unity's asset/package import and automatic populated-scene assembly.
- Play-mode movement, controls, collision traversal and graphical inspection.
- Shader compilation/rendering in Unity, runtime frame-rate profiling and Linux player build.

`Assets/Scenes/SipoSupermarket.unity` is created on the first successful licensed import by `Sipo.Editor.SupermarketProject`. The included FBX and metadata already contain the authored environment. The scene builder includes native checks for imported renderers, missing materials, collision count, one player and ground below the spawn. These checks are provided but are not reported as passed here.

The cloud machine is Debian 13, while Unity documents Ubuntu 22.04/24.04 support. The installed editor resolves its libraries and launches far enough to check licensing; that does not establish full platform compatibility. There is no configured graphical display or GPU for a Unity visual test.

## Preview provenance

Preview images under `Docs/Previews` are rendered from `ArtSource/SipoSupermarket.blend` using **Blender Cycles**, a linear HDR denoising pass and AgX color management. They show the actual authored geometry, licensed models, materials and offline lighting. They are **not Unity screenshots** and do not prove matching Unity lighting or runtime performance.

The initial test render was overexposed. Exposure was reduced to preserve the saturated orange/blue palette. The machine's Blender build lacks built-in OpenImageDenoise support, so the reproducible rendering helper uses the separately checksum-verified official OIDN executable. Intermediate HDR buffers and compiler reports are kept in ignored `Artifacts/`.

## Reproduction

From the repository root:

```bash
python3 Tools/validate_assets.py
python3 Tools/check_csharp.py
blender --background --threads 1 --python-exit-code 1 --python Tools/validate_fbx.py
```

See the README for the licensed Unity validation/build commands and source rendering commands. A saved cloud configuration draft is not publication or validation in a fresh task.
