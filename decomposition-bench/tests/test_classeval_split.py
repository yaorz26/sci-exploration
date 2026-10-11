"""`src/classeval_split.py` 的单元测试。

覆盖：基本切分、公开部分为空、无可切分类块、头部保留、以及 2026-09-29 修掉的拼接换行缺陷。
"""
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from classeval_split import split_public_private  # noqa: E402

METHODS = [
    {"method_name": "a", "test_class": "T1"},
    {"method_name": "b", "test_class": "T2"},
    {"method_name": "c", "test_class": "T3"},
    {"method_name": "d", "test_class": "T4"},
]

TEST = """import unittest

class T1(unittest.TestCase):
    def test_x(self):
        self.assertTrue(True)

class T2(unittest.TestCase):
    def test_y(self):
        self.assertTrue(True)

class T3(unittest.TestCase):
    def test_z(self):
        self.assertTrue(True)

class T4(unittest.TestCase):
    def test_w(self):
        self.assertTrue(True)
"""


def test_split_half_goes_public():
    r = split_public_private(TEST, METHODS)
    assert r["public_available"] is True
    assert r["public_classes"] == ["T1", "T2"], r["public_classes"]
    assert r["private_classes"] == ["T3", "T4"], r["private_classes"]
    assert r["public_tests"].startswith("import unittest")


def test_header_has_newline_before_first_class():
    """回归：初版漏了换行，产生 `import unittestclass T1(...)` 语法错误。"""
    r = split_public_private(TEST, METHODS)
    assert "unittestclass" not in r["public_tests"]
    assert re.search(r"import unittest\s+class T1", r["public_tests"])


def test_public_and_private_both_compile():
    r = split_public_private(TEST, METHODS)
    compile(r["public_tests"], "<public>", "exec")
    compile(r["private_tests"], "<private>", "exec")


def test_empty_public_is_flagged():
    """方法的 test_class 与测试类名对不上时，公开部分为空 → public_available=False。"""
    methods = [{"method_name": "a", "test_class": "NOT_THERE"}] * 2
    r = split_public_private(TEST, methods)
    assert r["public_available"] is False
    assert r["public_tests"] == ""
    assert len(r["private_classes"]) == 4


def test_public_without_test_methods_is_unavailable():
    """回归：ClassEval_69 的公开部分只有 setUp、没有 def test_，会跑出 0 个用例 → 判为不可用。"""
    test = """import unittest

class Base(unittest.TestCase):
    def setUp(self):
        self.x = 1

class T2(unittest.TestCase):
    def test_y(self):
        self.assertTrue(True)
"""
    methods = [{"method_name": "a", "test_class": "Base"},
               {"method_name": "b", "test_class": "T2"}]
    r = split_public_private(test, methods)
    assert r["public_available"] is False
    assert r["private_available"] is True


def test_no_class_block():
    r = split_public_private("import unittest\nassert True\n", METHODS)
    assert r["mode"] == "no_class"
    assert r["public_available"] is True
