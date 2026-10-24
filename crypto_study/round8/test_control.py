from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,tempfile,unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('round8_control',HERE/'control.py')
control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control)

class ControllerGuards(unittest.TestCase):
    def test_schedule_is_frozen_complete_and_relative(self):
        config=json.loads((HERE/'config.json').read_text());a=control.schedule(config);b=control.schedule(config)
        self.assertEqual(a,b);self.assertEqual(len(a),444)
        self.assertEqual(Counter(x['phase'] for x in a),{'crosshost':288,'q1_anchor':24,'controlled':72,'diagnostic':60})
        self.assertEqual(len({x['work_dir'] for x in a}),444)
        self.assertTrue(all(not Path(x['work_dir']).is_absolute() and '..' not in Path(x['work_dir']).parts for x in a))
        for epoch in [1,2,3]:
            self.assertEqual(sum(x['epoch']==epoch and x['phase']=='controlled' for x in a),24)
            self.assertEqual(sum(x['epoch']==epoch and x['phase']!='controlled' for x in a),124)
    def test_registration_rejects_changed_plan(self):
        with tempfile.TemporaryDirectory(dir=HERE/'validation') as d:
            previous=control.ROOT;control.ROOT=Path(d)
            try:
                p=control.ROOT/'PLAN.md';p.write_bytes(b'prospective fixed plan')
                r={'registered_before_formal':True,'files':{'PLAN.md':hashlib.sha256(p.read_bytes()).hexdigest()}}
                (control.ROOT/'REGISTRATION.json').write_text(json.dumps(r))
                self.assertTrue(control.verify_registration()['registered_before_formal'])
                p.write_bytes(b'changed after registration')
                with self.assertRaises(AssertionError):control.verify_registration()
            finally:control.ROOT=previous
    def test_registration_required(self):
        with tempfile.TemporaryDirectory(dir=HERE/'validation') as d:
            previous=control.ROOT;control.ROOT=Path(d)
            try:
                with self.assertRaises(FileNotFoundError):control.verify_registration()
            finally:control.ROOT=previous

if __name__=='__main__':unittest.main()
