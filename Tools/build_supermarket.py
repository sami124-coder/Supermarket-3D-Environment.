"""Build SIPO's editable Blender source, Unity FBX and physically rendered previews.

Run: blender --background --python Tools/build_supermarket.py -- --render
Kenney CC0 models are reused from Assets/ThirdParty; see Docs/ASSET_CREDITS.md.
"""
import bpy, bmesh, math, random, json, sys, argparse
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Assets/Environment'
OUT.mkdir(parents=True, exist_ok=True)
random.seed(28)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.materials): bpy.data.materials.remove(block)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
GROUP = 'Architecture'
DATA = {'schemaVersion': 1, 'materials': [], 'lights': [], 'colliders': [],
        'spawn': {'position': [0, .12, 19], 'yaw': 180},
        'viewpoints': [
          {'name':'Grand entrance','description':'Your first look at Sipo','position':[0,.12,19],'yaw':180,'pitch':-12},
          {'name':'Fresh garden','description':'Produce picked for a brighter day','position':[-8,.12,5],'yaw':225,'pitch':-5},
          {'name':'Atrium','description':'A little universe of everyday joy','position':[0,.12,6],'yaw':180,'pitch':-20},
          {'name':'Mezzanine','description':'The best view in the house','position':[-16,5.92,4],'yaw':110,'pitch':13},
          {'name':'Bakery','description':'Something lovely, fresh from the oven','position':[-17,.12,-6.5],'yaw':180,'pitch':0}],
        'departments': []}

def rgb(hex):
    return tuple(int(hex[i:i+2], 16)/255 for i in (0,2,4))
def lin(v): return v/12.92 if v < .04045 else ((v+.055)/1.055)**2.4
def mat(name, color, rough=.4, metal=0, emission=0):
    c = rgb(color) if isinstance(color,str) else color
    m = bpy.data.materials.new('SIPO_'+name)
    m.diffuse_color = (*c,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*(lin(v) for v in c),1)
    p.inputs['Metallic'].default_value=metal
    p.inputs['Roughness'].default_value=rough
    if emission:
        p.inputs['Emission Color'].default_value=(*c,1)
        p.inputs['Emission Strength'].default_value=emission
    DATA['materials'].append({'name':m.name,'color':list(c),'roughness':rough,'metallic':metal,
                             'emission':list(c) if emission else [0,0,0],'emissionStrength':emission})
    return m

M={}
for n,c,r,me,e in [
 ('Orange','FF780C',.24,.22,0),('Apricot','FFAF42',.34,.08,0),('Navy','133567',.27,.22,0),
 ('Blue','176DDD',.27,.2,0),('Cream','FFF1D4',.3,.06,0),('White','FFFDF6',.36,0,0),
 ('Gold','D89A43',.25,.75,0),('Chrome','CAD8E0',.22,.82,0),('Black','142132',.4,.3,0),
 ('Wood','B5713A',.48,0,0),('Oak','D99B58',.45,0,0),('Green','198151',.35,0,0),
 ('Leaf','35934A',.4,0,0),('LeafLight','70B544',.42,0,0),('LeafDark','165636',.44,0,0),
 ('Pink','D92170',.32,0,0),('Red','EF4237',.32,0,0),('Yellow','FFD74A',.3,0,0),
 ('Purple','7B54C7',.34,0,0),('Teal','1AA6AD',.27,.1,0),('Soil','38271E',.8,0,0),
 ('WarmLight','FFD29A',.2,0,4),('WhiteLight','FFF1D7',.2,0,3),('BlueLight','2C9EFF',.2,0,3),
 ('PinkLight','FF79BD',.2,0,2),('SignWhite','FFFFFF',.3,0,1.3),('Night','061744',.4,.1,0),
 ('Mint','B9DFC6',.4,0,0),('Glass','8BAFB8',.12,0,0)]: M[n]=mat(n,c,r,me,e)
M['Glass'].node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value=.88
M['Glass'].node_tree.nodes['Principled BSDF'].inputs['IOR'].default_value=1.45
glass_spec=next(m for m in DATA['materials'] if m['name']=='SIPO_Glass')
glass_spec.update({'transparent':True,'alpha':.18})

def finish(o,name,ma=None):
    o.name=name
    o['sipo_group']=GROUP
    if ma and ma.name not in o.data.materials:o.data.materials.append(ma)
    return o
PRIMITIVES={}
def primitive(shape,name,loc,scale,ma,segments=24,rings=12):
    key=(shape,segments,rings,ma.name)
    if key not in PRIMITIVES:
        mesh=bpy.data.meshes.new('Shared '+shape+' '+ma.name)
        bm=bmesh.new()
        if shape=='box':bmesh.ops.create_cube(bm,size=1)
        elif shape=='sphere':bmesh.ops.create_uvsphere(bm,u_segments=segments,v_segments=rings,radius=1)
        else:bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=segments,radius1=1,radius2=1,depth=1)
        bm.to_mesh(mesh);bm.free();mesh.materials.append(ma)
        if shape!='box':
            for p in mesh.polygons:p.use_smooth=len(p.vertices)<=4
        PRIMITIVES[key]=mesh
    o=bpy.data.objects.new(name,PRIMITIVES[key]);bpy.context.collection.objects.link(o)
    o.location=loc;o.scale=scale;return finish(o,name)
