"""策略失败记账和实际行为观察的不同分母，只读保存烟测。"""
import hashlib
import json
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))


def main():
    root=Path(__file__).resolve().parents[2];prior=root/'experiments/d1_allin_native_pair_b03_v1_20261008'
    summary=read(prior/'summary.json');freeze=read(prior/'selection_freeze.json');protocol=read(prior/'protocol_copy.json')
    out=root/'experiments/d1_failure_observation_v1_20261008';out.mkdir(exist_ok=False)
    assert summary['simulated'] is False and len(summary['candidates'])==len(freeze['candidates'])==2
    source_hashes={p.relative_to(root).as_posix():sha(p) for p in [prior/'summary.json',prior/'selection_freeze.json',prior/'protocol_copy.json',root/'scripts/d1/run_allin_pipeline.py']}
    rows=[]
    for candidate in summary['candidates']:
        arm=candidate['arm'];saved=next(r for r in freeze['candidates'] if r['arm']==arm and r['task_id']==candidate['task_id'])
        path=Path(saved['request_ledger_path']);ledger=read(path);source_hashes[path.relative_to(root).as_posix()]=sha(path)
        stages=[r['stage'] for r in ledger['calls']]
        assert ledger['known_token_spend']==candidate['total_token_spend']
        candidate_saved=saved['candidate_path'] is not None
        if candidate_saved:
            code=Path(saved['candidate_path']);assert code.exists() and sha(code)==saved['candidate_sha256']
        splits={}
        for split in ('public','private'):
            score=candidate[split];placeholder=score.get('generation_failure',False)
            actual_results=[] if placeholder else score['results']
            actual_cases=len(actual_results)
            assert placeholder==bool(candidate['generation_error'])
            if not placeholder:assert actual_cases==score['cases'] and sum(r['pass'] for r in actual_results)==score['passed']
            splits[split]={'assigned_case_count':score['cases'],'strategy_score_passed_count':score['passed'],
                'scoring_placeholder_for_generation_failure':placeholder,
                'actual_behavior_case_evaluations':actual_cases,
                'actual_behavior_passed':None if placeholder else score['passed'],
                'conditional_behavior_fraction':None if placeholder else {'numerator':score['passed'],'denominator':actual_cases},
                'main_whole_task_Y':int(candidate['all_pass'])}
        rows.append({'task_id':candidate['task_id'],'arm':arm,'predefined_task_denominator':1,'main_whole_task_Y':int(candidate['all_pass']),
            'candidate_saved':candidate_saved,'behavior_scored_candidate_count':int(candidate_saved),
            'result_status':'strategy_failed_before_candidate' if candidate['generation_error'] else 'behavior_scored_candidate_failed',
            'generation_error':candidate['generation_error'],'stage_requests_observed':stages,
            'helper_plan_text_exists':(prior/'candidates'/candidate['task_id']/arm/'plan.json').exists(),
            'actual_generated_plan_state_graph':'unknown_not_none' if not candidate_saved else '本阶段未分析，不能由存在代码就补标签',
            'splits':splits,'actual_total_tokens':candidate['total_token_spend'],'budget_limit':candidate['budget_limit'],
            'cost_status':candidate['cost_status'],'API_calls_saved':candidate['api_calls']})
    assert [r['main_whole_task_Y'] for r in rows]==[0,0]
    assert [sum(s['actual_behavior_case_evaluations'] for s in r['splits'].values()) for r in rows]==[14,0]
    diagnosis={'primary_estimand':'全部预定题上的策略整题全部通过，生成失败仍Y=0，不因无代码而排除',
        'conditional_estimand':'仅达到行为评分的候选；M2覆盖0/1时不可定义行为准确率，不与主方法指标混用',
        'plan_observation':'计划文本是提出方案，不是完成实现；实际共享状态图或局部正确性不可由缺程序编码none',
        'causal_limit':'不估计入口放宽/补entry后的反事实正确性；M0与M2观察阶段不同，不归因哪项结构造成效果',
        'original_primary_outcome_changed':False,'original_cost_changed':False,'scope':'一对工程烟测，非正式效应或适用边界确认'}
    for name,item in [('arm_observation_records.json',rows),('estimand_and_missingness_review.json',diagnosis),('input_sources.json',source_hashes)]:
        (out/name).write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding='utf-8')
    result={'status':'pass','predefined_tasks_per_arm':1,'main_all_pass_per_arm':{'M0':0,'M2':0},
        'behavior_scored_candidates_per_arm':{r['arm']:r['behavior_scored_candidate_count'] for r in rows},
        'actual_behavior_case_evaluations':{r['arm']:sum(s['actual_behavior_case_evaluations'] for s in r['splits'].values()) for r in rows},
        'generation_failure_placeholder_case_slots':{r['arm']:sum(s['assigned_case_count'] for s in r['splits'].values() if s['scoring_placeholder_for_generation_failure']) for r in rows},
        'actual_tokens_per_arm':{r['arm']:r['actual_total_tokens'] for r in rows},
        'model_calls':0,'API_calls':0,'new_task_scores':0,'human_reviewers':0,'script_sha256':sha(Path(__file__)),
        'finding':'两臂主策略0/1，但实际行为观察14对0；M2零passed是主计分占位，非已测逐例语义准确率0%',
        'limits':'只读一对烟测，无新效果或反事实；保持失败主分母，条件分母不替换预定分母'}
    (out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
