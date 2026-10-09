"""Convert the retained CC0 source models to Unity-native FBX, without altering originals."""
import bpy, json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
for pack in ('KenneyFoodKit','KenneyFurnitureKit'):
    path=root/'Assets/ThirdParty'/pack/'manifest.json'
    manifest=json.loads(path.read_text())
    for item in manifest:
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        for m in list(bpy.data.materials):bpy.data.materials.remove(m)
        source=root/item['source'];target=root/item['fbx'];target.parent.mkdir(parents=True,exist_ok=True)
        if source.suffix=='.glb':bpy.ops.import_scene.gltf(filepath=str(source))
        else:bpy.ops.wm.obj_import(filepath=str(source),forward_axis='NEGATIVE_Z',up_axis='Y')
        meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
        for m in bpy.data.materials:
            if m.use_nodes:
                p=m.node_tree.nodes.get('Principled BSDF')
                if p:p.inputs['Metallic'].default_value=0;p.inputs['Roughness'].default_value=.42
        pts=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
        item['dimensionsMetres']=[round(max(v[i] for v in pts)-min(v[i] for v in pts),4) for i in range(3)]
        item['materials']=[m.name for m in bpy.data.materials]
        bpy.ops.export_scene.fbx(filepath=str(target),object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',add_leaf_bones=False)
    path.write_text(json.dumps(manifest,indent=2)+'\n')
print('CC0_CONVERSION_COMPLETE',flush=True)
