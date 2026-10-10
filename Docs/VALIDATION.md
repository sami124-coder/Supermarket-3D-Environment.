# Validation record — grand retail hall art pass

For the later FBX material-name correction, see [material mapping validation and local repair steps](MATERIAL_REPAIR.md). Its offline regression covers all 2,176 material slots in both FBXs; native Unity import remains subject to the activation limitation below.

## Passed

- All 53 retained CC0 source-model hashes, license notices and standalone model conversions pass integrity checks. Original third-party sources are unchanged.
- The complete static art exports as two native FBX parts: 314 meshes / 3,542,714 triangles in `SipoSupermarket.fbx`, and 71 meshes / 4,467,503 triangles in `SipoMerchandise.fbx`. Total: 385 spatial batches, 8,010,217 triangles, 32 reused grocery types, 84 authored light records and 168 static collision boxes.
- Independent clean Blender imports of **both** FBX parts pass mesh-count, material-name, coordinate-anchor and floor-UV checks. Combined bounds are approximately `(-34.79, -45.44, -0.55)` to `(34.79, 31.95, 16.425)` metres in Blender coordinates, including exterior paving.
- The initial spawn and five existing scenic viewpoints pass floor-support and authored-box clearance checks after expansion. Escalators now have 36 treads per flight, keeping roughly 0.20m rises at the 7.25m gallery height. These checks do not substitute for a Unity walkthrough.
- All four original 1024px linear porcelain surface maps have recorded SHA-256 values in scene metadata. Every mapped material references existing texture files and Unity metadata. Floor UVs survive FBX export/readback.
- Both environment FBXs and both Blender source files stay below GitHub's 100MiB individual-file limit. The main `.blend` uses a relative link to `SipoMerchandiseLibrary.blend`; it opens and renders the complete scene.
- All project C# sources compile against the installed Unity 6000.3.26f1 and URP assemblies. This includes multipart model assembly, texture remapping, expanded reflection probes and visual post-processing. No runtime gameplay C# file changed.
- Art/export/render/validation Python scripts pass syntax compilation. `git diff --check` is clean.
- Nine current previews cover the eight requested subjects and a flagship mascot close-up. They are actual Cycles renders with 32 samples, HDR OIDN denoising and AgX. The PNG manifest records full decoding, opacity/nonblank checks, dimensions and hashes of the images and both Blender source files. Archived previous-pass PNGs retain separate provenance and are also fully decoded by validation.

## Unity activation remains unavailable

The verified official Unity editor installation launches but native batch project creation exits **198**:

> No valid Unity Editor license found. Please activate your license.

The populated `Assets/Scenes/SipoSupermarket.unity`, generated `.mat` files and URP settings assets have therefore **not been produced on this machine**. Native Unity import, shader execution, visual parity, collision traversal and runtime frame-rate/build checks remain untested. C# compilation establishes syntax/API compatibility, not successful engine execution.

Use supported activation and **Sipo → Build supermarket scene** to assemble both FBX parts and the metadata. This art pass has substantially increased geometry and lighting density; target-specific profiling and LODs are needed for production deployment. The cloud machine has no configured Unity graphics display/GPU and uses Debian 13, outside Unity's documented Ubuntu versions.

## Rendering provenance

The current gallery shows actual geometry, licensed assets and authored offline illumination from the linked Blender source. It is not a Unity capture. The verified official Open Image Denoise 2.5.1 release archive checksum is `743c3e2aff8c220d5d70fe6cb970fb3d36f2702d2693c61d1d148e404cf37cd6`. Intermediate HDR buffers and readback reports remain in ignored `Artifacts/`.

Original surface maps provide shared PBR inputs, but offline Cycles transport, AgX, small mascot subsurface/coat refinements and URP rendering remain different. A licensed Unity lighting and reflection pass is required to establish final parity.

## Reproduce checks

```bash
python3 Tools/validate_assets.py
python3 Tools/validate_previews.py
python3 Tools/check_csharp.py
blender -b -t 1 --python-exit-code 1 --python Tools/validate_fbx.py
```

See [PREVIEW_GUIDE.md](PREVIEW_GUIDE.md) for complete-source navigation and current render commands.
