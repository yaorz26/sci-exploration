from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
REPRO = ROOT.parents[1]
PROJECT = REPRO.parent
now = datetime.now(timezone.utc).isoformat()
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
snap = ROOT / 'state_before_cycle_checkpoint'
snap.mkdir()
for name in ('RESEARCH_TARGET.md', 'PROJECT_STATE.md'):
    shutil.copy2(REPRO / '.research-state' / name, snap / name)
shutil.copy2(PROJECT / 'PROJECT_MEMORY.md', snap / 'PROJECT_MEMORY.md')
current = '第一轮G1—G5零模型路线已完成；两项有限confuse任务交付v2，一cache待解。208号宏观v2/局部三审完成，当前只接续PR440组生命周期一次G2扩展，先公开排重/官方父恢复；原预算继承，失败No-Go不自动搜新题。'
target = REPRO / '.research-state/RESEARCH_TARGET.md'
text = target.read_text(encoding='utf-8')
anchor = '用户确认题目：'
pos = text.index(anchor)
text = text[:pos] + '最新恢复点（覆盖旧当前项）：' + current + '\n成果data/processed/d1_actual_project_candidate_v2_20261009；宏观v2完整见RESEARCH_PLAN/208号。主A收益关联未测，正式标签/split null、人类0、模型0。\n\n' + text[pos:]
target.write_text(text, encoding='utf-8')
state = REPRO / '.research-state/PROJECT_STATE.md'
text = state.read_text(encoding='utf-8').splitlines()
text[1] = '最后更新：' + now
text[2] = '状态：active（第一轮候选成果已交付；宏观v2只开放PR440一次限定扩展）'
text = '\n'.join(text) + '\n\n## 第一轮G1—G5成果/宏观v2当前恢复点\n\n' + current + '\n'
text += 'G2新PR142三场景12worker，合并/独立组织3/3、优先级遗漏2/3；G3结构证据分层，三管理候选两来源、有限可用两项同confuse，cache強时点与脚本缺口保留，K2/K3未填。PR466官方未合并No-Go，元数据公开ioutils测试暴露保留。G4原策略一题5—6请求/两题10—12，旧约98/100/DLL/人类/冻结缺口阻止运行。G5 v1复制因research_controls缺LICENSE失败；对应官方父许可证恢复到独占v2、CLI/hash接线通过，旧语义不重跑。formal_labels/split null，真实人工0/新增模型0。[evidence: experiments/d1_G3_structure_evidence_v1_20261009/structure_records.json; experiments/d1_G4_pair_design_v1_20261009/paired_design_v2.json; experiments/d1_G5_candidate_delivery_v1_20261009/delivery_wiring_check.json; ../docs/week3/data-route/20261009/207_macro_cycle_result_and_next_question_audit.md; ../docs/week3/data-route/20261009/208_macro_extension_pr440_plan.md]\n'
state.write_text(text, encoding='utf-8')
events = [
    ('G2-boltons', 'phase_review', 'revise', 'PR466官方未合并No-Go，源码/行为0；工具导入失败限定修复和上游公开测试误暴露保留',
     ['experiments/d1_G2_boltons_stream_reuse_v1_20261009/official_pr_metadata.json', 'experiments/d1_G2_boltons_reverse_jsonl_v1_20261009/accidental_public_test_exposure.json', '../docs/week3/data-route/20261009/201_G2_close_and_G3_question_audit.md']),
    ('G3', 'phase_review', 'complete', '三候选结构证据完成；两有限/一待解，任务/接口/组织/观察分层，来源机制共变保留',
     ['experiments/d1_G3_structure_evidence_v1_20261009/structure_records.json', '../docs/week3/data-route/20261009/203_G3_structure_result_and_G4_question_audit.md']),
    ('G4-design', 'phase_review', 'complete', '具体配对设计/下界完成；一题最低5—6调用，旧剩约2不够，未生成',
     ['experiments/d1_G4_pair_design_v1_20261009/paired_design_v2.json', 'experiments/d1_G4_pair_design_v1_20261009/resource_boundary.md', '../docs/week3/data-route/20261009/205_G4_result_and_G5_question_audit.md']),
    ('G5', 'phase_review', 'complete', '两有限真实任务一次交付v2；一待解，许可证复制失败保留一次修复，接线不重评',
     ['data/processed/d1_actual_project_candidate_v2_20261009/README.md', 'experiments/d1_G5_candidate_delivery_v1_20261009/delivery_v1_failure.json', 'experiments/d1_G5_candidate_delivery_v1_20261009/delivery_wiring_check.json']),
    ('macro-v2-PR440', 'direction_review', 'pass', '207号三轮深挖/208号宏观及局部三审后一次限定PR440扩展；继承预算，不重包旧成果',
     ['.research-state/RESEARCH_PLAN.md', '../docs/week3/data-route/20261009/207_macro_cycle_result_and_next_question_audit.md', '../docs/week3/data-route/20261009/208_macro_extension_pr440_plan.md']),
    ('G2-PR440', 'phase_contract', 'running', '已审定宏观v2/局部计划，现在只公开排重和必要官方父恢复，成功才冻结行为',
     ['.research-state/RESEARCH_PLAN.md', '../docs/week3/data-route/20261009/208_macro_extension_pr440_plan.md']),
]
with (REPRO / '.research-state/ledger.jsonl').open('a', encoding='utf-8') as output:
    for index, (phase, kind, status, summary, evidence) in enumerate(events):
        event = {'time': now, 'event_id': 'd1-cycle-completion-' + stamp + '-' + str(index),
                 'kind': kind, 'phase': phase, 'stage': 'D1-' + phase, 'status': status,
                 'summary': summary, 'evidence_kind': 'artifact', 'evidence': evidence,
                 'approval_required': False, 'supersedes': [],
                 'budget': '第一轮新增模型/人类0；PR142新增12worker；原约98/100、200MiB及G2上限继承',
                 'uncertainty': '有限域/同助手控制，正式标签null，污染/暴露保留，主A收益未测',
                 'next': '宏观v2 PR440一次自然生命周期任务扩展，先排重/父恢复，失败No-Go'}
        if kind == 'direction_review':
            event['decision'] = '已完成第一轮G1—G5；在已确认题目A/四来源/原上限内只扩展一个PR440具体未知，不自动搜题或增加模型。'
        output.write(json.dumps(event, ensure_ascii=False) + '\n')
