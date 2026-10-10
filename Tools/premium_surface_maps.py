"""Original tileable porcelain finishes shared by Blender and Unity 6 URP.

Execute in build_supermarket's globals AFTER static mesh consolidation and BEFORE
writing scene-data / exporting FBX. UVs are authored on the final meshes, so the
static batching step cannot discard them. No external texture sources are used.
"""
import hashlib
import struct
import uuid
import zlib
import numpy as np


def _surface_png(path, pixels):
    """Write lossless, untransformed linear data; alpha is smoothness, not opacity."""
    height, width, channels = pixels.shape
    assert pixels.dtype == np.uint8 and channels in (3, 4)
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    # PNG rows run top to bottom. Reversing makes its UV orientation agree with
    # Blender's image coordinates; both applications read the same saved map.
    rows = b''.join(b'\0' + row.tobytes() for row in pixels[::-1])
    payload = b'\x89PNG\r\n\x1a\n'
    payload += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2 if channels == 3 else 6, 0, 0, 0))
    payload += chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b'')
    path.write_bytes(payload)


def _surface_meta(path, folder=False, normal=False):
    relative = str(path.relative_to(ROOT))
    meta = Path(str(path) + '.meta')
    if meta.exists():
        return
    guid = uuid.uuid5(uuid.NAMESPACE_URL, 'sipo-premium-surface:' + relative).hex
    if folder:
        body = 'folderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n'
    else:
        body = ('TextureImporter:\n  externalObjects: {}\n  serializedVersion: 13\n'
                '  mipmaps:\n    enableMipMap: 1\n    sRGBTexture: 0\n'
                '  textureSettings:\n    serializedVersion: 2\n    filterMode: 1\n    aniso: 8\n'
                '    mipBias: 0\n    wrapU: 0\n    wrapV: 0\n    wrapW: 0\n'
                f'  textureType: {1 if normal else 0}\n  textureShape: 1\n'
                '  alphaSource: 1\n  alphaIsTransparency: 0\n  maxTextureSize: 1024\n'
                '  userData: Original Sipo porcelain surface data; linear color space\n'
                '  assetBundleName:\n  assetBundleVariant:\n')
    meta.write_text('fileFormatVersion: 2\nguid: ' + guid + '\n' + body)