def cube(name,loc,dim,ma,bevel=0):
    o=primitive('box',name,loc,dim,ma)
    if bevel:
        # Bake dimensions directly before bevel so its width remains in metres.
        o.data=o.data.copy()
        for v in o.data.vertices:v.co=Vector((v.co.x*dim[0],v.co.y*dim[1],v.co.z*dim[2]))
        o.scale=(1,1,1)
        b=o.modifiers.new('Soft manufactured edges','BEVEL');b.width=bevel;b.segments=2
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o
def uv(name,loc,scale,ma,seg=20,rings=12):
    return primitive('sphere',name,loc,scale,ma,seg,rings)
def cyl(name,loc,r,depth,ma,vertices=48):
    return primitive('cylinder',name,loc,(r,r,depth),ma,vertices)
def rod(name,a,b,r,ma):
    a,b=Vector(a),Vector(b)
    o=cyl(name,(a+b)*.5,r,(b-a).length,ma,12)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def torus(name,loc,major,minor,ma,yscale=1):
    verts=[];faces=[];n=96;k=10
    for i in range(n):
        a=i*math.tau/n
        for j in range(k):
            b=j*math.tau/k;r=major+minor*math.cos(b)
            verts.append((r*math.cos(a),r*math.sin(a)*yscale,minor*math.sin(b)))
    for i in range(n):
        for j in range(k):faces.append((i*k+j,((i+1)%n)*k+j,((i+1)%n)*k+(j+1)%k,i*k+(j+1)%k))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.location=loc;finish(o,name,ma)
    for p in o.data.polygons:p.use_smooth=True
    return o
def ring(name,rx,ry,z,width,height,ma,center=(0,0)):
    verts=[];faces=[];n=128
    for zz in (z-height/2,z+height/2):
        for r in (0,width):
            verts.extend((center[0]+(rx-r)*math.cos(i*math.tau/n),center[1]+(ry-r)*math.sin(i*math.tau/n),zz) for i in range(n))
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,2*n+j,2*n+i),(n+j,n+i,3*n+i,3*n+j),(2*n+i,2*n+j,3*n+j,3*n+i),(j,i,n+i,n+j)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);finish(o,name,ma)
    for p in mesh.polygons:p.use_smooth=True
    b=o.modifiers.new('Rounded ring edges','BEVEL');b.width=.055;b.segments=3
    return o
FONT=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf')
ITALIC=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf')
def text(body,loc,size,ma,rot=(math.pi/2,0,0),font=None,extrude=.006):
    curve=bpy.data.curves.new('Lettering '+body,'FONT');curve.body=body;curve.size=size
    curve.align_x='CENTER';curve.align_y='CENTER';curve.extrude=extrude;curve.bevel_depth=.002
    curve.font=font or FONT;curve.resolution_u=8
    o=bpy.data.objects.new('Sign '+body,curve);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=rot
    return finish(o,o.name,ma)
def coll(name,loc,size,rot=(0,0,0)):
    DATA['colliders'].append({'name':name,'position':[loc[0],loc[2],-loc[1]],'size':[size[0],size[2],size[1]],'rotation':list(rot)})
def light(name,loc,color,power,size=4,kind='AREA',target=None,unity_intensity=3,ran=14):
    d=bpy.data.lights.new(name,kind);d.energy=power;d.color=rgb(color)
    if kind=='AREA':d.shape='DISK';d.size=size
    elif kind=='POINT':d.shadow_soft_size=size
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc
    if target:o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    DATA['lights'].append({'name':name,'type':'point','position':[loc[0],loc[2],-loc[1]],
                           'rotation':[0,0,0],'color':list(rgb(color)),'intensity':unity_intensity,'range':ran,'spotAngle':75})
    return o

# Architectural shell: a 48 x 44 m market, open central volume and a walkable gallery.
cube('Foundation',(0,0,-.24),(49,45,.4),M['Navy'],.04);coll('Ground',(0,0,-.2),(49,45,.4))
for x in range(-12,12):
    for y in range(-11,11):
        color=M['Cream'] if (x+y)%2==0 else M['Blue']
        cube('Polished terrazzo tile',(x*2+1,y*2+1,-.025),(1.986,1.986,.06),color)
for r in (4.6,5,8.7):ring('Floor brass inlay',r,r,.016,.055,.012,M['Gold'],(0,-1))
cube('Rear wall',(0,22,6.5),(49,.5,13),M['Navy']);coll('Rear wall',(0,22,6.5),(49,.5,13))
for x in (-24,24):
    cube('Side wall',(x,0,6.5),(.5,44,13),M['Navy']);coll('Side wall',(x,0,6.5),(.5,44,13))
    cube('Gallery slab',(x/24*19,0,5.56),(10,44,.48),M['Apricot'],.06)
    coll('Upper side gallery',(x/24*19,0,5.56),(10,44,.48))
cube('Rear gallery',(0,18.5,5.56),(28,7,.48),M['Apricot'],.06);coll('Upper rear gallery',(0,18.5,5.56),(28,7,.48))
cube('Ceiling',(0,0,13),(49,45,.28),M['Black'])
for x in range(-22,24,4):
    cube('Roof structure',(x,0,12.77),(.15,44,.16),M['Chrome'])
