"""Label two frozen pairwise analyses without changing their arithmetic."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT.parent / 'round5/compare_platforms.py'
FROZEN_SHA = '61a81ff16d06e80555f6ac76b34b327a9c240c228e24c66649d9191e4ee2e1ec'
RUNS = {
    'windows_i5': ROOT.parent / 'round4/runs/conditions_001',
    'linux_w5': ROOT.parent / 'round5/runs/linux_001',
    'linux_gold': ROOT.parent / 'round5/runs/linux_host3_001',
}


def neutral_keys(value):
    if isinstance(value, list):
        return [neutral_keys(v) for v in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key == 'linux_windows_ratio_of_medians':
            key = 'target_reference_ratio_of_medians'
        elif key == 'windows' or key.startswith('windows_'):
            key = 'reference' + key[len('windows'):]
        elif key == 'linux' or key.startswith('linux_'):
            key = 'target' + key[len('linux'):]
        if key in result:
            raise ValueError('platform field collision')
        result[key] = neutral_keys(item)
    return result


def label_pair(raw, reference):
    if reference not in ('windows_i5', 'linux_w5'):
        raise ValueError('unknown reference platform')
    result = neutral_keys(raw)
    result['reference_id'] = reference
    result['target_id'] = 'linux_gold'
    shared = ('The Linux hosts use the same Linux executable and clock implementation; '
              'kernel, CPU, topology and surrounding activity differ. ' if reference == 'linux_w5'
              else 'CPU, OS, clock backend and surrounding activity differ. ')
    result['scope'] = (shared + 'Identical fixtures and order, one seed 3407 and one formal run per environment. '
                       'Cross-host ratios divide cell medians, not simultaneous paired observations. '
                       'No pooled timings, CPU-only causality or independent-seed inference.')
    return result


def save_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'THREE_PLATFORM.json')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if not __debug__:
        raise ValueError('Python optimization disables frozen comparison assertions')
    if hashlib.sha256(FROZEN.read_bytes()).hexdigest() != FROZEN_SHA:
        raise ValueError('frozen comparison implementation differs')
    spec = importlib.util.spec_from_file_location('frozen_round5_comparison', FROZEN)
    comparison = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(comparison)
    pairs = {}
    for reference in ('windows_i5', 'linux_w5'):
        pairs[reference] = label_pair(comparison.compare(RUNS[reference], RUNS['linux_gold']), reference)
    provenance = {
        platform: {name: hashlib.sha256((run / name).read_bytes()).hexdigest()
                   for name in ('completion.json', 'eval.json', 'measurements/log.jsonl')}
        for platform, run in RUNS.items()
    }
    save_new(args.output, {'frozen_analysis_sha256': FROZEN_SHA, 'inputs': provenance, 'comparisons': pairs})
    print(json.dumps({key: {'same_corpus_files': v['same_corpus_files'],
                          'same_observation_order': v['same_observation_order'],
                          'reference_gates': v['reference']['gates'], 'target_gates': v['target']['gates'],
                          'lifecycle_changed': v['decision_comparisons']['lifecycle']['changed']}
                      for key, v in pairs.items()}, indent=2))


if __name__ == '__main__':
    main()
