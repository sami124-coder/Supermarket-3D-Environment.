"""Grand atrium, planetarium, reception architecture and intentional scale pass.
Art only. Called after the previous design and before specialist art modules.
"""
GROUP='Premium atrium architecture'
# A human-scale sculpted reception counter replaces the oversized solid drum.
for o in list(scene.objects):
    if o.name.startswith(('Welcome desk','Service display')) or (o.type=='FONT' and o.data.body in ('WELCOME','a little joy in every aisle','HELLO')):
        bpy.data.objects.remove(o,do_unlink=True)
DATA['colliders']=[c for c in DATA['colliders'] if c['name']!='Welcome desk']
M['ReceptionOrange']=mat('ReceptionOrange','E76008',.21,.16)
M['StoneIvory']=mat('StoneIvory','FBE6C4',.19,.06)
M['CelestialInk']=mat('CelestialInk','061842',.35,0,.12)
# Partial annular prism, gently curved to form a crescent with an open service side.
def atrium_arc(name,center,outer,inner,bottom,top,start,end,material):
    verts=[];faces=[];n=96
    for z in (bottom,top):
        for radius in (outer,inner):
            for i in range(n+1):
                a=start+(end-start)*i/n
                verts.append((center[0]+radius*math.cos(a),center[1]+radius*math.sin(a),z))
    m=n+1
    for i in range(n):
        faces.extend([(i,i+1,2*m+i+1,2*m+i),(m+i+1,m+i,3*m+i,3*m+i+1),
                      (2*m+i,2*m+i+1,3*m+i+1,3*m+i),(i+1,i,m+i,m+i+1)])
    faces.extend([(0,2*m,3*m,m),(n,m+n,3*m+n,2*m+n)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);finish(obj,name,material)
    for p in mesh.polygons:p.use_smooth=len(p.vertices)==4
    bevel=obj.modifiers.new('Machined reception edge','BEVEL');bevel.width=.035;bevel.segments=3
    return obj
reception_before=set(scene.objects)
a0=math.radians(185);a1=math.radians(355)
atrium_arc('Crescent welcome sculpted front',(0,-1),3.7,2.88,.08,1.15,a0,a1,M['ReceptionOrange'])
atrium_arc('Ivory reception curved worktop',(0,-1),3.8,2.75,1.15,1.29,a0,a1,M['StoneIvory'])
for z in (.14,1.05):atrium_arc('Reception fine luminous inlay',(0,-1),3.715,3.68,z,z+.022,a0,a1,M['WarmLight'])
for i in range(58):
    a=a0+(a1-a0)*i/57;r=3.705
    rod('Reception bronze fluting',(r*math.cos(a),-1+r*math.sin(a),.28),(r*math.cos(a),-1+r*math.sin(a),.98),.014,M['Gold'])
# The inscription sits on a flat central emblem, letting the rest remain curved.
cube('Reception inscription shield',(0,-4.69,.7),(3.4,.08,.63),M['ReceptionOrange'],.09)
text('WELCOME',(0,-4.75,.76),.37,M['SignWhite'])
text('YOUR DAY, A LITTLE BRIGHTER',(0,-4.753,.45),.095,M['Cream'])
for x in (-1.45,1.45):
    cube('Reception terminal riser',(x,-2.4,1.4),(.15,.21,.28),M['Gold'],.03)
    screen=cube('Reception sculpted terminal',(x,-2.4,1.64),(.63,.10,.4),M['Navy'],.07)
    text('HELLO!',(x,-2.47,1.64),.11,M['WhiteLight'])
    for i in range(3):cube('Folded visitor leaflet',(x+.4,-2.35+i*.08,1.34),(.14,.23,.025),M[['Pink','Teal','Yellow'][i]],.01)
# All reception components keep human dimensions when the building expands.
for o in set(scene.objects)-reception_before:o['art_unit']='reception_crescent';o['art_anchor']=[0,-1,0]
coll('Crescent reception front',(0,-3.55,.62),(6.8,1.9,1.24))

# Replace the flat black ceiling disc with a shallow, faceted-color celestial dome.
GROUP='Celestial atrium'
for o in list(scene.objects):
    if o.name.startswith('Midnight celestial canopy'):bpy.data.objects.remove(o,do_unlink=True)
sky=[]
for i,col in enumerate(['071F68','082B8C','163297','233788','24337E','103889','102B70']):sky.append(mat('PlanetariumBlue'+str(i),col,.5,0,.28))
verts=[(0,0,12.72)];faces=[];indices=[];rings=18;segments=160
for j in range(1,rings+1):
    radius=11.5*j/rings
    for i in range(segments):
        a=i*math.tau/segments;verts.append((radius*math.cos(a),radius*.78*math.sin(a),12.72-.48*(radius/11.5)**2))
for i in range(segments):faces.append((0,1+(i+1)%segments,1+i));indices.append(3)
for j in range(1,rings):
    for i in range(segments):
        a=1+(j-1)*segments+i;b=1+(j-1)*segments+(i+1)%segments;c=1+j*segments+(i+1)%segments;d=1+j*segments+i
        faces.append((a,d,c,b));indices.append(int(3+2*math.sin(i*.043+j*.27))%len(sky))
mesh=bpy.data.meshes.new('Vaulted starfield enamel');mesh.from_pydata(verts,[],faces)
for m in sky:mesh.materials.append(m)
mesh.polygons.foreach_set('material_index',indices)
for p in mesh.polygons:p.use_smooth=True
obj=bpy.data.objects.new('Vaulted blue planetarium',mesh);bpy.context.collection.objects.link(obj);finish(obj,obj.name)
# Hundreds of geometric stars and sparse constellation traces remain visible in Unity.
rng=random.Random(404)
for i in range(610):
    a=rng.random()*math.tau;r=math.sqrt(rng.random())*11.2;x=r*math.cos(a);y=r*.78*math.sin(a);z=12.69-.48*(r/11.5)**2
    size=rng.uniform(.014,.038)
    uv('Dome starlight',(x,y,z),(size,size,size*.45),M['WhiteLight'] if i%5 else M['BlueLight'],8,4)
    if i%31==0:
        rod('Starlight sparkle',(x-.11,y,z-.01),(x+.11,y,z-.01),.007,M['WhiteLight'])
        rod('Starlight sparkle',(x,y-.11,z-.01),(x,y+.11,z-.01),.007,M['WhiteLight'])
# Perimeter orbital rail, small alternating decorative illuminated medallions.
ring('Second celestial orbit',11.0,8.55,11.93,.33,.22,M['Orange'])
for i in range(42):
    a=i*math.tau/42
    uv('Oculus perimeter jewel',(12.1*math.cos(a),9.42*math.sin(a),10.31),(.09,.09,.055),M['WhiteLight'],12,8)
# More depth planes in the hanging planetarium, with clear space around the logo.
for i,(x,y,z,r,col) in enumerate([(-9,3,9.8,.66,'Teal'),(-6,6,10.5,.5,'Pink'),(-2,7,10,.68,'Orange'),(3,7,9.8,.45,'Purple'),(7,5,10.7,.65,'Yellow'),(9,2,9.9,.5,'Teal'),(-9,-3,8.8,.47,'Orange'),(8,-4,9.1,.52,'Pink')]):
    rod('Fine planet hanging cable',(x,y,z),(x,y,12.3),.009,M['Gold'])
    uv('Additional suspended planet',(x,y,z),(r,)*3,M[col],40,24)
    for h in (-.65,-.28,.28,.65):torus('Fine candy planet latitude',(x,y,z+h*r),math.sqrt(1-h*h)*r,.018,M['WarmLight'])
    if i in (1,4,7):
        orbit=torus('Tilted Saturn orbit',(x,y,z),r*1.65,.035,M['Gold']);orbit.rotation_euler=(.25,.4,0)
for x,y,z in [(-8,5,8.8),(-3,8,9.1),(4,5,10.2),(8,0,8.7),(-8,-6,9.3)]:
    rod('Cloud pendant fine cable',(x,y,z),(x,y,12.3),.008,M['Gold'])
    for dx,dz,r in [(-.48,0,.39),(-.1,.23,.47),(.32,.12,.43),(.65,0,.3)]:
        uv('Sculpted cotton cloud',(x+dx,y,z+dz),(r,r*.65,r*.86),M['Cream'],28,16)
# Mini constellation mobiles, five pointed stars extruded for geometric shading.
for x,y,z,s in [(-5,5,8.6,.3),(4,0,8.8,.32),(7,7,8.4,.4),(-9,1,8,.25)]:
    v=[]
    for yy in (-.035,.035):
        for i in range(10):
            a=math.pi/2+i*math.pi/5;r=s if i%2==0 else s*.43;v.append((x+r*math.cos(a),y+yy,z+r*math.sin(a)))
    f=[tuple(reversed(range(10))),tuple(range(10,20))]+[(i,(i+1)%10,(i+1)%10+10,i+10) for i in range(10)]
    me=bpy.data.meshes.new('Star pendant');me.from_pydata(v,[],f);ob=bpy.data.objects.new('Five pointed hanging star',me);bpy.context.collection.objects.link(ob);finish(ob,ob.name,M['WarmLight'])
    rod('Star hanging cable',(x,y,z+s),(x,y,12.1),.008,M['Gold'])

# Retail hall dimension cues: repeating under-balcony bays with cornices and lamps.
GROUP='Premium architectural layers'
for x in (-23.5,23.5):
    for y in (-17,-10,-3,4,11,18):
        cube('Retail wall inset',(x,y,2.45),(.13,6.45,4.8),M['Blue'],.045)
        cube('Retail bay golden pilaster',(x-.1*(1 if x>0 else -1),y-3.3,2.5),(.22,.18,5),M['Gold'],.035)
for x in (-14,14):
    for y in range(-18,18,3):
        cyl('Under gallery downlight trim',(x+(1.2 if x>0 else -1.2),y,5.21),.13,.04,M['Gold'],20)
        cyl('Under gallery luminous spot',(x+(1.2 if x>0 else -1.2),y,5.18),.09,.016,M['WhiteLight'],16)
        light('Retail gallery warm pool',(x+(2 if x>0 else -2),y,5.0),'FFE0B0',150,1.0,unity_intensity=.6,ran=6)
# Low floral welcome benches give near-ground richness without blocking the main aisle.
GROUP='Premium atrium furniture'
for x in (-7,7):
    before=set(scene.objects)
    cube('Atrium curved bench base',(x,-10,.22),(2.8,1,.38),M['Blue'],.17)
    cube('Atrium tailored bench cushion',(x,-10,.49),(2.9,1.05,.22),M['Orange'],.15)
    for xx in (x-1.25,x+1.25):cyl('Bench brass foot',(xx,-10,.1),.1,.2,M['Gold'],16)
    for o in set(scene.objects)-before:o['art_unit']='welcome_bench_'+str(x);o['art_anchor']=[x,-10,0]
    coll('Welcome lounge bench',(x,-10,.36),(2.9,1.05,.72))

# Keep roof framing above the planetarium surface and remove visible utility spots inside it.
for o in list(scene.objects):
    if o.name.startswith(('Roof structure','Roof crossbeam')):o.location.z+=.16
    elif o.name.startswith(('Ceiling spot fixture','Ceiling luminous lens')) and abs(o.location.x)<13 and abs(o.location.y)<10:
        bpy.data.objects.remove(o,do_unlink=True)