for y in range(-20,22,4):cube('Roof crossbeam',(0,y,12.72),(48,.1,.2),M['Black'])

def railing(a,b,z):
    a,b=Vector(a),Vector(b);dist=(b-a).length
    for top,r in ((z+.18,.028),(z+.82,.027),(z+1.18,.055)):
        rod('Gallery rail',(*a,top),(*b,top),r,M['Gold'] if r>.05 else M['Chrome'])
    for i in range(int(dist/.85)+1):
        p=a+(b-a)*i/max(1,int(dist/.85));rod('Gallery baluster',(*p,z),(*p,z+1.18),.029,M['Navy'])
for x in (-14,14):
    railing((x,-22),(x,14.8),5.8);coll('Gallery balustrade',(x,-3.6,6.35),(.16,36.8,1.1))
railing((-14,15),(8,15),5.8);coll('Rear gallery balustrade',(-3,15,6.35),(22,.16,1.1))

# Tall illustrated columns with blue bases, orange crowns, and playful confetti.
for x in (-14,14):
    for y in (-12,3,16):
        cyl('Atrium column',(x,y,6.3),.66,12.6,M['Blue']);coll('Column',(x,y,6.3),(1.32,1.32,12.6))
        for z in (.25,5.65,11.9):cyl('Column gold collar',(x,y,z),.72,.2,M['Gold'])
        for i in range(25):
            a=random.uniform(0,math.tau);z=random.uniform(1,11.5)
            o=uv('Column confetti',(x+.66*math.cos(a),y+.66*math.sin(a),z),(.22,.06,.34),M['Apricot'],12,8)
            o.rotation_euler[2]=a-math.pi/2

# Giant suspended orange halo, a midnight planetarium and warm luminous trim.
GROUP='Celestial atrium'
ring('Signature orange oculus',12.8,10.1,10.95,1.5,1.22,M['Orange'],(0,0))
for z in (10.38,11.48):
    torus('Halo outer light',(0,0,z),12.76,.055,M['WarmLight'],10.06/12.76)
torus('Halo inner light',(0,0,10.32),11.25,.07,M['WarmLight'],8.55/11.25)
o=cyl('Midnight celestial canopy',(0,0,12.56),11.5,.12,M['Night'],128);o.scale.y*=.78
torus('Blue canopy rim',(0,0,12.35),11.45,.1,M['BlueLight'],.78)
for i in range(190):
    a=random.uniform(0,math.tau);r=math.sqrt(random.random())*10.8
    x,y=r*math.cos(a),r*.78*math.sin(a)
    uv('Constellation star',(x,y,12.42),(random.uniform(.018,.044),)*3,M['WarmLight'] if i%4 else M['BlueLight'],8,4)
    if i%18==0:
        rod('Starlight glint',(x-.09,y,12.42),(x+.09,y,12.42),.009,M['WhiteLight'])
        rod('Starlight glint',(x,y-.1,12.42),(x,y+.1,12.42),.009,M['WhiteLight'])
for i,(x,y,z,r,col) in enumerate([(-7,-1,9.2,.62,'Teal'),(-4,3,8.9,.5,'Yellow'),(5,2,9.5,.9,'Orange'),(8,-1,8.2,.6,'Red'),(1,4,10.1,.48,'Pink'),(-1,1,10.5,.42,'Teal')]):
    rod('Planet suspension',(x,y,z),(x,y,12.5),.012,M['Chrome'])
    uv('Orbit_Planet_%02d'%i,(x,y,z),(r,)*3,M[col],32,20)
    for dz in (-.42*r,0,.42*r):
        torus('Planet stripe',(x,y,z+dz),math.sqrt(r*r-dz*dz)*1.007,.032,M['Apricot'] if i%2 else M['Yellow'])
    if i==2:
        o=torus('Saturn golden rings',(x,y,z),r*1.5,.065,M['WarmLight']);o.rotation_euler=(.2,.32,0)
for x,y,z in [(-8,-4,9.1),(6,5,9.6),(2,-1,9.5),(-5,7,10.5)]:
    rod('Cloud suspension',(x,y,z),(x,y,12.5),.01,M['Chrome'])
    for dx,dz,r in [(-.48,0,.42),(0,.2,.57),(.48,0,.39)]:uv('Soft cloud',(x+dx,y,z+dz),(r,r*.55,r),M['WhiteLight'])

# The dimensional Sipo brand sign faces the entrance.
GROUP='Signage'
cube('Sipo suspended brand plaque',(0,-3.4,8.08),(6.5,.34,2.35),M['Orange'],.6)
cube('Sipo inner plaque',(0,-3.60,8.12),(6.23,.12,2.10),M['Red'],.53)
text('Sipo',(0,-3.69,8.25),1.96,M['SignWhite'],font=ITALIC,extrude=.025)
cube('Supermarket plaque',(0,-3.46,6.77),(5.1,.24,.58),M['Orange'],.12)
text('S U P E R M A R K E T',(0,-3.62,6.78),.32,M['SignWhite'])
for x in (-2.4,2.4):rod('Brand suspension',(x,-3.4,9.1),(x,-3.4,12.5),.028,M['Gold'])

