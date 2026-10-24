"""Focused tests for neutral platform labels; scientific arithmetic is inherited."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE = None
if (ROOT / 'compare_three.py').exists():
    spec = importlib.util.spec_from_file_location('third_comparison', ROOT / 'compare_three.py')
    MODULE = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(MODULE)


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(MODULE, 'third-platform label projection is not implemented')

    def test_recursive_labels_keep_values(self):
        source = {'windows': {'passed': False}, 'linux': {'passed': True},
                  'rows': [{'windows_ratio': 1.25, 'linux_ratio': 1.75,
                            'linux_windows_ratio_of_medians': 0.625}],
                  'identity': {'cell': 'unchanged'}, 'scope': 'legacy scope'}
        actual = MODULE.label_pair(source, 'linux_w5')
        self.assertEqual(actual['reference'], {'passed': False})
        self.assertEqual(actual['target'], {'passed': True})
        self.assertEqual(actual['rows'][0], {'reference_ratio': 1.25, 'target_ratio': 1.75,
                         'target_reference_ratio_of_medians': 0.625})
        self.assertEqual(actual['identity'], source['identity'])
        self.assertEqual(source['scope'], 'legacy scope')

    def test_linux_pair_scope_is_not_windows(self):
        actual = MODULE.label_pair({'scope': 'OS and clock differ'}, 'linux_w5')
        self.assertEqual(actual['reference_id'], 'linux_w5')
        self.assertEqual(actual['target_id'], 'linux_gold')
        self.assertIn('same Linux executable and clock implementation', actual['scope'])
        self.assertNotIn('OS and clock differ', actual['scope'])

    def test_unknown_platform_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.label_pair({}, 'unknown')

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='test_tmp_comparison_') as folder:
            path = Path(folder) / 'result.json'
            path.write_text('original', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                MODULE.save_new(path, {'new': 1})
            self.assertEqual(path.read_text(), 'original')


if __name__ == '__main__':
    unittest.main()