def apply_premium_surface_maps():
    size = 1024
    texdir = OUT / 'Textures'
    texdir.mkdir(exist_ok=True)
    _surface_meta(texdir, folder=True)
    rng = np.random.default_rng(20707)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
    broad = np.zeros((size, size), dtype=np.float32)
    polish = np.zeros_like(broad)
    # Integer periodic harmonics guarantee a seamless tile without edge filtering.
    for layer in range(42):
        limit = 7 if layer < 18 else 64
        fx, fy = rng.integers(1, limit + 1, size=2)
        phase = rng.uniform(0, math.tau)
        wave = np.sin(math.tau * (fx * xx + fy * yy) + phase)
        if layer < 18:
            broad += wave / 18
        else:
            polish += wave / 24
    broad /= max(float(np.max(np.abs(broad))), .001)
    polish /= max(float(np.max(np.abs(polish))), .001)
    height = broad * .00055 + polish * .00009
    spacing = 4.0 / size  # One authored UV tile covers 4 metres.
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) / (2 * spacing)
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) / (2 * spacing)
    vectors = np.stack((-dx, -dy, np.ones_like(height)), axis=-1)
    vectors /= np.linalg.norm(vectors, axis=-1)[..., None]
    normal_path = texdir / 'Porcelain_MicroNormal.png'
    _surface_png(normal_path, np.rint(np.clip(vectors * .5 + .5, 0, 1) * 255).astype(np.uint8))
    _surface_meta(normal_path, normal=True)
    normal_image = bpy.data.images.load(str(normal_path), check_existing=True)
    normal_image.colorspace_settings.name = 'Non-Color'
    normal_image.filepath = '//../Assets/Environment/Textures/' + normal_path.name
    entries = []
    floor_names = set()
    for spec in DATA['materials']:
        if not spec['name'].startswith('SIPO_Floor'):
            continue
        material = bpy.data.materials.get(spec['name'])
        if material is None:
            continue
        floor_names.add(spec['name'])
        rough = np.clip(spec['roughness'] + broad * .010 + polish * .003, .045, .28)
        packed = np.zeros((size, size, 4), dtype=np.uint8)
        packed[..., 0] = round(spec['metallic'] * 255)
        packed[..., 3] = np.rint((1 - rough) * 255).astype(np.uint8)
        packed_path = texdir / (spec['name'].removeprefix('SIPO_') + '_MetallicSmoothness.png')
        _surface_png(packed_path, packed)
        _surface_meta(packed_path)
        packed_image = bpy.data.images.load(str(packed_path), check_existing=True)
        packed_image.colorspace_settings.name = 'Non-Color'
        # Alpha stores an independent scalar, not transparency or premultiplication.
        packed_image.alpha_mode = 'CHANNEL_PACKED'
        packed_image.filepath = '//../Assets/Environment/Textures/' + packed_path.name
        nodes, links = material.node_tree.nodes, material.node_tree.links
        p = nodes.get('Principled BSDF')
        normal_texture = nodes.new('ShaderNodeTexImage')
        normal_texture.name = 'Original porcelain micro-normal'
        normal_texture.image = normal_image
        normal_texture.interpolation = 'Linear'
        normal = nodes.new('ShaderNodeNormalMap')
        normal.name = 'Subtle polished porcelain finish'
        normal.inputs['Strength'].default_value = .35
        links.new(normal_texture.outputs['Color'], normal.inputs['Color'])
        links.new(normal.outputs['Normal'], p.inputs['Normal'])
        packed_texture = nodes.new('ShaderNodeTexImage')
        packed_texture.name = 'URP metallic R and smoothness A'
        packed_texture.image = packed_image
        channels = nodes.new('ShaderNodeSeparateColor')
        links.new(packed_texture.outputs['Color'], channels.inputs['Color'])
        links.new(channels.outputs['Red'], p.inputs['Metallic'])
        roughness = nodes.new('ShaderNodeMath')
        roughness.operation = 'SUBTRACT'
        roughness.inputs[0].default_value = 1
        links.new(packed_texture.outputs['Alpha'], roughness.inputs[1])
        links.new(roughness.outputs[0], p.inputs['Roughness'])
        spec.update(normalMap=str(normal_path.relative_to(ROOT)),
                    metallicGlossMap=str(packed_path.relative_to(ROOT)),
                    normalScale=.35, textureScale=[1, 1])
        entries.append({'material': spec['name'], 'normalMap': spec['normalMap'],
                        'metallicGlossMap': spec['metallicGlossMap'], 'tileMetres': 4,
                        'normalConvention': 'OpenGL +Y tangent space',
                        'packedChannels': 'R metallic, A smoothness; linear import'})
    mapped_meshes = 0
    for obj in scene.objects:
        if obj.type != 'MESH' or not any(m and m.name in floor_names for m in obj.data.materials):
            continue
        mesh = obj.data
        uv = mesh.uv_layers.get('SurfaceUV') or mesh.uv_layers.new(name='SurfaceUV')
        coords = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
        values = [value for loop in mesh.loops for value in
                  (coords[loop.vertex_index].x / 4, coords[loop.vertex_index].y / 4)]
        uv.data.foreach_set('uv', values)
        mesh.uv_layers.active = uv
        mapped_meshes += 1
    DATA['surfaceTextures'] = {'authorship': 'Original procedural Sipo porcelain; no external textures',
                               'resolution': [size, size], 'uvMappedMeshes': mapped_meshes,
                               'materials': entries,
                               'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in sorted(texdir.glob('*.png'))}}
    print('SIPO_SURFACE_MAPS: %d materials, %d UV-mapped mesh batches' %
          (len(entries), mapped_meshes), flush=True)


apply_premium_surface_maps()
