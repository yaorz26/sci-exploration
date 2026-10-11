"""用保存关系检验复核单位；逻辑构造不冒充人类标注或κ。"""
import copy
import hashlib
import json
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


UNIT_FIELDS = ('task_id', 'history_domain', 'entity_fields', 'equivalence',
               'partition', 'observer', 'quantifier', 'domain')


def compare(left, right):
    # 这是两个已明确定义案例的口径演示，不能验证任意自由文本的语义。
    for record in (left, right):
        if record['task_id'] == 'E_M06' and record['domain']['mode'] == 'casefold' and record['equivalence'] != 'str.casefold':
            return 'contract_incompatible_entity'
        if record['quantifier'] == 'exists_in_contract_domain' and record['judgment'] == 'no' and record['support'] == 'finite_no_witness':
            return 'unsupported_universal_negative'
    if any(left[f] != right[f] for f in UNIT_FIELDS):
        return 'different_measurement_units'
    if 'unknown' in (left['judgment'], right['judgment']):
        return 'contains_unknown'
    if left['judgment'] == 'not_applicable' or right['judgment'] == 'not_applicable':
        return 'applicability_agreement' if left['judgment'] == right['judgment'] else 'applicability_disagreement'
    return 'same_unit_agreement' if left['judgment'] == right['judgment'] else 'same_unit_disagreement'


