import unittest
from summarize_repetitions import across


class RepetitionTests(unittest.TestCase):
    def fixture(self):
        return [{'cells':[{'domain':'dev','cell':'c','n':1,'q':1,'modes':{'ordinary':{
          'median_total_ns':t,'paired_total_ratio':1,'worst_byte_ratio':1}}}]} for t in (10,11,12,13,20)]

    def test_process_range_not_pooled_loops(self):
        out=across(self.fixture())
        self.assertEqual(out[0]['modes']['ordinary']['median_total_ns']['values'],[10,11,12,13,20])
        self.assertEqual(out[0]['modes']['ordinary']['absolute_spread'],2)
        self.assertTrue(out[0]['modes']['ordinary']['spread_over_120'])

    def test_missing_or_changed_matrix_rejected(self):
        with self.assertRaises(ValueError):across(self.fixture()[:4])
        x=self.fixture();x[-1]['cells'][0]['cell']='different'
        with self.assertRaises(ValueError):across(x)


if __name__=='__main__':unittest.main()
