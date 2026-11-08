"""Tests for the `read` tool in nanocode.py.

Plain Python only: no pytest, no unittest, no third-party code.

    python tests/test_read.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.dirname(HERE))

from nanocode import read  # noqa: E402  (needs sys.path set up first)


def test_read_uses_zero_based_offset_and_one_based_line_numbers():
    """offset=1, limit=2 -> 原文件第 2、3 行，显示行号 2 和 3。

    这是最容易出错的一处：offset 从 0 数，但打印出来的行号从 1 数。
    read_sample.py 的内容是：
        1  def greet(name):
        2      message = f"Hello, {name}!"
        3      print(message)
        4      return message
    """
    path = os.path.join(FIXTURES, "read_sample.py")
    print(f"读取的文件：{path}")
    result = read({"path": path, "offset": 1, "limit": 2})
    expected = '   2|     message = f"Hello, {name}!"\n   3|     print(message)\n'
    print(f"期望的输出（第 2、3 行，行号从 1 起）：\n{expected}")
    assert result == expected, f"expected {expected!r}, got {result!r}"


if __name__ == "__main__":
    test_read_uses_zero_based_offset_and_one_based_line_numbers()
    print("[PASS] test_read_uses_zero_based_offset_and_one_based_line_numbers")
