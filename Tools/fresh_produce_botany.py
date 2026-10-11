"""Original SIPO orchard tree and potted botanical meshes for Blender 4.3+.

This module has no import-time scene effects.  Its closed, curved leaf topology
is adapted from the project's original ``premium_botanical.BotanicalMesh``;
that older script is deliberately not executed because it mutates the old shop.
Geometry uses metres, Blender Z up, with the centre of the produce island at
the origin.  The caller owns grouping, export, material serialization and LODs.
No alpha cards, downloaded textures or third-party geometry are required.
"""

import math
import random

import bpy
from mathutils import Vector


PALETTE = (
    ('Emerald', '167640', .32, 0),
    ('Jade', '23854A', .31, 0),
    ('Lime', '75AD3D', .35, 0),
    ('NewGrowth', 'AFCC59', .36, 0),
    ('Rib', 'ABC76A', .4, 0),
    ('Bark', '865126', .46, 0),
    ('BarkLight', 'AF7139', .43, 0),
    ('BarkDark', '623C21', .5, 0),
    ('Stem', '607A2E', .4, 0),
    ('PotGreen', '0C5340', .25, .22),
    ('PotGold', 'DDA746', .25, .8),
    ('Soil', '302C20', .83, 0),
)


def _linear(value):
    return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4


