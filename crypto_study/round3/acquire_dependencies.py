"""Fetch pinned public dependencies into this workspace; no global installation."""
from pathlib import Path
from urllib.request import urlopen
import hashlib, json, zipfile, io

ROOT = Path(__file__).resolve().parent
TOOL = ROOT / 'toolchain'
TOOL.mkdir(exist_ok=True)
info = {'filename':'go1.27.3.windows-amd64.zip', 'sha256':'f26081f438319757f8a1b46d7d0b2c5ec7583d4038e485e0aa725cfde7885fff'}
commit = 'dba215ccb88452c31d823bf156d8f35406c1dc04'
def fetch(url):
    with urlopen(url, timeout=120) as r:
        return r.read()
def unpack(data, destination, strip=False):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for m in z.infolist():
            parts = Path(m.filename).parts[1:] if strip else Path(m.filename).parts
            if not parts or m.is_dir(): continue
            p = destination.joinpath(*parts).resolve()
            if not p.is_relative_to(destination.resolve()): raise ValueError('archive path escape')
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open('xb') as out: out.write(z.read(m))
archive = TOOL / info['filename']
if not archive.exists():
    data = fetch('https://go.dev/dl/' + info['filename'])
    assert hashlib.sha256(data).hexdigest() == info['sha256']
    archive.write_bytes(data)
data = archive.read_bytes()
assert hashlib.sha256(data).hexdigest() == info['sha256']
if not (TOOL/'go/bin/go.exe').exists(): unpack(data, TOOL)
vendor = ROOT / 'external/smt'
if not vendor.exists():
    data = fetch('https://codeload.github.com/celestiaorg/smt/zip/'+commit)
    (TOOL/'smt-source.zip').write_bytes(data)
    vendor.mkdir(parents=True)
    unpack(data,vendor,True)
record = {'go':info,'smt_commit':commit,'smt_archive_sha256':hashlib.sha256((TOOL/'smt-source.zip').read_bytes()).hexdigest(),
          'smt_files':{p.relative_to(vendor).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(vendor.rglob('*')) if p.is_file()}}
(ROOT/'dependencies.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print('Pinned toolchain and upstream source acquired and hashed.',flush=True)