topic = '''
## 四十二、首轮宏观成果完成与PR440限定接续（2026-10-09）

G2 boltons逆序来源查得自然生命周期PR466但官方merged=false/merged_at null，不按非空merge_commit_sha造合并版本；实际API一次、行为0。工具v1 requests缺依赖在网络前失败，v2 urllib一次修复保留；首判时完整读取旧boltons_commit_metadata误输出PR513无关ioutils公开测试补丁，不用于任务/期望/模型，暴露记录保留，与M03私有片段事件分开。198—201号/d1_G2_boltons_*。

G3一次只读结构构造：三管理候选/两来源，有限可用两confuse同配置家族、cache强时点与脚本缺口待解；K2真实非缓存历史/K3独立用途仍未满足。结构分任务义务/公开接口条件/内部组织/可测机会/观察条件，PR126单模块8/8不规定唯一次序；PR142连接优先级遗漏2/3不同于解析成功；cache合法委托5/5不要求外层基类容器，len/currsize补清理不能证先前物理时点。模型/行为新调用0，formal_labels/split null，人类0。202/203号，d1_G3_structure_evidence_v1_20261009。

G4设计原M0+M2一题seed最低5—6请求、有限两题10—12，B6500示例上限26000token（非费用/实际用量，另需校准烟测）；旧剩约2、DLL身份、人类/正式冻结不足，模型0。项目M2适配/父上下文尚未正式验证，不以补丁入口或给定patch补A；正式结构因果不估计。design原candidate_scope资格字段过强，v2改有限行为候选，原文件保留。204/205号/d1_G4_pair_design_v1_20261009。

G5成果data/processed/d1_actual_project_candidate_v2_20261009：两个有限包任务confusePR126/PR142可调用评价，cachepending保原条款；public父/需求与evaluation参考/替代/缺陷/旧结果分开，MIT保留，单一run_evaluation.py。v1因旧research_controls无LICENSE复制失败保留；唯一修复以官方同父LICENSE补入另v2目录，父源码hash一致/CLI列表与交付hash接线0差、新行为0。不声称新重评/跨平台/人工盲审/正式冻结/发布；目录是支撑，新实质结果仍PR142十二worker与结构边界。原20/307/11/9不改。206/207号/d1_G5_candidate_delivery_v1_20261009。

首轮G1—G5完成但按用户持续要求继续：207号三轮深挖识别已保存真实merged=true的more PR440（2020-07-02，78405e9b24d0ccdd67785136ecd56774f38ae95e）groupfunc处理懒组生命周期，备选PR196 map_reduce因旧P76同族重复风险暂否决。208号宏观v2受影响阶段/局部计划已依次三审，当前只做一次G2 PR440公开排重/官方父恢复，成功才最多3场景×4组织12worker、G3/G4增量/G5登记不重包；失败No-Go不自动搜新题。原8调查/4新增/规模6/G2六小时/200MiB继承不重置；题目A与模型/人类/付费/训练/RL/发布红线不变。
'''
with (PROJECT / 'memory/data-route-log.md').open('a', encoding='utf-8') as output:
    output.write(topic)