# Smile information desk, flower planters and the atrium's central tree island.
GROUP='Furniture'
cyl('Welcome desk body',(0,-1,.72),3.45,1.44,M['Orange'],96);coll('Welcome desk',(0,-1,.7),(6.9,6.9,1.4))
cyl('Welcome desk countertop',(0,-1,1.47),3.56,.14,M['Cream'],96)
for z in (.12,1.34):torus('Welcome desk light',(0,-1,z),3.47,.035,M['WarmLight'])
text('WELCOME',(0,-4.47,.86),.48,M['SignWhite'])
text('a little joy in every aisle',(0,-4.48,.43),.145,M['White'])
for x in (-1.5,1.5):
    cube('Service display',(x,-.25,1.82),(.67,.11,.5),M['Navy'],.05)
    cube('Service display stand',(x,-.25,1.57),(.12,.14,.28),M['Chrome'],.025)
    text('HELLO',(x,-.32,1.83),.12,M['WhiteLight'])

def planter(x,y,z=0,scale=1):
    global GROUP
    old=GROUP;GROUP='Botanical garden'
    cyl('Gold plant pot',(x,y,z+.36*scale),.40*scale,.72*scale,M['Gold'],24)
    cyl('Plant soil',(x,y,z+.73*scale),.36*scale,.035,M['Soil'],24)
    for i in range(10):
        a=i*2.4;h=random.uniform(1.1,2.3)*scale
        start=(x,y,z+.65*scale);tip=(x+math.cos(a)*.8*scale,y+math.sin(a)*.8*scale,z+h)
        rod('Botanical stem',start,tip,.018*scale,M['LeafDark'])
        o=uv('Broad glossy leaf',tip,(.2*scale,.085*scale,.61*scale),M['LeafLight'] if i%3==0 else M['Leaf'],12,8)
        o.rotation_euler=(math.cos(a)*.65,math.sin(a)*.65,a)
    GROUP=old

def tree(x,y,z=0,scale=1):
    global GROUP
    old=GROUP;GROUP='Botanical garden'
    cyl('Tree planter',(x,y,z+.34),1.04*scale,.68,M['Navy'],32)
    cyl('Tree soil',(x,y,z+.69),.98*scale,.04,M['Soil'],32)
    rod('Tree trunk',(x,y,z+.7),(x+.14,y,z+3.9*scale),.11*scale,M['Wood'])
    for i in range(12):
        a=i*2.4;rad=random.uniform(.7,1.5)*scale;h=random.uniform(2.8,4.7)*scale
        p=(x+math.cos(a)*rad,y+math.sin(a)*rad,z+h)
        rod('Tree branch',(x,y,z+2.4*scale),p,.042*scale,M['Wood'])
        for j in range(5):
            q=tuple(p[k]+random.uniform(-.3,.3)*scale for k in range(3))
            o=uv('Tree foliage',q,(.55*scale,.42*scale,.25*scale),M['LeafDark'] if j%3==0 else M['Leaf'],12,8)
            o.rotation_euler=(random.random(),random.random(),random.random()*6)
    GROUP=old

for x,y,s in [(-4,-2,1),(4,-2,1),(-5,1,1),(5,1,1),(-13,-10,1.2),(13,-10,1.2),(-20,-15,1.4),(20,-15,1.4),(-9,9,1.1),(7,12,1.1)]:planter(x,y,scale=s)
for x,y,s in [(-10,1,1.12),(-19,10,1),(19,7,1),(20,-5,1.1),(-20,-5,1.1),(-17,16,1)]:tree(x,y,scale=s)
for x in (-14.35,14.35):
    for y in (-17,-10,-3,5,12):
        planter(x+(-.5 if x<0 else .5),y,5.8,.7)
        for j in range(6):
            z=5.62
            for k in range(random.randint(4,8)):
                xx=x+math.sin(k+j)*.12;yy=y+j*.16
                z-=.22
                uv('Trailing balcony ivy',(xx,yy,z),(.12,.07,.18),M['Leaf'] if k%2 else M['LeafLight'],8,6)

# Reuse licensed Kenney groceries throughout the entire market.
GROUP='Licensed groceries'
PROTOS={}
assetdir=ROOT/'Assets/ThirdParty/KenneyFoodKit/Source'
def load_food(name):
    if name in PROTOS:return PROTOS[name]
    path=assetdir/(name+'.glb')
    if not path.is_file():raise FileNotFoundError('Required licensed source asset: '+str(path))
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    obs=[o for o in set(bpy.data.objects)-before if o.type=='MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    bpy.ops.object.join();o=bpy.context.object
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True,isolate_users=True)
    corners=[o.matrix_world@Vector(v) for v in o.bound_box]
    low=Vector(tuple(min(v[i] for v in corners) for i in range(3)))
    high=Vector(tuple(max(v[i] for v in corners) for i in range(3)))
    center=(low+high)*.5;center.z=low.z
    world=o.matrix_world.copy()
    for v in o.data.vertices:v.co=world@v.co-center
    o.matrix_world.identity()
    for m in o.data.materials:
        if m and m.use_nodes:
            p=m.node_tree.nodes.get('Principled BSDF')
            if p:p.inputs['Metallic'].default_value=0;p.inputs['Roughness'].default_value=.42
    o.name='SOURCE_'+name;o.hide_render=True;o.hide_viewport=True
    for other in list(set(bpy.data.objects)-before):
        if other!=o:bpy.data.objects.remove(other,do_unlink=True)
    PROTOS[name]=(o,high-low)
    return PROTOS[name]
