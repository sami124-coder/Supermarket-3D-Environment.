"""Compile project C# against an installed editor's real assemblies, without launching it.

This catches C# and API errors; it does NOT validate Unity import, shaders or Play mode.
"""
import argparse, pathlib, subprocess, sys
p=argparse.ArgumentParser();p.add_argument('--editor',default='/workspace/tools/unity/6000.3.26f1/Editor')
a=p.parse_args();editor=pathlib.Path(a.editor);root=pathlib.Path(__file__).resolve().parents[1]
data=editor/'Data';out=root/'Artifacts/Compilation';out.mkdir(parents=True,exist_ok=True)
refs=[data/'NetStandard/ref/2.1.0/netstandard.dll',data/'Managed/UnityEditor.dll']
refs+=list((data/'Managed/UnityEngine').glob('*.dll'))
cache=data/'Resources/PackageManager/ProjectTemplates/libcache'
templates=sorted(cache.glob('com.unity.template.3d-cross-platform-*/ScriptAssemblies'))
if not templates:raise SystemExit('Installed editor has no bundled URP template assemblies.')
refs+=list(templates[-1].glob('*.dll'))
unique={x.name:x for x in refs}
args=['-nologo','-nostdlib+','-target:library','-langversion:9.0','-define:UNITY_EDITOR,UNITY_6000_3_OR_NEWER',f'-out:{out}/Sipo.SourceCheck.dll']
args += ['-r:'+str(x) for x in unique.values()]
args += [str(x) for x in sorted((root/'Assets').rglob('*.cs'))]
rsp=out/'compile.rsp';rsp.write_text('\n'.join('"'+x+'"' for x in args)+'\n')
result=subprocess.run([str(data/'NetCoreRuntime/dotnet'),str(data/'DotNetSdkRoslyn/csc.dll'),'@'+str(rsp)],capture_output=True,text=True)
(out/'compiler.log').write_text(result.stdout+result.stderr)
print(result.stdout+result.stderr,end='')
print('C# source compilation '+('PASSED' if result.returncode==0 else 'FAILED'))
sys.exit(result.returncode)
