"""Premium botanical geometry, executed in the supermarket builder's globals.

Replaces the old ellipsoid foliage with closed, curved leaf meshes, fine woody
branches, leaf ribs, flower petals and layered balcony garlands. All models are
original authored geometry; no image cards or external textures are needed.
"""
bot_previous_group = GROUP
GROUP = 'Premium botanical art'
bot_rng = random.Random(7124)
bot_count = {'leaves': 0, 'branch_segments': 0, 'flowers': 0, 'assemblies': 0}
for bot_key, bot_hex, bot_rough in [
    ('BotJade', '16733F', .29), ('BotEmerald', '21844B', .27),
    ('BotLime', '77B538', .31), ('BotNewGrowth', 'B6D46E', .32),
    ('BotRib', '90B55A', .36), ('BotBark', '64432A', .48),
    ('BotTwig', '8A673E', .43), ('BotPetalPink', 'FD74A7', .3),
    ('BotPetalCoral', 'FF895E', .31), ('BotPetalCream', 'FFF5C3', .34),
    ('BotPollen', 'F5B914', .34)]:
    M[bot_key] = mat(bot_key, bot_hex, bot_rough)

bot_mats = [M[k] for k in ('BotJade', 'BotEmerald', 'BotLime', 'BotNewGrowth',
                           'BotRib', 'BotBark', 'BotTwig', 'BotPetalPink',
                           'BotPetalCoral', 'BotPetalCream', 'BotPollen')]


class BotanicalMesh:
    """One mesh per plant assembly, including a physical leaf back surface."""
    def __init__(self, name, anchor):
        self.name, self.anchor = name, Vector(anchor)
        self.vertices, self.faces, self.materials = [], [], []

    def geometry(self, verts, faces, material):
        offset = len(self.vertices)
        self.vertices.extend(tuple(Vector(v) - self.anchor) for v in verts)
        self.faces.extend(tuple(offset + i for i in f) for f in faces)
        self.materials.extend([material] * len(faces))

    def stem(self, a, b, ra, rb=None, material=6, sides=7):
        a, b = Vector(a), Vector(b)
        direction = b - a
        if direction.length < .0001:
            return
        direction.normalize()
        u = direction.cross(Vector((0, 0, 1)))
        if u.length < .001:
            u = direction.cross(Vector((0, 1, 0)))
        u.normalize()
        v = direction.cross(u)
        rb = rb if rb is not None else ra * .65
        verts = []
        for p, r in ((a, ra), (b, rb)):
            for j in range(sides):
                theta = j * math.tau / sides
                verts.append(p + r * (u * math.cos(theta) + v * math.sin(theta)))
        faces = [(i, (i + 1) % sides, (i + 1) % sides + sides, i + sides)
                 for i in range(sides)]
        faces.extend([tuple(range(sides - 1, -1, -1)), tuple(range(sides, sides * 2))])
        self.geometry(verts, faces, material)
        bot_count['branch_segments'] += 1

    def leaf(self, base, direction, length, width=.23, twist=0, material=1,
             curl=.15, rib=True):
        """Tapered six-station leaf with ridged midrib and curled pointed tip."""
        base, z = Vector(base), Vector(direction).normalized()
        helper = Vector((0, 0, 1)) if abs(z.z) < .94 else Vector((0, 1, 0))
        x = z.cross(helper).normalized()
        y = z.cross(x).normalized()
        x, y = x * math.cos(twist) + y * math.sin(twist), -x * math.sin(twist) + y * math.cos(twist)
        verts = []
        for side in (1, -1):
            for j in range(7):
                t = j / 6
                spread = max(.004, math.sin(math.pi * t) ** .76) * width
                center_curve = curl * t * t - .052 * math.sin(math.pi * t)
                for lateral in (-1, 0, 1):
                    # A raised central rib catches light, rolled edges stay thin.
                    cross_curve = -.068 * abs(lateral) * math.sin(math.pi * t)
                    yy = center_curve + cross_curve + side * .0035
                    verts.append(base + length * (x * lateral * spread + y * yy + z * t))
        faces = []
        for j in range(6):
            for i in range(2):
                a = j * 3 + i
                faces.append((a + 3, a + 4, a + 1, a))
                faces.append((a + 21, a + 22, a + 25, a + 24))
        for j in range(6):
            for edge in (0, 2):
                a = j * 3 + edge
                faces.append((a, a + 3, a + 24, a + 21))
        faces.extend([(0, 21, 22, 1), (1, 22, 23, 2),
                      (18, 19, 40, 39), (19, 20, 41, 40)])
        self.geometry(verts, faces, material)
        if rib:
            rib_verts = []
            for j in range(7):
                t = j / 6
                yy = curl * t * t - .052 * math.sin(math.pi * t) + .005
                p = base + length * (y * yy + z * t)
                rib_verts.extend([p - x * .006 * length, p + x * .006 * length])
            self.geometry(rib_verts, [(j * 2 + 2, j * 2 + 3, j * 2 + 1, j * 2)
                                      for j in range(6)], 4)
        bot_count['leaves'] += 1

    def flower(self, center, scale=.12, color=7, tilt=(0, -1, .3)):
        p, axis = Vector(center), Vector(tilt).normalized()
        tangent = axis.cross(Vector((1, 0, 0))).normalized()
        other = axis.cross(tangent)
        for j in range(7):
            theta = j * math.tau / 7
            radial = tangent * math.cos(theta) + other * math.sin(theta)
            self.leaf(p, radial + axis * .15, scale * 1.8, .43, .25,
                      color, curl=.22, rib=False)
        # Small golden pollen rosette, with an actual raised center.
        for j in range(9):
            theta = j * math.tau / 9
            tip = p + scale * .22 * (tangent * math.cos(theta) + other * math.sin(theta))
            self.stem(tip, tip + axis * scale * .38, scale * .095,
                      scale * .075, 10, sides=5)
        bot_count['flowers'] += 1

    def finish(self):
        if not self.vertices:
            return None
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.vertices, [], self.faces)
        for material in bot_mats:
            mesh.materials.append(material)
        mesh.polygons.foreach_set('material_index', self.materials)
        mesh.polygons.foreach_set('use_smooth', [True] * len(self.faces))
        mesh.update()
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.location = self.anchor
        obj['sipo_group'] = 'Premium botanical art'
        obj['art_unit'] = 'Botanical ' + self.name
        obj['art_anchor'] = list(self.anchor)
        bot_count['assemblies'] += 1
        return obj


