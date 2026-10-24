"""Package evidence without toolchain caches; verify every member's hash."""
from pathlib import Path
import hashlib,json,shutil,zipfile
from datetime import datetime,timezone
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[1]
OUT=BASE/'output'
M=ROOT.parent/'round2/manuscript'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pdf=OUT/'pdf/Cryptography_Transport_Revised_20261023.pdf'
archive=OUT/'Cryptography_Transport_Revised_Research_Archive_20261023.zip'
assert not pdf.exists() and not archive.exists()
assert len(PdfReader(M/'main.pdf').pages)==13
shutil.copyfile(M/'main.pdf',pdf)
files={}
for folder in ('round3','round3_qpc'):
    root=ROOT.parent/folder
    for p in root.rglob('*'):
        rel=p.relative_to(root)
        if not p.is_file() or any(x in ('toolchain','__pycache__','.pytest_cache','pdf_qa') or x.startswith('test_tmp') for x in rel.parts):continue
        files['crypto_study/'+folder+'/'+rel.as_posix()]=p
for p in M.rglob('*'):
    rel=p.relative_to(M)
    if not p.is_file() or any(x.startswith('qa') for x in rel.parts):continue
    if p.suffix not in ('.tex','.bib','.bbl','.pdf','.png','.svg'):continue
    files['manuscript/'+rel.as_posix()]=p
for name in ('Cryptography_Transport_Archive_20261023.zip','Cryptography_Transport_Manuscript_Polished_Source_20261023.zip'):
    p=OUT/name
    if p.exists():files['prior_delivery/'+name]=p
files['README.md']=ROOT/'README.md'
manifest={'utc':datetime.now(timezone.utc).isoformat(),'files':{name:{'sha256':sha(p),'bytes':p.stat().st_size} for name,p in sorted(files.items())}}
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name,p in sorted(files.items()):z.write(p,name)
    z.writestr('MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name,v in manifest['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==v['sha256'],name
check={'pdf':str(pdf),'pdf_sha256':sha(pdf),'pdf_pages':13,'archive':str(archive),'archive_sha256':sha(archive),'members':len(files)+1,'all_member_hashes_verified':True,'archive_bytes':archive.stat().st_size}
(ROOT/'delivery_checks.json').write_text(json.dumps(check,indent=2)+'\n')
print(json.dumps(check,indent=2))
