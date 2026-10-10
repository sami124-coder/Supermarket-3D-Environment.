"""Original Sipo Orbit Club mascot sculptures, pass three.

Executed in build_supermarket.py's namespace after redesign_art.py. This is
portable environment sculpture: no particles, rig, runtime component or gameplay.
Five characters share a sculpted design language and individually tagged art units.
"""

# Remove the earlier primitive bears while preserving the architectural art.
for premium_old in list(scene.objects):
    if premium_old.get('sipo_group') == 'Original orbit bear mascots':
        bpy.data.objects.remove(premium_old, do_unlink=True)

GROUP = 'Premium original Orbit Club mascots'
premium_materials = {}
for premium_name, premium_color, premium_rough, premium_metal in [
    ('PlushPorcelain', 'FFF0DA', .38, 0),
    ('PlushApricot', 'FF992D', .34, 0),
    ('PlushMuzzle', 'FFF8E8', .4, 0),
    ('EarVelvet', 'F69A8B', .47, 0),
    ('CheekVelvet', 'F29A9F', .46, 0),
    ('SuitTangerine', 'FF6E16', .27, .05),
    ('SuitGarden', '209573', .3, .04),
    ('SuitLagoon', '19AEBB', .27, .04),
    ('SuitIndigo', '163A8D', .26, .08),
    ('EyeSocket', '345288', .35, 0),
    ('EyeWhite', 'FFFDF9', .15, 0),
    ('IrisMidnight', '092955', .16, .12),
    ('IrisOcean', '287BBD', .14, .13),
    ('IrisAqua', '59C3E6', .17, .08),
    ('Pupil', '070C19', .075, .05),
    ('StitchGold', 'FFD088', .38, .05),
    ('Nose', '3B274B', .18, .03),
    ('Mouth', '67364D', .35, 0),
    ('Tongue', 'F299A3', .38, 0),
    ('BadgeGold', 'FFBB47', .2, .45),
]:
    premium_materials[premium_name] = mat('Mascot_' + premium_name, premium_color, premium_rough, premium_metal)

# Soft materials retain an explicit plain PBR fallback in scene-data.json.
# Subsurface is only an extra Blender shading refinement; all visible surface
# structure, piping, stitches, eyes and clothes are real exportable geometry.
for premium_name in ('PlushPorcelain', 'PlushApricot', 'PlushMuzzle', 'EarVelvet', 'CheekVelvet'):
    premium_p = premium_materials[premium_name].node_tree.nodes['Principled BSDF']
    premium_p.inputs['Subsurface Weight'].default_value = .055
    premium_p.inputs['Subsurface Radius'].default_value = (.7, .35, .2)
for premium_name in ('Pupil', 'IrisOcean', 'EyeWhite', 'Nose'):
    premium_materials[premium_name].node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = .45
    premium_materials[premium_name].node_tree.nodes['Principled BSDF'].inputs['Coat Roughness'].default_value = .075

premium_context = None
premium_created = []

