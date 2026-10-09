#!/usr/bin/env bash
set -euo pipefail
target=/workspace/tools/oidn/oidn-2.5.1.x86_64.linux
if test -x "$target/bin/oidnDenoise"; then exit 0; fi
mkdir -p /workspace/tools/downloads /workspace/tools/oidn
archive=/workspace/tools/downloads/oidn-2.5.1.x86_64.linux.tar.gz
curl --fail --location --proto '=https' --tlsv1.2 \
  https://github.com/RenderKit/oidn/releases/download/v2.5.1/oidn-2.5.1.x86_64.linux.tar.gz -o "$archive"
python3 - "$archive" <<'PY'
import hashlib,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1])
# SHA-256 published on the official RenderKit/oidn v2.5.1 GitHub release asset.
assert hashlib.sha256(p.read_bytes()).hexdigest()=='743c3e2aff8c220d5d70fe6cb970fb3d36f2702d2693c61d1d148e404cf37cd6'
with tarfile.open(p) as t:t.extractall('/workspace/tools/oidn',filter='data')
print('Verified and installed Open Image Denoise 2.5.1.')
PY
