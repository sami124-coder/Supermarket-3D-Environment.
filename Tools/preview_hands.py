"""Static first-person art pose: separate FBX; no rig, controls or gameplay."""
GROUP='Preview hands'
start=set(scene.objects)
for side in (-1,1):
    # Camera local coordinates: negative Z extends into the view.
    wrist=Vector((side*.43,-.34,-.66));palm=Vector((side*.37,-.23,-.91))
    rod('Orange sleeve',tuple(wrist+Vector((side*.18,-.23,.2))),wrist,.105,M['Orange'])
    rod('Ribbed sleeve cuff',wrist,wrist+Vector((-side*.018,.03,-.065)),.11,M['Cuff'])
    rod('Visible wrist',wrist,palm,.069,M['Skin'])
    uv('Relaxed hand palm',palm,(.115,.058,.15),M['Skin'],24,16)
    for i,length in enumerate((.17,.21,.19,.145)):
        x=palm.x+side*(-.077+i*.049)
        base=Vector((x,palm.y+.004,palm.z-.09))
        mid=base+Vector((-side*.012,.018,-length*.65));tip=mid+Vector((side*.007,-.015,-length*.35))
        rod('Finger proximal',base,mid,.023,M['Skin']);rod('Finger relaxed tip',mid,tip,.021,M['Skin'])
        for q in (base,mid,tip):uv('Finger rounded joint',q,(.023,.023,.025),M['Skin'],12,8)
    base=palm+Vector((-side*.08,-.012,.035));tip=base+Vector((-side*.075,.025,-.11))
    rod('Thumb',base,tip,.033,M['Skin']);uv('Thumb tip',tip,(.033,.03,.037),M['Skin'],16,8)
hand_objects=[o for o in scene.objects if o not in start]
for o in hand_objects:
    o.location.x+=.06 if o.location.x>0 else -.06
    o.location.y-=.10
    o.location.z-=.05
bpy.ops.object.select_all(action='DESELECT')
for o in hand_objects:o.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(OUT/'FirstPersonHands.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',add_leaf_bones=False)
cam=bpy.data.objects['12 First person'];bpy.context.view_layer.update()
for o in hand_objects:
    o.matrix_world=cam.matrix_world@o.matrix_world
    o['preview_hands']=True;o.hide_render=True
