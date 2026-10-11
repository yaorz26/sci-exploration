from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
REPRO = HERE.parents[1]
PROJECT = REPRO.parent
now = datetime.now(timezone.utc).isoformat()
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def write_new(path, obj):
    with path.open('x', encoding='utf-8') as output:
        json.dump(obj, output, ensure_ascii=False, indent=2)


rows = {label: json.loads((HERE / ('behavior_' + label + '.json')).read_text(encoding='utf-8'))
        for label in ('parent', 'feature', 'alternative', 'priority_omission')}
freeze = json.loads((HERE / 'freeze_before_execution.json').read_text(encoding='utf-8'))
predicted = {label: [r['passed'] for r in value['cases']] == freeze['predictions'][label]
             for label, value in rows.items()}
summary = {
    'time': now, 'macro_stage': 'G2', 'task_id': 'REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED',
    'results': {label: {'passed': value['passed'], 'total': value['total'],
                       'prediction_match': predicted[label]} for label, value in rows.items()},
    'distinct_public_scenarios': 3, 'worker_runs': 12, 'new_task_candidates': 1,
    'source_files_downloaded': 24, 'source_bytes_downloaded': 153274,
    'admission': '有限PR子范围的真实包配置连接研究候选',
    'visible_obligation': '环境来源解析后进入已有配置视图；高优先覆盖与下层回退共同决定输出',
    'organization_limit': '两个正确组织共享Loader/同助手构造，有限输入而非全域等价',
    'formal_labels': None, 'split': None, 'model_calls': 0, 'human_reviews': 0,
    'question_A_effect_measured': False, 'next_stage_question': 'G2 boltons逆序JSONL自然功能恢复；先计划三审',
}
write_new(HERE / 'stage_result.json', summary)
write_new(HERE / 'candidate' / 'task.json', {
    'task_id': summary['task_id'], 'status': 'research_pool_only',
    'official_requirement_url': 'https://github.com/beetbox/confuse/pull/142',
    'parent_commit': 'cd1db04b07db00050900d2f548baf144bb92d261',
    'feature_commit': '8c8c3df5b539ef45862a7043b31dccac3daf204a',
    'parent_workspace': 'workspaces/parent', 'requirement': 'requirement.md',
    'public_cases': 'public_cases.json', 'evaluation_entry': 'evaluate_env_source.py',
    'model_visible': ['workspaces/parent/confuse', 'workspaces/parent/LICENSE', 'requirement.md', 'public_cases.json'],
    'evaluation_only': ['workspaces/feature', 'workspaces/alternative', 'workspaces/priority_omission'],
    'formal_labels': None, 'split': None, 'human_reviews': 0,
    'contamination': 'unknown；先前K2意外暴露另存，不声称整个项目零暴露',
})
snapshots = HERE / 'state_before_checkpoint'
snapshots.mkdir()
for rel in ('.research-state/RESEARCH_PLAN.md', '.research-state/RESEARCH_TARGET.md', '.research-state/PROJECT_STATE.md'):
    shutil.copy2(REPRO / rel, snapshots / Path(rel).name)
shutil.copy2(PROJECT / 'PROJECT_MEMORY.md', snapshots / 'PROJECT_MEMORY.md')
plan = REPRO / '.research-state/RESEARCH_PLAN.md'
text = plan.read_text(encoding='utf-8')
text = text.replace('本轮总计划已审定，未开展P95或新研究实验。下一项固定为G1两已有任务的纳入条件核对：只读保存材料、45分钟内、零新增行为执行；形成G2缺口优先级后转真实功能构建。下次恢复先读本文件，不按历史P号自动接续。',
                    'G1已完成；G2的more游标重复/恢复失败No-Go已保留，PR142有限配置连接候选已完成（3场景×4组织=12worker）。当前下一项仅为G2内boltons逆序JSONL自然功能的定向恢复，先制定198号计划并顺序三审才读新功能。P95不恢复，主A生成不开启。')
