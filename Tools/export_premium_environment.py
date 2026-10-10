"""Export the dense static scene in two native FBX parts below GitHub's file limit."""
import uuid
merch_groups={'Licensed groceries','Boutique stocked shelving','Garden harvest boutique','Premium patisserie merchandising','Candy boutique abundance','Rainbow drinks boutique','Frost boutique merchandising'}
ENV_PARTS={ 'SipoSupermarket.fbx':[], 'SipoMerchandise.fbx':[] }
for obj in scene.objects:
    if obj.type!='MESH':continue
    group=obj.name.split(' [')[0]
    target='SipoMerchandise.fbx' if group in merch_groups else 'SipoSupermarket.fbx'
    ENV_PARTS[target].append(obj)
anchors=[o for o in scene.objects if o.name.startswith('Anchor_')]
DATA['modelParts']=[]
DATA['modelPartStatistics']=[]
for filename,objects in ENV_PARTS.items():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects+anchors:obj.select_set(True)
    path=OUT/filename
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_space_transform=False,mesh_smooth_type='FACE',use_mesh_modifiers=True,add_leaf_bones=False,path_mode='AUTO')
    assert path.stat().st_size<99*1024*1024,('FBX exceeds GitHub limit',filename)
    DATA['modelParts'].append(str(path.relative_to(ROOT)))
    DATA['modelPartStatistics'].append({'file':filename,'meshes':len(objects),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects),'bytes':path.stat().st_size})
    meta=Path(str(path)+'.meta')
    if not meta.exists():meta.write_text('fileFormatVersion: 2\nguid: '+uuid.uuid5(uuid.NAMESPACE_URL,'Sipo/'+str(path.relative_to(ROOT))).hex+'\n')
(OUT/'scene-data.json').write_text(json.dumps(DATA,indent=2)+'\n')
