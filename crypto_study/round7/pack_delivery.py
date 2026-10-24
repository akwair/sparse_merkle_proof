"""Preserve the prior delivery and add all new evidence with a checked manifest."""
from pathlib import Path
import hashlib,json,zipfile
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'crypto_study/round7'
OUT=ROOT/'output'
NAME='CCPE_Application_Replication_Study_20261023'
PDF='Sparse_Merkle_Proof_Application_Replication_Study_20261023.pdf'

def sha(data):return hashlib.sha256(data).hexdigest()

def file_sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def run():
    old=OUT/'CCPE_Three_Platform_Study_20261023.zip'
    assert file_sha(old)=='ea319cff24bc9f01bc843e0d82a7711a97d8abcd33b7cdc52103fd6f1d3506e2'
    assert file_sha(OUT/'pdf/Sparse_Merkle_Proof_Three_Platform_Study_20261023.pdf')=='31df3567510f6ce980758340896d64443e3eaf675aa0cc8e6949b57da641f54b'
    for base,count in [(ROUND,74),(ROUND/'diagnostics',34)]:
        reg=json.loads((base/'registration.json').read_text());assert len(reg['files'])==count
        for n,h in reg['files'].items():assert file_sha(base/n)==h,n
    qa=json.loads((ROUND/'pdf_qa/checks.json').read_text());assert qa['pages']==20 and not qa['unresolved_marker'] and not qa['replacement_characters']
    log=(ROUND/'manuscript/main.log').read_text()
    assert not any(x in log for x in ('Overfull \\hbox','Underfull \\hbox','LaTeX Warning:','Package natbib Warning:'))
    pdf=(ROUND/'manuscript/main.pdf').read_bytes();target=OUT/'pdf'/PDF
    with target.open('xb') as f:f.write(pdf)
    inventory={};old_map={};archive=OUT/(NAME+'.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        def add(n,data):
            assert n not in inventory and not n.startswith('/') and '..' not in Path(n).parts,n
            z.writestr(n,data);inventory[n]={'sha256':sha(data),'bytes':len(data)}
        with zipfile.ZipFile(old) as prior:
            assert len(prior.namelist())==7361
            for n in prior.namelist():
                dest={'README.md':'prior_delivery/round6/README.md','MANIFEST.json':'prior_delivery/round6/MANIFEST.json',
                      'crypto_study/round3/ALL_RUNS.log':'prior_delivery/round6/ALL_RUNS.log'}.get(n,n)
                add(dest,prior.read(n));old_map[n]=dest
        print('Preserved all 7361 prior entries',flush=True)
        files=[p for p in ROUND.rglob('*') if p.is_file() and not any(x in p.relative_to(ROUND).parts for x in ('go-cache','tmp','__pycache__'))]
        schedule=json.loads((ROUND/'schedule_completion.json').read_text())
        for b in schedule['blocks']:
            for rel in (b['frozen'],b['frozen_launch']):files.extend(p for p in (ROOT/'crypto_study/round5'/rel).rglob('*') if p.is_file())
        files += [ROOT/'crypto_study/round3/ALL_RUNS.log',target]
        for i,p in enumerate(sorted(files)):
            add(p.relative_to(ROOT).as_posix(),p.read_bytes())
            if i and i%5000==0:print('Added',i,'new files',flush=True)
        add('README.md',(ROUND/'DELIVERY_README.md').read_bytes())
        manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'complete':True,'prior_archive_sha256':file_sha(old),
          'prior_entry_mapping':old_map,'files':inventory,'omitted_new_material':'Only regenerable build caches, scratch directories and __pycache__; no raw measurements or failed experiments omitted.',
          'current_manuscript':'output/pdf/'+PDF,'seed':3407}
        z.writestr('MANIFEST.json',json.dumps(manifest,indent=2,ensure_ascii=False).encode())
    print('Checking every archived hash and CRC',flush=True)
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist())==len(set(z.namelist()))==len(inventory)+1
        for n,entry in inventory.items():
            content=z.read(n);assert sha(content)==entry['sha256'] and len(content)==entry['bytes'],n
    receipt={'complete':True,'archive':str(archive),'archive_bytes':archive.stat().st_size,'archive_sha256':file_sha(archive),
             'members':len(inventory)+1,'all_hashes_and_crc_verified':True,'prior_entries_preserved':len(old_map),
             'pdf':str(target),'pdf_bytes':len(pdf),'pdf_sha256':sha(pdf),'pdf_pages':20}
    with (OUT/(NAME+'.verification.json')).open('x') as f:json.dump(receipt,f,indent=2)
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':run()
