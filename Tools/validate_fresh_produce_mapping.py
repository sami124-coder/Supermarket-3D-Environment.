"""Execute the unchanged production C# material-name policy on both new FBXs.

Also audits the Blender/FBX assets and runs the existing supermarket material
regression. This does not execute native Unity import or GPU rendering.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--editor', default='/workspace/tools/unity/6000.3.26f1/Editor')
args = parser.parse_args()
subprocess.run(['blender', '-b', '-t', '2', '--python-exit-code', '1', '--python',
                str(ROOT / 'Tools/validate_fresh_produce.py')], cwd=ROOT, check=True)
# This compiles the real SupermarketMaterialNames class from SupermarketProject.cs
# with the existing regression harness, and checks the original two FBXs too.
subprocess.run([sys.executable, str(ROOT / 'Tools/validate_material_mapping.py'),
                '--editor', args.editor], cwd=ROOT, check=True)
run = subprocess.run([
    str(Path(args.editor) / 'Data/NetCoreRuntime/dotnet'),
    str(ROOT / 'Artifacts/MaterialMapping/MappingRegression.dll'),
    str(ROOT / 'Artifacts/FreshProduceValidation/fbx-materials.json')],
    cwd=ROOT, capture_output=True, text=True, check=True)
report_path = ROOT / 'Docs/FRESH_PRODUCE_VALIDATION.json'
report = json.loads(report_path.read_text())
report['productionMaterialMappingRegression'] = json.loads(run.stdout)
report['originalSupermarketMappingRegression'] = json.loads(
    (ROOT / 'Artifacts/MaterialMapping/report.json').read_text())
report_path.write_text(json.dumps(report, indent=2) + '\n')
print('FRESH_PRODUCE_MAPPING_VALIDATED ' + run.stdout.strip())
