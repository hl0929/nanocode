"""Tests for the `grep` tool in nanocode.py.

Plain Python only: no pytest, no unittest, no third-party code.

    python tests/test_grep.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.dirname(HERE))

from nanocode import grep  # noqa: E402  (needs sys.path set up first)


def test_grep_returns_file_line_and_content():
    """命中时输出 "文件:行号:内容"，方便模型接着 read / edit 那一行。

    tests/fixtures/read_sample.py 的内容：
        1  def greet(name):
        2      message = f"Hello, {name}!"
        3      print(message)
        4      return message
    """
    print(f"搜索目录：{FIXTURES}\n模式：return message")
    result = grep({"pat": "return message", "path": FIXTURES})

    expected = os.path.join(FIXTURES, "read_sample.py") + ":4:    return message"
    print(f"期望的输出（文件:行号:内容）：\n{expected}")

    assert result == expected, f"expected {expected!r}, got {result!r}"


def test_grep_returns_none_when_nothing_matches():
    """没有匹配时返回 "none"，和 glob 的行为保持一致。"""
    print(f"搜索目录：{FIXTURES}\n模式：zzz_no_such_thing")
    result = grep({"pat": "zzz_no_such_thing", "path": FIXTURES})

    expected = "none"
    print(f"期望的输出：{expected}")

    assert result == expected, f"expected {expected!r}, got {result!r}"


def banner(name):
    """打印一个分隔块，标明当前跑的是哪个测试函数。"""
    print(f"\n{'─' * 60}\n{name}\n{'─' * 60}")


if __name__ == "__main__":
    banner("test_grep_returns_file_line_and_content")
    test_grep_returns_file_line_and_content()
    print("[PASS] grep 命中时返回「文件:行号:内容」")
    banner("test_grep_returns_none_when_nothing_matches")
    test_grep_returns_none_when_nothing_matches()
    print("[PASS] 没有匹配时 grep 返回 'none'")
