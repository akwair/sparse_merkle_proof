"""Assemble a non-overwriting delivery and verify all archive members."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, shutil, zipfile
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parents[1]
OUT = BASE / 'output'
PAPER = ROOT.parent / 'round2/manuscript'
PDF = OUT / 'pdf/Sparse_Merkle_Proof_Empirical_Study_20261023.pdf'
ARCHIVE = OUT / 'CCPE_Proof_Representation_Study_20261023.zip'
OLD = OUT / 'Cryptography_Transport_Revised_Research_Archive_20261023.zip'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def paths(folder):
    for current, dirs, names in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in {'build_cache', 'go_mod_cache',
            'toolchain', '__pycache__', '.pytest_cache', 'pdf_qa'}
            and not d.startswith('test_tmp')]
        for name in names:
            yield Path(current) / name

def main():
    assert not PDF.exists() and not ARCHIVE.exists(), 'never overwrite delivery'
    assert (ROOT / 'manuscript_revision.tex').read_bytes() == (PAPER / 'main.tex').read_bytes()
    registered = {}
    for round_name in ('round3_qpc', 'round4'):
        folder = ROOT.parent / round_name
        reg = json.loads((folder / 'registration.json').read_text())
        for name, expected in reg['files'].items():
            assert digest((folder / name).read_bytes()) == expected, name
        registered[round_name] = len(reg['files'])
    reg = json.loads((ROOT / 'registration.json').read_text())
    for name, expected in reg['files'].items():
        assert digest((ROOT / 'runs/conditions_001/source' / name).read_bytes()) == expected
    completion = json.loads((ROOT / 'runs/conditions_001/completion.json').read_text())
    for name, expected in completion['files'].items():
        assert digest((ROOT / 'runs/conditions_001' / name).read_bytes()) == expected, name
    audit = json.loads((ROOT / 'AUDIT.json').read_text())
    assert audit['complete'] and audit['all_eval_fields_reproduced']
    assert len(PdfReader(PAPER / 'main.pdf').pages) == 12
    qa = json.loads((ROOT / 'pdf_qa/checks.json').read_text())
    assert qa['pages'] == 12 and not qa['unresolved_marker'] and qa['replacement_characters'] == 0
    log = (PAPER / 'main.log').read_text(errors='replace')
    assert all(s not in log for s in ('Overfull', 'Underfull', 'LaTeX Warning', 'undefined'))

    # Deliver a self-contained current manuscript snapshot.
    for p in PAPER.rglob('*'):
        rel = p.relative_to(PAPER)
        if not p.is_file() or any(x.startswith('qa') for x in rel.parts):
            continue
        if p.suffix not in {'.tex', '.bib', '.bbl', '.pdf', '.png', '.svg'}:
            continue
        dest = ROOT / 'manuscript' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
    shutil.copyfile(PAPER / 'main.pdf', PDF)

    members = {}
    # Preserve preceding evidence, including unsuccessful experiments and its
    # original nested deliveries; clearly label its superseded manuscript.
    with zipfile.ZipFile(OLD) as prior:
        assert prior.testzip() is None
        for entry in prior.infolist():
            if entry.is_dir() or entry.filename == 'MANIFEST.json':
                continue
            name = entry.filename
            if name == 'README.md':
                name = 'prior_delivery/round3_qpc_README.md'
            elif name.startswith('manuscript/'):
                name = 'prior_delivery/round3_qpc_' + name
            members[name] = prior.read(entry)

    for folder_name in ('round4', 'round4_design', 'ccpe_empirical_comparison'):
        for p in paths(ROOT.parent / folder_name):
            if p.name == 'delivery_checks.json':
                continue
            # The separately delivered comparison archive retains full papers.
            if folder_name == 'ccpe_empirical_comparison' and p.suffix.lower() not in {'.md', '.bib', '.json', '.txt'}:
                continue
            members[p.relative_to(BASE).as_posix()] = p.read_bytes()
    for p in PAPER.rglob('*'):
        rel = p.relative_to(PAPER)
        if p.is_file() and not any(x.startswith('qa') for x in rel.parts) and p.suffix in {'.tex', '.bib', '.bbl', '.pdf', '.png', '.svg'}:
            members[p.relative_to(BASE).as_posix()] = p.read_bytes()
    for name in ('checks.json', 'text.txt'):
        p = ROOT / 'pdf_qa' / name
        members[p.relative_to(BASE).as_posix()] = p.read_bytes()
    common = ROOT.parent / 'round3/ALL_RUNS.log'
    members[common.relative_to(BASE).as_posix()] = common.read_bytes()
    members['README.md'] = (ROOT / 'DELIVERY_README.md').read_bytes()
    manifest = {'created_utc': datetime.now(timezone.utc).isoformat(),
        'registration_files_verified': registered,
        'round4_run_files_verified': len(completion['files']),
        'files': {n: {'sha256': digest(b), 'bytes': len(b)} for n, b in sorted(members.items())}}
    with zipfile.ZipFile(ARCHIVE, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, data in sorted(members.items()):
            z.writestr(name, data)
        z.writestr('MANIFEST.json', json.dumps(manifest, indent=2))
    with zipfile.ZipFile(ARCHIVE) as z:
        assert len(z.namelist()) == len(set(z.namelist()))
        assert z.testzip() is None
        for name, expected in manifest['files'].items():
            assert digest(z.read(name)) == expected['sha256'], name
        # Verify that replay dependencies actually exist inside this delivery.
        for round_name in ('round3_qpc', 'round4'):
            prefix = 'crypto_study/' + round_name + '/'
            reg = json.loads(z.read(prefix + 'registration.json'))
            for name, expected in reg['files'].items():
                assert digest(z.read(prefix + name)) == expected
    checks = {'pdf': str(PDF), 'pdf_sha256': digest(PDF.read_bytes()),
        'pdf_pages': 12, 'archive': str(ARCHIVE),
        'archive_sha256': digest(ARCHIVE.read_bytes()), 'archive_bytes': ARCHIVE.stat().st_size,
        'archive_members': len(members) + 1, 'all_member_hashes_verified': True,
        'all_registrations_verified_in_archive': True, 'registrations': registered,
        'round4_run_files_verified': len(completion['files']),
        'unresolved_references_or_compile_warnings': False}
    (ROOT / 'delivery_checks.json').write_text(json.dumps(checks, indent=2) + '\n')
    print(json.dumps(checks, indent=2))

if __name__ == '__main__':
    main()