def food(name,loc,size,rotation=0):
    proto,dim=load_food(name)
    o=proto.copy();o.data=proto.data;bpy.context.collection.objects.link(o)
    o.name='Kenney '+name;o.hide_render=False;o.hide_viewport=False
    o.location=loc;o.scale=(size/max(dim),)*3;o.rotation_euler[2]=rotation
    o['sipo_group']='Licensed groceries'
    return o

# Tiered fresh produce island left of the welcome desk.
GROUP='Furniture'
for z,r in [(.34,3.15),(.9,2.55),(1.46,1.88)]:
    cyl('Garden produce island',(-10,1,z),r,.5,M['Oak'],64)
    torus('Produce basket trim',(-10,1,z+.27),r,.05,M['Green'])
for level,(z,r,n) in enumerate([(.61,2.84,42),(1.17,2.22,32),(1.73,1.6,22)]):
    for i in range(n):
        a=i*math.tau/n
        kind=['apple','lemon','tomato','pear','broccoli','banana'][int(i/n*6)]
        for dr in (0,-.36):food(kind,(-10+(r+dr)*math.cos(a),1+(r+dr)*math.sin(a),z),.38,random.random()*6)
coll('Produce island',(-10,1,.8),(6.3,6.3,1.6))
ring('Fresh produce suspended sign',3.5,3.5,4.05,.15,.8,M['Green'],(-10,1))
torus('Fresh garden light',(-10,1,3.64),3.49,.04,M['WarmLight'])
text('FRESH PRODUCE',(-10,-2.54,4.06),.42,M['SignWhite'])
text('GROWN WITH LOVE',(-10,-2.54,3.83),.1,M['Cream'])

