"""Render the actual additive department source; never synthesize reference images.
blender -b ArtSource/SipoFreshProduce.blend -t 6 --python-exit-code 1 --python Tools/render_fresh_produce.py -- --views=hero,eye,elevated,detail --samples=48
"""
import bpy, numpy as np, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OIDN=os.environ.get('OIDN_BIN','/workspace/tools/oidn/oidn-2.5.1.x86_64.linux/bin/oidnDenoise')
VIEWS={'hero':('FreshProduce_Hero','01-hero'),'eye':('FreshProduce_EyeLevel','02-eye-level'),'elevated':('FreshProduce_Elevated','03-elevated'),'detail':('FreshProduce_Detail','04-detail')}
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
def option(name,default):return next((a.split('=',1)[1] for a in args if a.startswith('--'+name+'=')),default)
scene=bpy.context.scene;scene.render.resolution_percentage=int(option('percentage','100'));scene.cycles.samples=int(option('samples','48'));scene.cycles.use_denoising=False
raw=ROOT/'Artifacts/FreshProduceRenders';raw.mkdir(parents=True,exist_ok=True)
out=ROOT/'Docs/Previews/FreshProduce';out.mkdir(parents=True,exist_ok=True)
for key in option('views','hero,eye,elevated,detail').split(','):
 name,slug=VIEWS[key];scene.camera=bpy.data.objects[name]
 scene.render.image_settings.file_format='OPEN_EXR';scene.render.image_settings.color_depth='32';scene.render.filepath=str(raw/(slug+'.exr'))
 bpy.ops.render.render(write_still=True)
 source=bpy.data.images.load(scene.render.filepath,check_existing=False);w,h=source.size
 pixels=np.empty(w*h*4,dtype=np.float32);source.pixels.foreach_get(pixels)
 rgb=np.ascontiguousarray(pixels.reshape(h,w,4)[:,:,:3],dtype='<f4');pfm=raw/(slug+'.pfm');result=raw/(slug+'-denoised.pfm')
 with pfm.open('wb') as f:f.write(f'PF\n{w} {h}\n-1.0\n'.encode());f.write(rgb.tobytes())
 subprocess.run([OIDN,'--device','cpu','--hdr',str(pfm),'-o',str(result),'--quality','high','--threads','6'],check=True)
 with result.open('rb') as f:
  assert f.readline().strip()==b'PF';assert tuple(map(int,f.readline().split()))==(w,h);assert float(f.readline())<0
  rgb=np.frombuffer(f.read(),dtype='<f4').reshape(h,w,3)
 rgba=np.ones((h,w,4),dtype=np.float32);rgba[:,:,:3]=rgb
 im=bpy.data.images.new(slug,width=w,height=h,float_buffer=True);im.colorspace_settings.name='Linear Rec.709';im.pixels.foreach_set(rgba.ravel())
 scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_depth='8';im.save_render(str(out/(slug+'.png')),scene=scene)
 bpy.data.images.remove(source);bpy.data.images.remove(im);print('FRESH_PRODUCE_PREVIEW_SAVED '+str(out/(slug+'.png')),flush=True)
