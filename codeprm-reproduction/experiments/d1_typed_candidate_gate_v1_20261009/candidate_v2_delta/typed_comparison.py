"""E_B09候选v2增量；复制原比较函数，仅本候选使用数字类型保持。"""

def json_equal(left, right, strict_numbers=False, ordered_objects=False):
    """布尔与数值分开；普通JSON数值允许1与1.0相等。输入不变检查更严格。"""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if type(left) in (int, float) and type(right) in (int, float):
        return (not strict_numbers or type(left) is type(right)) and left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(json_equal(a, b, strict_numbers, ordered_objects) for a, b in zip(left, right))
    if isinstance(left, dict):
        keys_match = list(left) == list(right) if ordered_objects else left.keys() == right.keys()
        return keys_match and all(json_equal(left[key], right[key], strict_numbers, ordered_objects) for key in left)
    return left == right

def accept_output(observed, expected):
    return (type(observed) is dict and set(observed) == {"count", "mode"}
            and type(observed["count"]) is int
            and json_equal(observed, expected, strict_numbers=True))
