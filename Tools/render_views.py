"""Render source cameras with Cycles and verified Open Image Denoise.

blender -b ArtSource/SipoSupermarket.blend -t 5 --python-exit-code 1 \
  --python Tools/render_views.py -- --views=hero,gallery,entrance

Run Tools/install_render_tools.sh once if the OIDN executable is not installed.
"""
import bpy, numpy as np, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OIDN=os.environ.get('OIDN_BIN','/workspace/tools/oidn/oidn-2.5.1.x86_64.linux/bin/oidnDenoise')
VIEWS={'hero':('01 Grand atrium','01-grand-atrium'),
       'produce':('02 Fresh garden','02-fresh-garden'),
       'gallery':('03 Mezzanine','03-mezzanine'),
       'entrance':('04 Grand entrance','04-grand-entrance')}

def render_view(key,samples=32,percentage=100):
    name,slug=VIEWS[key];scene=bpy.context.scene
    scene.camera=bpy.data.objects[name];scene.cycles.samples=samples;scene.cycles.use_denoising=False
    scene.render.resolution_percentage=percentage
    scene.view_settings.exposure=-1.7
    raw=ROOT/'Artifacts/Renders';raw.mkdir(parents=True,exist_ok=True)
    scene.render.image_settings.file_format='OPEN_EXR';scene.render.image_settings.color_depth='32'
    scene.render.filepath=str(raw/(slug+'.exr'))
    bpy.ops.render.render(write_still=True)
    source=bpy.data.images.load(scene.render.filepath,check_existing=False)
    width,height=source.size;pixels=np.empty(width*height*4,dtype=np.float32);source.pixels.foreach_get(pixels)
    rgb=np.ascontiguousarray(pixels.reshape(height,width,4)[:,:,:3],dtype='<f4')
    pfm=raw/(slug+'.pfm');denoised=raw/(slug+'-denoised.pfm')
    with pfm.open('wb') as f:
        f.write(f'PF\n{width} {height}\n-1.0\n'.encode());f.write(rgb.tobytes())
    subprocess.run([OIDN,'--device','cpu','--hdr',str(pfm),'-o',str(denoised),'--quality','high','--threads','5'],check=True)
    with denoised.open('rb') as f:
        assert f.readline().strip()==b'PF'
        w,h=map(int,f.readline().split());assert (w,h)==(width,height)
        assert float(f.readline())<0
        data=np.frombuffer(f.read(),dtype='<f4').reshape(height,width,3)
    rgba=np.ones((height,width,4),dtype=np.float32);rgba[:,:,:3]=data
    image=bpy.data.images.new('Denoised '+slug,width=width,height=height,float_buffer=True)
    image.colorspace_settings.name='Linear Rec.709';image.pixels.foreach_set(rgba.ravel())
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_depth='8'
    target=ROOT/'Docs/Previews'/(slug+'.png');target.parent.mkdir(parents=True,exist_ok=True)
    image.save_render(str(target),scene=scene)
    bpy.data.images.remove(source);bpy.data.images.remove(image)
    print('SIPO_PREVIEW_SAVED '+str(target),flush=True)

if __name__=='__main__':
    views=next((arg.split('=',1)[1] for arg in sys.argv if arg.startswith('--views=')),'hero,gallery,entrance')
    samples=int(next((arg.split('=',1)[1] for arg in sys.argv if arg.startswith('--samples=')),'32'))
    percentage=int(next((arg.split('=',1)[1] for arg in sys.argv if arg.startswith('--percentage=')),'100'))
    for key in views.split(','):render_view(key,samples,percentage)
