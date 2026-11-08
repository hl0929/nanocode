"""Tests for the `edit` tool in nanocode.py.

Plain Python only: no pytest, no unittest, no third-party code.

    python tests/test_edit.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.dirname(HERE))

from nanocode import edit, read  # noqa: E402  (needs sys.path set up first)


def test_edit_replaces_a_unique_string():
    """old 在文件里只出现一次时，替换成功并返回 "ok"。

    tests/edit_sample.py 原内容：
        1  def add(a, b):
        2      total = a + b
        3      return total
    """
    path = os.path.join(FIXTURES, "edit_sample.py")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("def add(a, b):\n    total = a + b\n    return total\n")

    print(f"编辑的文件：{path}")
    result = edit({"path": path, "old": "total = a + b", "new": "total = a + b + 0"})

    expected = (
        "   1| def add(a, b):\n   2|     total = a + b + 0\n   3|     return total\n"
    )
    print(f"期望的返回值：'ok'\n期望替换后读回：\n{expected}")
    assert result == "ok", f"expected 'ok', got {result!r}"
    assert read({"path": path}) == expected


def test_edit_refuses_a_non_unique_string():
    """old 在文件里出现多次且没传 all=true 时，报错并且文件保持原样。"""
    path = os.path.join(FIXTURES, "edit_sample.py")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("def add(a, b):\n    total = a + b\n    return total\n")

    print(f"编辑的文件（old 出现 2 次）：{path}")
    result = edit({"path": path, "old": "total", "new": "sum"})

    expected = "error: old_string appears 2 times, must be unique (use all=true)"
    print(f"期望的返回值：\n{expected}")

    assert result == expected, f"expected {expected!r}, got {result!r}"
    assert read({"path": path}) == (
        "   1| def add(a, b):\n   2|     total = a + b\n   3|     return total\n"
    ), "文件不应该被修改"


def banner(name):
    """打印一个分隔块，标明当前跑的是哪个测试函数。"""
    print(f"\n{'─' * 60}\n{name}\n{'─' * 60}")


if __name__ == "__main__":
    banner("test_edit_replaces_a_unique_string")
    test_edit_replaces_a_unique_string()
    print("[PASS] old 唯一时 edit 替换成功并返回 'ok'")
    banner("test_edit_refuses_a_non_unique_string")
    test_edit_refuses_a_non_unique_string()
    print("[PASS] old 不唯一时 edit 报错且不修改文件")
