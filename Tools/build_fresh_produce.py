"""Build only the additive Fresh Produce module. Never writes original supermarket assets.
blender -b -t 6 --python-exit-code 1 --python Tools/build_fresh_produce.py
"""
import bpy, bmesh, math, random, json, sys, uuid, shutil
from pathlib import Path
from mathutils import Vector, Matrix
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Assets/FreshProduce'; MODELS=OUT/'Models'; TEX=OUT/'Textures'
for p in (OUT,MODELS,TEX): p.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'Tools'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
rng=random.Random(40912);M={};SPECS={};PROTOS={};LIB=[];LODS=[];COUNTS={};GROUP='Architecture'
DATA={'schemaVersion':1,'name':'SIPO Fresh Produce | Orchard of little joys','modelParts':['Assets/FreshProduce/Models/SipoFreshProduce.fbx'],
 'libraryModel':'Assets/FreshProduce/Models/SipoProduceLibrary.fbx','preferredPosition':[-14.2,0,-2],
 'bounds':{'center':[0,4.875,0],'size':[26,10.75,26]},'colliders':[],'lights':[],'reflections':[], 'libraryItems':[], 'lodGroups':[],
 'viewpoints':[{'name':'Arrival','position':[0,1.7,11.6],'target':[0,3.4,0]}, {'name':'Accessible loop','position':[6.6,1.7,2],'target':[0,1.4,0]}]}
libcol=bpy.data.collections.new('Reusable source props (not scene instances)');scene.collection.children.link(libcol);libcol.hide_render=True
FONT=bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf')

def rgb(c):return tuple(int(c[i:i+2],16)/255 for i in (0,2,4)) if isinstance(c,str) else tuple(c)
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def material(name,col,rough=.4,metal=0,emit=0,alpha=1):
 m=bpy.data.materials.new('SIPO_FP_'+name);c=rgb(col);m.diffuse_color=(*c,alpha);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*(linear(v) for v in c),1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emit:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emit
 if alpha<1:p.inputs['Transmission Weight'].default_value=.78;p.inputs['IOR'].default_value=1.45
 SPECS[m.name]={'name':m.name,'color':list(c),'roughness':rough,'metallic':metal,'emission':list(c) if emit else [0,0,0],'emissionStrength':emit,'alpha':alpha,'transparent':alpha<1}
 M[name]=m;return m
for n,c,r,me,e in [('Emerald','12694D',.28,.12,0),('Jade','248C62',.3,.06,0),('Lime','9BBC45',.36,0,0),('Cream','FFF0CB',.31,.05,0),('Navy','10244D',.32,.05,0),('Cobalt','174CC0',.25,.12,0),('Orange','FF8621',.26,.18,0),('Gold','DAB264',.23,.78,0),('Steel','A6BCCB',.22,.9,0),('Black','19222B',.45,.1,0),('Wood','D7A163',.5,0,0),('DarkWood','8C552F',.55,0,0),('Soil','443123',.86,0,0),('WarmLED','FF951B',.32,0,2.2),('WhiteLED','FFF5D9',.3,0,1.0),('BlueLED','4FBBFF',.3,0,1.4),('RedApple','DD2533',.29,0,0),('GreenApple','A5C43D',.32,0,0),('OrangeFruit','FF971F',.37,0,0),('YellowPear','D9C948',.39,0,0),('RedPepper','E92C24',.29,0,0),('YellowPepper','FFCB30',.31,0,0),('Stem','634129',.62,0,0),('Leaf','388C37',.45,0,0),('Grape','702B71',.33,0,0),('Rose','F85787',.3,0,0)]:material(n,c,r,me,e)
material('Glass','B8DDD6',.16,0,0,.16)

def image(name,arr):
 h,w,_=arr.shape;im=bpy.data.images.new(name,width=w,height=h,alpha=True);im.pixels.foreach_set(np.asarray(arr,dtype=np.float32).ravel());im.filepath_raw=str(TEX/(name+'.png'));im.file_format='PNG';im.save();return im
# Original shared wood grain and small-scale skin normal maps; real exportable texture data.
w,h=512,512;y,x=np.mgrid[0:h,0:w]/512
noise=np.random.default_rng(88).random((h,w))
grain=.5+.5*np.sin(x*190+4*np.sin(y*12)+np.sin(x*31+y*18));grain=.88+.12*grain+.025*(noise-.5)
a=np.ones((h,w,4));a[:,:,:3]=np.array([.75,.48,.25])*grain[:,:,None];wood=image('OrchardWood_BaseColor',a)
a=np.ones((h,w,4));dx=np.cos(x*190+4*np.sin(y*12))*.15;a[:,:,0]=.5+dx*.5;a[:,:,1]=.5;a[:,:,2]=np.sqrt(1-dx*dx)*.5+.5;woodnormal=image('OrchardWood_Normal',a)
a=np.ones((h,w,4));nx=(noise-.5)*.28;ny=(np.roll(noise,2,axis=1)-.5)*.28;a[:,:,0]=nx*.5+.5;a[:,:,1]=ny*.5+.5;a[:,:,2]=np.sqrt(1-nx*nx-ny*ny)*.5+.5;skin=image('ProduceSkin_Normal',a)

def texture(ma,im,kind):
 n=ma.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;p=ma.node_tree.nodes['Principled BSDF']
 if kind=='baseMap':ma.node_tree.links.new(n.outputs['Color'],p.inputs['Base Color'])
 else:
  im.colorspace_settings.name='Non-Color';normal=ma.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.3;ma.node_tree.links.new(n.outputs['Color'],normal.inputs['Color']);ma.node_tree.links.new(normal.outputs['Normal'],p.inputs['Normal'])
 SPECS[ma.name][kind]=str(Path(im.filepath_raw).relative_to(ROOT));SPECS[ma.name]['normalScale']=.3
