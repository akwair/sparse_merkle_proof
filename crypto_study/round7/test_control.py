import tempfile
from pathlib import Path
import unittest
import control


class ControlTests(unittest.TestCase):
    def test_manifest_detects_mutation_and_escape(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'a').write_text('old')
            manifest={'a':control.sha(root/'a')}
            control.check_files(root,manifest)
            (root/'a').write_text('changed')
            with self.assertRaises(ValueError): control.check_files(root,manifest)
            with self.assertRaises(ValueError): control.check_files(root,{'../a':'bad'})

    def test_exclusive_save(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.json';control.save(p,{'v':1})
            with self.assertRaises(FileExistsError): control.save(p,{'v':2})

    def test_schedule_configuration_is_fixed(self):
        good={'process_blocks':5,'minimum_block_start_seconds':120,'seed':3407,'gomaxprocs':8}
        control.check_schedule(good)
        for key in good:
            bad=dict(good);bad[key]+=1
            with self.assertRaises(ValueError): control.check_schedule(bad)

    def test_preflight_refuses_failed_or_stale_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'source').write_bytes(b'code');(root/'test.log').write_text('PASS')
            receipt={'passed':True,'source_files':{'source':control.sha(root/'source')},
                     'tests':[{'name':name,'exit_code':0,'log':'test.log','log_sha256':control.sha(root/'test.log')}
                              for name in ('linux_go','python','frozen_validate')],
                     'corpus':{'artifacts':1542,'restorations':1728,'observations':36288,'legacy_frames':288}}
            control.check_preflight(root,receipt,{'source'})
            receipt['tests'][0]['exit_code']=1
            with self.assertRaises(ValueError):control.check_preflight(root,receipt,{'source'})
            receipt['tests'][0]['exit_code']=0;(root/'source').write_bytes(b'newcode')
            with self.assertRaises(ValueError):control.check_preflight(root,receipt,{'source'})


if __name__=='__main__': unittest.main()
