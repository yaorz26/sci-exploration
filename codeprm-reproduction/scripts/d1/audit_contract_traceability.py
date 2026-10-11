"""六题关键条款与既存案例的作者二次对照；不能替代盲审或完整覆盖。"""
import hashlib
import json
from pathlib import Path

RULES = {
'D1_B03':[
('完整码为ESC后接一个ASCII @到Z或反斜线到下划线字符','hidden_4 hidden_5','两字节控制码及范围端点'),
('零或多个ASCII 0到?参数字符','public_1 hidden_6 hidden_7','CSI参数与中间字符'),
('一个@到~终止字符','hidden_9','无参数也可构成完整CSI'),
('不完整、不符合该形式的片段逐字保留','public_2 hidden_3 hidden_8','缺终止符或遇换行保留'),
('返回去除完整ANSI控制码后的字符串','hidden_11 hidden_12','连续完整码及完整码前的不完整片段'),
('text是字符串','hidden_1 hidden_2','空串与普通文本')],
'D1_B04':[
('按&或;分段，忽略空段','public_1 hidden_2','两种分隔及空段'),
('每段只在第一个=处切开','hidden_6','值可包含等号'),
('键和值将+解为空格、%HH按UTF-8解码','hidden_4 hidden_5','加号、百分号和Unicode'),
('保留重复键和全局顺序','public_1 hidden_3 hidden_9 hidden_13','重复、替换和删除后的顺序'),
('null只写键，空字符串写key=','public_2 hidden_7 hidden_13','无值与显式空字符串区别'),
('编码前各字符串做Unicode NFC规范化','hidden_8','pairs不规范化而编码规范化'),
('其他字符用大写%HH编码UTF-8','hidden_11 hidden_12','允许原样的ASCII集合及需编码字符'),
('编码结果再次解析时不保证还原原pairs','hidden_14 hidden_15','分号与空键null非可逆情形')],
'D1_C03':[
('kwargs排列不影响键','hidden_2','关键字顺序不应造成额外计算'),
('位置传参与关键字传参仍不同','hidden_3 hidden_5 hidden_9','传参位置、位置次序、关键词名'),
('同键命中不增加计算次数并刷新最近使用顺序','hidden_4','命中后淘汰顺序与次数'),
('clear清空但不重置计算次数','public_1 hidden_7','清空后的累计次数和重新计算'),
('capacity=0仍返回计算结果而不存','public_2 hidden_6','零容量多次计算'),
('args整数列表（默认[]）、kwargs字符串键到整数的对象（默认{}）','hidden_8','省略参数与显式空参数同键')],
'D1_C04':[
('不同实例相同x也必须各自计算','public_1 hidden_2 hidden_7','实例内复用与实例间隔离'),
('满淘汰该实例最久未用x','hidden_3 hidden_4','LRU命中刷新与淘汰后重新计算'),
('clear只清空指定实例，计数不重置','hidden_2','清空一实例后另一实例仍命中'),
('capacity=0不缓存','hidden_1 hidden_8','零容量重复调用与清空'),
('后两项分别是所有实例id到累计次数/当前缓存项数的对象','public_2 hidden_5 hidden_6','空实例、空操作和初始清空')],
'D1_C05':[
('如1、1.0、true相等','public_1 hidden_7 hidden_10','非类型敏感的Python数值相等'),
('整数、浮点数、布尔分别算不同类型','public_2 hidden_6 hidden_8','类型敏感分离整数/浮点/布尔'),
('位置参数必须长度、顺序和值相等','hidden_2 hidden_9','位置参数顺序及长度'),
('名称排列无影响','public_1 hidden_4','关键字顺序不影响等价，名称不同仍不同'),
('args与kwargs互不互换','hidden_3','位置与关键字不混同'),
('args列表（默认[]）和kwargs对象（默认{}）','hidden_11','缺失与显式空参数'),
('参数值仅字符串、有限数、布尔或null','hidden_5 hidden_12','字符串与数字不同、null/Unicode可比较')],
'D1_M05':[
('同键行仍保持输入次序','public_1 hidden_3 hidden_11','升降序下同键行稳定'),
('为true则按键降序','hidden_7 hidden_8','默认键及其他列键的降序'),
('按keys列组成的字典序键稳定排序行','hidden_4 hidden_11','多关键列的字典序'),
('非键列保持行对齐','hidden_10','非键列嵌套对象原样对齐'),
('strict=true且长度不齐则引发ValueError','public_2 hidden_9','严格长度异常'),
('各列先截到最短长度','hidden_5','非严格模式截短'),
('没有任何行时返回[]','hidden_1 hidden_6','一列空或最短列空')]
}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    root=Path(__file__).resolve().parents[2]
    dataset=root/'data/processed/d1_project_initial20_v5_20261008'
    out=root/'experiments/d1_contract_traceability6_v1_20261008';out.mkdir(exist_ok=False)
    rows=[]
    for tid,rules in RULES.items():
        task_path=dataset/'public'/tid/'task.json'; cases_path=dataset/'private'/tid/'all_tests.json'
        task=json.loads(task_path.read_text(encoding='utf-8')); cases=json.loads(cases_path.read_text(encoding='utf-8'))
        by_id={c['case_id']:c for c in cases}
        for i,(excerpt,ids,reason) in enumerate(rules,1):
            assert excerpt in task['requirement'],(tid,excerpt)
            anchors=[by_id[cid] for cid in ids.split()]
            rows.append({'task_id':tid,'rule_id':f'{tid}-R{i:02d}','requirement_excerpt':excerpt,
                         'requirement_task_sha256':sha(task_path),'all_tests_sha256':sha(cases_path),
                         'evidence_cases':anchors,'author_rationale':reason,
                         'evidence_status':'当前助手按题面对照已存输入与期望；同一作者非独立语义复核'})
    report={'status':'linked','task_count':len(RULES),'rule_count':len(rows),
            'scope':'6题关键条款对照，不是20题全部条款、覆盖率或独立人工真值；规则关联不意味着所有分支已测',
            'full_behavior_coverage_assessed':False,'model_calls':0,'human_review_count':0,
            'discovered_blocking_requirement_contradictions':[],
            'judgment':'这些条款的所列输入与期望未见明显矛盾；其余条款与任务尚未在本次做完整语义审查',
            'rows':rows}
    (out/'traceability_private.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 六题关键行为条款与测试证据（管理端）','',report['scope'],'',
           '| 任务 | 条款原文 | 案例 | 对照理由 |','| --- | --- | --- | --- |']
    for r in rows:
        lines.append('| '+r['task_id']+' | '+r['requirement_excerpt']+' | '+', '.join(c['case_id'] for c in r['evidence_cases'])+' | '+r['author_rationale']+' |')
    lines+=['','这里只索引已有案例。没有新增数据集案例或模型成绩；包含隐藏案例标识，仅供管理端。','',
            '结构标签中的yes/partial/no仍是作者初标，不能因这些索引存在就升级为可靠标注。真实双审包不加入此材料。']
    (out/'traceability_private.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},ensure_ascii=False))

if __name__=='__main__':main()
