"""Tests for the `bash` tool in nanocode.py.

Plain Python only: no pytest, no unittest, no third-party code.

    python tests/test_bash.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.dirname(HERE))

from nanocode import bash  # noqa: E402  (needs sys.path set up first)


def test_bash_returns_the_command_output():
    """命令输出被原样收集成字符串返回，同时也会实时打印到终端。"""
    print("执行的命令：echo hello")
    result = bash({"cmd": "echo hello"})

    expected = "hello"
    print(f"期望的输出：{expected}")

    assert result == expected, f"expected {expected!r}, got {result!r}"


def test_bash_merges_stderr_into_the_output():
    """stderr 被合并进 stdout，所以命令报错时模型也能看到错误信息。

    这里用 Python 往 stderr 写一句固定文本，避免依赖具体的 shell 报错文案。
    """
    cmd = 'python -c "import sys; sys.stderr.write(\'boom\')"'
    print(f"执行的命令（只往 stderr 写）：{cmd}")
    result = bash({"cmd": cmd})

    expected = "boom"
    print(f"期望的输出（错误信息被合并进来）：{expected}")

    assert result == expected, f"expected {expected!r}, got {result!r}"


def test_bash_returns_empty_when_the_command_prints_nothing():
    """命令没有输出时返回 "(empty)"，避免交出空字符串让模型误判。"""
    print("执行的命令：python -c \"pass\"")
    result = bash({"cmd": 'python -c "pass"'})

    expected = "(empty)"
    print(f"期望的输出：{expected}")

    assert result == expected, f"expected {expected!r}, got {result!r}"


def banner(name):
    """打印一个分隔块，标明当前跑的是哪个测试函数。"""
    print(f"\n{'─' * 60}\n{name}\n{'─' * 60}")


if __name__ == "__main__":
    banner("test_bash_returns_the_command_output")
    test_bash_returns_the_command_output()
    print("[PASS] bash 正确返回命令输出")
    banner("test_bash_merges_stderr_into_the_output")
    test_bash_merges_stderr_into_the_output()
    print("[PASS] bash 把 stderr 合并进输出")
    banner("test_bash_returns_empty_when_the_command_prints_nothing")
    test_bash_returns_empty_when_the_command_prints_nothing()
    print("[PASS] 命令无输出时 bash 返回 '(empty)'")
