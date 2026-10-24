"""Verify and import remote artifacts without replacing prior evidence."""
from pathlib import Path
import hashlib
import json
import tarfile

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parents[1]
archive = ROOT / 'deployment/results_001.tar.gz'
expected = 'f9db37c771c4fff3a3d8a4307fc3bdab495963467a017de395f4d490a69a6fb0'
assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected
created = unchanged = appended = 0
with tarfile.open(archive, 'r:gz') as tar:
    for member in tar:
        dest = (BASE / member.name).resolve()
        assert dest.is_relative_to(BASE.resolve()), member.name
        if member.isdir():
            dest.mkdir(parents=True, exist_ok=True)
            continue
        assert member.isfile(), member.name
        raw = tar.extractfile(member).read()
        if member.name == 'crypto_study/round3/ALL_RUNS.log':
            copy = ROOT / 'deployment/remote_ALL_RUNS.log'
            if copy.exists():
                assert copy.read_bytes() == raw
            else:
                with copy.open('xb') as f:
                    f.write(raw)
            old = dest.read_bytes()
            assert raw.startswith(old), 'common log must retain its entire previous prefix'
            appended = len(raw) - len(old)
            with dest.open('ab') as f:
                f.write(raw[len(old):])
        elif dest.exists():
            assert dest.read_bytes() == raw, 'refusing to replace changed local file: ' + member.name
            unchanged += 1
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as f:
                f.write(raw)
            created += 1
result = {'remote_archive_sha256_verified': expected, 'created_files': created,
          'identical_existing_files': unchanged, 'common_log_bytes_appended': appended}
with (ROOT / 'deployment/results_receipt.json').open('x') as f:
    json.dump(result, f, indent=2)
print(json.dumps(result, indent=2))
