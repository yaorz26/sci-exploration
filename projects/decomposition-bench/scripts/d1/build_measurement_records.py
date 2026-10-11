"""保存结构证据的多层次记录与旧标签碰撞分析；零新任务求值。"""
from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[2]
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='experiments/d1_measurement_record_v2_20261008');args=parser.parse_args()
    out=root/args.output;out.mkdir(exist_ok=False)
    files={}
    def artifact(rel):
        p=root/rel;files[rel]=sha(p);return p
    manifest=read(artifact('data/processed/d1_project_initial20_v5_20261008/manifest.json'))
    old=read(artifact('experiments/d1_structure_evidence_sidecar_v1_20261008/task_evidence.json'))
    per_task={r['task_id']:r for r in old}; observed=[]
    def add(tid,pid,history,entity,equiv,observer,relation,ref,gate='正常值可观察',applicable=True,detail=None,conditions=None):
        observed.append({'record_id':tid+':'+pid,'task_id':tid,'layer':'task_behavior_observation',
            'question_unit':{'history_or_input_domain':history,'entity_definition':entity,'equivalence_rule':equiv,
                'observer':observer,'quantifier':'保存的有限输入对，不推广全域',
                'allowed_domain':'公开声明域；结论限保存有限输入对',
                'conditions':conditions},
            'measurement':{'observed_relation':relation,'projection_applicable':applicable,'outcome_gate':gate,
                'support':'有限观察/反例；相等不证明全域独立','detail':detail},
            'evidence_ref':{'artifact':ref,'record_key':pid},'human_reviewers':0})
    semantic_rel='experiments/d1_semantic_contrasts_v1_20261008/paired_probes.jsonl'
    for p in lines(artifact(semantic_rel)):
        assert p['pass']
        add(p['task_id'],p['probe_id'],'operation_history',p['entity_granularity'],'公开任务中的键/实例/调用身份',
            p['projection'],p['actual_relation'],semantic_rel,
            conditions={k:v for k,v in p['left_input'].items() if k!='operations'})
    unmeasured_rel='experiments/d1_unmeasured_task_probes_v1_20261008/paired_results.jsonl'
    for p in lines(artifact(unmeasured_rel)):
        assert p['pass']
        add(p['task_id'],p['probe_id'],p['history_domain'],p['entity_granularity'],
            ('Python调用等价，typed='+str(p['left_input'].get('typed',False)) if p['task_id']=='D1_C05' else '行/列身份，按公开keys稳定排序与最短域'),
            p['projection'],p['actual_relation'],unmeasured_rel,
            detail={'target_indexes':p['target_indexes'],'configuration_control_not_foreign_history':p['probe_id']=='typed_is_rule_control'},
            conditions={side:{k:v for k,v in p[side+'_input'].items() if k not in ('pairs','columns')} for side in ('left','right')})
    f_rel='experiments/d1_expected_rejection_v1_20261008/relation_results.json'
    f_rows=read(artifact(f_rel))
    for p in f_rows:
        if p['implementation']!='reference':continue
        assert p['pass']
        add('D1_F04',p['id'],'object_validation_input','name字段及其他字段','字段名身份','name值投影',
            p['actual_name_relation'],f_rel,gate='预期拒绝可正确，但name投影缺值' if not p['actual_name_projection_applicable'] else '正常值可观察',
            applicable=p['actual_name_projection_applicable'],detail={
                'semantic_outcome_relation':p['actual_semantic_relation'],
                'left_outcome_kind':p['left']['classification'],'right_outcome_kind':p['right']['classification'],
                'requirement_conformance':p['left']['correct'] and p['right']['correct']},
            conditions={'domain':'公开正常值及明确要求拒绝的字段类型输入','ignored_fields':'按需求忽略，不能泛化任意字段拒绝'})
    e_rel='experiments/d1_expansion_order_candidate_v1_20261008/paired_relations.json'
    for p in read(artifact(e_rel)):
        assert p['pass']
        add('E_M06',p['id'],'input_item_sequence',p['entity_granularity'],
            'mode=exact原key或mode=casefold的str.casefold类',p['projection'],p['actual_relation'],e_rel,
            applicable=True,
            detail={'foreign_entity_claim_applicable':p['id']!='raw_spelling_is_same_entity',
                    'note':'原拼写A/a是同规范类历史反例，非另一实体干扰' if p['id']=='raw_spelling_is_same_entity' else 'mode/域见保存输入'},
            conditions={'mode':p['mode']})
    support=read(artifact('experiments/d1_expansion_support_v1_20261008/encoding_frozen.json'))
    pair=support['evidence']['cache_fixed_capacity_saved_contrast']
    add('E_B07','same_capacity_saved_eviction','operation_history','key','字符串键身份','最后read(a)结果',
        'different','experiments/d1_expansion_support_v1_20261008/encoding_frozen.json',
        detail={'policy':'LRU','capacity':1,'saved_source_lines':[pair[s]['saved_line_number'] for s in ('left','right')],
                'original_source':'experiments/d1_expansion_cache_candidate_v1_20261008/finite_sequences.jsonl'},
        conditions={'policy':'LRU','capacity':1})
    plan_rel='experiments/d1_plan_state_distribution_v1_20261008/candidate_state_profiles_frozen.json'
    profiles=read(artifact(plan_rel)); assembly_rel='experiments/d1_alignment_composition_v1_20261008/summary.json'
    assembly=read(artifact(assembly_rel)); local_rel='experiments/d1_local_composition_v1_20261008/summary.json'
    local=read(artifact(local_rel))
    plan_rows=[{'task_id':'D1_C03','layer':'particular_handwritten_plan','evidence_ref':plan_rel,
        'plan_profiles':profiles,'usage':'生成后方案描述，不能替代任务真值/随机前置分组'},
        {'task_id':'D1_B05','layer':'particular_handwritten_plan','evidence_ref':local_rel,
         'obligations':per_task['D1_B05']['plan_boundary_evidence']['obligations'],
         'usage':'数据版本/阈值/路径义务，多个合法结构非唯一标准分解'},
        {'task_id':'D1_M05','layer':'particular_handwritten_plan','evidence_ref':assembly_rel,
         'obligations':['排序索引须最终属于所有列的共同有效域','允许先限制域或先排序后过滤'],
         'saved_correct_plans':assembly['correct_plans'],'saved_finite_inputs':assembly['finite_inputs'],
         'usage':'共同域义务不等于唯一阶段顺序或共享可变状态'}]
    budget_rel='experiments/d1_valid_text_budget_v1_20261008/rows.json';budgets=read(artifact(budget_rel))
    api_rel='experiments/d1_valid_text_budget_v1_20261008/P9_saved_output_audit.json';api=read(artifact(api_rel))
    cost_layers={'constructed_prompt_scenarios':{'evidence_ref':'experiments/d1_prompt_crowding_v1_20261008/rows.json',
        'usage':'占位计划情景，不是实际生成或正确方案'},
        'given_correct_text':{'evidence_ref':budget_rel,'rows':budgets,'usage':'可见给定文本存在性，不是新API花费/生成能力'},
        'actual_API_generation_vs_visible_text':{'evidence_ref':api_rel,'saved_output_audit':api,
        'usage':'保存API计费优先，四例差异不推通用加1界'}}
    task_rows=[]
    for meta in manifest['tasks']:
        tid=meta['task_id']; selected=[r for r in observed if r['task_id']==tid]
        task_rows.append({'task_id':tid,'split':meta['split'],'repository':meta['source']['repository'],
            'function_family':meta['function_family'],'original_author_v0_2':meta['structure_v2'],
            'task_behavior_measurement':None if not selected else {'status':'有限证据，非完整测量/人工真值',
                'observation_record_ids':[r['record_id'] for r in selected]},
            'unmeasured_is_negative':False,'plan_record_refs':[i for i,r in enumerate(plan_rows) if r['task_id']==tid],
            'cost_record_scope':'真实API/给定文本/占位情景分别记录，不从成本推任务因果',
            'usage':'管理端附件，不输入模型，不替换原作者标签或盲审ZIP'})
    candidate_rows=[]
    for directory in ('d1_expansion_cache_candidate_v1_20261008','d1_expansion_order_candidate_v1_20261008'):
        ref='experiments/'+directory+'/task_contract.json';contract=read(artifact(ref));tid=contract['task_id']
        candidate_rows.append({'task_id':tid,'split':contract['split'],'original_dataset_member':False,
            'source':contract['source'],'contract_ref':ref,'related_tasks':contract['related_tasks'],
            'observation_record_ids':[r['record_id'] for r in observed if r['task_id']==tid],
            'human_reviewers':0,'new_independent_family_claim':False})
    # 不是自定义测试通过即证实语义：下面比较旧公开编码能否区分保存的两种问题单位。
    groups=defaultdict(list)
    for row in task_rows:
        label=row['original_author_v0_2'];signature=[label[k] for k in ('cross_operation_state','state_scope','separate_behavior_testability')]
        signature.append(label['behavior_dependencies']);groups[json.dumps(signature,sort_keys=True)].append(row['task_id'])
    old_collisions=[{'label_signature':json.loads(k),'task_ids':ids} for k,ids in groups.items() if len(ids)>1]
    m=next(r for r in task_rows if r['task_id']=='D1_M05');f=next(r for r in task_rows if r['task_id']=='D1_F04')
    def coarse(row):return {k:row['original_author_v0_2'][k] for k in ('cross_operation_state','state_scope','separate_behavior_testability','behavior_dependencies')}
    assert coarse(m)==coarse(f)
    claims=[
        {'case':'C04两个合法粒度','old_label_unique':True,'observed_distinction':'实例隔离相等；实例内不同x淘汰不同',
         'record_ids':['D1_C04:different_instance','D1_C04:same_instance_different_key'],
         'needed_context':['entity_definition','observer','finite_domain'],'not_a_label_error':True},
        {'case':'C03任务与方案状态','task_id':'D1_C03','saved_helper_shared_state':[p['persistent_mutable_state_shared_between_helpers'] for p in profiles],
         'needed_context':['layer','particular_plan','state_holders'],'not_a_task_label_rewrite':True},
        {'case':'M05与F04旧编码相同但义务不同','same_old_coded_signature':coarse(m),
         'record_ids':['D1_M05:short_foreign_column_domain','D1_F04:invalid_scores_blocks_whole_output'],
         'observed_distinction':'共同有效行域与整题拒绝使局部字段不可观察','not_a_testability_yes_disproof':True,
         'needed_context':['input_domain','outcome_kind','projection_applicable']},
        {'case':'B05不同合法方案/变换版本','plan_record_task':'D1_B05','needed_context':['plan_connection','data_version'],
         'not_a_unique_decomposition':True},
        {'case':'casefold原拼写','record_ids':['E_M06:raw_spelling_is_same_entity'],
         'needed_context':['equivalence_rule','foreign_entity_claim_applicable'],'not_a_foreign_entity_witness':True},
        {'case':'错误程序相等关系','evidence_ref':'experiments/d1_relation_vacuity_v1_20261008/summary.json',
         'needed_context':['behavior_conformance','execution_validity','relation'],'not_a_model_score':True},
        {'case':'预算三层','needed_context':list(cost_layers),'not_a_model_ability_proof':True},
        {'case':'未测任务','task_ids':[r['task_id'] for r in task_rows if r['task_behavior_measurement'] is None],
         'needed_context':['null_unmeasured','plan_only_evidence_not_behavior_measurement'],'not_negative':True},
        {'case':'来源出现0','evidence_ref':'experiments/d1_expansion_support_v1_20261008/summary.json',
         'needed_context':['registered_evidence_zero_not_semantic_absence','history_domain','family_links']}]
    challenge={'status':'可表达保存反例，尚无独立语义可靠性验证','cases':claims,'old_label_collisions':old_collisions,
        'limits':'旧标签有文字证据，并非完全不含细节；此分析只排除以几个编码字段代替具体问题/方案/域的做法，不证明最小维数或一项二元补充不可能',
        'human_reviewers':0,'kappa_computed':False}
    # 证据文件重新散列只为本次新附件来源，不重复执行旧功能/评分/校准。
    for rel in ('experiments/d1_relation_vacuity_v1_20261008/summary.json',
                'experiments/d1_expansion_support_v1_20261008/summary.json',
                'experiments/d1_prompt_crowding_v1_20261008/rows.json'):
        artifact(rel)
    artifact('experiments/d1_measurement_record_v1_20261008/evidence_sources_extracted.json')
    for r in read(root/'experiments/d1_measurement_record_v1_20261008/evidence_sources_extracted.json'):
        assert sha(root/r['evidence_path'])==r['sha256'];artifact(r['evidence_path'])
    metadata={'schema_kind':'多层次候选证据记录，非新标签真值','layers':['task_behavior_observation','particular_handwritten_plan','method_cost'],
        'unit_fields':['history_or_input_domain','entity_definition','equivalence_rule','observer','quantifier','allowed_domain','conditions'],
        'evidence_ref_is_not_question_unit':True,'task_rows':20,'candidate_rows_separate':2,'human_reviewers':0,
        'original_author_labels_changed':False,'original_split_changed':False,'model_input_allowed':False,
        'unknown_policy':'未测null；不适用/不可观察不是无依赖；有限相等不是普遍独立',
        'v1_correction':'E_M06同规范实体关系的跨实体问题不适用，但目标记录投影仍可观察，v2分别登记；v1保留',
        'input_hashes':files,'script_sha256':sha(Path(__file__))}
    summary={'status':'candidate_multilevel_records','original_tasks':20,'behavior_evidence_tasks':sum(r['task_behavior_measurement'] is not None for r in task_rows),
        'behavior_unmeasured_tasks':sum(r['task_behavior_measurement'] is None for r in task_rows),
        'candidate_pool_separate':2,'observation_records':len(observed),'plan_evidence_tasks':len(plan_rows),
        'discriminating_cases':len(claims),'old_coded_signature_collision_groups':len(old_collisions),
        'model_calls':0,'API_calls':0,'task_calls':0,'human_reviewers':0,'kappa_computed':False,
        'finding':'保留旧编码同时表达不同问题单位、任务/方案/成本层与拒绝域；M05/F04编码相同不提供同一局部可观察条件',
        'limits':challenge['limits'],'script_sha256':sha(Path(__file__))}
    for name,value in [('task_records.json',task_rows),('expansion_records.json',candidate_rows),('observations.json',observed),
                       ('plan_records.json',plan_rows),('cost_layers.json',cost_layers),('discriminating_review.json',challenge),
                       ('record_schema_and_provenance.json',metadata),('summary.json',summary)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
