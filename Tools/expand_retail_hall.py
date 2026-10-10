"""Expand architecture to mall scale while preserving authored human-scale units."""
from mathutils import Matrix
HALL_SCALE=1.42
ARCH_Z=1.25
# These groups carry architecture or suspended ornament, and need full affine scale.
architectural={'Architecture','Entrance','Escalators','Celestial atrium','Premium architectural layers','Gallery ornament','Themed department halos','Signage'}
coherent_colliders={'Crescent reception front','Welcome lounge bench','Garden stocked harvest crate','Baguette boutique stand','Macaron boutique pedestal','Confection jar boutique','Juice tasting stand','Stocked freezer tower','Celebration cake boutique','Gallery café table and chairs','Gallery stocked display cabinet','Home studio window furniture','Toy boutique display island','Sunshine café servery','Botanica stepped plant display','Upper lounge banquette','Static gym cycle','Gym storage bench'}
def unit_z(z,unit=''):
    if unit.startswith('mascot_flagship'):return z*ARCH_Z
    if z>=9.3:return z*ARCH_Z
    if z>=5.7:return z+1.45
    return z
bpy.context.view_layer.update()
for o in list(scene.objects):
    if o.name.startswith('SOURCE_'):continue
    if o.type not in ('MESH','FONT','CURVE','LIGHT','EMPTY'):continue
    matrix=o.matrix_world.copy();anchor=o.get('art_anchor')
    if anchor is not None:
        a=Vector(anchor);delta=Vector((a.x*(HALL_SCALE-1),a.y*(HALL_SCALE-1),unit_z(a.z,o.get('art_unit',''))-a.z))
        o.matrix_world=Matrix.Translation(delta)@matrix
        continue
    if o.type=='LIGHT':
        p=o.location.copy();o.location=(p.x*HALL_SCALE,p.y*HALL_SCALE,p.z*ARCH_Z)
        o.data.energy*=1.45
        continue
    group=o.get('sipo_group','Architecture')
    # Real-sized groceries, with positions spread along the enlarged original shelves.
    if o.get('preserve_scale') or group=='Licensed groceries':
        p=matrix.translation.copy();q=Vector((p.x*HALL_SCALE,p.y*HALL_SCALE,unit_z(p.z)))
        o.matrix_world=Matrix.Translation(q-p)@matrix
    elif group in architectural:
        o.matrix_world=Matrix.Diagonal((HALL_SCALE,HALL_SCALE,ARCH_Z,1))@matrix
        if group=='Celestial atrium':o.matrix_world.translation.y+=3
    else:
        # Floor fixtures keep practical heights; upper fixtures are lifted to 7.25m.
        corners=[matrix@Vector(v) for v in o.bound_box] if o.type in ('MESH','FONT','CURVE') else [matrix.translation]
        lowest=min(v.z for v in corners);highest=max(v.z for v in corners)
        if lowest>5.65 and highest<9.8:
            o.matrix_world=Matrix.Translation((0,0,1.45))@Matrix.Diagonal((HALL_SCALE,HALL_SCALE,1,1))@matrix
        elif highest<4.0:o.matrix_world=Matrix.Diagonal((HALL_SCALE,HALL_SCALE,1,1))@matrix
        else:o.matrix_world=Matrix.Diagonal((HALL_SCALE,HALL_SCALE,ARCH_Z,1))@matrix
# Conservative axis-aligned scene boundaries remain compatible with the existing importer.
for c in DATA['colliders']:
    x,z,minus_y=c['position'];sx,sz,sy=c['size'];name=c['name']
    c['position'][0]=x*HALL_SCALE;c['position'][2]=minus_y*HALL_SCALE
    if name=='Crescent reception front':c['position'][2]=minus_y+(HALL_SCALE-1)
    if name not in coherent_colliders:c['size'][0]*=HALL_SCALE;c['size'][2]*=HALL_SCALE
    if name in ('Ground','Exterior walkway'):
        c['position'][1]*=ARCH_Z;c['size'][1]*=ARCH_Z
    elif name in ('Upper side gallery','Upper rear gallery','Gallery balustrade','Rear gallery balustrade','Column','Rear wall','Side wall','Entrance pier','Entrance side glazing','Escalator tread'):
        c['position'][1]*=ARCH_Z;c['size'][1]*=ARCH_Z
    elif z-sz/2>5.65:c['position'][1]+=1.45
    elif z+sz/2>4:c['position'][1]*=ARCH_Z;c['size'][1]*=ARCH_Z
for v in [DATA['spawn']]+DATA['viewpoints']:
    v['position'][0]*=HALL_SCALE;v['position'][2]*=HALL_SCALE
    if v['position'][1]>5:v['position'][1]+=1.45
for d in DATA['departments']:
    d['position'][0]*=HALL_SCALE;d['position'][2]*=HALL_SCALE
    if d['position'][1]>5:d['position'][1]+=1.45
    d['size'][0]*=HALL_SCALE;d['size'][2]*=HALL_SCALE
for l in DATA['lights']:
    l['position'][0]*=HALL_SCALE;l['position'][2]*=HALL_SCALE;l['position'][1]*=ARCH_Z
    l['range']*=1.25;l['intensity']*=1.15
DATA['environmentBounds']={'center':[0,8,6.7],'size':[72,18,80]}
DATA.setdefault('artStatistics',{}).update({'buildingFootprintMetres':[69.58,63.9],'atriumClearWidthMetres':39.76,'mezzanineHeightMetres':7.25,'ceilingHeightMetres':16.25})
# A deliberate mix of small warm pools and cool canopy light replaces flat frontal wash.
GROUP='Premium architectural lighting'
for x in (-22,22):
    for y in (-21,-10,2,14,25):
        light('Upper boutique ceiling wash',(x,y,13.3),'FFDEB8',530,2.4,unity_intensity=1.15,ran=9)
for x,y in [(-11,7),(0,11),(11,7)]:light('Cobalt planetarium uplight',(x,y,12.7),'387BFF',380,3,target=(x,y,16),unity_intensity=.85,ran=12)
light('Reception shaped warm key',(0,-5,7),'FFF1D4',460,3,target=(0,-2,1),unity_intensity=1.2,ran=10)
# Keep the welcome character seated on the new reception counter at its real height.
for o in scene.objects:
    if o.get('art_unit')=='mascot_welcome_desk':o.location.y-=1.4;o.location.z-=.1
print('Expanded retail hall: 69.58 x 63.9m; 39.76m clear atrium; mezzanine 7.25m',flush=True)