def premium_mesh(name, vertices, faces, material):
    mesh = bpy.data.meshes.new('Orbit Club sculpt | ' + name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(premium_materials.get(material, material))
    mesh.update()
    for face in mesh.polygons:
        face.use_smooth = True
    obj = bpy.data.objects.new('Premium mascot | ' + name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = premium_context['anchor']
    obj.scale = (premium_context['scale'],) * 3
    obj['sipo_group'] = 'Premium original Orbit Club mascots'
    obj['art_unit'] = premium_context['unit']
    obj['art_anchor'] = list(premium_context['anchor'])
    obj['asset_author'] = 'Original Sipo Orbit Club sculpture'
    premium_created.append(obj)
    return obj


def premium_surface(name, center, scale, material, segments=48, rings=32, deform=None):
    """Closed sculpt surface with optional silhouette deformation, no modifiers."""
    vertices = []
    for j in range(rings + 1):
        theta = math.pi * j / rings
        for i in range(segments):
            phi = math.tau * i / segments
            v = Vector((math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)))
            if deform:
                v = Vector(deform(v))
            vertices.append(tuple(Vector(center) + Vector((v.x * scale[0], v.y * scale[1], v.z * scale[2]))))
    faces = []
    for j in range(rings):
        for i in range(segments):
            faces.append((j*segments+i, (j+1)*segments+i, (j+1)*segments+(i+1)%segments, j*segments+(i+1)%segments))
    return premium_mesh(name, vertices, faces, material)


def premium_path(name, points, radius, material, sides=12):
    """Swept, tapered seamless tube; round joints survive FBX without curves."""
    points = [Vector(p) for p in points]
    radii = radius if isinstance(radius, (tuple, list)) else [radius] * len(points)
    vertices = []
    for i, point in enumerate(points):
        tangent = points[min(i+1, len(points)-1)] - points[max(i-1, 0)]
        tangent.normalize()
        guide = Vector((0, 1, 0))
        if abs(tangent.dot(guide)) > .92:
            guide = Vector((1, 0, 0))
        right = tangent.cross(guide).normalized()
        up = tangent.cross(right).normalized()
        for j in range(sides):
            a = math.tau * j / sides
            vertices.append(tuple(point + radii[i] * (math.cos(a)*right + math.sin(a)*up)))
    faces = []
    for i in range(len(points)-1):
        for j in range(sides):
            faces.append((i*sides+j, i*sides+(j+1)%sides, (i+1)*sides+(j+1)%sides, (i+1)*sides+j))
    faces += [tuple(reversed(range(sides))), tuple((len(points)-1)*sides+j for j in range(sides))]
    return premium_mesh(name, vertices, faces, material)


def premium_bezier(name, controls, radius, material, samples=24, sides=12):
    a,b,c,d = [Vector(p) for p in controls]
    points = []
    for i in range(samples):
        t=i/(samples-1)
        points.append((1-t)**3*a + 3*(1-t)**2*t*b + 3*(1-t)*t*t*c + t**3*d)
    return premium_path(name, points, radius, material, sides)


def premium_loop(name, center, rx, rz, tube, material, start=0, end=math.tau, ydepth=0, count=64):
    # Most loops face the viewer in the XZ plane, including embroidered piping.
    points = [(center[0]+rx*math.cos(start+(end-start)*i/count),
               center[1]+ydepth*math.sin(start+(end-start)*i/count),
               center[2]+rz*math.sin(start+(end-start)*i/count)) for i in range(count+1)]
    return premium_path(name, points, tube, material, 10)


def premium_collar(name, center, radius, depth, tube, material):
    points = [(center[0]+radius*math.cos(i*math.tau/64), center[1]+depth*math.sin(i*math.tau/64), center[2]) for i in range(65)]
    return premium_path(name, points, tube, material, 12)


def premium_profile(name, profile, material, yscale=.72, center=(0,0,0), lobes=0):
    """Catmull-Rom lathed plush/clothing shell with smooth silhouette control."""
    samples = []
    for k in range(len(profile)-1):
        p0=Vector(profile[max(0,k-1)]);p1=Vector(profile[k]);p2=Vector(profile[k+1]);p3=Vector(profile[min(len(profile)-1,k+2)])
        for j in range(8):
            t=j/8
            q=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
            samples.append(q)
    samples.append(Vector(profile[-1]))
    vertices=[];faces=[];n=64
    for z,r in samples:
        for i in range(n):
            a=i*math.tau/n
            rr=max(.003,r)*(1+lobes*.07*math.cos(a*5))
            vertices.append((center[0]+rr*math.cos(a),center[1]+rr*math.sin(a)*yscale,center[2]+z))
    for j in range(len(samples)-1):
        for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    faces += [tuple(reversed(range(n))), tuple((len(samples)-1)*n+i for i in range(n))]
    return premium_mesh(name,vertices,faces,material)


def premium_star(name, center, radius, material, depth=.055):
    vertices=[]
    for y in (-depth/2,depth/2):
        for i in range(10):
            a=math.pi/2+i*math.pi/5;r=radius if i%2==0 else radius*.48
            vertices.append((center[0]+r*math.cos(a),center[1]+y,center[2]+r*math.sin(a)))
    faces=[tuple(range(10)),tuple(reversed(range(10,20)))]
    faces += [(i,i+10,(i+1)%10+10,(i+1)%10) for i in range(10)]
    obj=premium_mesh(name,vertices,faces,material)
    modifier=obj.modifiers.new('Soft enamel star edges','BEVEL');modifier.width=radius*.09;modifier.segments=3
    return obj


def premium_leaf(name, center, angle, length=.5, width=.16):
    vertices=[];faces=[];rows=16
    for j in range(rows+1):
        t=j/rows
        for k in range(7):
            u=(k/6-.5)*2
            xx=width*math.sin(math.pi*t)*u
            zz=length*t
            yy=-.04*math.sin(math.pi*t)*(1-u*u)+.15*t*t
            vertices.append((center[0]+xx*math.cos(angle)+zz*math.sin(angle),center[1]+yy,center[2]+zz*math.cos(angle)-xx*math.sin(angle)))
    for j in range(rows):
        for k in range(6):faces.append((j*7+k,j*7+k+1,(j+1)*7+k+1,(j+1)*7+k))
    obj=premium_mesh(name,vertices,faces,M['LeafLight'])
    solid=obj.modifiers.new('Real leaf thickness','SOLIDIFY');solid.thickness=.012
    premium_path('Leaf central raised rib',[(center[0]+length*(j/12)*math.sin(angle),center[1]-.045*math.sin(math.pi*j/12)+.15*(j/12)**2,center[2]+length*(j/12)*math.cos(angle)) for j in range(13)],.009,M['LeafDark'],8)


def premium_eye(side):
    x=side*.355;z=.12
    premium_surface('Fitted indigo eyelid socket',(x,-.485,z),(.298,.145,.37),'EyeSocket')
    premium_surface('Porcelain eye white',(x,-.565,z),(.26,.115,.321),'EyeWhite')
    ix=x-side*.017
    premium_surface('Cobalt limbal iris',(ix,-.658,z+.018),(.195,.041,.253),'IrisMidnight',48,28)
    premium_surface('Ocean blue iris',(ix,-.689,z+.018),(.176,.028,.23),'IrisOcean',48,28)
    # Radial real-geometry iris fibers create detail that works in URP too.
    for i in range(28):
        a=i*math.tau/28
        r0=.137; r1=.171
        premium_path('Iris radial fiber',[(ix+r0*math.cos(a),-.713,z+.018+r0*1.3*math.sin(a)),(ix+r1*math.cos(a+.012),-.711,z+.018+r1*1.3*math.sin(a+.012))],.0045,'IrisAqua' if i%3 else 'IrisMidnight',6)
    premium_surface('Deep glossy pupil',(ix,-.714,z+.033),(.136,.04,.185),'Pupil',48,32)
    premium_surface('Large softbox reflection',(ix-.051,-.75,z+.122),(.06,.016,.078),'EyeWhite',24,16)
    premium_surface('Secondary pinpoint reflection',(ix+.063,-.75,z-.033),(.025,.012,.032),'EyeWhite',20,12)
    premium_surface('Tiny iris lower sparkle',(ix-.032,-.73,z-.151),(.014,.007,.017),'EyeWhite',16,12)
    premium_loop('Sculpted upper eyelid',(x,-.65,z+.005),.262,.322,.024,'EyeSocket',.07,math.pi-.07,count=32)
    premium_bezier('Soft expressive brow',[(x-.17,-.481,.538),(x-.065,-.537,.589),(x+.07,-.52,.599 if side<0 else .61),(x+.16,-.46,.565)],.023,'SuitIndigo',20)


def premium_paw(center, waving=False):
    x,y,z=center
    # A broad continuous mitten surface, with sunk folds and pads; fingers are
    # connected into the palm silhouette, instead of a fan of detached balls.
    premium_surface('Soft mitten palm',center,(.235,.17,.24),'PlushPorcelain',40,28,
                    lambda v:(v.x*(1+.055*math.sin(3*math.atan2(v.x,v.z))),v.y,v.z))
    premium_surface('Connected rounded thumb',(x+.175,y-.015,z-.06),(.12,.14,.16),'PlushPorcelain',32,24)
    if waving:
        premium_surface('Velvet paw heart',(x,y-.164,z-.035),(.095,.025,.085),'EarVelvet',28,20)
        for dx,dz in [(-.13,.11),(-.045,.16),(.05,.16),(.135,.1)]:
            premium_surface('Paw fingertip velvet',(x+dx,y-.137,z+dz),(.038,.025,.048),'EarVelvet',20,14)
        for dx in (-.085,0,.085):
            premium_bezier('Mitten fingertip crease',[(x+dx,y-.09,z+.225),(x+dx*.9,y-.142,z+.202),(x+dx,y-.167,z+.168),(x+dx,y-.169,z+.155)],.0048,'StitchGold',10,6)


def premium_character(unit, anchor, scale, role):
    global premium_context
    premium_context={'unit':unit,'anchor':anchor,'scale':scale}
    suit={'garden':'SuitGarden','checkout':'SuitLagoon'}.get(role,'SuitTangerine')
    # Seamless tailored pear-shaped torso and smooth flowing sleeves.
    premium_profile('Tailored flight suit',[(-1.64,.08),(-1.58,.3),(-1.42,.455),(-1.18,.49),(-.91,.445),(-.72,.33),(-.61,.2)],suit,.78)
    premium_surface('Indigo field backpack',(0,.29,-1.09),(.37,.19,.46),'SuitIndigo')
    for side in (-1,1):
        premium_bezier('Cream backpack shoulder strap',[(side*.24,.08,-.65),(side*.43,-.06,-.76),(side*.42,-.28,-1.01),(side*.34,-.3,-1.33)],.042,'PlushMuzzle',24)
    premium_surface('Fitted indigo chest panel',(0,-.352,-1.1),(.337,.066,.369),'SuitIndigo')
    premium_collar('Soft tangerine neck collar',(0,0,-.626),.3,.25,.084,suit)
    premium_collar('Cream collar piping',(0,0,-.66),.335,.268,.027,'PlushMuzzle')
    premium_bezier('Golden center zipper',[(0,-.368,-.77),(0,-.426,-.96),(0,-.426,-1.22),(0,-.376,-1.49)],.012,'BadgeGold',28,8)
    for j in range(18):
        zz=-.85-j*.031
        premium_path('Tailored zipper teeth',[(-.018,-.424,zz),(.018,-.424,zz)],.006,'StitchGold',6)
    premium_loop('Zipper pull',(0,-.442,-.91),.028,.04,.007,'BadgeGold',count=24)
    # Deliberately asymmetrical welcoming pose.
    premium_bezier('Left raised sleeve',[(-.28,.005,-.8),(-.63,-.015,-.95),(-.9,-.03,-.57),(-1.04,-.06,-.4)],.17,suit,32,20)
    premium_bezier('Right curved sleeve',[(.28,.005,-.81),(.52,-.01,-.92),(.68,-.1,-1.18),(.83,-.15,-1.12)],.17,suit,32,20)
    premium_surface('Raised indigo cuff',(-1.045,-.062,-.388),(.18,.175,.135),'SuitIndigo',40,24)
    premium_surface('Right indigo cuff',(.826,-.15,-1.12),(.145,.18,.18),'SuitIndigo',40,24)
    premium_paw((-1.115,-.086,-.19),True)
    premium_paw((.97,-.205,-1.11))
    # Boot volumes are continuous shaped shells, with toe guards and soles.
    for side in (-1,1):
        xx=side*.28
        premium_surface('Flight boot upper',(xx,-.065,-1.6),(.235,.31,.267),suit)
        premium_surface('Cream molded toe guard',(xx,-.194,-1.692),(.233,.274,.16),'PlushMuzzle')
        premium_surface('Indigo molded outsole',(xx,-.14,-1.803),(.244,.32,.069),'SuitIndigo')
        premium_collar('Boot gold welt',(xx,-.14,-1.755),.235,.314,.012,'BadgeGold')
        for dz in (0,.047):
            premium_path('Boot lace strap',[(xx-.125,-.298,-1.58+dz),(xx,-.343,-1.57+dz),(xx+.125,-.298,-1.58+dz)],.014,'PlushMuzzle',8)
        for dx in (-.12,0,.12):
            premium_path('Molded sole tread',[(xx+dx,-.397,-1.809),(xx+dx,-.421,-1.79)],.009,'StitchGold',6)
    # Brow, cheek and jaw shaping belong to one continuous high-resolution head.
    def sculpt_head(v):
        cheek=1+.075*math.exp(-((v.z+.25)/.28)**2)
        return (v.x*cheek, v.y*(1+.055*math.exp(-((v.z+.2)/.35)**2)), v.z+.025*(1-v.z*v.z))
    premium_surface('Sculpted cheek and forehead head',(0,0,0),(.865,.585,.86),'PlushPorcelain',80,56,sculpt_head)
    # Warm rear hood is recessed behind the cream face; ear cups have real depth.
    premium_surface('Apricot rear head hood',(0,.165,.12),(.89,.49,.83),'PlushApricot',64,40)
    for side in (-1,1):
        ex=side*.755;ez=.675
        premium_surface('Sculpted outer ear cup',(ex,.018,ez),(.358,.23,.398),'PlushApricot')
        premium_surface('Cream ear rolled lip',(ex,-.135,ez),(.281,.123,.315),'PlushMuzzle')
        premium_surface('Recessed inner velvet ear',(ex,-.222,ez+.015),(.216,.048,.256),'EarVelvet')
        premium_bezier('Inner ear curved fold',[(ex-side*.08,-.259,ez-.115),(ex-side*.15,-.273,ez+.06),(ex+side*.035,-.276,ez+.159),(ex+side*.105,-.25,ez+.093)],.014,'CheekVelvet',24,8)
    # Forelock flows into the face as a soft curved crest.
    premium_bezier('Sculpted cream forelock',[(.19,-.24,.718),(.09,-.47,.904),(-.07,-.536,.798),(-.075,-.519,.642)],.09,'PlushMuzzle',32,20)
    premium_eye(-1);premium_eye(1)
    premium_surface('Continuous soft muzzle',(0,-.508,-.333),(.39,.165,.24),'PlushMuzzle',56,36,
                    lambda v:(v.x,v.y*(1+.07*math.cos(v.x*math.pi)),v.z))
    premium_surface('Blueberry heart nose',(0,-.684,-.245),(.104,.068,.078),'Nose',40,28,
                    lambda v:(v.x*(.86+.17*v.z),v.y,v.z))
    premium_surface('Nose reflected glint',(-.026,-.744,-.213),(.025,.008,.012),'EyeWhite',20,12)
    premium_bezier('Mouth center philtrum',[(0,-.689,-.307),(0,-.703,-.334),(0,-.711,-.356),(0,-.706,-.374)],.012,'Mouth',16,8)
    for side in (-1,1):
        premium_bezier('Happy sculpted smile',[(0,-.706,-.373),(side*.045,-.706,-.429),(side*.12,-.684,-.406),(side*.164,-.655,-.366)],.013,'Mouth',24,8)
        premium_surface('Subtle blush cheek',(side*.597,-.463,-.28),(.12,.026,.072),'CheekVelvet',32,20)
        for dx,dz in [(-.035,.04),(.02,.028),(.048,-.012)]:
            premium_surface('Tiny golden cheek freckles',(side*(.52+dx),-.52,-.255+dz),(.012,.008,.012),'BadgeGold',12,8)
    premium_surface('Pink lower smile',(0,-.669,-.45),(.066,.012,.035),'Tongue',28,20)
    # Sewn chest insignia and separate enameled sun pins.
    premium_surface('Orbit Club embroidered badge',(-.184,-.422,-1.095),(.105,.017,.105),'PlushMuzzle',32,24)
    premium_loop('Embroidered orbital badge ring',(-.184,-.442,-1.095),.07,.05,.008,'BadgeGold',count=40)
    premium_star('Orbit Club chest star',(-.184,-.462,-1.095),.04,'BadgeGold',.014)
    for i in range(12):
        a=i*math.tau/12
        premium_path('Visible badge stitching',[(-.184+.096*math.cos(a),-.441,-1.095+.096*math.sin(a)),(-.184+.087*math.cos(a),-.441,-1.095+.087*math.sin(a))],.003,'SuitIndigo',6)
    if role=='garden':
        for j in range(7):
            premium_leaf('Garden crown leaf',(-.4+j*.13,.0,.76),-.6+j*.2,.44 if j%2 else .34,.12)
        premium_surface('Held orchard apple',(1.035,-.39,-1.06),(.19,.17,.2),M['Red'],40,28,
                        lambda v:(v.x,v.y,v.z-.07*(1-v.x*v.x-v.y*v.y)))
        premium_path('Apple stem',[(1.035,-.39,-.91),(1.066,-.4,-.824)],.014,M['Wood'],8)
        premium_leaf('Apple leaf',(1.05,-.4,-.862),.75,.17,.055)
    elif role=='chef':
        premium_profile('Sculpted five-lobed chef toque',[(.79,.29),(.85,.53),(1.0,.55),(1.15,.67),(1.34,.65),(1.51,.43),(1.6,.04)],'PlushMuzzle',.68,lobes=1)
        premium_collar('Chef toque soft brim',(0,0,.85),.56,.37,.065,'PlushMuzzle')
        premium_collar('Chef toque gold piping',(0,0,.835),.561,.373,.012,'BadgeGold')
        for xx in (-.31,-.15,.02,.18,.34):
            premium_bezier('Chef hat tailored fold',[(xx,-.356,.91),(xx*1.3,-.411,1.08),(xx*1.35,-.398,1.32),(xx*.87,-.3,1.47)],.008,'StitchGold',20,8)
        premium_star('Chef hat sun insignia',(0,-.409,1.031),.09,'BadgeGold',.024)
        premium_surface('Chef apron front',(0,-.405,-1.248),(.3,.035,.24),'PlushMuzzle',40,28)
        for zz in (-1.13,-1.29):
            for xx in (-.095,.095):premium_surface('Chef apron button',(xx,-.445,zz),(.023,.014,.023),'BadgeGold',16,12)
        premium_path('Chef pastry spoon handle',[(1.02,-.31,-1.18),(1.19,-.32,-.64)],.026,M['Wood'],12)
        premium_surface('Chef wooden spoon',(1.215,-.32,-.56),(.083,.035,.12),M['Oak'],28,20)
    else:
        premium_star('Held joy star',(1.02,-.41,-1.055),.25,'BadgeGold',.08)
        premium_star('Inset star enamel',(1.02,-.459,-1.055),.18,M['Yellow'],.012)
        if role=='checkout':
            premium_surface('Cashier tailored cap',(0,.045,.728),(.66,.43,.26),'SuitLagoon',48,28)
            premium_surface('Cashier cap cream peak',(0,-.358,.721),(.57,.25,.065),'PlushMuzzle',48,24)
            premium_star('Cashier cap sun pin',(0,-.391,.822),.09,'BadgeGold',.022)
    # Tiny seams set the toy scale and catch grazing light on close-up shots.
    for side in (-1,1):
        for j in range(10):
            zz=-.88-j*.053;xx=side*(.405-.05*abs(zz+1.15))
            premium_path('Suit side seam stitch',[(xx,-.183,zz),(xx,-.183,zz-.021)],.005,'StitchGold',6)

premium_character('mascot_flagship_orbit_club',(-6,-3.4,8.6),1.6,'flagship')
premium_character('mascot_welcome_desk',(1.9,-1.3,2.25),.5,'desk')
premium_character('mascot_garden_keeper',(-10,1,5.95),.67,'garden')
premium_character('mascot_pastry_chef',(-18,12,3.05),.72,'chef')
premium_character('mascot_checkout_host',(18,-9.5,2.65),.63,'checkout')
print('Premium original mascot sculptures:',len(premium_created),'mesh parts, five individually tagged art units',flush=True)