texture(M['Wood'],wood,'baseMap');SPECS[M['Wood'].name]['color']=[1,1,1];texture(M['Wood'],woodnormal,'normalMap')
for n in ('RedApple','GreenApple','OrangeFruit','YellowPear','RedPepper','YellowPepper'):texture(M[n],skin,'normalMap')
# Existing project porcelain microstructure is reused through an independent copy.
shutil.copyfile(ROOT/'Assets/Environment/Textures/Porcelain_MicroNormal.png',TEX/'Porcelain_MicroNormal.png')
floornormal=bpy.data.images.load(str(TEX/'Porcelain_MicroNormal.png'))
for n in ('Cobalt','Cream'):texture(M[n],floornormal,'normalMap')

def finish(o,name,ma=None,group=None):
 o.name=name;o['department_group']=group or GROUP
 if ma:o.data.materials.append(ma)
 return o
def mesh(name,verts,faces,ma,smooth=True):
 d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.validate(verbose=True);d.update();o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);finish(o,name,ma)
 for p in d.polygons:p.use_smooth=smooth
 uv=d.uv_layers.new(name='UVMap')
 for p in d.polygons:
  normal=p.normal;axis=max(range(3),key=lambda j:abs(normal[j]));axes=[j for j in range(3) if j!=axis]
  for i in p.loop_indices:
   v=d.vertices[d.loops[i].vertex_index].co;uv.data[i].uv=(v[axes[0]],v[axes[1]])
 return o
def primitive(shape,name,pos,size,ma,segments=24,rings=12):
 d=bpy.data.meshes.new(name);bm=bmesh.new();bm.loops.layers.uv.verify()
 if shape=='box':bmesh.ops.create_cube(bm,size=1,calc_uvs=True)
 elif shape=='sphere':bmesh.ops.create_uvsphere(bm,u_segments=segments,v_segments=rings,radius=1,calc_uvs=True)
 else:bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=segments,radius1=1,radius2=1,depth=1,calc_uvs=True)
 bm.to_mesh(d);bm.free();o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos
 for v in d.vertices:v.co=Vector((v.co.x*size[0],v.co.y*size[1],v.co.z*size[2]))
 finish(o,name,ma)
 for p in d.polygons:p.use_smooth=shape!='box' and len(p.vertices)<=4
 return o
def box(name,pos,size,ma,bevel=.025):
 o=primitive('box',name,pos,size,ma)
 if bevel:b=o.modifiers.new('Manufactured soft edges','BEVEL');b.width=bevel;b.segments=2;o.modifiers.new('Corner normals','WEIGHTED_NORMAL')
 return o
def sphere(name,pos,size,ma,seg=20,rings=12):return primitive('sphere',name,pos,size,ma,seg,rings)
def cylinder(name,pos,radius,depth,ma,vertices=64):return primitive('cylinder',name,pos,(radius,radius,depth),ma,vertices)
def rod(name,a,b,r,ma,vertices=10):
 a,b=Vector(a),Vector(b);o=cylinder(name,(a+b)/2,r,(b-a).length,ma,vertices);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def ring(name,r,width,z,height,ma,center=(0,0),n=128):
 verts=[]
 for zz in (z-height/2,z+height/2):
  for rr in (r,r-width):verts += [(center[0]+rr*math.cos(i*math.tau/n),center[1]+rr*math.sin(i*math.tau/n),zz) for i in range(n)]
 faces=[]
 for i in range(n):
  j=(i+1)%n;faces += [(i,j,2*n+j,2*n+i),(n+j,n+i,3*n+i,3*n+j),(2*n+i,2*n+j,3*n+j,3*n+i),(j,i,n+i,n+j)]
 return mesh(name,verts,faces,ma)
