import hashlib
import json
from pathlib import Path

from build_input_result_tree_pair import PROJECT, now, save, sha

ROOT = PROJECT / 'experiments/d1_repository_feature_candidate_v1_20261009/path_context_v1'
CANDIDATE = ROOT / 'candidate'
OUT = ROOT / 'integrity_v2'


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    task = json.loads((CANDIDATE / 'task.json').read_text(encoding='utf-8'))
    anchors = json.loads((CANDIDATE / 'public_examples.json').read_text(encoding='utf-8'))
    files = sorted(p.relative_to(CANDIDATE).as_posix() for p in CANDIDATE.rglob('*') if p.is_file())
    forbidden_fragments = ['tests/', 'test/', 'hidden', 'private', 'patch', 'diff', 'source/']
    forbidden_ext = ['.pyc', '.py']
    path_checks = {f: not any(x in f.lower() for x in forbidden_fragments) and not any(f.lower().endswith(x) for x in forbidden_ext) for f in files}
    required = ['task_id', 'entrypoint', 'candidate_status', 'formal_labels', 'split', 'human_reviews', 'published']
    requirement = (CANDIDATE / 'requirement.md').read_text(encoding='utf-8')
    model_prompt = requirement
    model_prompt_check = all(x not in model_prompt.lower() for x in ['merge_commit', 'parent_commit', 'pull/126', 'source_hash'])
    self_contained = all('input' in x and 'output' in x and x['input'].get('app_dir') for x in anchors)
    required_ok = all(k in task for k in required)
    path_ok = all(path_checks.values())
    result = dict(checked_at=now(), stage='D1-P79-repository-candidate-integrity', candidate='E_C11',
        candidate_files=files, required_fields={k: k in task for k in required}, path_checks=path_checks,
        no_solution_source_in_candidate=path_ok, model_prompt_source='candidate/requirement.md',
        model_prompt_check=model_prompt_check, public_examples_count=len(anchors), public_examples_self_contained=self_contained,
        provenance_sidecar_outside_candidate=(ROOT / 'source').exists() and not (CANDIDATE / 'source').exists(),
        task_hashes={f: sha(CANDIDATE / f) for f in files}, formal_labels=task.get('formal_labels'), split=task.get('split'),
        human_reviews=task.get('human_reviews'), model_calls=0, private_reads=0, published=False,
        passed=all(flag for flag in [path_ok, model_prompt_check,
            self_contained, required_ok,
            (ROOT / 'source').exists() and not (CANDIDATE / 'source').exists()]))
    save(OUT / 'summary.json', result)
    print(json.dumps({k: result[k] for k in ['passed','candidate_files','model_prompt_check','public_examples_self_contained','provenance_sidecar_outside_candidate']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
