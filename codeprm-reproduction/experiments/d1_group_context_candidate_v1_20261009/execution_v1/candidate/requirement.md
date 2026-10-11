实现solve(data)。data包含items和threshold。items是按输入順序给出的
{group,value}列表，group是字符串，value是精确int，不含bool；长度≤16，整数绝对值≤32。
threshold是[-16,64]精确整数。只要求合法域，不得改变输入。
按group首次出现顺序分组。每组取本组最小值base，对原序每个值计算normalized=value-base，
再计算total=sum(normalized)。只保留total≥threshold的组。
输出恰含groups字段，groups为保留组记录列表，每条恰含group、normalized、total。
保留重复项及组内顺序，空输入返回{"groups":[]}。内部结构、helper与执行次序自由。
这是基于公开map_reduce聚合功能的研究适配，未声称上游已有这一联合需求。