with (PROJECT / 'memory/artifact-map.md').open('a', encoding='utf-8') as output:
    output.write('\n- 首轮宏观成果：data/processed/d1_actual_project_candidate_v2_20261009/{README.md,manifest.json,run_evaluation.py,public/,evaluation/,pending/,evidence/}；v1部分目录及复制失败保留。198—208号：来源/暴露/No-Go、G3结构、G4设计、G5一次交付、宏观v2限定PR440；d1_G3_structure_evidence_v1_20261009/、d1_G4_pair_design_v1_20261009/、d1_G5_candidate_delivery_v1_20261009/、d1_G2_more_pr440_group_lifetime_v1_20261009/，详细口径data-route-log§四十二。\n')
with (PROJECT / 'memory/decisions-and-next-steps.md').open('a', encoding='utf-8') as output:
    output.write('\n## 2026-10-09宏观第一轮结束/限定第二轮\n\n首轮交付两项有限confuse真实任务，cache待解，主A收益未测。公开PR466未合并No-Go与暴露保留。207号三轮深挖+208号宏观/局部三审后，仅续已保存真实合并PR440组生命周期任务，先公开M题排重和父恢复；原额度继承，成功G3/G4增量/G5登记，不重复旧包/评分，失败不自动搜新题。data-route-log§四十二。\n')
memory = PROJECT / 'PROJECT_MEMORY.md'
text = memory.read_text(encoding='utf-8')
lines = text.splitlines()
lines[2] = '最后更新：2026-10-09（首轮G1—G5候选成果已交付，宏观v2限定PR440接续）'
for i, line in enumerate(lines):
    if line.startswith('- **当前研究总路线**'):
        lines[i] = '- **当前研究总路线**：首轮G1—G5完成，成果d1_actual_project_candidate_v2_20261009（两有限confuse任务/一cache待解）；PR142新增3场景×4组织12worker，合并/替代3/3、优先级遗漏2/3。G3结构分层不填正式轴，G4一题需5—6请求旧剩约2不运行。more游标重复/PR466未合并No-Go与两暴露保留。207号三轮深挖和208号宏观/局部三审后，仅续PR440组生命周期一次G2扩展，原上限继承，成功只增量、不重包/旧重评；失败不自动搜题。标签/split null、人类/模型0、主A收益未测，详data-route-log§四十二。'
text = '\n'.join(lines) + '\n'
memory.write_text(text, encoding='utf-8')
with (ROOT / 'memory_compression_check.json').open('x', encoding='utf-8') as output:
    json.dump({'time': now, 'lines': len(lines), 'threshold_about': 150,
               'compression_needed': len(lines) >= 150,
               'action': '详情先落主题，主记忆替换当前入口；135行无需进一步压缩，核心数字/负结果/纠正保留'}, output, ensure_ascii=False, indent=2)
print(json.dumps({'saved': True, 'ledger_added': len(events), 'memory_lines': len(lines), 'next': 'G2 PR440'}, ensure_ascii=False))
