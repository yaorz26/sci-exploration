"""仅保存用户中断状态；不执行研究、评测或下一问题。"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
REPO = PROJECT / 'codeprm-reproduction'
STATE = REPO / '.research-state'
now = datetime.now(timezone.utc)
stamp = now.strftime('%Y%m%dT%H%M%SZ')
out = Path(__file__).resolve().parent / f'interrupt_{stamp}'
out.mkdir(exist_ok=False)
for source in (STATE/'RESEARCH_TARGET.md', STATE/'RESEARCH_PLAN.md', STATE/'PROJECT_STATE.md', PROJECT/'PROJECT_MEMORY.md'):
    shutil.copy2(source, out / source.name)

resume = ('用户明确中断，D1研究及自动接续暂停。只读契约核对已完成：PR126直接YamlSource参数、'
          'PR142未显式调用前的自动加入、PR440默认回调有未独立观察条款；静态缺口不等于已证假通过。'
          '218号PR126最小反例计划仅完成第一轮可行性审查，第二/三轮未执行；'
          '未构造控制、未冻结/运行新行为，新增模型/行为/人工/下载均0。'
          '必须等用户明确恢复后，先完成剩余审查再决定执行；旧结果、候选与失败全部保留。')
with (out/'interrupt.json').open('x', encoding='utf-8') as h:
    json.dump({'time':now.isoformat(),'status':'paused','reason':'用户当前明确指令：中断',
               'resume_point':resume,'next_started':False,'background_research_running':False,
               'new_model_calls':0,'new_behavior_calls':0,'new_human_reviews':0,
               'plan_reviews_completed':1,'plan_reviews_remaining':2}, h, ensure_ascii=False, indent=2)

p = STATE/'PROJECT_STATE.md'
t = p.read_text(encoding='utf-8').splitlines()
t[1] = f'最后更新：{now.isoformat()}'
t[2] = '状态：paused（用户明确中断；不执行旧持续授权或自动接续，明确恢复后才继续）'
p.write_text('\n'.join(t)+'\n\n## 用户中断恢复点（覆盖旧当前项）\n\n'+resume+
             '\n[evidence: experiments/d1_G3_contract_integrity_v1_20261009/contract_observation_audit.json; '
             '../docs/week3/data-route/20261009/218_pr126_direct_entry_counterexample_plan.md]\n', encoding='utf-8')

for name in ('RESEARCH_TARGET.md','RESEARCH_PLAN.md'):
    p = STATE/name
    t = p.read_text(encoding='utf-8')
    p.write_text(t+'\n\n## 用户中断：暂停覆盖所有旧接续\n\n'+resume+'\n',encoding='utf-8')

topic = ('\n\n## 四十五、任务契约观察核对与用户中断（2026-10-09）\n\n'
         '215号问题三轮深挖、216号计划顺序三审后，限定只读核对三个有限任务及cache题面，'
         '输出contract_observation_audit.json。首脚本根路径错误保留attempt1_failure.json，仅修路径后完成。'
         'PR126直接YamlSource新增参数及relative_to、PR142显式set_env前的自动加入、PR440默认key/value回调'
         '没有独立观察；set_file间接执行YamlSource，不能说该类完全未执行。固定公开API不等于固定内部helper。'
         '这是支撑性静态核对，非已证误收/全域完备/模型效果；模型/行为/下载/人工0，标签split null。\n\n'
         '217号三轮接续深挖选择PR126直接API遗漏反例；218号只完成第一轮可行性审查时用户中断。'
         '新目录仅含草案及第一轮版本，没有反例工作区、冻结或行为结果。研究状态paused，'
         '等待用户明确恢复；不继续第二/三轮、不启动新问题。恢复先完成剩余计划审查。\n')
with (PROJECT/'memory/data-route-log.md').open('a',encoding='utf-8') as h: h.write(topic)
with (PROJECT/'memory/decisions-and-next-steps.md').open('a',encoding='utf-8') as h:
    h.write('\n\n## 2026-10-09用户中断（最新状态）\n\n'+resume+' 证据见data-route-log§四十五。\n')
with (PROJECT/'memory/artifact-map.md').open('a',encoding='utf-8') as h:
    h.write('\n- 契约核对与暂停：215—218号报告；experiments/d1_G3_contract_integrity_v1_20261009/'
            '{contract_observation_audit.json,attempt1_failure.json,plan_v*.md,interrupt_'+stamp+'/}；'
            'd1_G3_pr126_entry_gap_v1_20261009仅plan_v0/plan_v1，无新行为结果。详data-route-log§四十五。\n')
main = PROJECT/'PROJECT_MEMORY.md'
text = main.read_text(encoding='utf-8')
text = text.replace('## 当前状态（2026-10-09；D1研究持续接续）','## 当前状态（2026-10-09；用户中断，D1暂停）')
lines = text.splitlines()
lines[2] = '最后更新：2026-10-09（用户明确中断；已保存恢复点，等待明确恢复）'
header = lines.index('## 当前状态（2026-10-09；用户中断，D1暂停）')
lines.insert(header+2, '- **最新中断状态**：用户明确“中断”，研究及自动接续暂停。契约静态核对已保存但不算已证反例；218号仅首轮可行性审查，后二轮未执行，无新控制/行为/模型。恢复须用户明确授权，再完成审查；详data-route-log§四十五。')
main.write_text('\n'.join(lines)+'\n',encoding='utf-8')
count = len(main.read_text(encoding='utf-8').splitlines())
if count >= 150:
    raise RuntimeError('主记忆达到阈值，需要先保留细节再压缩；暂停研究不影响记忆保存')
with (out/'memory_compression_check.json').open('x',encoding='utf-8') as h:
    json.dump({'main_memory_lines':count,'threshold_approx':150,'compression_required':False,
               'detail_saved':'memory/data-route-log.md§四十五','reason':'低于阈值；研究结果、用户纠正和旧红线未删除'},h,ensure_ascii=False,indent=2)
with (STATE/'ledger.jsonl').open('a',encoding='utf-8') as h:
    event={'time':now.isoformat(),'event_id':f'd1-user-interrupt-{stamp}','kind':'decision',
           'stage':'D1-G3-contract-integrity','phase':'user_interrupt','status':'paused',
           'summary':resume,'decision':'当前用户中断覆盖所有旧持续授权；明确恢复前不得继续研究。',
           'evidence_kind':'artifact','evidence':[
               'experiments/d1_G3_contract_integrity_v1_20261009/contract_observation_audit.json',
               f'experiments/d1_G3_contract_integrity_v1_20261009/interrupt_{stamp}/interrupt.json',
               '../docs/week3/data-route/20261009/218_pr126_direct_entry_counterexample_plan.md'],
           'approval_required':False,'supersedes':[],
           'budget':'本轮模型/行为/下载/人工0；旧约98/100及全部权限边界保持',
           'uncertainty':'静态未观察不等于假通过；PR126反例未构造、未冻结、未执行',
           'next':'等待用户明确恢复；218号只完成首轮，恢复后先完成剩余两轮计划审查'}
    h.write(json.dumps(event,ensure_ascii=False)+'\n')
print(json.dumps({'status':'paused','checkpoint':str(out),'main_memory_lines':count,
                  'new_behavior_calls':0,'new_model_calls':0},ensure_ascii=False))