# Retain the existing planters, replacing their old capsule foliage and stems.
bot_pots = [o for o in scene.objects if o.name.startswith('Gold plant pot')]
for bot_obj in list(scene.objects):
    if bot_obj.name.startswith(('Tree foliage', 'Tree trunk', 'Tree branch',
                                'Broad glossy leaf', 'Botanical stem',
                                'Trailing balcony ivy', 'Trailing gallery ivy',
                                'Garden flower heart', 'Garden flower petals')):
        bpy.data.objects.remove(bot_obj, do_unlink=True)

for bot_index, bot_pot in enumerate(bot_pots):
    bot_s = bot_pot.scale.x / .4
    bot_anchor = Vector((bot_pot.location.x, bot_pot.location.y,
                         bot_pot.location.z - .36 * bot_s))
    bot_plant = BotanicalMesh('Sculpted leafy planter %02d' % bot_index, bot_anchor)
    bot_pot['art_unit'] = 'Botanical ' + bot_plant.name
    bot_pot['art_anchor'] = list(bot_anchor)
    for bot_soil in scene.objects:
        if bot_soil.name.startswith('Plant soil') and (bot_soil.location.xy - bot_anchor.xy).length < .03:
            bot_soil['art_unit'] = 'Botanical ' + bot_plant.name
            bot_soil['art_anchor'] = list(bot_anchor)
    for bot_j in range(13):
        bot_theta = bot_j * 2.399 + bot_index * .21
        bot_h = bot_rng.uniform(1.05, 2.15) * bot_s
        bot_rad = bot_rng.uniform(.24, .68) * bot_s
        bot_base = bot_anchor + Vector((0, 0, .70 * bot_s))
        bot_tip = bot_anchor + Vector((math.cos(bot_theta) * bot_rad,
                                       math.sin(bot_theta) * bot_rad, bot_h))
        bot_mid = bot_base.lerp(bot_tip, .62)
        bot_plant.stem(bot_base, bot_mid, .013 * bot_s, .009 * bot_s, 0)
        bot_plant.stem(bot_mid, bot_tip, .009 * bot_s, .004 * bot_s, 0)
        for bot_l in range(3):
            bot_p = bot_base.lerp(bot_tip, .5 + bot_l * .23)
            bot_a = bot_theta + (-1 if bot_l % 2 else 1) * .65
            bot_d = (math.cos(bot_a), math.sin(bot_a), .36 - bot_l * .32)
            bot_plant.leaf(bot_p, bot_d, bot_rng.uniform(.46, .78) * bot_s,
                           .21 if bot_j % 3 else .31, bot_rng.uniform(-.7, .7),
                           bot_j % 4, curl=.20)
    # Low ferns drape softly across the metallic planter's rim.
    for bot_j in range(5):
        bot_a = bot_j * math.tau / 5
        bot_b = bot_anchor + Vector((0, 0, .79 * bot_s))
        bot_t = bot_anchor + Vector((.57 * bot_s * math.cos(bot_a),
                                     .57 * bot_s * math.sin(bot_a), .58 * bot_s))
        bot_plant.stem(bot_b, bot_t, .005 * bot_s, .002 * bot_s, 0, sides=5)
        for bot_k in range(4):
            for bot_sign in (-1, 1):
                bot_angle = bot_a + bot_sign * .72
                bot_plant.leaf(bot_b.lerp(bot_t, .15 + bot_k * .23),
                               (math.cos(bot_angle), math.sin(bot_angle), .1),
                               (.22 - bot_k * .025) * bot_s, .25, bot_a, 2,
                               curl=.20, rib=False)
    bot_plant.finish()


