"""`src/classeval_assemble.py` 的单元测试（含 2026-09-29 组装缺陷的回归用例）。"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from classeval_assemble import assemble_class, method_def_count  # noqa: E402

SKELETON = '''import math


class Demo:
    """Demo class."""

    def __init__(self):
        self.items = []

    def add(self, x):
        """
        Add x.
        :param x: number
        """
        pass

    def total(self):
        """Return sum."""
        pass
'''


def test_all_methods_survive_when_model_returns_full_defs():
    """回归：初版会把第一个方法之后的**所有方法一起吞掉**，导致 M2 只实现了一个方法。"""
    impls = {
        "__init__": "def __init__(self):\n    self.items = []",
        "add": "def add(self, x):\n    self.items.append(x)",
        "total": "def total(self):\n    return sum(self.items)",
    }
    out = assemble_class(SKELETON, impls)
    assert set(method_def_count(out, ["__init__", "add", "total"]).values()) == {1}, method_def_count(out, ["__init__", "add", "total"])
    ns = {}
    exec(compile(out, "<assembled>", "exec"), ns)
    d = ns["Demo"]()
    d.add(2)
    d.add(3)
    assert d.total() == 5


def test_body_only_output_keeps_signature_and_docstring():
    impls = {"add": "self.items.append(x)", "total": "return sum(self.items)", "__init__": "self.items = []"}
    out = assemble_class(SKELETON, impls)
    assert re.search(r"def add\(self, x\):", out)
    assert "Add x." in out  # 骨架 docstring 被保留
    ns = {}
    exec(compile(out, "<assembled>", "exec"), ns)
    d = ns["Demo"]()
    d.add(1)
    assert d.total() == 1


def test_missing_method_keeps_skeleton_block():
    out = assemble_class(SKELETON, {"add": "def add(self, x):\n    self.items.append(x)"})
    assert out.count("def total(self)") == 1
    assert "pass" in out


def test_staticmethod_decorator_is_preserved():
    sk = '''class C:
    @staticmethod
    def f(x):
        pass

    def g(self):
        return C.f(1)
'''
    out = assemble_class(sk, {"f": "return x + 1", "g": "return C.f(1)"})
    assert "@staticmethod" in out
    assert out.count("def f") == 1 and out.count("def g") == 1
    ns = {}
    exec(compile(out, "<a>", "exec"), ns)
    assert ns["C"].f(1) == 2
