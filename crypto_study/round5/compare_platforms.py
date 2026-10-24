"""Compare preregistered runs without pooling observations or selecting cells."""
from pathlib import Path
import argparse
import hashlib
import json
import statistics

ROOT = Path(__file__).resolve().parent


def load(p):
    return json.loads(p.read_text())


def corpus_files(root):
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file() and
            (p.suffix == '.wire' or p.name in {'bundle.json', 'diagnostics.json', 'execution_order.json'}
             or p.name.startswith('tree_') and p.suffix == '.json')}


def compare_files(left, right):
    if set(left) != set(right):
        raise ValueError('corpus file set differs')
    for name in sorted(left):
        if left[name].read_bytes() != right[name].read_bytes():
            raise ValueError('corpus bytes differ: ' + name)
    return len(left)


def row_identity(row):
    return tuple(row[k] for k in ('domain', 'n', 'q', 'kind', 'pattern', 'batch',
                                  'cell', 'id', 'repeat', 'order', 'mode', 'bytes'))


def decision_comparison(left, right, keys, decision):
    before = {tuple(r[k] for k in keys): r for r in left}
    after = {tuple(r[k] for k in keys): r for r in right}
    if len(before) != len(left) or len(after) != len(right) or before.keys() != after.keys():
        raise ValueError('decision identities differ or repeat')
    items = [{'identity': dict(zip(keys, key)), 'windows': before[key], 'linux': after[key],
              'changed': before[key][decision] != after[key][decision]} for key in sorted(before)]
    return {'total': len(items), 'changed': sum(x['changed'] for x in items), 'items': items}


def summarize(e):
    modes = sorted(e['cells'][0]['modes'])
    summary = {'gates': e['gates'], 'effective_cells': sum(v['effective'] for v in e['effective']),
               'mode_ranges': {}, 'lifecycle_counts': {}, 'locality': e['locality']}
    for m in modes:
        values = [c['modes'][m] for c in e['cells']]
        times = [v['paired_total_ratio'] for v in values]
        summary['mode_ranges'][m] = {
            'paired_total_ratio_min': min(times), 'paired_total_ratio_max': max(times),
            'cells_over_105': sum(t > 1.05 for t in times),
            'dev_gate_count': sum(c['modes'][m]['gate'] for c in e['cells'] if c['domain'] == 'dev'),
            'pareto_cells': sum(not v['dominated_by'] for v in values),
            'pareto_q_ge_8_cells': sum(not c['modes'][m]['dominated_by'] for c in e['cells'] if c['q'] >= 8),
            'largest_observed_ns': max(v['max_total_ns'] for v in values),
        }
    for domain in ('dev', 'confirm'):
        for q in (1, 8):
            for m in ('reset-zlib-ordinary', 'reset-zlib-compact', 'reset-zlib-dictionary'):
                values = [r for r in e['lifecycle'] if r['domain'] == domain and
                          f'_q{q}_' in r['cell'] and r['mode'] == m]
                assert len(values) == 8
                summary['lifecycle_counts'][f'{domain}/q{q}/{m}'] = {
                    'pass': sum(v['passed'] for v in values), 'total': len(values),
                    'ratio_min': min(v['ratio'] for v in values),
                    'ratio_max': max(v['ratio'] for v in values)}
    return summary


def compare(left, right):
    for root in (left, right):
        c = load(root / 'completion.json')
        assert c['complete'] and c['rows'] == 36288
        assert not (root / 'failure.json').exists()
    lm, rm = left / 'measurements', right / 'measurements'
    count = compare_files(corpus_files(lm), corpus_files(rm))
    assert count == 1542
    rows_left = [json.loads(s) for s in (lm / 'log.jsonl').read_text().splitlines()]
    rows_right = [json.loads(s) for s in (rm / 'log.jsonl').read_text().splitlines()]
    assert len(rows_left) == len(rows_right) == 36288
    assert list(map(row_identity, rows_left)) == list(map(row_identity, rows_right))
    le, re = load(left / 'eval.json'), load(right / 'eval.json')
    lc = {(c['domain'], c['cell']): c for c in le['cells']}
    pairs = []
    for c in re['cells']:
        old = lc[(c['domain'], c['cell'])]
        for mode, value in c['modes'].items():
            previous = old['modes'][mode]
            pairs.append({'domain': c['domain'], 'cell': c['cell'], 'mode': mode,
                          'windows_ratio': previous['paired_total_ratio'],
                          'linux_ratio': value['paired_total_ratio'],
                          'windows_median_total_ns': previous['median_total_ns'],
                          'linux_median_total_ns': value['median_total_ns'],
                          'linux_windows_ratio_of_medians': value['median_total_ns'] / previous['median_total_ns'],
                          'windows_p95_ns': previous['p95_total_ns'], 'linux_p95_ns': value['p95_total_ns'],
                          'windows_max_ns': previous['max_total_ns'], 'linux_max_ns': value['max_total_ns']})
    return {'same_corpus_files': count, 'same_unique_frames': 1152, 'same_bundles': 192,
            'same_tree_checkpoints': 4, 'same_observation_order': True,
            'observations_per_platform': 36288,
            'windows': summarize(le), 'linux': summarize(re), 'matched_cell_summaries': pairs,
            'decision_comparisons': {
                'locality': decision_comparison(le['locality'], re['locality'], ('domain', 'n', 'q', 'kind'), 'passed'),
                'lifecycle': decision_comparison(le['lifecycle'], re['lifecycle'], ('domain', 'cell', 'mode'), 'passed'),
                'effective': decision_comparison(le['effective'], re['effective'], ('cell', 'mode'), 'effective')},
            'scope': 'Two platforms, same inputs and order; hardware, OS and clock differ. '
                     'Ratios between platforms are ratios of cell medians, not paired simultaneous observations. '
                     'Do not pool timings or infer CPU-only causality. Single seed 3407.'}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--windows', type=Path, default=ROOT.parent / 'round4/runs/conditions_001')
    p.add_argument('--linux', type=Path, default=ROOT / 'runs/linux_001')
    p.add_argument('--output', type=Path, default=ROOT / 'CROSS_PLATFORM.json')
    a = p.parse_args()
    assert not a.output.exists(), 'refusing to overwrite comparison'
    result = compare(a.windows, a.linux)
    with a.output.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'matched_cell_summaries'}, indent=2))


if __name__ == '__main__':
    main()
