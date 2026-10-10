"""Independent readback of every FBX part, coordinate markers, materials and UVs."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
spec=json.loads((root/'Assets/Environment/scene-data.json').read_text())
parts=spec.get('modelParts',['Assets/Environment/SipoSupermarket.fbx'])
all_bounds=[];mesh_count=0;reports=[]
names={m['name'] for m in spec['materials']}
floor_names={m['name'] for m in spec['materials'] if m.get('normalMap')}
for path in parts:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(root/path))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    mesh_count+=len(meshes)
    points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    all_bounds.extend(points)
    for name,p in [('Origin',(0,0,0)),('Right',(1,0,0)),('Back',(0,-1,0)),('Up',(0,0,1))]:
        obj=bpy.data.objects.get('Anchor_'+name)
        assert obj and (obj.matrix_world.translation-Vector(p)).length<.001,(name,obj)
    missing=sorted({m.name for o in meshes for m in o.data.materials if m and m.name not in names})
    assert not missing,('Unmapped imported materials',path,missing)
    for o in meshes:
        if any(m and m.name in floor_names for m in o.data.materials):assert o.data.uv_layers,('Floor UVs missing',o.name)
    reports.append({'file':path,'meshes':len(meshes),'bytes':(root/path).stat().st_size})
assert mesh_count==spec['statistics']['staticMeshes'],mesh_count
minimum=[min(p[i] for p in all_bounds) for i in range(3)]
maximum=[max(p[i] for p in all_bounds) for i in range(3)]
assert all(math.isfinite(v) for v in minimum+maximum)
assert 68<maximum[0]-minimum[0]<72
assert 75<maximum[1]-minimum[1]<81
assert 16<maximum[2]-minimum[2]<18
report={'result':'passed','meshCount':mesh_count,'parts':reports,'boundsBlenderMetres':{'min':minimum,'max':maximum},'coordinateAnchors':'passed','materialMapping':'passed','floorUVs':'passed'}
out=root/'Artifacts/Validation';out.mkdir(parents=True,exist_ok=True)
(out/'fbx-readback.json').write_text(json.dumps(report,indent=2)+'\n')
print('FBX_READBACK_PASSED '+json.dumps(report),flush=True)