def shelf(x,y,width=6,z=0,kind='pantry'):
    global GROUP
    GROUP='Furniture'
    cube('Shelf backing',(x,y+.34,z+1.64),(width,.16,3.05),M['Navy'],.035)
    for xx in (x-width/2,x+width/2):cube('Shelf upright',(xx,y,z+1.65),(.1,.9,3.15),M['Gold'],.025)
    options={'pantry':['carton','sodaCan','honey','peanutButter','bottleOil','bottleKetchup'],
             'bakery':['loaf','bread','croissant','cupcake','muffin','donutChocolate'],
             'drinks':['sodaBottle','sodaCan','cartonSmall','carton'],
             'fresh':['apple','pear','lemon','banana','tomato','carrot'],
             'frozen':['fish','cheese','carton','cartonSmall']}
    types=options.get(kind,options['pantry'])
    for row in range(4):
        height=z+.35+row*.72
        cube('Retail shelf',(x,y,height),(width,.95,.07),M['Cream'],.018)
        cube('Price strip',(x,y-.48,height+.015),(width,.035,.08),M['Orange'])
        for col in range(int(width/.43)-1):
            xx=x-width/2+.38+col*.43
            name=types[(col//3+row)%len(types)]
            food(name,(xx,y-.14,height+.04),.40 if kind!='bakery' else .45,0)
            if col%3==0:
                cube('Price ticket',(xx,y-.503,height+.015),(.2,.008,.053),M['White'])
    coll('Stocked shelf',(x,y,z+1.65),(width,1,3.3))

def department(name,x,y,color,kind,z=0,w=7):
    global GROUP
    GROUP='Signage'
    cube('Department '+name,(x,y,z+4.2),(w,.28,.96),M[color],.09)
    cube('Sign light '+name,(x,y-.17,z+3.74),(w-.14,.05,.035),M['WarmLight'])
    text(name,(x,y-.18,z+4.21),.43 if len(name)<12 else .31,M['SignWhite'])
    shelf(x,y+.7,w-.3,z,kind)
    DATA['departments'].append({'name':name.title(),'position':[x,z,-(y-2)],'size':[w,4,5],'color':list(M[color].diffuse_color[:3])})

for name,x,color,kind in [('BAKERY',-18,'Orange','bakery'),('SNACKS',-9,'Pink','pantry'),('FROZEN',0,'Blue','frozen'),('DRINKS',9,'Orange','drinks'),('HEALTH & BEAUTY',18,'Pink','pantry')]:
    department(name,x,18.4,color,kind,w=7.9)
for name,x,color,kind in [('HOME & LIVING',-18,'Teal','pantry'),('LITTLE WONDERS',-9,'Purple','pantry'),('EVERYDAY JOY',0,'Orange','pantry'),('TOYS',9,'Orange','pantry'),('THE GREEN ROOM',18,'Green','fresh')]:
    department(name,x,20.5,color,kind,z=5.8,w=7.9)
# Side aisle rows keep clear sightlines from the entrance.
for x in (-20,20):
    for y in (-8,0,8):
        shelf(x,y,5.1,0,'fresh' if x<0 and y<0 else 'pantry')
        shelf(x,y+1.1,5.1,0,'bakery' if x<0 and y>0 else 'drinks')
        shelf(x,y,5.1,5.8,'pantry')
for x in (-8,0):shelf(x,13,5.5,0,'pantry' if x<0 else 'frozen')
# Low bakery presentation island with reusable breads, pastry and cakes.
GROUP='Furniture'
cube('Bakery island',(-17,10,.65),(6,2.4,1.3),M['Oak'],.1);coll('Bakery island',(-17,10,.65),(6,2.4,1.3))
cube('Bakery marble counter',(-17,10,1.34),(6.15,2.55,.12),M['Cream'],.06)
for i in range(12):
    food(['loaf','croissant','donutChocolate','cupcake'][i%4],(-19.45+(i%6)*.9,9.4+(i//6)*.9,1.41),.65)
text('FRESHLY BAKED',(-17,8.77,.8),.35,M['White'])

# Twin escalators with visible comb plates, treads, and continuous balustrades.
GROUP='Escalators'
for x in (10,12.55):
    for i in range(29):
        h=(i+1)*5.8/29;y=3.65+i*.40
        cube('Escalator step',(x,y,h-.1),(2.12,.42,.2),M['Chrome'],.012)
        cube('Escalator yellow nosing',(x,y-.19,h+.003),(2.08,.026,.014),M['Yellow'])
        coll('Escalator tread',(x,y,h-.1),(2.12,.42,.2))
        for dx in (-.66,-.22,.22,.66):cube('Tread grooves',(x+dx,y,h+.009),(.01,.35,.012),M['Black'])
    for dx in (-1.15,1.15):
        a=(x+dx,3.4,.48);b=(x+dx,15.1,6.26)
        rod('Escalator side trim',a,b,.12,M['Gold'])
        rod('Escalator handrail',(a[0],a[1],a[2]+.64),(b[0],b[1],b[2]+.64),.075,M['Black'])
        rod('Escalator edge lighting',(a[0],a[1],a[2]+.48),(b[0],b[1],b[2]+.48),.025,M['BlueLight'])
        for i in range(15):
            t=i/14;xx=a[0];yy=a[1]+t*(b[1]-a[1]);zz=a[2]+t*(b[2]-a[2])
            rod('Escalator baluster',(xx,yy,zz-.1),(xx,yy,zz+.61),.023,M['Chrome'])
    for y,z in [(3.1,.02),(15.35,5.82)]:cube('Escalator landing',(x,y,z),(2.3,.9,.035),M['Black'],.025)
text('DISCOVER MORE',(11.3,15.4,7.8),.4,M['SignWhite'])

# Checkout lanes in the front right and neatly nested chrome carts left.
GROUP='Furniture'
for x in (10,14,18):
    cube('Checkout counter',(x,-11,.7),(2.4,3.8,1.4),M['Orange'],.12);coll('Checkout counter',(x,-11,.7),(2.4,3.8,1.4))
    cube('Checkout conveyor',(x,-11,1.44),(1.7,2.5,.12),M['Black'],.06)
    cube('Payment screen',(x,-9.55,1.93),(.7,.12,.55),M['Navy'],.035)
    text('SIPO',(x,-9.63,1.93),.16,M['WhiteLight'])
    rod('Lane number stand',(x+.8,-9.5,1.5),(x+.8,-9.5,3.8),.04,M['Chrome'])
    cube('Checkout lane number',(x+.8,-9.5,3.8),(.66,.2,.7),M['Green'],.08)
    text('%02d'%((x-10)//4+1),(x+.8,-9.63,3.8),.38,M['SignWhite'])
for i in range(7):
    x=-17+i*.64;y=-15.8+i*.37
    for xx in (x-.48,x+.48):
        for yy in (y-.62,y+.65):
            wheel=cyl('Cart wheel',(xx,yy,.19),.15,.11,M['Black'],16);wheel.rotation_euler[1]=math.pi/2
            rod('Cart chassis',(xx,yy,.27),(xx,yy,1.13),.025,M['Chrome'])
    for z in (.57,1.25):
        for xx in (x-.5,x+.5):rod('Cart basket wire',(xx,y-.68,z),(xx,y+.6,z),.022,M['Chrome'])
        for yy in (y-.68,y+.6):rod('Cart basket wire',(x-.5,yy,z),(x+.5,yy,z),.022,M['Chrome'])
    for j in range(8):
        yy=y-.68+j*.18
        for xx in (x-.5,x+.5):rod('Cart basket lattice',(xx,yy,.59),(xx,yy,1.24),.012,M['Chrome'])
    for j in range(6):
        xx=x-.5+j*.2;rod('Cart front lattice',(xx,y-.68,.59),(xx,y-.68,1.24),.012,M['Chrome'])
        rod('Cart basket floor',(xx,y-.68,.59),(xx,y+.6,.59),.012,M['Chrome'])
    rod('Orange cart handle',(x-.58,y+.76,1.34),(x+.58,y+.76,1.34),.058,M['Orange'])
    cube('Cart front badge',(x,y-.71,.99),(.45,.025,.36),M['Orange'],.045)
    text('S',(x,y-.73,1),.28,M['White'])
coll('Cart bay',(-15,-14.8,.7),(6,3,1.4))

# Complete entrance portal, glazed side panels and exterior welcome paving.
GROUP='Entrance'
cube('Entrance lintel',(0,-22,10.8),(48,1.1,2.8),M['Orange'],.2)
for x in (-19,19):
    cube('Entrance portal pier',(x,-22,4.7),(10,1.1,9.4),M['Orange'],.15);coll('Entrance pier',(x,-22,4.7),(10,1.1,9.4))
cube('Entrance light',(0,-22.6,9.5),(28,.06,.07),M['WarmLight'])
text('Sipo',(0,-22.61,11.0),2.3,M['SignWhite'],font=ITALIC)
text('COME IN. FIND YOUR HAPPY.',(0,-22.62,9.95),.31,M['White'])
for x in (-10,10):
    cube('Entrance side glass',(x,-22,3.6),(7,.08,6.8),M['Glass'],.03)
    for dx in (-3.45,3.45):rod('Door frame',(x+dx,-22,.2),(x+dx,-22,7),.055,M['Chrome'])
    coll('Entrance side glazing',(x,-22,3.6),(7,.15,6.8))
cube('Exterior walkway',(0,-27,-.14),(49,10,.25),M['Cream'],.05);coll('Exterior walkway',(0,-27,-.14),(49,10,.25))
for x in (-7,7):planter(x,-24,scale=1.3)
for x in (-5,5):
    cube('Security gate',(x,-20,.58),(.12,1.25,1.16),M['Chrome'],.05)
    cube('Security light',(x,-20,1.19),(.14,1.2,.035),M['BlueLight'])

# The reference's friendly character is expressed as an original orange sun mascot.
GROUP='Mascot'
mc=Vector((-6,-3.2,8.8))
for i in range(12):
    a=i*math.tau/12
    o=uv('Sunny mascot ray',mc+Vector((math.cos(a)*1.05,0,math.sin(a)*1.05)),(.24,.3,.51),M['Orange'])
    o.rotation_euler[1]=math.pi/2-a
uv('Sunny mascot face',mc,(1.04,.42,1.02),M['Cream'],32,20)
for dx in (-.34,.34):
    uv('Mascot eye',mc+Vector((dx,-.40,.12)),(.19,.09,.27),M['Navy'])
    uv('Mascot eye sparkle',mc+Vector((dx-.05,-.48,.21)),(.05,.025,.066),M['WhiteLight'])
    uv('Mascot rosy cheek',mc+Vector((dx*1.55,-.40,-.19)),(.17,.035,.075),M['Pink'])
uv('Mascot happy smile',mc+Vector((0,-.44,-.31)),(.23,.04,.16),M['Orange'])
rod('Mascot hanging wire',mc+Vector((0,0,1.5)),(-6,-3.2,12.5),.016,M['Gold'])

# Warm architectural lighting, cool constellation light and reflected storefront color.
for x in (-18,-9,0,9,18):
    for y in (-15,-5,7,17):
        z=5.2 if abs(x)>14 else 12.3
        cyl('Ceiling spot fixture',(x,y,z),.2,.15,M['Black'],16)
        cyl('Ceiling luminous lens',(x,y,z-.085),.15,.025,M['WhiteLight'],16)
        light('Warm ceiling wash',(x,y,z-.25),'FFD5A2',950 if z<6 else 1800,4,unity_intensity=2.4,ran=13)
for x,y in [(-8,0),(8,0),(0,7),(0,-7)]:light('Atrium amber bounce',(x,y,9.8),'FFAE57',1200,4,unity_intensity=2.8,ran=14)
light('Entrance daylight',(0,-19,8),'BFD9FF',2300,12,target=(0,5,2),unity_intensity=2,ran=20)
light('Welcome warm pool',(0,-1,6),'FFBE75',600,4,unity_intensity=1.5,ran=8)
light('Canopy blue atmosphere',(0,0,11.8),'3978FF',550,4,unity_intensity=1.8,ran=12)
for x in (-18,18):light('Gallery warm wash',(x,5,11.4),'FFE0B0',1800,8,unity_intensity=2.5,ran=20)

# Apply the major environment-art revision to the existing layout.
exec(compile((ROOT/'Tools/redesign_art.py').read_text(), str(ROOT/'Tools/redesign_art.py'), 'exec'))

# Bake static meshes into material-aware spatial groups for a manageable Unity hierarchy.
# Linked copies of the CC0 source meshes are consolidated; originals stay in ThirdParty.
for proto,_ in PROTOS.values():bpy.data.objects.remove(proto,do_unlink=True)
bpy.context.view_layer.update()
depsgraph=bpy.context.evaluated_depsgraph_get()
groups={}
for o in list(scene.objects):
    if o.type in ('MESH','FONT','CURVE'):
        # Spatial cells preserve culling for supermarket aisles.
        key=(o.get('sipo_group','Architecture'),int(o.location.x//8),int(o.location.y//8))
        groups.setdefault(key,[]).append(o)
original_objects=[]
for (group,x,y),obs in groups.items():
    # Copy evaluated solid-color geometry into fresh meshes. This avoids Blender's
    # destructive join on linked glTF custom-data layers and keeps source meshes intact.
    verts=[];faces=[];indices=[];smooth=[];materials=[];material_ids={}
    for source_obj in obs:
        evaluated=source_obj.evaluated_get(depsgraph)
        mesh=evaluated.to_mesh();matrix=source_obj.matrix_world;offset=len(verts)
        verts.extend(tuple(matrix@v.co) for v in mesh.vertices)
        remap={}
        for i,evaluated_material in enumerate(mesh.materials):
            m=bpy.data.materials.get(evaluated_material.name)
            if m is None:raise RuntimeError('Missing original material '+evaluated_material.name)
            if m.name not in material_ids:material_ids[m.name]=len(materials);materials.append(m)
            remap[i]=material_ids[m.name]
        for p in mesh.polygons:
            faces.append(tuple(offset+i for i in p.vertices));indices.append(remap.get(p.material_index,0));smooth.append(p.use_smooth)
        evaluated.to_mesh_clear()
    name=f'{group} [{x},{y}]'
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces)
    for m in materials:mesh.materials.append(m)
    mesh.polygons.foreach_set('material_index',indices);mesh.polygons.foreach_set('use_smooth',smooth);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o)
    original_objects.extend(obs)
del depsgraph
bpy.data.batch_remove(ids=original_objects)
bpy.context.view_layer.update()
print('Geometry consolidated into',len(groups),'spatial batches',flush=True)
for name,loc in [('Origin',(0,0,0)),('Right',(1,0,0)),('Back',(0,-1,0)),('Up',(0,0,1))]:
    o=bpy.data.objects.new('Anchor_'+name,None);bpy.context.collection.objects.link(o);o.location=loc
# Record imported solid-color materials too, avoiding any unlicensed external textures.
known={m['name'] for m in DATA['materials']}
for m in bpy.data.materials:
    if m.name in known:continue
    p=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
    c=p.inputs['Base Color'].default_value[:3] if p else m.diffuse_color[:3]
    srgb=lambda v:12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055
    DATA['materials'].append({'name':m.name,'color':[srgb(v) for v in c],'roughness':float(p.inputs['Roughness'].default_value) if p else .42,'metallic':float(p.inputs['Metallic'].default_value) if p else 0,'emission':[0,0,0],'emissionStrength':0})
DATA['statistics']={'staticMeshes':sum(o.type=='MESH' for o in scene.objects),
                    'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in scene.objects if o.type=='MESH'),
                    'reusedAssetTypes':len(PROTOS),'lightCount':len(DATA['lights']),'colliderCount':len(DATA['colliders'])}
(OUT/'scene-data.json').write_text(json.dumps(DATA,indent=2)+'\n')
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in ('MESH','EMPTY'):o.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(OUT/'SipoSupermarket.fbx'),use_selection=True,object_types={'MESH','EMPTY'},
                         axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_space_transform=False,
                         mesh_smooth_type='FACE',use_mesh_modifiers=True,add_leaf_bones=False,path_mode='AUTO')

world=bpy.data.worlds.new('Evening in Sipo');world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.21,.34,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.24
scene.world=world
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32
scene.cycles.use_denoising=False;scene.cycles.max_bounces=7
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-1.7
scene.use_nodes=True
nt=scene.node_tree;nt.nodes.clear();rl=nt.nodes.new('CompositorNodeRLayers');gl=nt.nodes.new('CompositorNodeGlare')
gl.glare_type='FOG_GLOW';gl.quality='HIGH';gl.threshold=1.8
comp=nt.nodes.new('CompositorNodeComposite');nt.links.new(rl.outputs['Image'],gl.inputs['Image']);nt.links.new(gl.outputs['Image'],comp.inputs['Image'])
def camera(name,loc,target,lens):
    d=bpy.data.cameras.new(name);d.lens=lens;d.clip_end=200
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
hero=camera('01 Grand atrium',(0,-20.4,3.5),(0,3.5,6.05),21)
camera('02 Fresh garden',(-8,-8.5,1.7),(-10,1,3),21)
camera('03 Mezzanine',(-17,-8,8.5),(1,3,4.9),23)
camera('04 Grand entrance',(0,-38,5.5),(0,-15,6.7),25)
camera('05 Bakery',(-17.5,3.8,1.7),(-18,11,2.7),20)
camera('06 Snacks',(-6.5,.8,1.7),(-6.5,8.6,2.7),21)
camera('07 Drinks',(7,-12,1.7),(7,-4.3,2.6),21)
camera('08 Frozen',(1,3,1.7),(1,10,2.7),20)
camera('09 Kitchen',(-19,-6.7,7.5),(-19,.3,7.6),22)
camera('10 Gym',(19,-6.7,7.5),(19,.3,7.6),22)
camera('11 Checkout',(13,-20,1.7),(15,-10,3),19)
camera('12 First person',(0,-17.8,1.7),(0,1,5.2),19)
scene.camera=hero
exec(compile((ROOT/'Tools/preview_hands.py').read_text(),str(ROOT/'Tools/preview_hands.py'),'exec'))
# Save .blend outside Assets, so Unity never tries to launch Blender as an importer.
source=ROOT/'ArtSource';source.mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(source/'SipoSupermarket.blend'),compress=True)
print('SIPO_BUILD_COMPLETE '+json.dumps(DATA['statistics']),flush=True)
if '--render' in sys.argv:
    import runpy
    runpy.run_path(str(ROOT/'Tools/render_views.py'))['render_view']('hero')
