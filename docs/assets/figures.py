# -*- coding: utf-8 -*-
"""Figure definitions for docs/nanocode-explained.md.

    python docs/assets/figures.py

13 hand-laid-out SVGs sharing one design system: rounded cards, semantic
colours, monospace for anything that is code, and a subtle animated "flow"
on the edges that actually carry data.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import Fig, CO  # noqa: E402

FIG = []


def fig(fn):
    FIG.append(fn)
    return fn


def seq(f, lanes, top, bottom):
    """lanes = [(key, label, color, x)] -> {key: x}; draws heads + lifelines"""
    X = {}
    for key, label, color, x in lanes:
        X[key] = x
        f.node(x - 76, top, 152, 44, [label], color, fs=13.5)
        f.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
              'stroke-width="1.4" stroke-dasharray="4 6" opacity=".45"/>'
              % (x, top + 44, x, bottom, CO[color][0]))
    return X


# ---------------------------------------------------------------------------
# 01 - three parties
# ---------------------------------------------------------------------------
@fig
def f01():
    f = Fig(940, 560, "三方关系：谁碰得到硬盘，谁碰不到",
            "你说一句话，程序把全部历史发给云端 AI；AI 只能回 text / tool_use，"
            "真正执行的是本机程序。")

    f.pill(300, 56, 240, 54, ["你", "键盘 / 屏幕"], "user")
    f.node(300, 190, 240, 74, ["nanocode.py", "本地进程（有手）"], "proc")
    f.node(110, 340, 320, 84, ["AI 模型", "云端（只有嘴）"], "ai")
    f.node(480, 340, 320, 84, ["文件系统 + shell", "本机（真的会动）"], "fs")

    # you <-> program
    f.arrow([(380, 110), (380, 190)], "user", flow=True)
    f.arrow([(460, 190), (460, 110)], "user", flow=True)
    f.badge(380, 150, "①", "user", r=10, fs=10.5)
    f.badge(460, 150, "⑥", "user", r=10, fs=10.5)

    # program <-> AI  (down = request, up = reply)
    f.arrow([(340, 264), (340, 340)], "ai", flow=True)
    f.arrow([(240, 340), (240, 264)], "ai", flow=True)
    f.badge(340, 302, "②", "ai", r=10, fs=10.5)
    f.badge(240, 302, "③", "ai", r=10, fs=10.5)

    # program <-> filesystem
    f.arrow([(560, 264), (560, 340)], "fs", flow=True)
    f.arrow([(660, 340), (660, 264)], "fs", flow=True)
    f.badge(560, 302, "④", "fs", r=10, fs=10.5)
    f.badge(660, 302, "⑤", "fs", r=10, fs=10.5)

    f.card(650, 44, 270, 246, "图例")
    legend = [
        ("①", "user", "你输入一句话"),
        ("②", "ai", "请求：全部历史 + 工具菜单"),
        ("③", "ai", "回复：text / tool_use（只说不做）"),
        ("④", "fs", "程序真正执行工具"),
        ("⑤", "fs", "返回结果字符串"),
        ("⑥", "user", "打印到屏幕"),
    ]
    for i, (n, c, t) in enumerate(legend):
        y = 92 + i * 33
        f.badge(678, y, n, c, r=9.5, fs=10)
        f.text(696, y + 4.5, t, 11.5, "#334155")

    f.text(60, 474, "从 AI 出来的箭头只有一条，只通向程序，永远不直接通向文件系统。",
           12.5, CO["warn"][2], weight="600")
    f.text(60, 498, "AI 唯一能做的事，就是「输出一段 JSON 说我想要什么工具」。",
           12.5, "#475569")
    return f, "01-roles.svg"


# ---------------------------------------------------------------------------
# 02 - main loop
# ---------------------------------------------------------------------------
@fig
def f02():
    f = Fig(900, 730, "主循环流程图：那个圈怎么转",
            "六行伪代码画成图：只有「有 tool_use」自环，和「没有 tool_use」出口两条箭头。")

    f.pill(250, 56, 260, 46, ["等你输入  ❯"], "user")
    f.node(250, 140, 260, 58, ["messages += user", "你说的话"], "user")
    f.node(250, 238, 260, 62, ["call_api(...)", "发：全部历史 + 工具菜单"], "proc")
    f.node(250, 336, 260, 56, ["response.content", "（block 列表）"], "ai")
    f.diamond(380, 472, 112, 64, ["里面有", "tool_use 块？"], "ink")

    f.arrow([(380, 102), (380, 140)], "user", flow=True)
    f.arrow([(380, 198), (380, 238)], "proc", flow=True)
    f.arrow([(380, 300), (380, 336)], "ai", flow=True)
    f.arrow([(380, 392), (380, 408)], "ink")

    f.node(110, 596, 270, 66, ["run_tool 执行工具", "打包成 tool_result"], "fs")
    f.pill(536, 604, 208, 50, ["这轮回答结束"], "muted")

    f.arrow([(380, 536), (380, 596)], "fs", flow=True)
    f.tag(396, 570, "有 → 还要干活", color="fs", anchor="start", fs=11.5)
    f.arrow([(492, 472), (536, 472), (536, 604)], "ink")
    f.tag(548, 458, "没有 → 只想说话", color="muted", anchor="start", fs=11.5)

    # feedback loop down the left side
    f.arrow([(110, 629), (36, 629), (36, 169), (250, 169)], "proc", flow=True)
    f.text(60, 428, "自环这两步：", 10.5, "#475569", weight="600")
    f.text(60, 450, "① messages += assistant 原始块", 10.5, CO["proc"][2])
    f.text(60, 468, "② messages += user 工具结果", 10.5, CO["proc"][2])
    f.text(60, 490, "然后回到 call_api 再问一次", 10.5, "#475569")

    # outer loop down the right side
    f.arrow([(744, 629), (812, 629), (812, 79), (510, 79)], "user")
    f.tag(828, 360, "下一句话", color="user", rot=-90, fs=11.5)

    f.card(556, 200, 240, 112, "两条箭头 = 全部逻辑", "warn")
    f.text(574, 250, "自环：有 tool_use", 12, "#b91c1c")
    f.text(574, 270, "　　　→ 干活 → 再问一次", 12, "#b91c1c")
    f.text(574, 292, "出口：没有 tool_use → 停", 12, "#b91c1c")
    return f, "02-main-loop.svg"


# ---------------------------------------------------------------------------
# 03 - dispatching content blocks
# ---------------------------------------------------------------------------
@fig
def f03():
    f = Fig(1000, 520, "content 块分拣图",
            "一个 response.content 列表，按 block['type'] 分流到三个出口。")

    f.node(360, 56, 280, 62, ["response.content", "（block 列表）"], "ai")
    f.node(340, 162, 320, 54, ["for block in blocks", "逐个看每个块"], "proc")
    f.diamond(500, 300, 118, 60, ["block['type']"], "ink")
    f.arrow([(500, 118), (500, 162)], "ai", flow=True)
    f.arrow([(500, 216), (500, 240)], "proc", flow=True)

    outs = [
        (170, "text", ["text → 打印到屏幕", "用户看到回答"], "user"),
        (500, "tool_use", ["tool_use → run_tool", "真去动硬盘"], "fs"),
        (830, "其它", ["其它类型 → 忽略", "不认识，跳过"], "muted"),
    ]
    f.arrow([(500, 360), (500, 388)], "ink", head=False)
    f.add('<path d="M 170 388 L 830 388" stroke="#94a3b8" stroke-width="1.6" '
          'stroke-linecap="round"/>')
    for cx, key, lines, color in outs:
        f.arrow([(cx, 388), (cx, 422)], color, flow=(color != "muted"))
        f.node(cx - 105, 422, 210, 56, lines, color, fs=12.5)
        f.tag(cx, 412, key, color=color, mono=True, fs=11.5, weight="700")

    f.card(50, 56, 250, 140, "一句话记住", "amber")
    f.text(68, 106, "列表里出现", 12.5, "#b45309")
    f.text(68, 126, "type == \"tool_use\"", 12.5, "#b45309", mono=True, weight="600")
    f.text(68, 148, "就是要干活；一个都没有，", 12.5, "#b45309")
    f.text(68, 170, "就是纯聊天，停。", 12.5, "#b45309")

    f.card(700, 56, 250, 140, "一个容易漏的点", "warn")
    f.text(718, 106, "text 和 tool_use 可以", 12, "#b91c1c")
    f.text(718, 126, "同时存在于同一个列表：", 12, "#b91c1c")
    f.text(718, 148, "先打印，再去干活 ——", 12, "#b91c1c")
    f.text(718, 170, "两者不互斥。", 12, "#b91c1c")
    return f, "03-block-dispatch.svg"


# ---------------------------------------------------------------------------
# 04 - tool_use_id pairing
# ---------------------------------------------------------------------------
@fig
def f04():
    f = Fig(960, 520, "tool_use_id 叫号配对图",
            "AI 一口气提 3 个请求，程序回 3 条结果，顺序乱了也能靠 id 一一对上。")

    f.text(50, 52, "① AI 一口气提 3 个请求（同一轮）", 13.5, CO["ai"][2], weight="700")
    f.text(510, 52, "② 程序回 3 条结果（顺序可以乱）", 13.5, CO["fs"][2], weight="700")

    req = [("toolu_A1", "glob", "*.py"), ("toolu_A2", "read", "main.py"),
           ("toolu_A3", "bash", "pytest")]
    res = [("toolu_A3", "3 passed"), ("toolu_A1", "nanocode.py"),
           ("toolu_A2", "import os...")]

    ys = [92, 204, 316]
    pos = {}
    for (rid, name, arg), y in zip(req, ys):
        pos[rid] = y + 39
        f.node(50, y, 300, 78, [{"t": name + "()", "mono": True, "fs": 13},
                                {"t": "id = " + rid, "fs": 11.5},
                                {"t": "input  " + arg, "fs": 11.5}],
               "ai", align="left")
    for i, (rid, out) in enumerate(res):
        y = ys[i]
        f.node(510, y, 300, 78, [{"t": "tool_use_id = " + rid, "fs": 11.5},
                                 {"t": "content  " + out, "fs": 12}],
               "fs", align="left", bold_first=False)
        f.arrow([(350, pos[rid]), (510, y + 39)], "fs", flow=True)

    f.card(50, 424, 760, 68, "为什么要编号", "amber")
    f.text(70, 472, "就像食堂叫号取餐：不喊号的话，三份结果摆在那，谁都不敢拿。",
           12.5, "#b45309")
    return f, "04-tool-use-id-pairing.svg"


# ---------------------------------------------------------------------------
# 05 - history resend
# ---------------------------------------------------------------------------
@fig
def f05():
    f = Fig(1010, 780, "历史累积时序图：为什么每轮都要整个重发",
            "三条消息被一遍遍全量重发；第二次请求里，第 1 条又被发了一次。")

    X = seq(f, [("you", "你", "user", 110), ("proc", "程序", "proc", 400),
                ("ai", "AI（无状态）", "ai", 720)], 56, 690)

    def msg(y, a, b, label, color, num, dash=False):
        ax, bx = X[a], X[b]
        f.arrow([(ax, y), (bx, y)], color, dash=dash, flow=not dash)
        f.badge(min(ax, bx) + 24, y - 15, num, color, r=9.5, fs=10)
        f.tag(min(ax, bx) + 46, y - 15, label, color=color, anchor="start", fs=11.5)

    def act(y, lines, color, h=36):
        f.node(X["proc"] - 120, y, 240, h, lines, color, fs=11, bold_first=False)

    msg(160, "you", "proc", "有什么文件?", "user", "1")
    act(196, [{"t": "messages = [① user]", "fs": 11}], "proc", 34)
    msg(252, "proc", "ai", "发 ①", "proc", "2")
    msg(312, "ai", "proc", "text + tool_use", "ai", "3", dash=True)
    act(352, [{"t": "执行 glob → \"nanocode.py\"", "fs": 11},
              {"t": "messages = [①, ②, ③]", "fs": 11}], "fs", 52)
    msg(456, "proc", "ai", "发 ①②③（整个重发）", "proc", "4")
    f.card(772, 236, 210, 128, "看清楚第 ④ 步", "amber")
    f.text(788, 280, "「发 ①②③」里，① 已经", 11, "#b45309")
    f.text(788, 300, "是第二遍了 —— 上一轮发", 11, "#b45309")
    f.text(788, 320, "过的历史，这一轮又原样", 11, "#b45309")
    f.text(788, 340, "整个发了一次。", 11, "#b45309")
    f.arrow([(772, 300), (742, 300), (742, 458), (706, 458)], "amber", w=1.3)
    msg(560, "ai", "proc", "只有 text（不再要工具）", "ai", "5", dash=True)
    act(600, [{"t": "打印回答 → 这轮结束", "fs": 11}], "user", 34)

    # highlight: the re-sent block
    f.add('<rect x="%d" y="%d" width="%d" height="%d" rx="16" fill="none" stroke="%s" '
          'stroke-width="2" stroke-dasharray="8 6" opacity=".75"/>'
          % (X["proc"] - 168, 128, 470, 512, CO["amber"][0]))
    f.tag(X["proc"] + 70, 660, "虚线框 = 每轮都要全量重发的历史 ①②③", color="amber", fs=11.5)

    f.card(820, 56, 168, 148, "关键", "warn")
    f.text(836, 104, "AI 那边没有记忆。", 12, "#b91c1c")
    f.text(836, 126, "每次调 API 对它都是", 12, "#b91c1c")
    f.text(836, 148, "「第一次见面」。", 12, "#b91c1c")
    f.text(836, 176, "不给全历史 = 完全失忆", 11.5, "#b91c1c", weight="600")

    f.card(820, 620, 168, 92, "代价", "amber")
    f.text(836, 668, "越聊越长、越慢越贵，", 11.5, "#b45309")
    f.text(836, 688, "最终撞上上下文上限。", 11.5, "#b45309")
    return f, "05-history-resend.svg"


# ---------------------------------------------------------------------------
# 06 - tool contract
# ---------------------------------------------------------------------------
@fig
def f06():
    f = Fig(960, 730, "工具统一契约图：六个工具的共同形状",
            "入参 dict → 出参 str；任何异常都在 run_tool 里被兜成字符串。")

    f.node(40, 100, 330, 68, ["AI 说：想用 glob",
                              {"t": "input = {\"pat\": \"*.py\"}", "fs": 11.5}],
           "ai", align="left")
    f.node(40, 232, 330, 68, ["run_tool(name, args)",
                              {"t": "try / except", "fs": 11.5}], "proc", align="left")
    f.arrow([(205, 168), (205, 232)], "ai", flow=True)
    f.tag(222, 204, "① 入参是一个 dict", color="ai", anchor="start", fs=11.5)

    tools = ["read()", "write()", "edit()", "glob()", "grep()", "bash()"]
    tw_, gap = 124, 14
    xs = [40 + i * (tw_ + gap) for i in range(6)]
    y0 = 388
    for i, t in enumerate(tools):
        f.node(xs[i], y0, tw_, 48, [{"t": t, "mono": True}], "fs", fs=13)

    # spine from run_tool to the six tools
    cx = [x + tw_ / 2 for x in xs]
    f.arrow([(205, 300), (205, 352)], "fs", head=False)
    f.add('<path d="M %.1f 352 L %.1f 352" stroke="%s" stroke-width="1.6" '
          'stroke-linecap="round"/>' % (cx[0], cx[-1], CO["fs"][0]))
    for x in cx:
        f.arrow([(x, 352), (x, y0)], "fs", w=1.5)

    f.node(40, 500, 844, 62, ["统一返回一个字符串",
                              {"t": "直接当 tool_result.content 喂回 AI", "fs": 11.5}],
           "fs", align="left", fs=12.5)
    for x in cx:
        f.arrow([(x, y0 + 48), (x, 500)], "fs", w=1.1, opacity=.5)

    f.node(300, 622, 584, 64, [{"t": "error: No such file: xxx.py", "fs": 11.5},
                               "（失败也是一条字符串，同样喂回 AI）"],
           "warn", align="left", dashed=True, bold_first=False)
    f.arrow([(370, 266), (900, 266), (900, 654), (884, 654)], "warn", dash=True,
            flow=True)
    f.tag(912, 460, "任何异常", color="warn", rot=-90, fs=11.5)

    f.text(40, 592, "六个工具形状完全一致：进去是参数，", 12, "#475569")
    f.text(40, 612, "出来是字符串，中间无论怎么炸，", 12, "#475569")
    f.text(40, 632, "都不会漏到外面。", 12, "#475569")
    return f, "06-tool-contract.svg"


# ---------------------------------------------------------------------------
# 07 - read slicing
# ---------------------------------------------------------------------------
@fig
def f07():
    f = Fig(900, 570, "read 切片示意图：offset / limit 切哪几行",
            "offset 是 0 基下标，打印出来的行号却是 1 基 —— 差一行的地方就在这。")

    f.text(46, 52, "① 原文件 lines：按行拆成的列表", 13.5, "#0f172a", weight="700")
    rows = ["import os", "import sys", "def main():", "    pass",
            "if __name__ == ...", "    return 0"]
    for i, r in enumerate(rows):
        y = 64 + i * 40
        sel = 2 <= i <= 4
        color = "fs" if sel else "muted"
        f.node(46, y, 54, 34, [{"t": "[%d]" % i, "fs": 11.5}], color, dashed=not sel)
        f.node(108, y, 306, 34, [{"t": r, "fs": 12}], color,
               align="left", dashed=not sel, bold_first=False)

    f.add('<rect x="38" y="138" width="382" height="126" rx="12" fill="none" '
          'stroke="%s" stroke-width="2.2"/>' % CO["fs"][0])
    f.arrow([(420, 201), (486, 201)], "fs", flow=True)

    f.text(486, 108, "③ 每行前加行号 offset+idx+1", 13, "#0f172a", weight="700")
    out = ["   3| def main():", "   4|     pass", "   5| if __name__ == ..."]
    f.node(486, 122, 366, 112, [{"t": o, "fs": 12, "mono": True} for o in out], "fs",
           align="left", bold_first=False, lh=1.6)

    f.node(486, 262, 366, 116, [
        {"t": "输出行号 = offset + idx + 1", "fs": 12, "mono": True},
        {"t": "         = 2 + 0 + 1 = 3", "fs": 12, "mono": True},
        {"t": "idx = selected 里的下标，从 0 数", "fs": 11.5, "color": "#475569"},
    ], "amber", align="left", lh=1.9)

    f.tag(46, 332, "② lines[2 : 2+3]   offset=2, limit=3", color="fs",
          anchor="start", fs=12)

    f.node(46, 420, 400, 76, [
        {"t": "⚠ offset 本身是 0 基，行号是 1 基", "fs": 12},
        {"t": "offset=2 → 显示第 3 行，AI 很容易错位一行", "fs": 11.5,
         "color": "#b91c1c"},
    ], "warn", align="left")
    f.text(46, 528, "虚线框 = 未选中，实线框 = 选中", 11.5, "#64748b")
    return f, "07-read-slice.svg"


# ---------------------------------------------------------------------------
# 08 - edit decision tree
# ---------------------------------------------------------------------------
@fig
def f08():
    f = Fig(1100, 720, "edit 唯一性判定决策树",
            "只有一条路能走到「写文件」；两条 ❌ 虚线都是不动盘的报错路。")

    f.pill(420, 44, 280, 48, ["收到 {path, old, new, all?}"], "proc", fs=11.5)
    f.diamond(560, 168, 120, 56, ["old 在文件里？"], "ink")
    f.arrow([(560, 92), (560, 112)], "proc", flow=True)

    f.node(740, 140, 320, 56, ["❌ error: old_string not found"], "warn",
           align="left", dashed=True, fs=11.5)
    f.arrow([(680, 168), (740, 168)], "warn", dash=True)
    f.tag(710, 150, "找不到", color="warn", fs=11)

    f.arrow([(560, 224), (560, 264)], "fs", flow=True)
    f.tag(576, 248, "找到了", color="fs", anchor="start", fs=11)
    f.diamond(560, 318, 112, 52, ["出现几次？"], "ink")

    f.arrow([(448, 318), (370, 318), (370, 380)], "fs", flow=True)
    f.tag(392, 302, "1 次（唯一）", color="fs", anchor="start", fs=11)
    f.node(240, 380, 260, 56, ["replace(old, new, 1)", "只换第一处"], "fs",
           align="left", fs=12)

    f.arrow([(672, 318), (760, 318)], "amber")
    f.tag(716, 302, "多次", color="amber", fs=11)
    f.diamond(880, 318, 100, 48, ["all=true ?"], "amber")

    f.arrow([(880, 366), (880, 404)], "fs", flow=True)
    f.tag(896, 390, "是", color="fs", anchor="start", fs=11)
    f.node(740, 404, 280, 56, ["replace(old, new)", "全部替换"], "fs",
           align="left", fs=12)

    f.arrow([(980, 318), (1060, 318), (1060, 632), (1020, 632)], "warn", dash=True)
    f.tag(1044, 302, "否", color="warn", anchor="end", fs=11)
    f.node(760, 600, 260, 64, ["❌ error: appears N times", "必须唯一（use all=true）"],
           "warn", align="left", dashed=True, fs=11)

    f.node(300, 600, 320, 58, ["写回文件 → \"ok\""], "fs", fs=13)
    f.arrow([(370, 436), (370, 600)], "fs", flow=True)
    f.arrow([(740, 432), (700, 432), (700, 629), (620, 629)], "fs", flow=True)
    f.tag(660, 476, "两条好路", color="fs", fs=11)
    f.tag(660, 496, "都汇到写回文件", color="fs", fs=11)

    f.card(40, 470, 230, 210, "两条 ❌ 死路", "warn")
    f.text(58, 522, "宁可报错让 AI 重试，", 11.5, "#b91c1c")
    f.text(58, 544, "也绝不在「不确定改", 11.5, "#b91c1c")
    f.text(58, 566, "哪一处」的情况下写盘。", 11.5, "#b91c1c")
    f.text(58, 598, "这就是 edit 比 write", 11.5, "#64748b")
    f.text(58, 620, "安全的原因。", 11.5, "#64748b")
    return f, "08-edit-decision.svg"


# ---------------------------------------------------------------------------
# 09 - schema pipeline
# ---------------------------------------------------------------------------
@fig
def f09():
    f = Fig(1060, 372, "schema 转换流水线",
            "TOOLS 里的一行紧凑写法，经过 4 站变成 API 认识的 JSON Schema。")

    steps = [
        ("人写的紧凑格式",
         ["\"read\": (", "  \"Read file...\",",
          "  {\"path\": \"string\",", "   \"offset\": \"number?\"},", "  read)"],
         "proc"),
        ("拆开三元组", ["description", "params", "fn   ← 下标 [2]", ""], "proc"),
        ("逐个参数处理", ["number? → integer", "→ 不进 required",
                      "string → string", "→ 进 required", ""], "fs"),
        ("组装 input_schema", ["type: object", "properties: {...}", "required: [path]", ""],
         "amber"),
        ("塞进请求的 tools", ["tools: [...]", "→ AI 读这份菜单", "→ 决定调哪个工具"], "ai"),
    ]
    w, gap = 180, 26
    for i, (title, lines, color) in enumerate(steps):
        x = 32 + i * (w + gap)
        f.node(x, 98, w, 172,
               [{"t": title, "fs": 12.5}] +
               [{"t": l, "fs": 10.5, "mono": True} for l in lines],
               color, align="left", lh=1.75)
        if i:
            f.arrow([(x - gap, 184), (x, 184)], color, flow=True)
        f.badge(x + 16, 86, str(i + 1), color, r=9.5, fs=10)

    f.card(32, 292, 986, 62, "为什么要费这劲", "amber")
    f.text(52, 340, "API 只认标准 JSON Schema，手写 6 个工具的 JSON 又长又易错；"
                    "写小表自动转 —— 加新工具 = 一个函数 + 一行注册。", 12.5, "#b45309")
    return f, "09-schema-pipeline.svg"


# ---------------------------------------------------------------------------
# 10 - backend switch
# ---------------------------------------------------------------------------
@fig
def f10():
    f = Fig(920, 540, "后端切换分支图",
            "一个环境变量决定认证头，两条分支最后汇到同一个 body。")

    f.diamond(300, 104, 190, 54, ["OPENROUTER_API_KEY 存在？"], "ink", fs=12)

    f.node(40, 220, 380, 132, [
        {"t": "OpenRouter 分支", "fs": 13.5},
        {"t": "URL    openrouter.ai/api/v1/messages", "fs": 10.5},
        {"t": "MODEL  anthropic/claude-opus-4.5", "fs": 10.5},
        {"t": "HDR    Authorization: Bearer", "fs": 10.5},
    ], "ai", align="left")
    f.arrow([(220, 158), (220, 220)], "ai", flow=True)
    f.tag(236, 202, "有", color="ai", anchor="start", fs=11)

    f.node(500, 220, 380, 132, [
        {"t": "Anthropic 官方分支", "fs": 13.5},
        {"t": "URL    api.anthropic.com/v1/messages", "fs": 10.5},
        {"t": "MODEL  claude-opus-4-5", "fs": 10.5},
        {"t": "HDR    x-api-key", "fs": 10.5},
    ], "proc", align="left")
    f.arrow([(490, 104), (690, 104), (690, 220)], "proc", flow=True)
    f.tag(706, 186, "没有", color="proc", anchor="start", fs=11)

    f.node(250, 400, 420, 64, ["同一个 body 结构",
                               {"t": "{model, system, messages, tools}", "fs": 11.5}],
           "amber", fs=13)
    f.arrow([(230, 352), (230, 376), (400, 376), (400, 400)], "ai", flow=True)
    f.arrow([(690, 352), (690, 376), (520, 376), (520, 400)], "proc", flow=True)

    f.text(460, 492, "→ urlopen → json.loads → 返回同样的 {'content': [...]}", 11.5,
           "#64748b", anchor="middle")
    f.text(40, 470, "分支只在这里出现一次", 11.5, "#475569", weight="600")
    f.text(40, 492, "main() 完全不用关心后端", 11.5, "#475569")
    return f, "10-backend-switch.svg"


# ---------------------------------------------------------------------------
# 11 - nested loops
# ---------------------------------------------------------------------------
@fig
def f11():
    f = Fig(1010, 830, "三层嵌套结构图：三个 while / for 谁管谁",
            "外层等你输入，内层负责一次回答，for 遍历这一轮返回的每个 block。")

    f.frame(30, 70, 690, 690, "① 外层 while —— 一轮对话（等你输入）", "user")
    f.frame(64, 166, 618, 470, "② 内层 while —— 一次回答（问 AI → 干活 → 再问）", "proc")
    f.frame(98, 374, 500, 148, "③ for block —— 本轮每个块", "fs")

    f.pill(230, 96, 280, 42, ["input('❯ ') 等你输入"], "user", fs=12)
    f.node(230, 208, 280, 40, ["messages += user 你说的话"], "user", fs=11.5)
    f.node(230, 278, 280, 40, ["call_api(messages + 工具菜单)"], "proc", fs=11)
    f.arrow([(370, 138), (370, 208)], "user", flow=True)
    f.arrow([(370, 248), (370, 278)], "proc", flow=True)

    # enter the for-frame, then fan out to the two block types
    f.arrow([(370, 318), (370, 342), (452, 342), (452, 414)], "proc", flow=True)
    f.add('<path d="M 204 414 L 452 414" stroke="%s" stroke-width="1.7" '
          'stroke-linecap="round"/>' % CO["fs"][0])
    f.arrow([(204, 414), (204, 434)], "fs", w=1.6)
    f.arrow([(452, 414), (452, 434)], "fs", w=1.6)

    f.node(126, 434, 156, 46, ["text → 打印"], "ai", fs=11.5)
    f.node(330, 434, 240, 46, ["tool_use → run_tool"], "fs", fs=11.5)
    f.text(110, 508, "tool_results.append(...) 攒着，稍后一起发回", 10.5,
           CO["fs"][2], weight="600")

    f.node(240, 536, 260, 36, ["messages += assistant 原始块"], "proc", fs=11)
    f.arrow([(452, 480), (452, 522), (370, 522), (370, 536)], "proc", flow=True)

    f.diamond(370, 610, 100, 34, ["tool_results 空？"], "ink", fs=11.5)
    f.arrow([(370, 572), (370, 576)], "ink", flow=True)

    # 空 -> 跳出内层 while，回到等你输入
    f.arrow([(370, 644), (370, 692), (300, 692)], "muted", flow=True)
    f.tag(388, 666, "空", color="muted", anchor="start", fs=11)
    f.node(50, 674, 250, 38, ["这轮完了 → 等下一句话"], "muted", fs=11)

    # 不空 -> 原路回到 call_api
    f.arrow([(470, 610), (652, 610), (652, 298), (510, 298)], "proc", flow=True)
    f.tag(500, 594, "不空 → 回到 call_api", color="proc", anchor="start", fs=11)

    # /q exit
    f.node(770, 96, 190, 42, ["/q 或 exit → 退出"], "warn", fs=11.5)
    f.arrow([(510, 117), (770, 117)], "warn", dash=True)
    f.tag(640, 99, "是", color="warn", fs=11)

    f.card(750, 184, 220, 210, "三层各管什么")
    f.text(766, 234, "① 一次用户提问", 11, "#334155", weight="600")
    f.text(766, 254, "　　→ /q 退出", 11, "#475569")
    f.text(766, 282, "② 问 AI → 干活 → 再问", 11, "#334155", weight="600")
    f.text(766, 302, "　　→ 不再要工具就结束", 11, "#475569")
    f.text(766, 330, "③ 遍历本轮返回的块", 11, "#334155", weight="600")
    f.text(766, 350, "　　→ 遍历完就往下走", 11, "#475569")
    return f, "11-nested-loops.svg"


# ---------------------------------------------------------------------------
# 12 - full sequence
# ---------------------------------------------------------------------------
@fig
def f12():
    f = Fig(1010, 810, "全流程泳道图：一次提问的完整来回",
            "你 → 程序 → AI → 文件系统，一次提问怎么来回走完。")

    X = seq(f, [("you", "你", "user", 90), ("proc", "程序", "proc", 320),
                ("fs", "文件系统", "fs", 620), ("ai", "AI", "ai", 880)], 56, 680)

    def msg(y, a, b, label, color, num, dash=False):
        ax, bx = X[a], X[b]
        f.arrow([(ax, y), (bx, y)], color, dash=dash, flow=not dash)
        f.badge(min(ax, bx) + 22, y - 15, num, color, r=9.5, fs=10)
        f.tag(min(ax, bx) + 42, y - 15, label, color=color, anchor="start", fs=11.5)

    def act(y, lane, lines, color, h=34):
        f.node(X[lane] - 104, y, 208, h, lines, color, fs=11, bold_first=False)

    msg(152, "you", "proc", "有什么文件?", "user", "1")
    act(186, "proc", [{"t": "messages += user", "fs": 11}], "proc")
    msg(252, "proc", "ai", "请求：全部历史 + 工具菜单", "proc", "2")
    msg(318, "ai", "proc", "text + tool_use(glob)", "ai", "3", dash=True)
    act(350, "proc", [{"t": "⏺ 我先看看   ← 打印 text", "fs": 11}], "user")
    msg(418, "proc", "fs", "glob ./*.py", "fs", "4")
    msg(486, "fs", "proc", "nanocode.py", "fs", "5", dash=True)
    msg(548, "proc", "ai", "请求：带上 tool_result", "proc", "6")
    msg(614, "ai", "proc", "只有 text → break", "ai", "7", dash=True)

    f.text(60, 730, "整条链路里，AI 只做了 2 件事：", 12, "#475569", weight="600")
    f.text(60, 752, "回 text、回 tool_use。", 12, "#475569", weight="600")
    f.text(60, 774, "它一次都没碰过你的硬盘。", 12, "#475569", weight="600")

    f.card(400, 690, 610, 104, "两条分支都在内层 while 里", "warn")
    f.text(420, 736, "有 tool_use → 回到「请求」再问一次；没有 tool_use → break 出内层。",
           11.5, "#b91c1c")
    f.text(420, 760, "这一次就是「没有」，所以流程停在 ⑦。", 11.5, "#b91c1c")
    return f, "12-full-sequence.svg"


# ---------------------------------------------------------------------------
# 13 - bash timeout bug
# ---------------------------------------------------------------------------
@fig
def f13():
    f = Fig(980, 620, "bash 超时 bug 时序图",
            "readline() 无限阻塞，proc.wait(timeout=30) 永远走不到 —— 实际等于没有超时。")

    seq(f, [("bash", "bash()", "proc", 240), ("proc", "子进程", "fs", 700)], 56, 430)

    f.node(150, 116, 180, 34, [{"t": "Popen(\"sleep 100\")", "fs": 10.5}], "proc")
    f.arrow([(330, 133), (700, 133)], "proc", flow=True)
    f.badge(352, 133, "1", "proc", r=9.5, fs=10)
    f.tag(372, 133, "启动，而且不产生任何输出", color="proc", anchor="start", fs=11.5)

    f.arrow([(240, 196), (700, 196)], "warn", dash=True)
    f.badge(262, 196, "2", "warn", r=9.5, fs=10)
    f.tag(282, 196, "readline() 在这里无限阻塞", color="warn", anchor="start", fs=11.5)

    f.add('<rect x="140" y="222" width="560" height="76" rx="10" fill="%s" '
          'fill-opacity=".85" stroke="%s" stroke-width="1.6" stroke-dasharray="6 5"/>'
          % (CO["warn"][1], CO["warn"][0]))
    f.text(160, 252, "代码卡死在这里 —— proc.wait(timeout=30) 永远走不到", 12.5,
           "#b91c1c", weight="700")
    f.text(160, 278, "timeout 只作用在「等进程退出」，管不了「等一行输出」。", 11.5,
           "#b91c1c")

    # 30s mark: the timeout that should have fired here
    f.add('<line x1="240" y1="318" x2="700" y2="318" stroke="%s" stroke-width="1.2" '
          'stroke-dasharray="2 7" opacity=".75"/>' % CO["amber"][0])
    f.tag(690, 318, "第 30 秒 —— 本该在这里超时，但没有", color="amber",
          anchor="end", fs=11)

    f.arrow([(700, 348), (240, 348)], "fs", dash=True)
    f.badge(678, 348, "3", "fs", r=9.5, fs=10)
    f.tag(658, 348, "100 秒后子进程结束，readline() 才返回空串 → break", color="fs",
          anchor="end", fs=11.5)

    f.node(150, 380, 180, 36, [{"t": "proc.wait(timeout=30)", "fs": 10.5}], "muted")
    f.tag(348, 398, "此时才轮到 wait()：进程早结束了 → 超时形同虚设", color="muted",
          anchor="start", fs=11.5)

    f.card(60, 466, 860, 130, "根本原因 & 修法", "warn")
    f.text(80, 512, "timeout 参数只作用在「等进程退出」上，管不了「等一行输出」；"
                    "而 readline() 恰恰在等输出。", 12.5, "#b91c1c")
    f.text(80, 544, "方案 A：threading.Timer(30, proc.kill) 到点直接 kill，"
                    "再 communicate() 阻塞读完。", 12, "#b45309")
    f.text(80, 568, "方案 B：把 readline 放进子线程，主线程 join(timeout=30)。", 12,
           "#b45309")
    return f, "13-bash-timeout-bug.svg"


if __name__ == "__main__":
    for fn in FIG:
        obj, name = fn()
        obj.save(name)