def label(body,pos,size,ma,angle=0):
 d=bpy.data.curves.new('Extruded lettering '+body,'FONT');d.body=body;d.size=size;d.align_x='CENTER';d.align_y='CENTER';d.extrude=.006;d.bevel_depth=.001;d.resolution_u=3;d.font=FONT
 o=bpy.data.objects.new('Lettering '+body,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(math.pi/2,0,angle);finish(o,o.name,ma);return o
def unity(v):return [float(v[0]),float(v[2]),float(-v[1])]
def coll(name,pos,size,rot=0):DATA['colliders'].append({'name':name,'position':unity(pos),'size':[size[0],size[2],size[1]],'rotation':[0,-math.degrees(rot),0]})
def combine(objects,name,remove=True):
 objects=[o for o in objects if o.type in ('MESH','FONT','CURVE')]
 if not objects:return None
 authored_group=objects[0].get('department_group',GROUP)
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:
  if o.type=='MESH':o.data=o.data.copy() # Joining must never mutate a shared reusable prototype.
  o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 bpy.ops.object.convert(target='MESH')
 if len(objects)>1:bpy.ops.object.join()
 result=bpy.context.object;result.name=name;result['department_group']=authored_group
 # Bake the merged local transform before reusing as an origin-centred mesh.
 matrix=result.matrix_world.copy()
 result.data.transform(matrix);result.matrix_world=Matrix.Identity(4)
 return result

def tolibrary(objects,name):
 obj=combine(objects,'Library_'+name);print('LIB',name,len(obj.data.polygons),flush=True);LIB.append(obj);PROTOS[name]=obj
 for col in list(obj.users_collection):col.objects.unlink(obj)
 libcol.objects.link(obj);obj['asset_role']='Reusable prototype';DATA['libraryItems'].append({'name':name,'objectNames':[obj.name]});return obj

def instance(key,pos,scale=1,angle=0):
 source=PROTOS[key];o=bpy.data.objects.new('Placed_'+key,source.data);scene.collection.objects.link(o);o.location=pos;o.scale=(scale,)*3;o.rotation_euler[2]=angle;finish(o,o.name);COUNTS[key]=COUNTS.get(key,0)+1;return o

def fruitprofile(kind,matname):
 before=set(scene.objects);verts=[];faces=[];N=24;R=15
 for j in range(R+1):
  t=math.pi*j/R;z=math.cos(t);rad=math.sin(t)
  for i in range(N):
   a=math.tau*i/N
   if kind=='Pepper':rr=.089*rad*(1+.14*math.cos(4*a));zz=.105*z+.012*math.cos(4*a)*rad**2
   elif kind=='Pear':rr=.083*rad*(1-.33*z);zz=.12*z
   elif kind=='Orange':rr=.092*rad*(1+.015*math.cos(8*a));zz=.086*z
   else:rr=.092*rad*(1+.033*math.cos(5*a)*abs(z));zz=.083*z-.015*(max(z,0)**10)+.007*(max(-z,0)**8)
   verts.append((rr*math.cos(a),rr*math.sin(a),zz+.095 if kind!='Pear' else zz+.13))
 for j in range(R):
  for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 o=mesh(kind,verts,faces,M[matname]);uv=o.data.uv_layers.active
 for p in o.data.polygons:
  for li in p.loop_indices:
   vi=o.data.loops[li].vertex_index;uv.data[li].uv=((vi%N)/N,(vi//N)/R)
 if kind!='Orange':
  top=.215 if kind=='Pepper' else (.245 if kind=='Pear' else .16);rod('Sculpted stem',(0,0,top),(.01,0,top+.05),.006,M['Stem'])
  mesh('Curled fruit leaf',[(0,0,top+.025),(.026,-.014,top+.045),(.064,0,top+.05),(.032,.02,top+.045),(.027,0,top+.056)],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],M['Leaf'])
 result=tolibrary(list(set(scene.objects)-before),matname)
 minimum=min(v.co.z for v in result.data.vertices)
 for v in result.data.vertices:v.co.z-=minimum
 return result
print('BUILD HERO FRUIT',flush=True)
for kind,ma in [('Apple','RedApple'),('Apple','GreenApple'),('Orange','OrangeFruit'),('Pear','YellowPear'),('Pepper','RedPepper'),('Pepper','YellowPepper')]:
 print('FRUIT',kind,ma,flush=True);fruitprofile(kind,ma)

print('# Retained CC0',flush=True)
# Retained CC0 produce forms: scaled to edible grocery sizes; original files untouched.
licensed=['banana','broccoli','carrot','grapes','pineapple','cabbage','lemon','watermelon','eggplant','corn','tomato','sodaBottle','fish']
for key in licensed:
 print('CC0',key,flush=True)
 before=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/f'Assets/ThirdParty/KenneyFoodKit/Source/{key}.glb'));objects=[o for o in set(scene.objects)-before if o.type=='MESH'];obj=combine(objects,'CC0 '+key)
 for m in obj.data.materials:
  if m.name not in SPECS:
   n=m.node_tree.nodes.get('Principled BSDF');c=tuple(n.inputs['Base Color'].default_value[:3]);srgb=tuple(12.92*v if v<.0031308 else 1.055*v**(1/2.4)-.055 for v in c)
   m.name='SIPO_FP_CC0_'+m.name;m.diffuse_color=(*srgb,1);n.inputs['Metallic'].default_value=0;n.inputs['Roughness'].default_value=.36
   SPECS[m.name]={'name':m.name,'color':list(srgb),'roughness':.36,'metallic':0,'emission':[0,0,0],'emissionStrength':0}
 # Recenter / normalize actual vertex positions, including GLTF transforms.
 coords=[v.co for v in obj.data.vertices];lo=Vector(tuple(min(v[j] for v in coords) for j in range(3)));hi=Vector(tuple(max(v[j] for v in coords) for j in range(3)))
 longest=max(hi-lo);desired={'banana':.31,'broccoli':.24,'carrot':.3,'grapes':.24,'pineapple':.42,'cabbage':.25,'lemon':.14,'watermelon':.36,'eggplant':.24,'corn':.25,'tomato':.16,'sodaBottle':.3,'fish':.32}[key];center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
 for v in obj.data.vertices:v.co=(v.co-center)*(desired/longest)
 for p in obj.data.polygons:p.use_smooth=True
 # Small bevels soften the licensed stylized silhouettes without inventing texture detail.
 if key not in ('grapes','broccoli','cabbage'):
  bevel=obj.modifiers.new('Softened CC0 edges','BEVEL');bevel.width=.003;bevel.segments=2
 tolibrary([obj],key)
 for o in set(scene.objects)-before:
  if o.type=='EMPTY':bpy.data.objects.remove(o,do_unlink=True)

print('# Reusable open',flush=True)
# Reusable open slatted crate with real gaps, label holder, metal corners and wood bottom.
before=set(scene.objects)
box('Crate bottom',(0,0,.035),(.94,.69,.06),M['Wood'],.012)
box('Raised ventilated produce deck',(0,0,.175),(.86,.60,.045),M['DarkWood'],.01)
for xx in (-.3,.3):box('Crate deck support',(xx,0,.11),(.045,.6,.14),M['Wood'],.01)
for x in (-.45,.45):
 for y in (-.325,.325):box('Corner',(x,y,.18),(.045,.045,.33),M['DarkWood'],.012)
