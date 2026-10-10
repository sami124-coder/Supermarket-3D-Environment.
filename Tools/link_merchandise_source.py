"""Keep the full editable scene portable in two Blender files below 100 MiB."""
source=ROOT/'ArtSource';source.mkdir(exist_ok=True)
objects=ENV_PARTS['SipoMerchandise.fbx']
library_path=source/'SipoMerchandiseLibrary.blend'
bpy.data.libraries.write(str(library_path),set(objects),fake_user=False,compress=True)
names=[o.name for o in objects]
bpy.data.batch_remove(ids=objects)
# Remove unused consolidated meshes so they cannot bloat the main scene file.
for mesh in list(bpy.data.meshes):
    if mesh.users==0:bpy.data.meshes.remove(mesh)
with bpy.data.libraries.load(str(library_path),link=True) as (available,loaded):
    loaded.objects=names
for obj in loaded.objects:
    bpy.context.collection.objects.link(obj)
    obj.library.filepath='//SipoMerchandiseLibrary.blend'
assert library_path.stat().st_size<99*1024*1024
print('Editable merchandise library:',library_path.stat().st_size,'bytes',flush=True)
