import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

out = Path(__file__).resolve().parent
inputs = {
    'control_legacy': out / 'results_legacy_control.json',
    'control_direct': out / 'results_direct_control.json',
    'complete_legacy': out / 'results_legacy_control.json',
    'complete_direct': out / 'results_direct_complete.json',
}
raw = {key: json.loads(path.read_text(encoding='utf-8')) for key, path in inputs.items()}
old = {'C': raw['control_legacy']['all_pass'], 'F': raw['complete_legacy']['all_pass']}
full = {'C': old['C'] and raw['control_direct']['passed'],
        'F': old['F'] and raw['complete_direct']['passed']}
rows = []
for m0, m2 in (('C', 'F'), ('F', 'C')):
    old_delta = int(old[m2]) - int(old[m0])
    full_delta = int(full[m2]) - int(full[m0])
    rows.append({'M0_candidate_position': m0, 'M2_candidate_position': m2,
                 'old_evaluator': {'M0_Y': int(old[m0]), 'M2_Y': int(old[m2]), 'delta': old_delta},
                 'full_evaluator': {'M0_Y': int(full[m0]), 'M2_Y': int(full[m2]), 'delta': full_delta},
                 'delta_changed': old_delta != full_delta,
                 'delta_sign_changed': (old_delta > 0) != (full_delta > 0) or (old_delta < 0) != (full_delta < 0)})
result = {
    'created_at': datetime.now(timezone.utc).isoformat(),
    'question': '同一评价器的公开入口盲点是否会改变相对收益？',
    'candidate_positions': {'C': '真实控制：旧8/8、直接入口0/1', 'F': '真实完整实现：旧8/8、直接入口1/1'},
    'rows': rows,
    'formula': 'Y_full = Y_old AND direct_entry_pass; delta = Y(M2)-Y(M0)',
    'visible_result': '旧评价两种分配均delta=0；补充入口后分别delta=+1和delta=-1，交换臂位置会翻转符号。',
    'interpretation': '证明评价器盲点可能扭曲相对差值的机制；不代表M0/M2模型效果，不估计概率或显著性。',
    'input_hashes': {key: {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for key, path in inputs.items()},
    'model_calls': 0, 'behavior_calls': 0, 'human_reviews': 0,
    'formal_labels': None, 'split': None,
}
with (out / 'evaluator_blindspot_delta_counterexample.json').open('x', encoding='utf-8') as handle:
    json.dump(result, handle, ensure_ascii=False, indent=2)
print(json.dumps({'rows': rows, 'model_calls': 0, 'behavior_calls': 0}, ensure_ascii=False))
