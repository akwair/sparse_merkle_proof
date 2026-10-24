import json
from pathlib import Path
import tempfile
import unittest
from audit_application import inventory, old


class AuditTests(unittest.TestCase):
    def test_inventory_binds_exact_files_and_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'data').write_bytes(b'evidence')
            (p/'completion.json').write_text(json.dumps({'complete':True,'files':{'data':old.file_sha(p/'data')}}))
            self.assertTrue(inventory(p)['complete'])
            (p/'extra').write_bytes(b'undeclared')
            with self.assertRaises(ValueError):inventory(p)
            (p/'extra').unlink();(p/'data').write_bytes(b'changed')
            with self.assertRaises(ValueError):inventory(p)


if __name__=='__main__':unittest.main()