def main():
    root = Path(__file__).resolve().parents[2]
    out = root/'experiments/d1_granularity_review_v2_20261008'
    out.mkdir(exist_ok=False)
    if (out/'review_summary.json').exists():
        raise FileExistsError('禁止覆盖既有研究输出')
    extraction = root/'experiments/d1_granularity_review_v1_20261008/evidence_extraction.json'
    data = json.loads(extraction.read_text(encoding='utf-8'))
    coarse, fine = data['existing_C04_relations']
    canonical = data['existing_canonical_key_relation'][0]
    assert coarse['probe_id'] == 'different_instance' and coarse['actual_relation'] == 'equal'
    assert fine['probe_id'] == 'same_instance_different_key' and fine['actual_relation'] == 'different'
    assert canonical['actual_relation'] == 'different'
    instance = {'task_id':'D1_C04', 'history_domain':'operation_history', 'entity_fields':['instance'],
                'equivalence':'identity', 'partition':'per_instance_cache', 'observer':'target_final_call_computation_increment',
                'quantifier':'within_declared_probe_pair', 'domain':{'capacity':1, 'instances':['a','b'], 'x_values':[1,2]},
                'evidence_ref':coarse['probe_id'],
                'judgment':'no', 'support':'finite_no_witness', 'evidence_relation':[coarse['left_projection'],coarse['right_projection']]}
    call_key = {**copy.deepcopy(instance), 'entity_fields':['instance','x'], 'partition':'shared_cache_within_instance',
                'evidence_ref':fine['probe_id'], 'judgment':'yes', 'support':'counterexample',
                'evidence_relation':[fine['left_projection'],fine['right_projection']]}
    normalized = {'task_id':'E_M06','history_domain':'input_item_sequence','entity_fields':['key'],
                  'equivalence':'str.casefold','partition':'normalized_key_class','observer':'target_class_first_record',
                  'quantifier':'within_declared_probe_pair','domain':{'mode':'casefold','raw_keys':['a','A']},
                  'evidence_ref':canonical['id'], 'judgment':'not_applicable','support':'counterexample',
                  'evidence_relation':[canonical['left_projection'],canonical['right_projection']]}
    naive_spelling = {**copy.deepcopy(normalized),'equivalence':'identity','judgment':'yes'}
    examples = [
        {'case_id':'C04_valid_grains', 'descriptions':[instance,call_key],
         'flat_labels_differ':instance['judgment'] != call_key['judgment'],
         'unit_aware_result':compare(instance,call_key),
         'implication':'两个已保存问题单位不同，扁平标签差不能自动判断谁误判；有限观察不等于全域不干扰'},
        {'case_id':'E_M06_invalid_raw_equivalence','descriptions':[normalized,naive_spelling],
         'flat_labels_differ':normalized['judgment'] != naive_spelling['judgment'],
         'unit_aware_result':compare(normalized,naive_spelling),
         'implication':'粒度不同也可能违反公开等价规则，不能一律当作合法选择并排除分歧'},
    ]
    wrong_judgment = {**copy.deepcopy(instance),'judgment':'yes','support':'claimed_counterexample'}
    wrong_observer = {**copy.deepcopy(instance),'observer':'all_instances_aggregate_computations'}
    unknown = {**copy.deepcopy(instance),'judgment':'unknown','support':'unassessed'}
    universal = {**copy.deepcopy(instance),'quantifier':'exists_in_contract_domain'}
    other_evidence = {**copy.deepcopy(instance),'evidence_ref':'另一证据编号，仅检验比较口径、不证明该证据有效'}
    paths = [
        ('same_unit',instance,copy.deepcopy(instance),'same_unit_agreement'),
        ('valid_different_grains',instance,call_key,'different_measurement_units'),
        ('same_unit_opposite_judgment',instance,wrong_judgment,'same_unit_disagreement'),
        ('different_observer',instance,wrong_observer,'different_measurement_units'),
        ('unknown_retained',instance,unknown,'contains_unknown'),
        ('wrong_contract_equivalence',normalized,naive_spelling,'contract_incompatible_entity'),
        ('finite_absence_not_universal',universal,copy.deepcopy(universal),'unsupported_universal_negative'),
        ('same_unit_different_evidence_id',instance,other_evidence,'same_unit_agreement'),
    ]
    cases = [{'id':name,'left':a,'right':b,'expected':expected,'actual':compare(a,b),
              'pass':compare(a,b)==expected,'kind':'助手构造的口径分支演示，非人类一致性'} for name,a,b,expected in paths]
    categories = {label:sum(c['actual']==label for c in cases) for label in sorted({c['actual'] for c in cases})}
    assert sum(categories.values()) == len(cases) and all(c['pass'] for c in cases)
    schema = {'schema_version':'candidate_0.3_unit_definition','required_unit_fields':list(UNIT_FIELDS),
              'judgments':['yes','no','unknown','not_applicable'],
              'evidence_strength':['counterexample','finite_no_witness','contract_argument','unassessed'],
              'quantifiers':['exists_in_contract_domain','within_declared_probe_pair','within_declared_finite_domain'],
              'reporting':['预定题目及问题单位总分母','两人粒度选择与等价规则分布','单位不匹配/未知/不适用/契约不兼容数',
                           '所有预定单位的原始判断表和分歧理由','同一预先规定单位上的一致率和κ，unknown按登记类别保留',
                           '若另报明确判断子集一致率，同时报其分子分母和覆盖，不能替代总体'],
              'semantic_checks':'字段相同只表示形式同单位；需人工复核字段含义，不能验证任意自由文本正确性',
              'usage':'管理端候选协议，不替换原v0.2、旧审查员ZIP、旧κ；真实人工仍0'}
    schema['evidence_ref_not_unit'] = '不同反例/文件编号不改变所问属性；引用存在性与证据有效性另审查'
    summary = {'status':'measurement_unit_refinement_supported','evidence_cases':len(examples),'saved_relations_used':3,
               'logical_paths':len(cases),'logical_paths_passed':sum(c['pass'] for c in cases),'path_counts':categories,
               'human_reviewers':0,'model_calls':0,'API_calls':0,'new_task_evaluations':0,'kappa_computed':False,
               'evidence_extraction_sha256':sha(extraction),'script_sha256':sha(Path(__file__)),
               'finding':'先核对合法实体/观察/量词/范围，再区分单位选择与同问题判断分歧；不能一律排除粒度分歧或把有限无反例写全域无干扰',
               'second_pass_revision':'v1将probe_id混入问题单位domain会误排不同证据的同一属性比较；v2移到evidence_ref。规范键反例的跨实体比较标不适用，不用无干扰替代。v1输出保留。',
               'limits':'两个已有案例与八条助手逻辑路径；路径通过仅程序口径自检，不是人类一致性数据、通用语义校验器或模型效应'}
    for name,value in [('measurement_unit_examples.json',examples),('logical_path_review.json',cases),
                       ('candidate_annotation_schema.json',schema),('review_summary.json',summary)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':
    main()
