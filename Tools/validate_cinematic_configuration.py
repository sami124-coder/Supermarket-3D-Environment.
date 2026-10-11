#!/usr/bin/env python3
"""Check serialized preset links and guarded fields against installed URP 17.3 source.

This does not launch Unity, import assets, execute Editor commands or verify an image.
"""
import argparse
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--editor', default='/workspace/tools/unity/6000.3.26f1/Editor')
    args = parser.parse_args()
    urp = Path(args.editor) / 'Data/Resources/PackageManager/BuiltInPackages/com.unity.render-pipelines.universal'
    assert json.loads((urp / 'package.json').read_text())['version'] == '17.3.0'
    assert '6000.3.26f1' in (ROOT / 'ProjectSettings/ProjectVersion.txt').read_text()
    assert json.loads((ROOT / 'Packages/manifest.json').read_text())['dependencies']['com.unity.render-pipelines.universal'] == '17.3.0'

    asset = (ROOT / 'Assets/Settings/SipoCinematicLightingSettings.asset').read_text()
    settings_source = (ROOT / 'Assets/Editor/SipoCinematicLightingSettings.cs').read_text()
    def guid(path):
        return re.search(r'^guid: ([a-f0-9]{32})$', (ROOT / (path + '.meta')).read_text(), re.M)[1]
    assert f'guid: {guid("Assets/Editor/SipoCinematicLightingSettings.cs")}' in asset
    assert f'guid: {guid("Assets/Settings/SipoCinematicLighting.json")}' in asset
    assert 'SipoCinematicLighting.ReadLayout(this)' in settings_source
    scalars = {name: float(value) for name, value in re.findall(r'^\s+(\w+): (-?\d+(?:\.\d+)?)$', asset, re.M)}
    ranges = {
        'lightIntensityMultiplier': (0, 4), 'aoIntensity': (0, 1), 'aoRadius': (.05, 2),
        'shadowDistance': (1, 200), 'ambientIntensity': (0, 4), 'reflectionIntensity': (0, 4),
        'postExposure': (-5, 5), 'bloomIntensity': (0, 2), 'bloomThreshold': (0, 8),
        'bloomScatter': (0, 1), 'contrast': (-100, 100), 'saturation': (-100, 100),
        'temperature': (-100, 100), 'tint': (-100, 100), 'vignetteIntensity': (0, .5),
        'warmEmissionMultiplier': (0, 3), 'blueEmissionMultiplier': (0, 3),
        'ceilingEmissionMultiplier': (0, 3), 'signEmissionCeiling': (.1, 4),
    }
    for name in ('floorSmoothness', 'chromeSmoothness', 'goldSmoothness', 'chromeMetallic',
                 'goldMetallic', 'blueSmoothness', 'orangeSmoothness', 'glassSmoothness'):
        ranges[name] = (0, 1)
    for name, (low, high) in ranges.items():
        assert name in scalars and math.isfinite(scalars[name]) and low <= scalars[name] <= high, name
    assert scalars['msaaSamples'] in (1, 2, 4, 8)
    assert scalars['shadowAtlasResolution'] in (512, 1024, 2048, 4096)
    assert scalars['tonemapping'] in (0, 1, 2)
    assert all(scalars[name] in (0, 1) for name in ('enableAmbientOcclusion', 'replaceGeneratedLighting', 'polishSurfaces'))

    # Serialized fields are not checked by the C# compiler. Confirm each guarded
    # property name exists in the installed package source for this exact version.
    helper = (ROOT / 'Assets/Editor/SipoCinematicPipeline.cs').read_text()
    pipeline = (urp / 'Runtime/Data/UniversalRenderPipelineAsset.cs').read_text()
    ao = (urp / 'Runtime/RendererFeatures/ScreenSpaceAmbientOcclusion.cs').read_text()
    renderer = (urp / 'Runtime/ScriptableRendererData.cs').read_text()
    fields = sorted(set(re.findall(r'"(m_\w+(?:\.\w+)?)"', helper)))
    for field in fields:
        if field.startswith('m_Settings.'):
            assert re.search(r'\binternal\s+\w+\s+' + field.split('.')[1] + r'\b', ao), field
        else:
            assert re.search(r'\b' + field + r'\b', pipeline + renderer), field
    # Reject preset/asset GUID collisions before Unity imports the new files.
    owners = {}
    for meta in (ROOT / 'Assets').rglob('*.meta'):
        match = re.search(r'^guid: (\w+)$', meta.read_text(), re.M)
        assert match, f'Missing GUID: {meta}'
        value = match[1]
        assert value not in owners, f'Duplicate GUID: {meta} and {owners.get(value)}'
        owners[value] = str(meta.relative_to(ROOT))
    for directory in ('Assets/Editor', 'Assets/Scripts/Rendering', 'Assets/Settings'):
        for path in (ROOT / directory).glob('*'):
            if path.is_file() and path.suffix != '.meta':
                assert Path(str(path) + '.meta').is_file(), f'Missing meta: {path}'
    print('SIPO_CINEMATIC_ASSET_CONFIGURATION_PASSED')
    print(json.dumps({'serializedPresetLinks': 2, 'boundedPresetScalars': len(ranges),
                      'guardedUrpFields': len(fields), 'uniqueAssetGuids': len(owners),
                      'unityImportExecuted': False, 'nativeRenderedAppearanceVerified': False}, indent=2))


if __name__ == '__main__':
    main()
