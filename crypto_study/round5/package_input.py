"""Build a verifiable, offline deployment package without credentials."""
from pathlib import Path
import hashlib
import io
import json
import os
import tarfile

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parents[1]


def main():
    files = {}
    for name in ('round3_qpc', 'round4'):
        folder = ROOT.parent / name
        reg = json.loads((folder / 'registration.json').read_text())
        for rel, expected in reg['files'].items():
            p = folder / rel
            assert hashlib.sha256(p.read_bytes()).hexdigest() == expected
            files[p.relative_to(BASE).as_posix()] = p
        files[(folder / 'registration.json').relative_to(BASE).as_posix()] = folder / 'registration.json'
    legacy = ROOT.parent / 'round3_qpc/runs/screening_001/external'
    for p in legacy.rglob('*'):
        if p.is_file():
            files[p.relative_to(BASE).as_posix()] = p
    common = ROOT.parent / 'round3/ALL_RUNS.log'
    files[common.relative_to(BASE).as_posix()] = common
    for current, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {'build_cache', '__pycache__', 'deployment',
            'runs', 'launches', 'manuscript', 'pdf_qa'} and not d.startswith('tmp')]
        for name in names:
            p = Path(current) / name
            files[p.relative_to(BASE).as_posix()] = p
    for needed in ('PLAN.md', 'LITERATURE.md', 'ADAPTATION.md', 'launch.sh', 'run_study.py',
                   'runner/conditional_runner', 'runner/runner_tests_linux'):
        assert (ROOT / needed).is_file(), needed
    manifest = {n: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
                for n, p in sorted(files.items())}
    output = ROOT / 'deployment'
    output.mkdir(exist_ok=True)
    archive = output / 'input_001.tar.gz'
    assert not archive.exists()
    with tarfile.open(archive, 'x:gz') as t:
        for n, p in sorted(files.items()):
            info = t.gettarinfo(str(p), arcname=n)
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            info.mode = 0o755 if p.suffix == '.sh' or p.name in {'conditional_runner', 'runner_tests_linux'} else 0o644
            with p.open('rb') as f:
                t.addfile(info, f)
        raw = json.dumps(manifest, indent=2).encode()
        info = tarfile.TarInfo('DEPLOYMENT_MANIFEST.json')
        info.size = len(raw)
        info.mode = 0o644
        t.addfile(info, io.BytesIO(raw))
    result = {'archive': str(archive), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
              'files': len(files), 'bytes': archive.stat().st_size}
    (output / 'input_001.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
