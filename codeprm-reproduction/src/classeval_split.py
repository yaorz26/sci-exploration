"""ClassEval 公开/私有测试切分工具（WP3/WP4A 共用）。

规则（预注册）：
- 按 `methods_info` 的方法顺序，前 ⌈n/2⌉ 个方法对应的测试类为**公开**，其余为**私有**；
- 无法映射到任何方法的测试类一律归入**私有**（保守，避免泄漏）；
- 若公开部分为空（无任何测试类被映射），标记 `public_available=False`——此时"公开测试选择"规则不可用；
- 头部（imports 等）与尾部（类定义之外的代码）在所有切分中保留，避免破坏语法或用例依赖。

2026-09-29 修复记录：初版在拼接时漏了换行，导致 `import unittestclass X(...)` 语法错误
（ClassEval_49 因此失败）；另初版未处理"公开部分为空"的情况（ClassEval_69 跑出 0 个用例）。
"""
import re


def _split_blocks(test_code: str):
    """返回 (头部, 类块列表, 尾部)。头部=第一个 class 之前；尾部=最后一个类的末尾之后没有独立块。"""
    m = re.search(r"\n(?=class\s)", test_code)
    if not m:
        return test_code, [], ""
    cut = m.start()
    header = test_code[:cut]
    body = test_code[cut + 1:]
    blocks = re.split(r"\n(?=class\s)", body)
    return header, blocks, ""


def _class_name(chunk: str) -> str:
    mm = re.search(r"class\s+([A-Za-z_][\w]*)\s*\(", chunk)
    return mm.group(1) if mm else ""


def split_public_private(test_code: str, methods_info):
    """返回 dict：public_tests / private_tests / public_available / public_classes / private_classes。"""
    header, blocks, _ = _split_blocks(test_code)
    if not blocks:
        return {
            "public_tests": test_code,
            "private_tests": "",
            "public_available": True,
            "public_classes": [],
            "private_classes": [],
            "mode": "no_class",
        }
    half = (len(methods_info) + 1) // 2
    public_names = {mi.get("test_class") for mi in methods_info[:half] if mi.get("test_class")}
    pub = [b for b in blocks if _class_name(b) in public_names]
    priv = [b for b in blocks if _class_name(b) not in public_names]
    pub_text = (header + "\n" + "\n".join(pub)).rstrip() if pub else ""
    priv_text = (header + "\n" + "\n".join(priv)).rstrip() if priv else ""
    # 公开/私有两侧都必须真的含测试方法（`def test_`），否则该侧的判分是空的：
    # 2026-09-29 发现 ClassEval_69 的公开部分只有一个含 setUp 的类、跑出 0 个用例。
    pub_has_tests = bool(re.search(r"\bdef test_", pub_text))
    priv_has_tests = bool(re.search(r"\bdef test_", priv_text))
    return {
        "public_tests": pub_text,
        "private_tests": priv_text,
        "public_available": bool(pub) and pub_has_tests,
        "private_available": bool(priv) and priv_has_tests,
        "public_classes": [_class_name(b) for b in pub],
        "private_classes": [_class_name(b) for b in priv],
        "mode": "by_method",
        "split_rule": "前 ceil(n/2) 个方法的测试类为公开，其余与无法映射者为私有；两侧都必须含 def test_",
    }
