import copy,itertools,unittest
from analyze import CASES,STAGES,MODES,evaluate

class AllocationAnalysisTests(unittest.TestCase):
    def fixture(self):
        rows=[]
        for case in CASES:
            for rep,stage in itertools.product(range(5),STAGES):
                for order,mode in enumerate(MODES):
                    b=16 if mode.startswith('reset') else 64
                    rows.append(dict(id=case,q=128 if '_q128_' in case else 1,distribution='zipf' if '_zipf_' in case else 'uniform',stage=stage,mode=mode,repeat=rep,order=order,sequence=len(rows),batch_operations=32,allocated_bytes=b*32,mallocs=64,frees=0,num_gc=0,pause_ns=0,bytes_per_operation=b,mallocs_per_operation=2))
        return rows,{'execution_order':copy.deepcopy(rows)}
    def test_complete_matrix_and_threshold(self):
        r,e=self.fixture();v=evaluate(r,e)
        self.assertTrue(v['allocation_hypothesis']);self.assertEqual(len(v['cells']),108)
        for row in r:
            if row['id']==CASES[0] and row['stage']=='encode' and row['mode']=='reset-zlib-ordinary':row['allocated_bytes']=33*32;row['bytes_per_operation']=33
        self.assertFalse(evaluate(r,e)['allocation_hypothesis'])
    def test_reject_incomplete_or_bad_arithmetic(self):
        r,e=self.fixture()
        with self.assertRaises(ValueError):evaluate(r[:-1],e)
        r[0]['bytes_per_operation']+=1
        with self.assertRaises(ValueError):evaluate(r,e)
    def test_reject_changed_identity_and_counter(self):
        r,e=self.fixture();r[0]['order']=8
        with self.assertRaises(ValueError):evaluate(r,e)
        r,e=self.fixture();r[0]['mallocs']=-1
        with self.assertRaises(ValueError):evaluate(r,e)

if __name__=='__main__':unittest.main()