for z in (.13,.255):
 for y in (-.33,.33):box('Long slat',(0,y,z),(.94,.038,.095),M['Wood'],.012)
 for x in (-.46,.46):box('Short slat',(x,0,z),(.035,.65,.095),M['Wood'],.01)
box('Price holder',(0,-.359,.2),(.25,.035,.115),M['Gold'],.009)
box('Paper price tag',(0,-.38,.203),(.224,.008,.085),M['Cream'],.002)
tolibrary(list(set(scene.objects)-before),'WoodCrate')

print('START FLOOR',flush=True)
GROUP='Porcelain and brass walking court'
box('Department foundation',(0,0,-.18),(26,26,.34),M['Navy'],.04);coll('Walkable department floor',(0,0,-.18),(26,26,.34))
for x in range(-13,13):
 for y in range(-13,13):box('Inlaid porcelain tile',(x+.5,y+.5,.005),(.988,.988,.035),M['Cobalt' if (x//2+y//2)%2==0 else 'Cream'],.009)
for r in (5.6,5.68,7.45,7.53,10.4):ring('Curved brass floor inlay',r,.025,.028,.008,M['Gold'])
# Modular floor batching, no full-department combined mesh.
for quadrant in range(4):
 objs=[o for o in scene.objects if o.get('department_group')==GROUP and o.type=='MESH' and not o.name.startswith('Floor_Quadrant_') and ((o.location.x>=0)+2*(o.location.y>=0))==quadrant]
 combine(objs,'Floor_Quadrant_%d'%quadrant)
print('START CENTRAL',flush=True)
GROUP='Central radial merchandising'
for r,z,h in [(4.9,.37,.7),(3.62,.98,.46),(2.42,1.41,.39)]:
 cylinder('Tiered green plinth',(0,0,z),r,h,M['Emerald'],96);ring('Champagne plinth moulding',r+.025,.06,z+h/2,.055,M['Gold']);ring('Plinth kicklight',r+.01,.025,z-h/2+.045,.025,M['WarmLED'])
# Sector colliders follow the circular boundary rather than a square blocking the aisle.
for i in range(20):
 a=i*math.tau/20;coll('Central island guard %02d'%i,(math.cos(a)*4.25,math.sin(a)*4.25,.66),(1.7,1.32,1.32),a+math.pi/2)
coll('Central tree core',(0,0,1),(6.1,6.1,2))
varieties=['RedApple','OrangeFruit','GreenApple','YellowPear','banana','RedPepper','pineapple','broccoli','grapes','carrot','YellowPepper','lemon','cabbage','tomato']
PRICES={'RedApple':'APPLE  2.90','OrangeFruit':'ORANGE  1.90','GreenApple':'APPLE  2.60','YellowPear':'PEAR  2.50','banana':'BANANA  1.80','RedPepper':'PEPPER  3.20','pineapple':'PINEAPPLE  3.90','broccoli':'BROCCOLI  2.40','grapes':'GRAPES  3.60','carrot':'CARROT  1.40','YellowPepper':'PEPPER  3.20','lemon':'LEMON  1.60','cabbage':'GREENS  2.20','tomato':'TOMATO  2.80'}

def batchlod(objs,name):
 print('BATCH',name,len(objs),sum(len(o.data.polygons) for o in objs if o.type=='MESH'),flush=True)
 hi=combine(objs,name+'_LOD0');lo=hi.copy();lo.data=hi.data.copy();lo.name=name+'_LOD1';scene.collection.objects.link(lo)
 dec=lo.modifiers.new('Distance silhouette LOD','DECIMATE');dec.ratio=.27
 bpy.context.view_layer.objects.active=lo;bpy.ops.object.modifier_apply(modifier=dec.name)
 lo.hide_render=True;LODS.append(lo);DATA['lodGroups'].append({'name':name,'lod0':[hi.name],'lod1':[lo.name]});return hi

for tier,(rad,z,n) in enumerate([(4.24,.76,16),(3.05,1.23,14),(1.96,1.67,12)]):
 for i in range(n):
  a=-math.pi/2+i*math.tau/n;key=varieties[(i+tier*5)%len(varieties)];before=set(scene.objects);center=Vector((rad*math.cos(a),rad*math.sin(a),z));rot=a+math.pi/2
  crate=instance('WoodCrate',center,1,rot);crate.scale=(1.75 if tier==0 else 1.4,1.25,1)
  width=1.48 if tier==0 else 1.15;depth=.69;spacing=.225 if key not in ('pineapple','broccoli','cabbage','carrot','banana') else .29
  cols=max(3,int(width/spacing));rows=3
  for row in range(rows):
   for col in range(cols):
    u=(col-(cols-1)/2)*spacing+rng.uniform(-.018,.018);v=(row-1)*.245+rng.uniform(-.018,.018);p=center+Vector((-math.sin(a)*u+math.cos(a)*v, math.cos(a)*u+math.sin(a)*v,.205))
    scale=rng.uniform(.9,1.1);o=instance(key,p,scale,rng.uniform(0,math.tau));o.rotation_euler.x=rng.uniform(-.12,.12);o.rotation_euler.y=rng.uniform(-.12,.12)
    if row<2 and col<cols-1 and key in ('RedApple','OrangeFruit','GreenApple','YellowPear','RedPepper','YellowPepper','lemon','tomato'):
     p+=Vector((-math.sin(a)*spacing*.5+math.cos(a)*.12,math.cos(a)*spacing*.5+math.sin(a)*.12,.105));instance(key,p,rng.uniform(.93,1.08),rng.uniform(0,math.tau))
     if row==0 and col<cols-2:
      p+=Vector((-math.sin(a)*spacing*.5+math.cos(a)*.12,math.cos(a)*spacing*.5+math.sin(a)*.12,.105));instance(key,p,rng.uniform(.92,1.04),rng.uniform(0,math.tau))
  batchlod(list(set(scene.objects)-before),'Harvest_T%d_Bay%02d'%(tier,i))
  if tier==0:
   # The crate's radial scale places the tag face 0.48m from its centre.
   # Keep the lettering just outside that face so URP depth testing cannot hide it.
   pos=((rad+.49)*math.cos(a),(rad+.49)*math.sin(a),z+.205);label(PRICES[key],pos,.063,M['Navy'],rot)
   # Physical colorful fruit medallions on the green facade, with brass border.
   badge=sphere('Raised produce medallion',(4.91*math.cos(a),4.91*math.sin(a),.36),(.21,.035,.2),M['OrangeFruit' if i%3==0 else ('RedApple' if i%3==1 else 'Lime')],16,10);badge.rotation_euler[2]=rot
   # Stems and curled leaves make these sculpted fruit icons rather than plain discs.
   icon=Vector((4.96*math.cos(a),4.96*math.sin(a),.56));tangent=Vector((-math.sin(a),math.cos(a),0))
   rod('Fruit icon stem',icon,icon+Vector((0,0,.07)),.014,M['Gold'])
   mesh('Fruit icon leaf',[icon,icon+tangent*.06+Vector((0,0,.105)),icon+tangent*.19+Vector((0,0,.10)),icon+tangent*.12+Vector((0,0,.012))],[(3,2,1,0)],M['Lime'])
   label('FRESH',((4.94)*math.cos(a),(4.94)*math.sin(a),.17),.08,M['Cream'],rot)
print('# Side displays',flush=True)
# Side displays leave a 1.8m minimum clear loop around the central display.
for island,(x,y) in enumerate([(-8.2,-5.8),(8.2,-5.8),(-8.8,2.9),(8.8,2.9)]):
 before=set(scene.objects);cylinder('Satellite produce plinth',(x,y,.42),1.62,.84,M['Emerald']);ring('Satellite brass crown',1.64,.045,.86,.05,M['Gold'],(x,y));ring('Satellite warm kicklight',1.63,.025,.1,.025,M['WarmLED'],(x,y))
 for i in range(8):
  a=i*math.tau/8;key=varieties[(island*3+i)%len(varieties)];cx=x+1.1*math.cos(a);cy=y+1.1*math.sin(a);instance('WoodCrate',(cx,cy,.84),.85,a+math.pi/2)
  for j in range(12):
   u=(j%4-1.5)*.18;v=(j//4-1)*.18;instance(key,(cx-u*math.sin(a)+v*math.cos(a),cy+u*math.cos(a)+v*math.sin(a),1.02),rng.uniform(.84,.98),rng.random()*math.tau)
   if j%4<3 and j//4<2 and key in ('RedApple','OrangeFruit','GreenApple','YellowPear','RedPepper','YellowPepper','lemon','tomato'):
    u+=.09;v+=.09;instance(key,(cx-u*math.sin(a)+v*math.cos(a),cy+u*math.cos(a)+v*math.sin(a),1.13),rng.uniform(.82,.96),rng.random()*math.tau)
 cylinder('Satellite harvest crown',(x,y,.94),.57,.22,M['Wood'])
 for level in range(3):
  count=14-level*4;radius=.40-level*.13
  for j in range(count):
   a=j*math.tau/count;instance('OrangeFruit' if island%2 else 'RedApple',(x+radius*math.cos(a),y+radius*math.sin(a),1.055+level*.135),.92,rng.random()*math.tau)
 for i in range(10):
  a=i*math.tau/10;coll('Satellite %d guard %d'%(island,i),(x+1.15*math.cos(a),y+1.15*math.sin(a),.65),(1.05,1.05,1.3),a)
 coll('Satellite core %d'%island,(x,y,.5),(1.9,1.9,1))
 batchlod(list(set(scene.objects)-before),'Satellite_Island_%d'%island)

print('# Back merchandising',flush=True)
# Back merchandising wall: cold produce/drinks and market fish, no gameplay doors.
GROUP='Refrigerated market arcade'
for side in (-1,1):
 x=side*7.65;y=9.65;before=set(scene.objects)
 box('Cold cabinet back',(x,y,1.5),(6,.16,2.95),M['Navy']);box('Cold cabinet base',(x,y-.57,.25),(6,1.2,.5),M['Emerald'],.07)
 for shelf in range(4):
  zz=.6+shelf*.53;box('Refrigerated shelf',(x,y-.47,zz),(5.8,1,.065),M['Steel'],.015);box('Shelf LED',(x,y-.99,zz), (5.8,.022,.025),M['WhiteLED'],.004)
  for j in range(22):
   key='sodaBottle' if side>0 else ('fish' if shelf<2 else 'tomato');instance(key,(x-2.7+j*.255,y-.53,zz+.05),.87,rng.random()*.1)
 for dx in (-3,-1,1,3):box('Glass door mullion',(x+dx,y-1.05,1.65),(.045,.08,2.5),M['Gold'],.008)
 # Glass at outer edges only leaves a readable open-merchandise centre.
 for dx in (-2,2):box('Cold display glazing',(x+dx,y-1.03,1.55),(1.85,.015,2.25),M['Glass'],.002)
 box('Cold header',(x,y-.45,3),(6,1.15,.42),M['Emerald'],.05);label('PRESSED & CHILLED' if side>0 else 'MARKET CATCH',(x,y-1.045,3.03),.24,M['WhiteLED'])
 coll('Cold display '+str(side),(x,y-.5,1.5),(6,1.2,3));batchlod(list(set(scene.objects)-before),'Cold_Arcade_'+str(side))
# Sculptural columns and a shallow background gallery complete the module's retail setting.
GROUP='Orchard architecture'
box('Rear botanical arcade wall',(0,12.75,4.95),(26,.22,10.1),M['Navy'],.04);coll('Rear arcade wall',(0,12.75,4.95),(26,.22,10.1))
for xx in range(-10,11,4):
 box('Upper gallery inset',(xx,12.60,6.8),(3.2,.10,2.7),M['Emerald'],.18)
 box('Golden gallery sill',(xx,12.40,5.5),(3.5,.5,.18),M['Gold'],.05)
 label('SIPO  /  GARDEN CLUB',(xx,12.47,7.7),.18,M['WhiteLED'])
 for zz in (6,6.9):box('Upper stocked display shelf',(xx,12.38,zz),(2.9,.45,.075),M['Wood'],.015)
 for jj in range(12):
  for zz in (6.06,6.96):instance('sodaBottle',(xx-1.2+jj*.22,12.25,zz),.8,jj*.2)
for xx in (-12.7,12.7):
 box('Side arcade backdrop',(xx,6,4.8),(.22,13.6,9.7),M['Navy'],.04);coll('Side arcade wall',(xx,6,4.8),(.22,13.6,9.7))
 for zz in (3.9,8.7):box('Orange arcade ribbon',(xx,6,zz),(.3,13.6,.42),M['Orange'],.03)
for x in (-11.25,11.25):
 for y in (-8.7,8.7):
  cylinder('Cobalt column',(x,y,4.55),.45,9.1,M['Cobalt']);coll('Column', (x,y,4.55),(.9,.9,9.1))
  for z in (.3,3.8,7.9):ring('Tangerine column collar',.49,.09,z,.28,M['Orange'],(x,y),64)
  for z in (1.4,2.2,5.4,6.4):
   sphere('Harvest column applique',(x,y-.46,z),(.18,.025,.25),M['Orange' if int(z)%2 else 'Lime'],16,8)
# Rear gallery is scenic decoration at safe overhead height, not a falsely reachable secondfloor.
box('Rear floating arcade lintel',(0,11.8,4.9),(24,1.1,.58),M['Orange'],.06);box('Rear cobalt fascia',(0,11.2,4.92),(24,.06,.22),M['Cobalt'],.02)
label('SIPO   /   THE ORCHARD OF LITTLE JOYS',(0,11.1,4.95),.32,M['WhiteLED'])
for x in range(-11,12,2):
 rod('Arcade suspension',(x,11.8,5.2),(x,11.8,9.5),.035,M['Gold']);sphere('Arcade harvest orb',(x,11.8,6.4),(.24,.24,.24),M['OrangeFruit'],20,12)

GROUP='Suspended emerald sign and pendant canopy'
ring('FRESH PRODUCE monumental green drum',5.45,.32,6.35,1.25,M['Emerald'])
for z in (5.71,6.99):
 ring('Continuous amber illuminated rim',5.49,.045,z,.045,M['WarmLED']);ring('Champagne polished rim',5.50,.075,z+.055,.065,M['Gold'])
for a in [i*math.tau/8 for i in range(8)]:rod('Ring suspension cable',(5.1*math.cos(a),5.1*math.sin(a),6.98),(5.1*math.cos(a),5.1*math.sin(a),9.8),.014,M['Steel'])
word='FRESH PRODUCE';spacing=.116
for i,ch in enumerate(word):
 a=-math.pi/2+(i-(len(word)-1)/2)*spacing;label(ch,(5.48*math.cos(a),5.48*math.sin(a),6.35),.8,M['WhiteLED'],a+math.pi/2)
# Three-dimensional leaf emblem alongside the lettering, no image plane.
a=-.56;c=Vector((5.5*math.cos(a),5.5*math.sin(a),6.35));t=Vector((-math.sin(a),math.cos(a),0));up=Vector((0,0,1))
leafverts=[c-t*.19-up*.25,c-t*.24+up*.12,c+up*.43,c+t*.25+up*.11,c+t*.12-up*.18,c+Vector((math.cos(a),math.sin(a),0))*.03]
mesh('Embossed leaf insignia',leafverts,[(5,1,0),(5,2,1),(5,3,2),(5,4,3),(5,0,4)],M['WhiteLED'])
for i in range(24):
 a=i*math.tau/24;rr=3.6+(i%3)*.48;z=3.9+(i%5)*.31
 rod('Pendant braided flex',(rr*math.cos(a),rr*math.sin(a),6.7),(rr*math.cos(a),rr*math.sin(a),z+.16),.013,M['Black'])
 cylinder('Pendant brass socket',(rr*math.cos(a),rr*math.sin(a),z+.18),.063,.14,M['Gold'],16)
 sphere('Warm pendant pearl',(rr*math.cos(a),rr*math.sin(a),z),(.09,.09,.13),M['WarmLED'],20,12)
for i in range(20):
 a=i*math.tau/20;cylinder('Recessed rim luminaire',(5.25*math.cos(a),5.25*math.sin(a),5.72),.065,.018,M['WhiteLED'],16)

print('# Reuse the existing',flush=True)
# Reuse the existing flagship mascot, copied and relocated; original blend remains untouched.
GROUP='SIPO garden mascot'
source_name='Premium original Orbit Club mascots [-2,0]'
with bpy.data.libraries.load(str(ROOT/'ArtSource/SipoSupermarket.blend'),link=False) as (src,dst):dst.objects=[source_name]
mascot=dst.objects[0];scene.collection.objects.link(mascot);mascot.name='SIPO garden host';coords=[v.co.copy() for v in mascot.data.vertices];low=Vector(tuple(min(v[j] for v in coords) for j in range(3)));high=Vector(tuple(max(v[j] for v in coords) for j in range(3)));center=(low+high)/2
for v in mascot.data.vertices:v.co=(v.co-center)*1.3
mascot.location=(7.2,1,7);mascot.rotation_euler[2]=-.15;mascot['department_group']=GROUP
for i,m in enumerate(mascot.data.materials):
 cp=m.copy();cp.name='SIPO_FP_'+m.name.removeprefix('SIPO_');mascot.data.materials[i]=cp
 p=cp.node_tree.nodes.get('Principled BSDF');c=tuple(cp.diffuse_color[:3]);SPECS[cp.name]={'name':cp.name,'color':list(c),'roughness':float(p.inputs['Roughness'].default_value),'metallic':float(p.inputs['Metallic'].default_value),'emission':[0,0,0],'emissionStrength':0}
# Preserve a reusable mascot mesh in addition to the placed host.
local=mascot.copy();local.data=mascot.data.copy();local.location=(0,0,0);local.rotation_euler=(0,0,0);scene.collection.objects.link(local);tolibrary([local],'GardenMascot')
batchlod([mascot],'Garden_Host')

print('# Original tree',flush=True)
# Original tree helper builds only this module's vegetation.
import fresh_produce_botany
GROUP='Orchard tree and foliage'
before=set(scene.objects);fresh_produce_botany.build()
for o in set(scene.objects)-before:o['department_group']=GROUP
for i,pos in enumerate([(-11,-2,0),(11,-2,0),(-3.8,8.5,0),(3.8,8.5,0)]):
 before=set(scene.objects);fresh_produce_botany.potted_plant('Orchard planter %d'%i,pos,1.2)
 for o in set(scene.objects)-before:o['department_group']=GROUP
 coll('Planter %d'%i,(pos[0],pos[1],.65),(1.1,1.1,1.3))
# Retain an editable reusable plant prototype as requested.
before=set(scene.objects);fresh_produce_botany.potted_plant('Reusable fern',(0,0,0),1);tolibrary(list(set(scene.objects)-before),'LeafyPlanter')
for o in scene.objects:
 if o.type=='MESH':
  for m in o.data.materials:
   if m is None or m.name in SPECS:continue
   p=m.node_tree.nodes.get('Principled BSDF');c=rgb(m['sipo_source_srgb_hex']) if 'sipo_source_srgb_hex' in m else tuple(m.diffuse_color[:3]);SPECS[m.name]={'name':m.name,'color':list(c),'roughness':float(p.inputs['Roughness'].default_value),'metallic':float(p.inputs['Metallic'].default_value),'emission':[0,0,0],'emissionStrength':0}
# Batch foliage by assembly, with lightweight distance LODs.
for o in list(scene.objects):
 if o.type=='MESH' and o.get('department_group')==GROUP and o not in LIB:batchlod([o],'Botany_'+o.name.replace(' ','_'))

GROUP='Whimsical space ornaments'
for i,(x,y,z,r) in enumerate([(-8,0,8.2,.62),(8,-5,8.5,.5),(-4,7,8.4,.48),(5,8.1,8.8,.65)]):
 sphere('Harvest planet',(x,y,z),(r,r,r),M['OrangeFruit' if i%2==0 else 'Cobalt'],32,20)
 for j in (-1,0,1):ring('Planet latitude ribbon',r*math.sqrt(1-(j*.4)**2)+.012,.035,z+j*r*.4,.055,M['WarmLED'],(x,y),64)
 rod('Planet suspension',(x,y,z+r),(x,y,10),.012,M['Steel'])
 if i in (0,2):ring('Planet orbital ring',r*1.6,.08,z,.035,M['Gold'],(x,y),64)
for x,y,z in [(-7,-5,7.8),(6,6,8.7)]:
 for dx,dz,s in [(-.45,0,.4),(0,.17,.55),(.47,0,.37)]:sphere('Cloud ornament',(x+dx,y,z+dz),(s,.23,s*.65),M['Cream'],24,16)
for i in range(38):
 x=rng.uniform(-10,10);y=rng.uniform(-3,10);z=rng.uniform(8.6,9.5);r=rng.uniform(.06,.16)
 verts=[(x+math.cos(j*math.pi/5)*(r if j%2==0 else r*.38),y,z+math.sin(j*math.pi/5)*(r if j%2==0 else r*.38)) for j in range(10)]+[(x,y-.02,z)]
 mesh('Raised hanging star',verts,[(10,j,(j+1)%10) for j in range(10)],M['WhiteLED'])
# Upper thin space canopy behind the emerald crown. Structural beams remain airy.
ring('Blue celestial canopy outer halo',8.2,.23,9.8,.16,M['Cobalt']);ring('Canopy amber pinstripe',8.22,.028,9.7,.025,M['WarmLED'])
for x in (-10,-5,0,5,10):box('Open ceiling lattice',(x,0,10.05),(.055,24,.075),M['Navy'],.008)
for y in (-10,-5,0,5,10):box('Open roof cross rail',(0,y,10.05),(24,.055,.075),M['Navy'],.008)

# Seven directed/soft sources, one real-time shadow spotlight, no per-bulb shadow cost.
def light(name,pos,target,col,power,intensity,ran,angle=95,shadow=False,area=4):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=rgb(col);d.shape='DISK';d.size=area;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler()
 DATA['lights'].append({'name':name,'type':'spot','position':unity(pos),'target':unity(target),'color':list(rgb(col)),'intensity':intensity,'range':ran,'spotAngle':angle,'shadow':shadow})
light('Orchard soft merchandise key',(0,-5,8.5),(0,0,1),'FFE1B0',2300,125,19,100,True,5)
light('Cool cobalt shoulder',(-8,0,8),(0,0,2),'C0D6FF',1800,85,20,105,False,5)
light('Warm tree canopy',(1,3,7),(0,0,3),'FFBD65',1500,75,14,100,False,4)
light('East produce bays',(8,-2,7),(7,-4,1),'FFF2D8',1600,90,16,100,False,4)
light('West produce bays',(-8,-2,7),(-7,-4,1),'FFF2D8',1600,90,16,100,False,4)
light('Fresh arcade wash',(0,7,7),(0,9,1.5),'DBF0FF',1900,95,17,110,False,5)
light('Garden host portrait',(8,-4,8.5),(7,1,7),'FFE4BC',850,65,12,75,False,3)
DATA['reflections']=[{'name':'Orchard main HDR','position':[0,2.6,3.3],'center':[0,4.5,0],'size':[26,10,26],'resolution':512}, {'name':'Harvest counters HDR','position':[0,2.0,-7],'center':[0,3.5,-6],'size':[24,7,13],'resolution':256}]
print('# Organize architecture',flush=True)
# Organize architecture into spatial/material-family batches, preserving reusable source meshes in the .blend.
for group in sorted(set(o.get('department_group','') for o in scene.objects if o.type in ('MESH','FONT'))):
 if not group or group in ('Orchard tree and foliage',):continue
 objs=[o for o in scene.objects if o.type in ('MESH','FONT') and o.get('department_group')==group and o not in LIB and o not in LODS and not o.name.endswith('_LOD0') and not o.name.startswith('Floor_Quadrant')]
 if objs:combine(objs,'Architecture_'+group.replace(' ','_'))
# Anchors make the Unity FBX conversion self-checking even when exporter/importer axes differ.
anchors=[]
for n,pos in [('Origin',(0,0,0)),('Up',(0,0,1)),('Back',(0,-1,0)),('Right',(1,0,0))]:
 o=bpy.data.objects.new('Anchor_'+n,None);scene.collection.objects.link(o);o.location=pos;anchors.append(o)
# Named true scene cameras; no painted reference used anywhere.
def camera(name,pos,target,lens):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=150;return o
camera('FreshProduce_Hero',(0,-13,1.72),(0,.2,3.9),22)
camera('FreshProduce_EyeLevel',(-6,-8.8,1.7),(0,0,3.1),21)
camera('FreshProduce_Elevated',(12,-15,10.5),(0,0,2.8),32)
camera('FreshProduce_Detail',(-3.9,-5.9,1.78),(-2,-2.7,1.3),42)
scene.camera=bpy.data.objects['FreshProduce_Hero'];scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=False;scene.cycles.max_bounces=7
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.13,.21,.38,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.24
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.7
# Gentle optical glow for emissive mesh strips, not fog or a fabricated background.
scene.use_nodes=True;nodes=scene.node_tree.nodes;nodes.clear();rl=nodes.new('CompositorNodeRLayers');gl=nodes.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='HIGH';gl.threshold=2;gl.size=7;gl.mix=-.94;out=nodes.new('CompositorNodeComposite');scene.node_tree.links.new(rl.outputs['Image'],gl.inputs['Image']);scene.node_tree.links.new(gl.outputs['Image'],out.inputs['Image'])
print('# Export the scene',flush=True)
# Export the scene meshes and separate original reusable library. Distinct assets stay editable.
sceneobjects=[o for o in scene.objects if o.type=='MESH' and o not in LIB]
for path,objects in [(MODELS/'SipoFreshProduce.fbx',sceneobjects),(MODELS/'SipoProduceLibrary.fbx',LIB)]:
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects+anchors:o.select_set(True)
 bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,path_mode='AUTO')
 assert path.stat().st_size<99*1024*1024,(path,'GitHub file size limit')
DATA['materials']=list(SPECS.values());DATA['statistics']={'produceInstances':sum(COUNTS.get(k,0) for k in varieties+['sodaBottle','fish']),'instanceCounts':COUNTS,'highLodTriangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in sceneobjects if o not in LODS),'lowLodTriangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in LODS),'sceneMeshes':len(sceneobjects),'reusableAssets':len(LIB),'lodGroups':len(DATA['lodGroups'])}
DATA['licenseSources']=['Kenney Food Kit 1.2 CC0 (retained sources and notices)','Existing original SIPO Garden Orbit Club mascot','Original department architecture, produce sculptures, wood/skin textures and botany'];DATA['renderNote']='Blender Cycles previews of actual module geometry, not Unity renders.'
(OUT/'fresh-produce.json').write_text(json.dumps(DATA,indent=2)+'\n')
# Relative paths and packed shared images make the new source portable without modifying the original .blend.
for im in bpy.data.images:
 if im.source=='FILE':
  try:im.pack()
  except RuntimeError:pass
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'ArtSource/SipoFreshProduce.blend'),compress=True)
# Deterministic GUIDs; never replace an existing .meta.
for path in [OUT]+sorted(OUT.rglob('*')):
 if path.suffix=='.meta':continue
 meta=Path(str(path)+'.meta')
 if meta.exists():continue
 content='fileFormatVersion: 2\nguid: '+uuid.uuid5(uuid.NAMESPACE_URL,'Sipo/'+str(path.relative_to(ROOT))).hex+'\n'
 if path.is_dir():content+='folderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n'
 meta.write_text(content)
print('FRESH_PRODUCE_BUILD_COMPLETE '+json.dumps(DATA['statistics']),flush=True)
