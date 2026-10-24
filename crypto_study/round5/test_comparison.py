import tempfile
import unittest
from pathlib import Path
from compare_platforms import compare_files, row_identity, decision_comparison


class ComparisonTests(unittest.TestCase):
    def test_changed_and_unmatched_decisions(self):
        old = [{'id': 1, 'passed': False}, {'id': 2, 'passed': True}]
        new = [{'id': 2, 'passed': True}, {'id': 1, 'passed': True}]
        result = decision_comparison(old, new, ('id',), 'passed')
        self.assertEqual((result['total'], result['changed']), (2, 1))
        with self.assertRaises(ValueError):
            decision_comparison(old, new[:1], ('id',), 'passed')
        with self.assertRaises(ValueError):
            decision_comparison(old, [new[0], new[0]], ('id',), 'passed')

    def test_changed_or_missing_frame_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
            p, q = Path(temp) / 'a', Path(temp) / 'b'
            p.write_bytes(b'frame1'); q.write_bytes(b'frame1')
            self.assertEqual(compare_files({'proof.wire': p}, {'proof.wire': q}), 1)
            q.write_bytes(b'frame2')
            with self.assertRaises(ValueError):
                compare_files({'proof.wire': p}, {'proof.wire': q})
            with self.assertRaises(ValueError):
                compare_files({'proof.wire': p}, {})

    def test_order_identity_ignores_only_timing(self):
        row = dict(domain='dev', n=4096, q=1, kind='member', pattern='dispersed',
                   batch=0, cell='x', id='x0', repeat=0, order=0, mode='ordinary', bytes=42,
                   total_ns=100)
        self.assertEqual(row_identity(row), row_identity({**row, 'total_ns': 200}))
        self.assertNotEqual(row_identity(row), row_identity({**row, 'order': 1}))
        self.assertNotEqual(row_identity(row), row_identity({**row, 'bytes': 41}))


if __name__ == '__main__':
    unittest.main()
