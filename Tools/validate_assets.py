"""Check retained asset provenance, generated exports and physically safe tour positions."""
import hashlib,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for manifest in (root/'Assets/ThirdParty').glob('*/manifest.json'):
    assert (manifest.parent/'LICENSE.txt').is_file(),manifest
    for asset in json.loads(manifest.read_text()):
        p=root/asset['source'];assert p.is_file(),p
        assert hashlib.sha256(p.read_bytes()).hexdigest()==asset['sha256'],p
        assert (root/asset['fbx']).is_file(),asset['fbx']
data=json.loads((root/'Assets/Environment/scene-data.json').read_text())
assert data['schemaVersion']==1
assert data['statistics']['reusedAssetTypes']>=12
assert data['statistics']['staticMeshes']>=30
assert (root/'Assets/Environment/SipoSupermarket.fbx').stat().st_size>100000
assert (root/'ArtSource/SipoSupermarket.blend').stat().st_size>100000
def contains_xz(p,c,margin=0):
    return all(abs(p[i]-c['position'][i])<c['size'][i]/2+margin for i in (0,2))
for v in [data['spawn']]+data['viewpoints']:
    p=v['position'];assert all(math.isfinite(x) for x in p)
    support=[c for c in data['colliders'] if contains_xz(p,c) and -.02<p[1]-(c['position'][1]+c['size'][1]/2)<.35]
    assert support,('No floor under viewpoint',v)
    obstacles=[c for c in data['colliders'] if contains_xz(p,c,.28)
               and c['position'][1]-c['size'][1]/2<p[1]+1.8
               and c['position'][1]+c['size'][1]/2>p[1]+.05]
    assert not obstacles,('Viewpoint intersects obstacle',v,obstacles)
print('ASSET_VALIDATION_PASSED: source hashes, licenses, FBX exports and all tour positions.')
print(json.dumps(data['statistics'],indent=2))
