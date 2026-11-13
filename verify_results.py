"""Verify release integrity and recompute supplementary metrics offline."""
from pathlib import Path
import hashlib
import json
import math
import platform
import sys

ROOT = Path(__file__).resolve().parent

def read(path):
    text = path.read_text(encoding='utf-8-sig')
    return [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == '.jsonl' else json.loads(text)

def require(condition, message):
    if not condition:
        raise ValueError(message)

def main():
    checksums = read(ROOT/'SHA256SUMS.json')
    for rel, expected in checksums.items():
        path = ROOT/rel
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'Integrity failure: '+rel)
    result = {'status':'passed','python':sys.version,'platform':platform.platform(),'verified_files':len(checksums),'groups':{}}
    base = ROOT/'analysis/reviewer_revision_results_20261104/results'
    reference_rows = read(ROOT/'analysis/results1046_snapshot_20261030T093341Z/results/paper_suite_v1/main/predictions.jsonl')
    reference = {r['key']:(r['label'],r['subject']) for r in reference_rows}
    for group, n in [('offline',1046),('evidence',120),('cost',60)]:
        rows = read(base/group/('predictions.jsonl' if group == 'offline' else 'paired_predictions.jsonl'))
        summary = read(base/group/'summary.json')
        arms = summary.get('metrics',summary)['arms']
        require(len(rows) == len({r['key'] for r in rows}) == n, group+' sample count')
        require(all(reference[r['key']] == (r['label'],r['subject']) for r in rows), group+' alignment')
        recomputed = {}
        for arm, saved in arms.items():
            correct = sum(r['predictions'][arm] == r['label'] for r in rows)
            fixed = sum(r['predictions']['numeric_baseline'] != r['label'] and r['predictions'][arm] == r['label'] for r in rows)
            broken = sum(r['predictions']['numeric_baseline'] == r['label'] and r['predictions'][arm] != r['label'] for r in rows)
            accepted = [r for r in rows if not r['rejected']]
            ac = sum(r['predictions'][arm] == r['label'] for r in accepted)
            f1 = []
            for c in range(40):
                tp = sum(r['label'] == c and r['predictions'][arm] == c for r in rows)
                fp = sum(r['label'] != c and r['predictions'][arm] == c for r in rows)
                fn = sum(r['label'] == c and r['predictions'][arm] != c for r in rows)
                f1.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.)
            metrics = dict(correct=correct,accuracy=correct/n,fixed=fixed,broken=broken,net=fixed-broken,macro_f1=sum(f1)/40,accepted=len(accepted),accepted_correct=ac,coverage=len(accepted)/n,accepted_accuracy=ac/len(accepted))
            for key,value in metrics.items():
                require(key in saved and math.isclose(value,saved[key],rel_tol=1e-10,abs_tol=1e-10), f'{group}/{arm}/{key}: {value} != {saved.get(key)}')
            recomputed[arm] = metrics
        if group != 'offline':
            requests = read(base/group/'request_metrics.jsonl')
            for condition, saved in summary['costs'].items():
                subset = [r for r in requests if r['condition'] == condition]
                for key,value in {'actual_attempts':len(subset),'prompt_tokens_recorded':sum(r.get('prompt_eval_count') or 0 for r in subset),'output_tokens_recorded':sum(r.get('eval_count') or 0 for r in subset),'failed_attempts':sum(r['failed'] for r in subset)}.items():
                    require(value == saved[key], f'{group}/{condition}/{key}: {value} != {saved[key]}')
        result['groups'][group] = {'samples':n,'arms':recomputed}
    (ROOT/'verification_report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS:',len(checksums),'file hashes; offline 1046, evidence 120, cost 60; metrics and request counters.')

if __name__ == '__main__':
    main()
