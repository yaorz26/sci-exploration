"""ClassEval M2 臂的"逐方法实现 → 组装成类"工具（WP6）。

背景（2026-09-29 修正）：初版组装用"跳过后续所有缩进行"的方式替换方法体，
结果把紧随其后的其它方法一并吞掉——M2 实际只实现了第一个方法，
因此 M2 的 0/24 是**工具缺陷造成的假结果**，不是方法本身失败。
本模块按"逐方法块"组装：先按缩进定位每个方法的块边界，再决定用模型的完整定义或"骨架签名+模型方法体"。

规则（预注册）：
- 模型给出含 `def <name>(` 的完整定义 → 用它，按类内缩进重新对齐；
- 模型只给出方法体 → 保留骨架里的签名与 docstring，接上模型方法体；
- 某方法完全没有生成 → 保留骨架原样（并调用方负责记录该情况）。
"""
import re

DEF_RE = re.compile(r"^(\s+)def\s+([A-Za-z_]\w*)\s*\(")


def _method_marks(lines):
    marks = []
    for idx, line in enumerate(lines):
        m = DEF_RE.match(line)
        if m:
            marks.append((idx, m.group(1), m.group(2)))
    return marks


def _docstring_end(block):
    """返回 docstring 结束在 block 内的下标；没有 docstring 时返回 -1。"""
    if len(block) < 2:
        return -1
    first = block[1].strip()
    if not (first.startswith('"""') or first.startswith("'''")):
        return -1
    quote = first[:3]
    if first.endswith(quote) and len(first) > 3:
        return 1
    for k in range(2, len(block)):
        if quote in block[k]:
            return k
    return -1


def assemble_class(skeleton: str, impls: dict) -> str:
    lines = skeleton.splitlines()
    marks = _method_marks(lines)
    if not marks:
        return skeleton

    out = list(lines[: marks[0][0]])
    for j, (idx, indent, name) in enumerate(marks):
        end = marks[j + 1][0] if j + 1 < len(marks) else len(lines)
        block = lines[idx:end]
        while block and not block[-1].strip():
            block.pop()
        impl = impls.get(name)
        if impl is None or not impl.strip():
            out.extend(block)
            out.append("")
            continue
        impl_lines = impl.splitlines()
        k = next((i for i, l in enumerate(impl_lines) if re.match(r"^\s*def\s+" + re.escape(name) + r"\s*\(", l)), None)
        if k is not None:
            body = impl_lines[k:]
            base = len(body[0]) - len(body[0].lstrip())
            out.extend([(indent + l[base:]) if l.strip() else "" for l in body])
        else:
            sig = [block[0]]
            de = _docstring_end(block)
            if de > 0:
                sig.extend(block[1: de + 1])
            out.extend(sig)
            inner = indent + "    "
            out.extend([(inner + l) if l.strip() else "" for l in impl_lines])
        out.append("")
    return "\n".join(out)


def method_def_count(source: str, names) -> dict:
    """统计组装结果里每个方法名出现的 `def` 次数（用于自检）。"""
    return {n: len(re.findall(r"\bdef\s+" + re.escape(n) + r"\s*\(", source)) for n in names}