def _materials():
    result = []
    for key, rgb, roughness, metallic in PALETTE:
        name = 'SIPO_FP_Bot' + key
        mat = bpy.data.materials.get(name)
        if mat is None:
            mat = bpy.data.materials.new(name)
            mat.use_nodes = True
            color = tuple(_linear(int(rgb[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1,)
            mat.diffuse_color = color
            bsdf = mat.node_tree.nodes.get('Principled BSDF')
            bsdf.inputs['Base Color'].default_value = color
            bsdf.inputs['Roughness'].default_value = roughness
            bsdf.inputs['Metallic'].default_value = metallic
            if key in ('Emerald', 'Jade', 'Lime', 'NewGrowth'):
                bsdf.inputs['Subsurface Weight'].default_value = .035
                bsdf.inputs['Coat Weight'].default_value = .16
                bsdf.inputs['Coat Roughness'].default_value = .3
            mat['sipo_source_srgb_hex'] = rgb
            mat['sipo_license'] = 'Original project-authored geometry and materials'
        result.append(mat)
    return result


class BotanicalMesh:
    """Batched closed leaves, ribs and tapered stems; one mesh per assembly."""

    def __init__(self, name, anchor=(0, 0, 0), materials=None):
        self.name = name
        self.anchor = Vector(anchor)
        self.vertices, self.faces, self.indices = [], [], []
        self.materials = materials if materials is not None else _materials()
        self.leaves = 0

    def geometry(self, vertices, faces, material):
        offset = len(self.vertices)
        self.vertices.extend(tuple(Vector(v) - self.anchor) for v in vertices)
        self.faces.extend(tuple(offset + i for i in face) for face in faces)
        if isinstance(material, int):
            self.indices.extend([material] * len(faces))
        else:
            self.indices.extend(material)

    def tube(self, points, radii, material=5, sides=8, flute=0):
        """Continuous tapered branch rings with subtle bark-colour striping."""
        points = [Vector(p) for p in points]
        vertices, faces, indices = [], [], []
        for i, (point, radius) in enumerate(zip(points, radii)):
            tangent = (points[min(i + 1, len(points) - 1)] - points[max(0, i - 1)]).normalized()
            helper = Vector((0, 1, 0)) if abs(tangent.z) > .92 else Vector((0, 0, 1))
            u = tangent.cross(helper).normalized()
            v = tangent.cross(u).normalized()
            for side in range(sides):
                theta = math.tau * side / sides
                r = radius * (1 + flute * math.sin(theta * 5 + i * .22))
                vertices.append(point + r * (u * math.cos(theta) + v * math.sin(theta)))
        for i in range(len(points) - 1):
            for j in range(sides):
                k = i * sides + j
                faces.append((k, i * sides + (j + 1) % sides,
                              (i + 1) * sides + (j + 1) % sides, k + sides))
                indices.append(6 if material == 5 and j % 7 == 0 else
                               7 if material == 5 and j % 9 == 0 else material)
        faces.extend((tuple(range(sides - 1, -1, -1)),
                      tuple((len(points) - 1) * sides + j for j in range(sides))))
        indices.extend((material, material))
        self.geometry(vertices, faces, indices)

    def stem(self, start, end, radius=.009, material=8):
        self.tube([start, end], [radius, radius * .35], material, sides=5)

    def leaf(self, base, direction, length, width=.25, twist=0, material=1,
             curl=.14, rib=True):
        """Five-station curved leaf, closed back, raised midrib and pointed tip."""
        base, axis = Vector(base), Vector(direction).normalized()
        helper = Vector((0, 0, 1)) if abs(axis.z) < .94 else Vector((0, 1, 0))
        u = axis.cross(helper).normalized()
        v = axis.cross(u).normalized()
        u, v = u * math.cos(twist) + v * math.sin(twist), -u * math.sin(twist) + v * math.cos(twist)
        vertices, faces = [], []
        for side in (1, -1):
            for station in range(5):
                t = station / 4
                spread = max(.003, math.sin(math.pi * t) ** .76) * width
                curve = curl * t * t - .046 * math.sin(math.pi * t)
                for edge in (-1, 0, 1):
                    roll = -.072 * abs(edge) * math.sin(math.pi * t)
                    vertices.append(base + length * (axis * t + u * edge * spread +
                                                     v * (curve + roll + side * .003)))
        for j in range(4):
            for i in range(2):
                a = j * 3 + i
                faces.extend(((a + 3, a + 4, a + 1, a),
                              (a + 15, a + 16, a + 19, a + 18)))
            for edge in (0, 2):
                a = j * 3 + edge
                faces.append((a, a + 3, a + 18, a + 15))
        faces.extend(((0, 15, 16, 1), (1, 16, 17, 2),
                      (12, 13, 28, 27), (13, 14, 29, 28)))
        self.geometry(vertices, faces, material)
        if rib:
            vertices = []
            for j in range(5):
                t = j / 4
                point = base + length * (axis * t + v * (curl * t * t - .046 * math.sin(math.pi * t) + .007))
                vertices.extend((point - u * .006 * length, point + u * .006 * length))
            self.geometry(vertices, [(j * 2, j * 2 + 1, j * 2 + 3, j * 2 + 2)
                                     for j in range(4)], 4)
        self.leaves += 1

    def finish(self):
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.vertices, [], self.faces)
        for material in self.materials:
            mesh.materials.append(material)
        mesh.polygons.foreach_set('material_index', self.indices)
        mesh.polygons.foreach_set('use_smooth', [True] * len(self.faces))
        mesh.update()
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.location = self.anchor
        obj['sipo_fresh_produce'] = True
        obj['sipo_botanical_leaf_count'] = self.leaves
        obj['sipo_group'] = 'Fresh Produce / Orchard Botany'
        return obj


def _polar(radius, theta, height):
    return Vector((radius * math.cos(theta), radius * math.sin(theta), height))


def create_tree_and_vines(api=None):
    """Return new tree/canopy/vine objects; never touch pre-existing objects.

    ``api`` is reserved for caller compatibility. Every mesh is already batched
    by a spatial assembly and uses the reusable SIPO_FP_Bot material palette.
    """
    rng = random.Random(6102026)
    materials = _materials()
    objects = []
    bark = BotanicalMesh('FP_Orchard_Sculpted_Trunk_And_Branches', materials=materials)
    trunk = [Vector(p) for p in ((0, 0, 1.65), (.04, .06, 2.25),
                                (-.14, .04, 3.05), (-.02, -.13, 3.9),
                                (.2, -.12, 4.7), (.13, .06, 5.5),
                                (.35, .16, 6.2), (.27, .2, 7.12))]
    bark.tube(trunk, [.59, .47, .39, .34, .29, .21, .12, .03], sides=20, flute=.12)
    # Broad buttress roots integrate the trunk into the mound without covering
    # the product tiers or spilling beyond the central planting bed.
    for i in range(9):
        a = i * math.tau / 9 + .13
        bark.tube([_polar(1.04, a, 1.65), _polar(.7, a + .1, 1.76),
                   _polar(.38, a + .19, 2.24), _polar(.2, a + .17, 2.65)],
                  [.025, .11, .19, .10], sides=10, flute=.12)

    # Every visible crown cluster has connected primary/secondary branches;
    # foliage therefore reads as an orchard tree rather than floating blobs.
    for cluster in range(24):
        a = cluster * 2.399963 + .2
        band = cluster % 3
        radius = (3.28, 2.9, 2.05)[band] + rng.uniform(-.16, .16)
        z = (5.42, 6.48, 7.23)[band] + rng.uniform(-.18, .16)
        tip = _polar(radius, a, z)
        origin = trunk[3 + band].copy()
        elbow = origin.lerp(tip, .47) + Vector((0, 0, -.18))
        outer = origin.lerp(tip, .81) + Vector((0, 0, .1))
        bark.tube([origin, elbow, outer, tip],
                  [.155 - band * .025, .11 - band * .018, .051, .008], sides=10, flute=.07)
        crown = BotanicalMesh('FP_Orchard_Canopy_%02d' % cluster, tip, materials)
        for shoot in range(9):
            phi = a + shoot * 2.399 + rng.uniform(-.2, .2)
            start = outer.lerp(tip, rng.uniform(.12, .92))
            end = tip + _polar(rng.uniform(.29, .69), phi, rng.uniform(-.4, .36))
            crown.stem(start, end, .011, 6)
            for leaf in range(8):
                t = .15 + (leaf // 2) * .245
                base = start.lerp(end, t)
                leaf_angle = phi + (1 if leaf % 2 else -1) * rng.uniform(.62, 1.18)
                direction = (math.cos(leaf_angle), math.sin(leaf_angle), rng.uniform(-.45, .6))
                crown.leaf(base, direction, rng.uniform(.35, .61),
                           rng.uniform(.22, .29), rng.uniform(-1.0, 1.0),
                           rng.choices([0, 1, 2, 3], [4, 6, 3, 1])[0], curl=.17,
                           rib=leaf % 2 == 0)
        objects.append(crown.finish())

    # A few long intertwined bark furrows add a hand-sculpted silhouette.
    for i in range(7):
        angle = math.tau * i / 7
        points = []
        for j in range(7):
            point = trunk[j].copy()
            r = (.54, .44, .36, .31, .27, .19, .105)[j]
            point += _polar(r, angle + .16 * math.sin(j * .7), 0)
            points.append(point)
        bark.tube(points, [.048, .042, .034, .03, .022, .014, .004], material=6, sides=6)
    # Flatten the buried root soles onto the raised planting-bed surface.
    bark.vertices = [(x, y, max(1.65, z)) for x, y, z in bark.vertices]
    objects.insert(0, bark.finish())

    for index in range(24):
        theta = math.tau * index / 24
        radius = rng.uniform(4.32, 4.55)
        top = rng.uniform(6.7, 7.12)
        drop = rng.uniform(1.2, 2.4)
        vine = BotanicalMesh('FP_Orchard_Hanging_Vine_%02d' % index,
                             _polar(radius, theta, top), materials)
        points = [_polar(radius + .07 * math.sin(j * .9 + index),
                         theta + .018 * math.sin(j * .63), top - drop * j / 9)
                  for j in range(10)]
        vine.tube(points, [.018 - j * .0012 for j in range(10)], material=8, sides=5)
        for j in range(1, 10):
            for side in (-1, 1):
                phi = theta + side * 1.08 + rng.uniform(-.22, .22)
                direction = (math.cos(phi) * .8, math.sin(phi) * .8, -.48)
                vine.leaf(points[j], direction, rng.uniform(.24, .4), .32,
                          rng.uniform(-.7, .7), (index + j) % 4, curl=.23, rib=False)
        objects.append(vine.finish())
    return objects


def potted_plant(name, position, scale=1):
    """Return one batched emerald/gold pot and one lush banana/fern assembly."""
    if scale <= 0:
        raise ValueError('Potted plant scale must be positive')
    rng = random.Random(name)
    anchor = Vector(position)
    materials = _materials()
    pot = BotanicalMesh(name + '_Emerald_Gold_Planter', anchor, materials)
    z = [0, .055, .12, .66, .72, .77]
    radii = [.30, .34, .32, .42, .44, .41]
    pot.tube([anchor + Vector((0, 0, zz * scale)) for zz in z],
             [r * scale for r in radii], material=9, sides=32)
    for height, radius in ((.055, .347), (.71, .45)):
        pot.tube([anchor + Vector((0, 0, (height - .025) * scale)),
                  anchor + Vector((0, 0, (height + .025) * scale))],
                 [radius * scale] * 2, material=10, sides=32)
    pot.tube([anchor + Vector((0, 0, .749 * scale)),
              anchor + Vector((0, 0, .759 * scale))], [.386 * scale] * 2,
             material=11, sides=32)
    foliage = BotanicalMesh(name + '_Banana_And_Ferns', anchor, materials)
    for i in range(16):
        theta = i * 2.399
        height = rng.uniform(1.35, 2.05)
        if i < 5:
            height += .45
        base = anchor + Vector((0, 0, .75 * scale))
        tip = anchor + _polar(rng.uniform(.25, .55) * scale, theta, height * scale)
        middle = base.lerp(tip, .57)
        foliage.tube([base, middle, tip], [.017 * scale, .01 * scale, .004 * scale],
                     material=8, sides=6)
        foliage.leaf(tip, (math.cos(theta), math.sin(theta), -.12),
                     rng.uniform(.58, .92) * scale, .29, rng.uniform(-.55, .55),
                     i % 4, curl=.24)
        foliage.leaf(middle, (math.cos(theta + .8), math.sin(theta + .8), .28),
                     rng.uniform(.43, .65) * scale, .24, -.2, i % 3, curl=.19)
    for i in range(7):
        theta = i * math.tau / 7
        base = anchor + Vector((0, 0, .81 * scale))
        tip = anchor + _polar(.69 * scale, theta, .54 * scale)
        midpoint = base.lerp(tip, .5) + Vector((0, 0, .21 * scale))
        foliage.tube([base, midpoint, tip], [.008 * scale, .005 * scale, .002 * scale],
                     material=8, sides=5)
        for j in range(6):
            p = base.lerp(midpoint, j / 3) if j <= 3 else midpoint.lerp(tip, (j - 3) / 2)
            for side in (-1, 1):
                phi = theta + side * .75
                foliage.leaf(p, (math.cos(phi), math.sin(phi), -.15),
                             (.29 - j * .023) * scale, .23, -.3,
                             2 if j % 3 else 0, curl=.16, rib=False)
    return [pot.finish(), foliage.finish()]


def build():
    """Convenience alias used by standalone build scripts."""
    return create_tree_and_vines()
