import unittest
from app_analysis import summarize_cell, boundary, classify, hot_decisions, validate_rows


class AnalysisTests(unittest.TestCase):
    def test_paired_ratio_not_ratio_of_medians(self):
        rows = []
        for i, (base, alt) in enumerate([(1, 2), (10, 5), (100, 300)]):
            for mode, value in [('ordinary', base), ('dictionary', alt)]:
                rows.append(dict(batch=0, repeat=i, mode=mode, bytes=100 if mode=='ordinary' else 70,
                    proof_ns=value, encode_ns=value, decode_ns=value, verify_ns=value,
                    total_ns=4*value, codec_total_ns=3*value))
        result = summarize_cell(rows, modes=['ordinary','dictionary'], expected_pairs=3)
        self.assertEqual(result['dictionary']['paired_total_ratio'], 2)
        self.assertEqual(result['dictionary']['worst_byte_ratio'], .7)
        self.assertFalse(result['dictionary']['service_gate'])

    def test_missing_pair_rejected(self):
        with self.assertRaises(ValueError):
            summarize_cell([], modes=['ordinary','dictionary'], expected_pairs=1)

    def test_boundary_units_and_classes(self):
        self.assertEqual(boundary(1000, 1000000)['bits_per_second'], 8_000_000)
        self.assertEqual(boundary(1000, 0)['class'], 'model_dominates')
        self.assertEqual(boundary(-1, 100)['class'], 'no_byte_saving')

    def test_gate_keeps_confirmation_direction_and_codec_separate(self):
        dev={'worst_byte_ratio':.8,'paired_total_ratio':1.05,'paired_codec_ratio':1.2}
        confirm={'worst_byte_ratio':.9,'paired_total_ratio':1.01,'paired_codec_ratio':1.2}
        self.assertEqual(classify(dev,confirm), {'service':True,'codec':False})
        confirm['worst_byte_ratio']=1
        self.assertFalse(classify(dev,confirm)['service'])

    def test_empty_matrix_rejected(self):
        with self.assertRaises(ValueError):
            validate_rows([], [])

    def test_hot_all_conditions_and_confirmation(self):
        ds=[]
        for d in ('dev','confirm'):
            for n in (4096,16384):
                for v in (32,1000):
                    for q in (32,128):
                        for dist, size in [('uniform',90),('zipf',80)]:
                            for b in range(3):
                                ds.append(dict(domain=d,n=n,value_bytes=v,q=q,distribution=dist,
                                               batch=b,sizes={'ordinary':100,'dictionary':size}))
        out=hot_decisions(ds)
        self.assertEqual(len(out),16)
        self.assertTrue(all(x['passed'] for x in out))
        ds[-1]['sizes']['dictionary']=100
        ds[-2]['sizes']['dictionary']=100
        self.assertFalse(all(x['passed'] for x in hot_decisions(ds)))


if __name__ == '__main__': unittest.main()
