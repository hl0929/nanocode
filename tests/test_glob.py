"""Tests for the `glob` tool in nanocode.py.

Plain Python only: no pytest, no unittest, no third-party code.

    python tests/test_glob.py
"""

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.dirname(HERE))

from nanocode import glob  # noqa: E402  (needs sys.path set up first)


def test_glob_finds_files_sorted_by_mtime_newest_first():
    """按修改时间倒序：最近改过的文件排最前。

    tests/fixtures/glob_sample_old.py 和 glob_sample_new.py 内容相同，
    但把 old 的 mtime 调早 100 秒，所以结果里 new 应该排在 old 前面。
    """
    old = os.path.join(FIXTURES, "glob_sample_old.py")
    new = os.path.join(FIXTURES, "glob_sample_new.py")
    now = time.time()
    os.utime(old, (now - 100, now - 100))
    os.utime(new, (now, now))

    print(f"搜索目录：{FIXTURES}\n模式：glob_sample_*.py")
    result = glob({"pat": "glob_sample_*.py", "path": FIXTURES})

    expected = f"{new}\n{old}"
    print(f"期望的输出（新的在前）：\n{expected}")

    assert result == expected, f"expected {expected!r}, got {result!r}"


def test_glob_returns_none_when_nothing_matches():
    """没有匹配时返回 "none"，避免交出空字符串让模型以为工具坏了。"""
    print(f"搜索目录：{FIXTURES}\n模式：*.no_such_extension")
    result = glob({"pat": "*.no_such_extension", "path": FIXTURES})

    expected = "none"
    print(f"期望的输出：{expected}")

    assert result == expected, f"expected {expected!r}, got {result!r}"


def banner(name):
    """打印一个分隔块，标明当前跑的是哪个测试函数。"""
    print(f"\n{'─' * 60}\n{name}\n{'─' * 60}")


if __name__ == "__main__":
    banner("test_glob_finds_files_sorted_by_mtime_newest_first")
    test_glob_finds_files_sorted_by_mtime_newest_first()
    print("[PASS] glob 找到文件并按修改时间倒序排列")
    banner("test_glob_returns_none_when_nothing_matches")
    test_glob_returns_none_when_nothing_matches()
    print("[PASS] 没有匹配时 glob 返回 'none'")
