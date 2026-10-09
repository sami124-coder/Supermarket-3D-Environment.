"""Independent Blender FBX readback; run with --background --python-exit-code 1."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(root/'Assets/Environment/SipoSupermarket.fbx'))
spec=json.loads((root/'Assets/Environment/scene-data.json').read_text())
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(meshes)==spec['statistics']['staticMeshes'],len(meshes)
points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
minimum=[min(p[i] for p in points) for i in range(3)];maximum=[max(p[i] for p in points) for i in range(3)]
assert all(math.isfinite(v) for v in minimum+maximum)
assert 48<maximum[0]-minimum[0]<51
assert 50<maximum[1]-minimum[1]<60
assert 12<maximum[2]-minimum[2]<15
for name,p in [('Origin',(0,0,0)),('Right',(1,0,0)),('Back',(0,-1,0)),('Up',(0,0,1))]:
    obj=bpy.data.objects.get('Anchor_'+name)
    assert obj and (obj.matrix_world.translation-Vector(p)).length<.001,(name,obj)
names={m['name'] for m in spec['materials']}
missing=sorted({m.name for o in meshes for m in o.data.materials if m and m.name not in names})
assert not missing,('Unmapped imported materials',missing)
report={'result':'passed','meshCount':len(meshes),'boundsBlenderMetres':{'min':minimum,'max':maximum},'coordinateAnchors':'passed','materialMapping':'passed'}
out=root/'Artifacts/Validation';out.mkdir(parents=True,exist_ok=True)
(out/'fbx-readback.json').write_text(json.dumps(report,indent=2)+'\n')
print('FBX_READBACK_PASSED '+json.dumps(report),flush=True)