text = text.replace('## 当前阶段内计划：G1（2026-10-09）', '## 历史阶段内计划：G1（2026-10-09；已完成，以下保留原审定文本）')
text += '\n## G2 PR142已完成及当前接续\n\n196号执行完成：父/合并非测试源码与MIT许可已恢复；三个公开场景×四组织共12worker，父0/3（入口缺失）、合并/独立模块各3/3、优先级遗漏2/3（冲突来源错误）。新增的是有限项目配置连接任务，不是完整PR/人工真值/模型效果；标签与split null、模型/人工0。197号有阶段/方向审查及三轮下一问题深挖，选G2内boltons逆序JSONL真实文件操作历史任务；198号必须先计划三审后执行，最多少量来源/两次恢复，不因凑来源名扩量。\n'
plan.write_text(text, encoding='utf-8')
target = REPRO / '.research-state/RESEARCH_TARGET.md'
text = target.read_text(encoding='utf-8')
pos = text.index('用户确认题目：')
text = text[:pos] + '当前恢复点：G1完成，G2-K2游标重复No-Go/污染保留；G2-K1 PR142有限项目候选完成，3公开场景/12worker，合并与独立组织各3/3、优先级遗漏2/3。下一项G2内boltons逆序JSONL官方功能恢复，先198号计划三审；不是自动扩PR142参数或恢复P95。197号为当前阶段/方向和下一问题证据入口。\n\n' + text[pos:]
target.write_text(text, encoding='utf-8')
state = REPRO / '.research-state/PROJECT_STATE.md'
text = state.read_text(encoding='utf-8').splitlines()
text[1] = '最后更新：' + now
text[2] = '状态：active（宏观G1完成，G2 PR142有限候选完成；下一G2 boltons来源问题先三审）'
text = '\n'.join(text) + '\n\n## 宏观G1/G2当前恢复点（覆盖旧当前项）\n\n' + (
    'G1只读两现有候选，无新增行为；cache物理时点/脚本文字缺口保留。G2 more游标与公开M03重复，父恢复失败；全根检索意外private/公开测试片段暴露登记，未用于构建/评分。PR142官方父/合并非测试源码153274字节/24文件；有限公开3场景×4组织12worker，父0/3入口缺失，合并/替代各3/3，优先级遗漏2/3。正式标签/split null，真实人工/模型0，主A关联未测。下一问题G2 boltons逆序JSONL，先198号三审后读来源，不恢复P95。[evidence: experiments/d1_G1_task_admission_v1_20261009/task_admission_and_gaps.json; experiments/d1_G2_more_itertools_cursor_v1_20261009/accidental_exposure.json; experiments/d1_G2_confuse_pr142_env_source_v1_20261009/stage_result.json; ../docs/week3/data-route/20261009/197_G2_env_source_result_and_next_question_audit.md]\n')
state.write_text(text, encoding='utf-8')
ledger = REPRO / '.research-state/ledger.jsonl'
events = [
    ('G1', 'phase_review', 'complete', 'G1两现有候选只读纳入条件完成；有限范围及cache交付缺口保留',
     ['experiments/d1_G1_task_admission_v1_20261009/task_admission_and_gaps.json', '../docs/week3/data-route/20261009/193_G1_admission_result_and_G2_questions.md'], '转G2具体缺口'),
    ('G2-K2', 'phase_review', 'revise', 'more游标重复M03且父/feature恢复失败No-Go；意外检索暴露保留，未用来构建/评分',
     ['experiments/d1_G2_more_itertools_cursor_v1_20261009/source_branch_disposition.json', 'experiments/d1_G2_more_itertools_cursor_v1_20261009/accidental_exposure.json', '../docs/week3/data-route/20261009/195_G2_cursor_nogo_and_next_question_audit.md'], '195号三轮深挖转G2-K1 PR142'),
    ('G2-K1-PR142', 'phase_review', 'complete', '有限项目配置连接候选完成；三场景12worker，两个组织3/3，优先级遗漏2/3',
     ['experiments/d1_G2_confuse_pr142_env_source_v1_20261009/stage_result.json', '../docs/week3/data-route/20261009/196_G2_confuse_pr142_env_source_plan.md', '../docs/week3/data-route/20261009/197_G2_env_source_result_and_next_question_audit.md'], 'G2 boltons逆序JSONL来源问题先计划三审'),
    ('G2-K1-PR142', 'direction_review', 'pass', 'K1真实非路径连接有限支持；停止参数扩量，三轮深挖后选G2非缓存文件历史问题',
     ['experiments/d1_G2_confuse_pr142_env_source_v1_20261009/freeze_before_execution.json', 'experiments/d1_G2_confuse_pr142_env_source_v1_20261009/stage_result.json', '../docs/week3/data-route/20261009/197_G2_env_source_result_and_next_question_audit.md'], '198号先三审，不能直接读新功能'),
]
with ledger.open('a', encoding='utf-8') as output:
    for index, (phase, kind, status, description, evidence, nxt) in enumerate(events):
        record = {'time': now, 'event_id': 'd1-G1-G2-checkpoint-' + stamp + '-' + str(index),
                  'kind': kind, 'phase': phase, 'stage': 'D1-' + phase, 'status': status,
                  'summary': description, 'evidence_kind': 'artifact', 'evidence': evidence,
                  'approval_required': False, 'supersedes': [], 'next': nxt,
                  'budget': 'G1行为0；PR142新增12worker/源码153274字节，模型/人工0，旧约98/100保持',
                  'uncertainty': '有限域、同助手构造/共享Loader，标签与split null，主A未测；既有暴露保留'}
        if kind == 'direction_review':
            record['decision'] = 'G2内选择非重复实际功能线索，不改题目A/宏观顺序；不能以参数/数量扩量。'
        output.write(json.dumps(record, ensure_ascii=False) + '\n')