def bot_tree(x, y, scale=1, lush=1):
    anchor = Vector((x, y, 0))
    plant = BotanicalMesh('Layered orchard crown %s %s' % (x, y), anchor)
    # Curved trunk tapers continuously, with branching visible through the crown.
    trunk = [anchor + Vector((0, 0, .66)), anchor + Vector((.05, .02, 1.7 * scale)),
             anchor + Vector((.12, -.03, 2.6 * scale)),
             anchor + Vector((.02, .05, 3.45 * scale))]
    for j in range(3):
        plant.stem(trunk[j], trunk[j + 1], (.13 - j * .028) * scale,
                   (.10 - j * .028) * scale, 5, sides=11)
    for j in range(15):
        theta = j * 2.399
        radius = bot_rng.uniform(.78, 1.48) * scale
        end = anchor + Vector((math.cos(theta) * radius, math.sin(theta) * radius,
                               bot_rng.uniform(3.15, 4.18) * scale))
        start = trunk[1].lerp(trunk[2], (j % 5) / 5)
        elbow = start.lerp(end, .62) + Vector((0, 0, .18 * scale))
        plant.stem(start, elbow, .05 * scale, .028 * scale, 5)
        plant.stem(elbow, end, .028 * scale, .009 * scale, 6)
        for k in range(7):
            angle = theta + k * .95
            shoot_start = elbow.lerp(end, .3 + (k % 4) * .19)
            shoot_end = shoot_start + Vector((math.cos(angle) * .42 * scale,
                                               math.sin(angle) * .42 * scale,
                                               bot_rng.uniform(-.1, .26) * scale))
            plant.stem(shoot_start, shoot_end, .008 * scale, .002 * scale, 6, sides=5)
            for m in range(8 if lush else 5):
                p = shoot_start.lerp(shoot_end, .1 + (m // 2) * .23)
                leaf_angle = angle + (-1 if m % 2 else 1) * .86
                plant.leaf(p, (math.cos(leaf_angle), math.sin(leaf_angle),
                                bot_rng.uniform(-.3, .45)),
                           bot_rng.uniform(.27, .42) * scale, .24,
                           bot_rng.uniform(-1.15, 1.15),
                           bot_rng.choices([0, 1, 2, 3], [4, 6, 3, 1])[0], curl=.14)
    plant.finish()
    for o in scene.objects:
        if o.name.startswith(('Tree planter', 'Tree soil')) and (o.location.xy - anchor.xy).length < .1:
            o['art_unit'] = 'Botanical ' + plant.name
            o['art_anchor'] = list(anchor)


for bot_x, bot_y, bot_s in [(-10, 1, 1.08), (19, 7, .98),
                              (20, -5, 1.04), (-20, -5, 1.04), (-17, 16, .92)]:
    bot_tree(bot_x, bot_y, bot_s, 1 if bot_x == -10 else 0)
# The former tree at the bakery entrance is deliberately a low herb arrangement:
# it keeps the chef, donut displays and pastry frontage visible from eye level.
bot_herbs = BotanicalMesh('Bakery living herb garden', (-19, 10, 0))
for bot_j in range(32):
    bot_a = bot_j * 2.399
    bot_r = .25 + (bot_j % 4) * .15
    bot_p = Vector((-19 + bot_r * math.cos(bot_a), 10 + bot_r * math.sin(bot_a), .69))
    bot_q = bot_p + Vector((.08 * math.cos(bot_a), .08 * math.sin(bot_a), .28 + (bot_j % 5) * .055))
    bot_herbs.stem(bot_p, bot_q, .006, .002, 0, sides=5)
    for bot_k in range(6):
        bot_angle = bot_a + bot_k * 2.4
        bot_herbs.leaf(bot_p.lerp(bot_q, .3 + bot_k * .12),
                       (math.cos(bot_angle), math.sin(bot_angle), .3),
                       .18, .32, bot_angle, 2)
bot_herbs.finish()

# Deep but irregular gallery foliage: thick on rail tops, finer hanging trails.
# Separate units keep the botanical details at believable scale after expansion.
for bot_side in (-1, 1):
    for bot_y in range(-18, 16, 3):
        bot_x = bot_side * 14.12
        bot_vine = BotanicalMesh('Gallery hanging garden %s %s' % (bot_side, bot_y),
                                 (bot_x, bot_y, 5.8))
        for bot_j in range(6):
            bot_yy = bot_y - .68 + bot_j * .26
            bot_length = bot_rng.uniform(.65, 1.75)
            bot_nodes = [Vector((bot_x - bot_side * .08 + .045 * math.sin(k * .85 + bot_j),
                                 bot_yy + .09 * math.sin(k * .68),
                                 5.95 - k * bot_length / 10)) for k in range(11)]
            for bot_k in range(10):
                bot_vine.stem(bot_nodes[bot_k], bot_nodes[bot_k + 1], .007, .004, 0, sides=5)
                for bot_sign in (-1, 1):
                    bot_vine.leaf(bot_nodes[bot_k],
                                   (-bot_side * .32, bot_sign * .85, -.32),
                                   .22 if bot_k < 6 else .16, .38,
                                   bot_side * .6, (bot_j + bot_k) % 3,
                                   curl=.12, rib=bot_k < 7)
        for bot_j in range(14):
            bot_p = Vector((bot_x + bot_side * .12, bot_y + bot_rng.uniform(-.95, .95),
                             5.9 + bot_rng.uniform(0, .12)))
            bot_a = bot_j * 2.399
            bot_vine.leaf(bot_p, (math.cos(bot_a), math.sin(bot_a), .4),
                           bot_rng.uniform(.24, .42), .31, bot_a, bot_j % 4)
            if bot_j % 4 == 0:
                bot_vine.flower(bot_p + Vector((-bot_side * .12, 0, .17)), .065,
                                7 + (bot_j // 4) % 3,
                                (-bot_side, -.5, .35))
        bot_vine.finish()

# Bouquets at the produce crown replace isolated floating flower balls.
for bot_j in range(12):
    bot_a = bot_j * math.tau / 12
    bot_anchor = (-10 + 3.04 * math.cos(bot_a), 1 + 3.04 * math.sin(bot_a), 3.45)
    bot_bouquet = BotanicalMesh('Produce crown floral cluster %02d' % bot_j, bot_anchor)
    for bot_k in range(5):
        bot_theta = bot_k * 2.399
        bot_start = Vector(bot_anchor)
        bot_tip = bot_start + Vector((.18 * math.cos(bot_theta), .18 * math.sin(bot_theta),
                                       .16 + (bot_k % 3) * .06))
        bot_bouquet.stem(bot_start, bot_tip, .007, .003, 0, sides=5)
        bot_bouquet.leaf(bot_start, (math.cos(bot_theta), math.sin(bot_theta), .25),
                         .34, .26, bot_theta, 1)
        bot_bouquet.flower(bot_tip, .072, 7 + bot_j % 3,
                           (math.cos(bot_a), math.sin(bot_a), .3))
    bot_bouquet.finish()

DATA['botanicalArt'] = dict(bot_count)
print('Premium botanical art:', bot_count, flush=True)
GROUP = bot_previous_group
