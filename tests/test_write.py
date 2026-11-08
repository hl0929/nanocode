"""Tests for the `write` tool in nanocode.py.

Plain Python only: no pytest, no unittest, no third-party code.

    python tests/test_write.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.dirname(HERE))

from nanocode import read, write  # noqa: E402  (needs sys.path set up first)


def test_write_creates_the_file_when_it_does_not_exist():
    """write 在文件不存在时会新建文件，并把 content 原样写进去，返回 "ok"。

    测试开始前先确保 tests/write_sample.py 不存在：
        删掉后调用 write(...) -> 目录里重新出现该文件
    """
    path = os.path.join(FIXTURES, "write_sample.py")
    if os.path.exists(path):
        os.remove(path)

    print(f"写入的文件（当前不存在，应被新建）：{path}")
    result = write({"path": path, "content": "def add(a, b):\n    return a + b\n"})

    expected = "   1| def add(a, b):\n   2|     return a + b\n"
    print(f"期望的返回值：'ok'\n期望新建后读回：\n{expected}")

    assert result == "ok", f"expected 'ok', got {result!r}"
    assert os.path.exists(path), "文件没有被新建"
    assert read({"path": path}) == expected


def test_write_overwrites_the_existing_file():
    """write 是覆盖写：文件已存在时，原有内容全部清空，只留下新内容。

    先写入旧内容：
        1  def add(a, b):
        2      total = a + b
        3      return total
    """
    path = os.path.join(FIXTURES, "write_sample.py")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("def add(a, b):\n    total = a + b\n    return total\n")

    print(f"写入的文件（已有旧内容）：{path}")
    result = write({"path": path, "content": "def add(a, b):\n    return a + b\n"})

    expected = "   1| def add(a, b):\n   2|     return a + b\n"
    print(f"期望的返回值：'ok'\n期望覆盖后读回：\n{expected}")

    assert result == "ok", f"expected 'ok', got {result!r}"
    assert read({"path": path}) == expected


def banner(name):
    """打印一个分隔块，标明当前跑的是哪个测试函数。"""
    print(f"\n{'─' * 60}\n{name}\n{'─' * 60}")


if __name__ == "__main__":
    banner("test_write_creates_the_file_when_it_does_not_exist")
    test_write_creates_the_file_when_it_does_not_exist()
    print("[PASS] 文件不存在时 write 能新建文件")
    banner("test_write_overwrites_the_existing_file")
    test_write_overwrites_the_existing_file()
    print("[PASS] 文件已存在时 write 会覆盖旧内容")