topic = '''
## 四十一、宏观G1/G2恢复与PR142真实连接候选（2026-10-09）

G1一次只读完成：confuse PR126有限候选已有完整/替代各8/8，source-only5/8/core遗漏7/8；cache公开完整/委托5/5、报告/延迟各1/5，额外物理完成时点未充分识别，当前requirement提evaluate_timing.py但目录只有evaluate.py，缺口保留。不重跑旧例、不恢复P95。192/193号及d1_G1_task_admission_v1_20261009。

G2 K2最低成本定位否决more游标新增：原initial20公开M03已有next/peek/seek/relative_seek/elements，父/feature恢复经代理和HTTP500失败，未形成真实任务。一次全根rg误输出上游公开测试和D1_M03 private/all_tests/private_tests/curator/变异路径片段；没有继续读取或用于期望/提示/调参/模型，但相关题不再声称未见。accidental_exposure.json保存范围，原数据/分母/11/9不改。194/195号记录No-Go与三轮后续深挖转PR142。

PR142父cd1db04b07db00050900d2f548baf144bb92d261/merge8c8c3df5b539ef45862a7043b31dccac3daf204a从官方GitHub tree/blob恢复24非测试文件153274源码字节，MIT，未取测试内容。196号三审后冻结有限需求/3手算场景，Python3.13.7/PyYAML6.0.3下12隔离worker（3×4）：父0/3缺set_env；合并/父加独立env_overlay组织各3/3；仅优先级set改add的遗漏2/3，文件/环境冲突host误为file.local而应env.local，下层timeout仍7。区分来源解析与项目叠加错误；组织自由只在这有限域得到证据。同助手/同Loader非独立人类真值，全PR列表/完整YAML/reload/冲突键未纳入；set_env最高优先入口是构建者约束，正式标签/split null，模型/真实人工0。原20/307不改，仍同confuse来源，主A收益关联未测。

197号阶段/方向通过；三轮从重复/机制/资源深挖选G2内boltons逆序JSONL自然功能恢复问题，先198号三审后查现有非测试源码/CHANGELOG与官方提交。拒绝PR142参数扩量、cache时点返回和more游标重复。成功形成非缓存文件历史任务，失败限定G2可得范围后转G3，不为第三来源凑数。当前证据d1_G2_confuse_pr142_env_source_v1_20261009/stage_result.json和candidate/，旧约98/100、DLL身份、付费/训练/RL/发布红线保持。
'''
with (PROJECT / 'memory/data-route-log.md').open('a', encoding='utf-8') as output:
    output.write(topic)
with (PROJECT / 'memory/artifact-map.md').open('a', encoding='utf-8') as output:
    output.write('\n- G1/G2本次证据：192/193号纳入、194/195号游标No-Go与污染、196/197号PR142计划/结果；experiments/d1_G1_task_admission_v1_20261009/、d1_G2_more_itertools_cursor_v1_20261009/、d1_G2_confuse_pr142_env_source_v1_20261009/（官方父/merge、freeze、12worker原始结果、stage_result、candidate/）；主记忆恢复入口data-route-log§四十一。\n')
with (PROJECT / 'memory/decisions-and-next-steps.md').open('a', encoding='utf-8') as output:
    output.write('\n## 2026-10-09 G2真实任务接续\n\nG1完成，more游标重复No-Go/暴露保留。PR142有限项目配置连接候选完成：3场景×4组织12worker，合并/替代各3/3，优先级遗漏2/3；只支持有限连接义务/组织自由，模型收益未测。下一G2 boltons逆序JSONL官方历史线索先198号三审，不扩同配置参数；若不可得按宏观G3接续，不回P95。完整口径data-route-log§四十一/197号。\n')
memory = PROJECT / 'PROJECT_MEMORY.md'
text = memory.read_text(encoding='utf-8')
text = text.replace('最后更新：2026-10-09（宏观总计划顺序三审完成；P95停止自动接续，下一阶段G1）',
                    '最后更新：2026-10-09（宏观G1完成；G2 PR142有限配置连接候选完成，下一G2文件历史来源问题）')
old = next(line for line in text.splitlines() if line.startswith('- **当前研究总路线**'))
new = '- **当前研究总路线**：已审定G1→G2→G3→G4条件比较→G5；G1只读完成，G2 more游标重复M03/恢复失败No-Go及误检索private片段暴露保留。PR142有限项目配置连接任务3场景×4组织12worker，父0/3、合并/独立模块各3/3、优先级遗漏2/3。当前下一G2 boltons逆序JSONL自然功能恢复，先198号计划三审；P95不恢复/不扩配置参数，不为数量凑题。标签/split null、模型/人工0、主A收益未测，旧约98/100与DLL限制保持。详data-route-log§四十一/197号。'
text = text.replace(old, new)
memory.write_text(text, encoding='utf-8')
lines = len(text.splitlines())
write_new(HERE / 'memory_compression_check.json', {
    'time': now, 'lines': lines, 'threshold_about': 150, 'compression_needed': lines >= 150,
    'action': '当前结果详情先保存主题记忆，主记忆只替换当前入口；低于阈值无需进一步移动',
    'details_preserved': 'memory/data-route-log.md§四十一',
})
print(json.dumps({'stage_saved': True, 'worker_runs': 12, 'memory_lines': lines, 'ledger_events_added': 4}, ensure_ascii=False))
