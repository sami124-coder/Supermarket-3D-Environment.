"""Fully decode every required PNG and record hashes against the current source scene."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageStat
ROOT=Path(__file__).resolve().parents[1]
NAMES=['01-grand-atrium','02-fresh-garden','03-mezzanine','05-bakery','06-snacks','07-drinks','08-frozen','12-first-person','13-mascot-detail']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
images=[]
for name in NAMES:
    p=ROOT/'Docs/Previews'/(name+'.png')
    assert p.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n',p
    with Image.open(p) as im:assert im.format=='PNG';im.verify()
    with Image.open(p) as im:
        im.load();assert im.width>=1280 and im.height>=800,(p,im.size)
        assert max(ImageStat.Stat(im.convert('RGB')).stddev)>10,('Blank image',p)
        alpha=im.convert('RGBA').getchannel('A').getextrema();assert alpha==(255,255),(p,alpha)
        images.append(dict(file=p.name,format='PNG',width=im.width,height=im.height,mode=im.mode,alphaRange=list(alpha),bytes=p.stat().st_size,sha256=digest(p),fullyDecoded=True))
manifest=dict(schemaVersion=1,sourceScene='ArtSource/SipoSupermarket.blend',sourceSceneSha256=digest(ROOT/'ArtSource/SipoSupermarket.blend'),linkedLibrary='ArtSource/SipoMerchandiseLibrary.blend',linkedLibrarySha256=digest(ROOT/'ArtSource/SipoMerchandiseLibrary.blend'),renderer='Blender Cycles, 32 samples, HDR Open Image Denoise; not Unity captures',images=images)
(ROOT/'Docs/Previews/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for archived in (ROOT/'Docs/Previews/Archive').glob('*.png'):
    with Image.open(archived) as im:assert im.format=='PNG';im.verify()
    with Image.open(archived) as im:im.load()
print('PREVIEW_VALIDATION_PASSED: all 9 current PNGs fully decode, opaque, nonblank, at least 1280x800.')
