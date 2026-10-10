"""Execute the production C# mapping policy against actual FBX material slots.

Requires Blender and the official Unity 6000.3.26f1 compiler/runtime installed
at --editor. Does not require activation; does not simulate a Unity import.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Artifacts/MaterialMapping'


def extract_fbx():
    from io_scene_fbx import parse_fbx
    spec = json.loads((ROOT / 'Assets/Environment/scene-data.json').read_text())
    result = {'materialNames': [m['name'] for m in spec['materials']], 'parts': []}
    for path in spec['modelParts']:
        tree, version = parse_fbx.parse(str(ROOT / path))
        objects = next(e for e in tree.elems if e.id == b'Objects')
        connections = next(e for e in tree.elems if e.id == b'Connections')
        def name(element):
            return element.props[1].split(b'\x00\x01')[0].decode('utf-8')
        materials = {e.props[0]: name(e) for e in objects.elems if e.id == b'Material'}
        renderers = {e.props[0]: {'name': name(e), 'slots': []} for e in objects.elems
                     if e.id == b'Model' and e.props[2] == b'Mesh'}
        for connection in connections.elems:
            kind, child, parent = connection.props[:3]
            if kind == b'OO' and child in materials and parent in renderers:
                renderers[parent]['slots'].append(materials[child])
        assert materials and renderers, path
        assert all(r['slots'] for r in renderers.values()), (path, 'empty material slots')
        result['parts'].append({'file': path, 'fbxVersion': version,
                                'sha256': hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                                'sourceNames': sorted(materials.values()),
                                'renderers': list(renderers.values())})
    assert sum(len(p['renderers']) for p in result['parts']) == spec['statistics']['staticMeshes']
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'fbx-materials.json').write_text(json.dumps(result, indent=2) + '\n')
    print('FBX_MATERIAL_SLOTS_EXTRACTED', flush=True)


HARNESS = r'''
class MappingRegression
{
    static int assertions;
    static void Check(bool value,string message)
    { assertions++; if(!value)throw new Exception(message); }
    static void Reject(Action action,string message)
    {
        assertions++;
        try { action(); } catch(InvalidDataException) { return; }
        throw new Exception("Expected rejection: "+message);
    }
    static void Main(string[] args)
    {
        using var input=System.Text.Json.JsonDocument.Parse(File.ReadAllText(args[0]));
        var data=input.RootElement;
        var known=data.GetProperty("materialNames").EnumerateArray().Select(n=>n.GetString()).ToArray();
        var parts=data.GetProperty("parts").EnumerateArray().ToArray();
        var paths=parts.Select(p=>p.GetProperty("file").GetString()).ToArray();
        var policy=new Sipo.Editor.SupermarketMaterialNames(known,paths);
        int slots=0, renderers=0, sourceNames=0;
        foreach(var part in parts)
        {
            foreach(var source in part.GetProperty("sourceNames").EnumerateArray())
            {
                string name=source.GetString(); sourceNames++;
                Check(policy.Resolve(name)==name,"Source identifier: "+name);
            }
            foreach(var renderer in part.GetProperty("renderers").EnumerateArray())
            {
                renderers++;
                foreach(var slot in renderer.GetProperty("slots").EnumerateArray())
                {
                    string name=slot.GetString(); slots++;
                    Check(policy.Resolve(name)==name,"Raw slot: "+name);
                    foreach(string path in paths)
                    {
                        string display=Path.GetFileNameWithoutExtension(path)+"-"+name;
                        Check(policy.Resolve(display)==name,"Prefixed slot: "+display);
                        Check(policy.Resolve(policy.Resolve(display))==name,"Repeated resolution: "+display);
                    }
                    Sipo.Editor.SupermarketMaterialNames.RequireSlot(name,Sipo.Editor.SupermarketMaterialNames.ShaderName,true);
                    assertions++;
                }
            }
        }
        foreach(string name in new[]{null,"","Unknown-SIPO_Chrome","SipoSupermarket-NOT_IN_THE_SPEC","SIPO_Chrome (Instance)"})
            Reject(()=>policy.Resolve(name),"unmapped name "+name);
        var suffix=new Sipo.Editor.SupermarketMaterialNames(new[]{"brown","brown.001","Part-brown"},new[]{"Part.fbx"});
        Check(suffix.Resolve("Part-brown.001")=="brown.001","Numeric suffix must survive");
        Check(suffix.Resolve("Part-brown")=="Part-brown","Exact match precedes prefix removal");
        foreach(string shader in new[]{null,"Standard","Standard (Specular setup)","Hidden/InternalErrorShader","Universal Render Pipeline/Simple Lit"})
            Reject(()=>Sipo.Editor.SupermarketMaterialNames.RequireSlot("bad shader",shader,true),shader);
        Reject(()=>Sipo.Editor.SupermarketMaterialNames.RequireSlot("wrong or null asset",Sipo.Editor.SupermarketMaterialNames.ShaderName,false),"wrong asset");
        Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(new{result="passed",assertions,renderers,slots,sourceNames,modelParts=parts.Length,unityImportExecuted=false}));
    }
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--editor', default='/workspace/tools/unity/6000.3.26f1/Editor')
    args = parser.parse_args()
    subprocess.run(['blender', '-b', '-t', '2', '--python-exit-code', '1', '--python',
                    str(Path(__file__).resolve()), '--', '--extract-fbx'], cwd=ROOT, check=True)
    source_path = ROOT / 'Assets/Editor/SupermarketProject.cs'
    source = source_path.read_text()
    start = source.index('    internal sealed class SupermarketMaterialNames')
    end = source.index('    /// <summary>Assembles', start)
    # Compile the actual production implementation, never a Python translation.
    program = 'using System; using System.IO; using System.Linq; using System.Collections.Generic;\n'
    program += 'namespace Sipo.Editor {\n' + source[start:end] + '\n}\n' + HARNESS
    code = OUT / 'MappingRegression.cs'
    code.write_text(program)
    data = Path(args.editor) / 'Data'
    dotnet = data / 'NetCoreRuntime/dotnet'
    runtimes = list((data / 'NetCoreRuntime/shared/Microsoft.NETCore.App').iterdir())
    runtime = max(runtimes, key=lambda p: tuple(map(int, p.name.split('.'))))
    dll = OUT / 'MappingRegression.dll'
    options = ['-nologo', '-nostdlib+', '-target:exe', '-langversion:9.0', '-out:' + str(dll)]
    options += ['-r:' + str(p) for p in sorted(runtime.glob('*.dll'))] + [str(code)]
    response = OUT / 'compile.rsp'
    response.write_text('\n'.join('"' + option + '"' for option in options))
    subprocess.run([str(dotnet), str(data / 'DotNetSdkRoslyn/csc.dll'), '@' + str(response)], check=True)
    dll.with_suffix('.runtimeconfig.json').write_text(json.dumps({'runtimeOptions': {
        'tfm': 'net' + '.'.join(runtime.name.split('.')[:2]),
        'framework': {'name': 'Microsoft.NETCore.App', 'version': runtime.name}}}))
    run = subprocess.run([str(dotnet), str(dll), str(OUT / 'fbx-materials.json')],
                         check=True, capture_output=True, text=True)
    report = json.loads(run.stdout)
    inventory = json.loads((OUT / 'fbx-materials.json').read_text())
    report['editorSourceSha256'] = hashlib.sha256(source_path.read_bytes()).hexdigest()
    report['parts'] = [{'file': p['file'], 'sha256': p['sha256'],
                        'renderers': len(p['renderers']), 'slots': sum(len(r['slots']) for r in p['renderers'])}
                       for p in inventory['parts']]
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('MATERIAL_MAPPING_REGRESSION_PASSED ' + json.dumps(report), flush=True)


if __name__ == '__main__':
    if '--extract-fbx' in sys.argv:
        extract_fbx()
    else:
        main()
