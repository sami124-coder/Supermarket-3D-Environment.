"""Audit delivered Blender geometry, FBX source material slots and circulation.
Run with Blender: blender -b -t 3 --python-exit-code 1 --python Tools/validate_fresh_produce.py
Native Unity command execution and rendered URP appearance require local validation.
"""
import bpy, json, math, hashlib
from collections import deque
from pathlib import Path
from mathutils import Vector
from io_scene_fbx import parse_fbx
ROOT=Path(__file__).resolve().parents[1]
spec=json.loads((ROOT/'Assets/FreshProduce/fresh-produce.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'ArtSource/SipoFreshProduce.blend'))
scene=bpy.context.scene
library=set(o for o in scene.objects if any(c.name.startswith('Reusable source') for c in o.users_collection))
meshes=[o for o in scene.objects if o.type=='MESH' and o not in library]
known={m['name'] for m in spec['materials']}
assert len(known)==len(spec['materials'])
assert len(spec['lights'])==7 and sum(l['shadow'] for l in spec['lights'])==1
assert len(spec['reflections'])==2
assert len(spec['libraryItems'])>=20
mesh_by_name={o.name:o for o in meshes}
for lod in spec['lodGroups']:
 assert all(name in mesh_by_name for name in lod['lod0']+lod['lod1']),lod['name']
 high=sum(sum(len(f.vertices)-2 for f in mesh_by_name[n].data.polygons) for n in lod['lod0'])
 low=sum(sum(len(f.vertices)-2 for f in mesh_by_name[n].data.polygons) for n in lod['lod1'])
 assert 0<low<high,lod['name']
center=spec['bounds']['center'];size=spec['bounds']['size']
for o in meshes:
 assert len(o.data.vertices)>0 and len(o.data.polygons)>0,o.name
 for corner in o.bound_box:
  v=o.matrix_world@Vector(corner);u=(v.x,v.z,-v.y)
  assert all(math.isfinite(a) and abs(a-c)<=s/2+.1 for a,c,s in zip(u,center,size)),(o.name,'outside advertised placement bounds',u)
 assert all(m and m.name in known for m in o.data.materials),o.name
for m in spec['materials']:
 assert len(m['color'])==3 and all(0<=c<=1 for c in m['color']),m['name']
 assert 0<=m['roughness']<=1 and 0<=m['metallic']<=1,m['name']
 for key in ('baseMap','normalMap','metallicGlossMap'):
  if m.get(key):assert (ROOT/m[key]).is_file(),m[key]
parts=[];mapping_parts=[]
for rel in spec['modelParts']+[spec['libraryModel']]:
 tree,version=parse_fbx.parse(str(ROOT/rel));objects=next(e for e in tree.elems if e.id==b'Objects');connections=next(e for e in tree.elems if e.id==b'Connections')
 def name(e):return e.props[1].split(b'\x00\x01')[0].decode('utf8')
 mats={e.props[0]:name(e) for e in objects.elems if e.id==b'Material'}
 renderers={e.props[0]:[] for e in objects.elems if e.id==b'Model' and e.props[2]==b'Mesh'}
 renderer_names={e.props[0]:name(e) for e in objects.elems if e.id==b'Model' and e.props[2]==b'Mesh'}
 for c in connections.elems:
  if c.props[0]==b'OO' and c.props[1] in mats and c.props[2] in renderers:renderers[c.props[2]].append(mats[c.props[1]])
 assert renderers and all(renderers.values()),rel
 assert all(n in known for names in renderers.values() for n in names),rel
 # Same strict known-prefix contract used by the production C# remapper.
 prefix=Path(rel).stem+'-'
 assert all((prefix+n)[len(prefix):] in known for n in mats.values())
 assert (ROOT/rel).stat().st_size<99*1024*1024
 parts.append({'file':rel,'renderers':len(renderers),'materialSlots':sum(map(len,renderers.values())),'sourceMaterials':len(mats),'sha256':hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()})
 mapping_parts.append({'file':rel,'sourceNames':sorted(mats.values()),'renderers':[{'name':renderer_names[key],'slots':slots} for key,slots in renderers.items()]})
# Ground-level human capsule footprint on a 0.25m navigation audit grid, not a gameplay navmesh.
# Exclude floor itself and geometry entirely above a standing person's head.
obstacles=[c for c in spec['colliders'] if c['name']!='Walkable department floor' and c['position'][1]-c['size'][1]/2<1.85]
def blocked(x,z):
 for c in obstacles:
  a=math.radians(c['rotation'][1]);dx=x-c['position'][0];dz=z-c['position'][2]
  u=math.cos(a)*dx-math.sin(a)*dz;v=math.sin(a)*dx+math.cos(a)*dz
  if abs(u)<c['size'][0]/2+.3 and abs(v)<c['size'][2]/2+.3:return True
 return False
start=(0,46);seen={start};todo=deque([start])
while todo:
 a,b=todo.popleft()
 for da,db in ((1,0),(-1,0),(0,1),(0,-1)):
  p=(a+da,b+db)
  if p in seen or max(abs(p[0]),abs(p[1]))>49 or blocked(p[0]/4,p[1]/4):continue
  seen.add(p);todo.append(p)
landmarks=[(0,46),(-27,0),(27,0),(0,-30),(-36,40),(36,40)]
assert all(p in seen for p in landmarks),'Walking route is blocked'
report={'status':'passed','statistics':spec['statistics'],'fbxParts':parts,'safeWalkingLandmarks':len(landmarks),'collisionGridSpacingMetres':.25,'testedCapsuleRadiusMetres':.3,'boundsContainAllModuleMeshes':True,'nativeUnityImportExecuted':False,'nativeUnityRenderingVerified':False}
(ROOT/'Docs/FRESH_PRODUCE_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
inventory=ROOT/'Artifacts/FreshProduceValidation/fbx-materials.json';inventory.parent.mkdir(parents=True,exist_ok=True)
inventory.write_text(json.dumps({'materialNames':sorted(known),'parts':mapping_parts},indent=2)+'\n')
print('FRESH_PRODUCE_ASSETS_VALIDATED '+json.dumps(report),flush=True)
