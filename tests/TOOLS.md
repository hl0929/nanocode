# 六个工具与工具定义

`nanocode.py` 里的六个工具函数、工具定义（`TOOLS` / `make_schema` / `run_tool`），以及 `tests/` 下对应的测试。

六个工具是同一套约定下的六个「通道」：

> **入参是一个字典，出参是一个字符串。**

出参字符串会原样塞进 `tool_result.content` 回传给 AI。**所以工具永远不能把异常抛到外面** —— 全部由 `run_tool` 兜成 `"error: ..."` 字符串。

| 工具 | 一句话 | 看名字还是看内容 | 对应测试 |
|---|---|---|---|
| `read` | 按行读文件，带行号 | 内容 | `test_read.py` |
| `write` | 整体覆盖写文件 | 内容 | `test_write.py` |
| `edit` | 替换文件里的一段字符串 | 内容 | `test_edit.py` |
| `glob` | 按通配符找文件 | **名字** | `test_glob.py` |
| `grep` | 按正则搜文件内容 | 内容 | `test_grep.py` |
| `bash` | 跑 shell 命令 | 命令 | `test_bash.py` |

> 记忆点：`glob` 只看名字，其余五个都碰内容。

前六节讲「每个工具怎么干活」，**第 7 节讲「AI 怎么知道有这些工具」** —— 即 `TOOLS` 注册表、`make_schema()` 翻译器、`run_tool()` 分发器。想加新工具的话直接跳到 [7.4](#74-这三部分怎么串起来)。

---

## 1. `read` — 读文件

`nanocode.py:24-29`

```python
def read(args):
    lines = open(args["path"]).readlines()
    offset = args.get("offset", 0)
    limit = args.get("limit", len(lines))
    selected = lines[offset : offset + limit]
    return "".join(f"{offset + idx + 1:4}| {line}" for idx, line in enumerate(selected))
```

**四步：**

1. 整个文件读成行列表
2. `offset` 是**从 0 数**的起始下标，默认 0
3. `limit` 是要几行，默认全要
4. 每行前面加 `   1| ` 形式的行号（宽度 4、右对齐）

**为什么加行号**：AI 之后要改文件时，得能说「改第 20 行」。没有行号它就对不准。

**输入输出示例**（`offset=1, limit=2`）：

```text
输入：tests/fixtures/read_sample.py
    1  def greet(name):
    2      message = f"Hello, {name}!"
    3      print(message)
    4      return message

输出："   2|     message = f\"Hello, {name}!\"\n   3|     print(message)\n"
```

**两个坑：**

- `offset` 是 **0 基**，但显示的行号是 **1 基**。`offset=1` 给的是第 2 行。这是最容易错位的地方，`test_read.py` 专门锁死这个行为。
- `open()` 没写 `encoding`，Windows 下默认 GBK，读 UTF-8 文件会抛 `UnicodeDecodeError`。

**对应测试** `tests/test_read.py`：验证 `offset=1, limit=2` 返回第 2、3 行，且行号显示为 2 和 3。

---

## 2. `write` — 写文件

`nanocode.py:32-35`

```python
def write(args):
    with open(args["path"], "w") as f:
        f.write(args["content"])
    return "ok"
```

**三行，一件事：把 `content` 整个写进 `path`。**

- `"w"` 模式 = **覆盖**。文件原有内容全没了
- 文件不存在则**新建**
- 返回值固定 `"ok"`

**不做的事：** 不建父目录、不检查权限、不做原子写（写一半崩了会留下半截文件）。出错由 `run_tool` 兜成 `"error: ..."`。

**对应测试** `tests/test_write.py`，两个用例：

1. 文件不存在时能新建，`read()` 回读确认内容
2. 文件已存在时旧内容被完全覆盖

---

## 3. `edit` — 改文件

`nanocode.py:38-51`

```python
def edit(args):
    text = open(args["path"]).read()
    old, new = args["old"], args["new"]
    if old not in text:
        return "error: old_string not found"
    count = text.count(old)
    if not args.get("all") and count > 1:
        return f"error: old_string appears {count} times, must be unique (use all=true)"
    replacement = (
        text.replace(old, new) if args.get("all") else text.replace(old, new, 1)
    )
    with open(args["path"], "w") as f:
        f.write(replacement)
    return "ok"
```

**三步判断，只有一条路能走到写盘：**

```text
old 找不到          → error: old_string not found      不写
old 出现多次且没 all → error: ... must be unique ...    不写
否则                → 替换（all=true 全换，否则只换第一处） → 写
```

**为什么必须唯一？**

假设 AI 说「把 `return` 改成 `return None`」。文件里有 5 个 `return`，猜错就毁代码。所以逼 AI 把上下文写长，长到只匹配一处：

```python
old: "def foo():\n    return"
```

报错信息里直接告诉它 `use all=true`，AI 一看就知道怎么改。

**这是六个工具里唯一有「安全保护」的**：宁可报错让 AI 重试，也不在不确定改哪一处时动手。

**对应测试** `tests/test_edit.py`，两个用例：

1. `old` 唯一 → 返回 `"ok"`，回读确认替换生效
2. `old` 出现 2 次 → 返回错误，并断言**文件没被修改**

---

## 4. `glob` — 按名字找文件

`nanocode.py:54-62`

```python
def glob(args):
    pattern = (args.get("path", ".") + "/" + args["pat"]).replace("//", "/")
    files = globlib.glob(pattern, recursive=True)
    files = sorted(
        files,
        key=lambda f: os.path.getmtime(f) if os.path.isfile(f) else 0,
        reverse=True,
    )
    return "\n".join(files) or "none"
```

**三步：**

1. 拼路径：`path + "/" + pat`，比如 `"." + "/" + "**/*.py"`
2. `glob(..., recursive=True)`，只有 `recursive=True` 时 `**` 才能递归进子目录
3. 按**修改时间倒序**

**为什么按时间排而不是字母排？**

AI 找文件通常是为了改它。**刚改过的文件大概率就是现在要动的那个。** 字母序对 AI 没什么用。

**两个防御细节：**

- `getmtime` 对目录会出错，所以加了 `if os.path.isfile(f) else 0`
- 空结果返回 `"none"`，不然交出空字符串，AI 会以为工具挂了

**什么时候会用到：**

- 「看看这个项目有什么文件」→ `**/*.py`
- 「帮我改下配置」→ `**/*config*`
- 「所有测试文件」→ `**/test_*.py`

**对应测试** `tests/test_glob.py`，两个用例：

1. 两个样本文件，把 old 的 mtime 调早 100 秒，断言新文件排在前面
2. 搜索不存在的扩展名，断言返回 `"none"`

---

## 5. `grep` — 按内容搜文件

`nanocode.py:65-75`

```python
def grep(args):
    pattern = re.compile(args["pat"])
    hits = []
    for filepath in globlib.glob(args.get("path", ".") + "/**", recursive=True):
        try:
            for line_num, line in enumerate(open(filepath), 1):
                if pattern.search(line):
                    hits.append(f"{filepath}:{line_num}:{line.rstrip()}")
        except Exception:
            pass
    return "\n".join(hits[:50]) or "none"
```

**两层循环 + 一个收集：**

1. 外层遍历目录下所有文件（`/**` 递归）
2. 内层逐行读
3. 正则命中就拼成 `文件:行号:内容` 存进 `hits`

最后只返回**前 50 条**。

**输出格式为什么是 `文件:行号:内容`？**

刻意的。AI 看到 `main.py:20: return None` 就知道「去 main.py 第 20 行」，能直接接着 `read` 或 `edit`。

**`except Exception: pass` 为什么要有？**

遇到二进制文件、没权限的文件、编码错的，**静默跳过**。不跳过的话，搜一次仓库就直接崩了。

**三个已知问题：**

- `hits[:50]` 只是返回时截断，文件还是全读完了，没有提前退出 → 大仓库很慢
- `open()` 没指定 `encoding`，Windows 下 GBK 遇到 UTF-8 文件会抛异常，**又被 `except` 吞掉 → 该文件静默搜不到**
- 会进 `.git`、`node_modules` 等目录

**`glob` 和 `grep` 的区别** —— 最容易混的一对：

| | `glob` | `grep` |
|---|---|---|
| 搜什么 | 路径名 | 一行行文本 |
| 输入 | 通配符 `**/*.py` | 正则 `def \w+\(` |
| 输出 | 文件路径列表 | `文件:行号:内容` |
| 回答 | 「有哪些文件」 | 「哪里出现了这段」 |

实际用起来是组合拳：**`glob` 缩小范围，`grep` 精确定位到行。**

**对应测试** `tests/test_grep.py`，两个用例：

1. 搜 `"return message"`，断言返回 `...read_sample.py:4:    return message`
2. 搜不存在的内容，断言返回 `"none"`

---

## 6. `bash` — 跑命令

`nanocode.py:78-97`

```python
def bash(args):
    proc = subprocess.Popen(
        args["cmd"], shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True
    )
    output_lines = []
    try:
        while True:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if line:
                print(f"  {DIM}│ {line.rstrip()}{RESET}", flush=True)
                output_lines.append(line)
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        output_lines.append("\n(timed out after 30s)")
    return "".join(output_lines).strip() or "(empty)"
```

**设计要点：**

| 设计 | 原因 |
|---|---|
| `Popen` 而非 `run` | 要能边跑边看输出；`run` 得等跑完才一次性给 |
| `stderr=STDOUT` | 把错误输出并进标准输出，报错也能被 AI 看到（很重要） |
| `readline()` 循环 | 读到一行就打印一行（带 `│` 前缀），同时存起来 |
| 实时打印 | 长命令（如 `npm install`）你能看到进度，不是干等 |

**🔴 那个超时是假的：**

```python
line = proc.stdout.readline()   # ← 这里能无限阻塞
...
proc.wait(timeout=30)           # ← 超时写在这，走不到
```

命令不产出任何输出时（比如 `sleep 100`），`readline()` 就一直卡着，30 秒超时根本轮不到执行。**实际等于没有超时。**

根本原因：`timeout` 参数只作用在「等进程退出」上，**管不了「等一行输出」**。

**另一个坑**：每次 `bash` 都是全新进程，`cd`、`export` 这类操作**不会跨调用保留**。先 `cd` 再执行，第二次会回到原目录。Windows 下 `shell=True` 走 `cmd.exe`，Unix 命令不一定有。

**对应测试** `tests/test_bash.py`，三个用例：

1. `echo hello` → 断言返回 `"hello"`
2. 只往 stderr 写 `boom` → 断言返回 `"boom"`（验证合并）
3. `python -c "pass"` 无输出 → 断言返回 `"(empty)"`

---

## 7. Tool Definitions — 工具定义

`nanocode.py:100-167`

前面六节讲的是「工具怎么干活」，这一节讲的是「AI 怎么知道有这些工具」。

这段代码由三部分组成：

```text
TOOLS      一张小表        声明有哪些工具、要什么参数
make_schema()  翻译器      把小表变成 API 要的 JSON Schema
run_tool()     分发器      按名字找到函数并执行，兜住所有异常
```

---

### 7.1 `TOOLS` — 一张小表

`nanocode.py:100-133`

```python
# --- Tool definitions: (description, schema, function) ---

TOOLS = {
    "read": (
        "Read file with line numbers (file path, not directory)",
        {"path": "string", "offset": "number?", "limit": "number?"},
        read,
    ),
    "write": (
        "Write content to file",
        {"path": "string", "content": "string"},
        write,
    ),
    "edit": (
        "Replace old with new in file (old must be unique unless all=true)",
        {"path": "string", "old": "string", "new": "string", "all": "boolean?"},
        edit,
    ),
    "glob": (
        "Find files by pattern, sorted by mtime",
        {"pat": "string", "path": "string?"},
        glob,
    ),
    "grep": (
        "Search files for regex pattern",
        {"pat": "string", "path": "string?"},
        grep,
    ),
    "bash": (
        "Run shell command",
        {"cmd": "string"},
        bash,
    ),
}
```

**字典的键是工具名，值是一个三元组 `(描述, 参数表, 函数)`。**

| 位置 | 内容 | 给谁看 | 作用 |
|---|---|---|---|
| `[0]` | `description` | **AI** | 让它知道这工具是干啥的 |
| `[1]` | `params` 参数表 | **AI** | 告诉它要传什么参数、哪些必填 |
| `[2]` | 函数对象 | **程序自己** | AI 要调时就去执行这个 |

> 🔑 **记住下标 `[2]`**：`run_tool` 里就是靠 `TOOLS[name][2]` 取到函数本体的。

**参数表里的类型写法是自定义的迷你语法，不是 JSON Schema：**

| 写法 | 含义 |
|---|---|
| `"string"` | 字符串，必填 |
| `"number?"` | 数字，**可选**（`?` 后缀） |
| `"boolean?"` | 布尔，可选 |

`?` 只表示「可选」，它本身不是类型的一部分 —— `make_schema()` 会把它剥掉。

**为什么不用手写完整 JSON Schema？**

因为真正发给 API 的 schema 长这样，六个工具就是六坨：

```json
{
  "name": "read",
  "description": "Read file with line numbers (file path, not directory)",
  "input_schema": {
    "type": "object",
    "properties": {
      "path":   {"type": "string"},
      "offset": {"type": "integer"},
      "limit":  {"type": "integer"}
    },
    "required": ["path"]
  }
}
```

手写六份这种 JSON，又长又容易打错括号。换成这种一行式的小表，读起来跟函数签名差不多，**改起来不容易错**。

---

### 7.2 `make_schema()` — 把表翻译成 JSON Schema

`nanocode.py:143-167`

```python
def make_schema():
    result = []
    for name, (description, params, _fn) in TOOLS.items():
        properties = {}
        required = []
        for param_name, param_type in params.items():
            is_optional = param_type.endswith("?")          # 有问号 = 可选
            base_type = param_type.rstrip("?")              # 去掉问号
            properties[param_name] = {
                "type": "integer" if base_type == "number" else base_type
            }
            if not is_optional:
                required.append(param_name)                 # 没问号 → 必填
        result.append(
            {
                "name": name,
                "description": description,
                "input_schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            }
        )
    return result
```

**干的就三件事：**

1. **剥问号**：`"number?"` → 类型 `number` + 记下「可选」
2. **翻译类型**：`number` → JSON Schema 的 `integer`
3. **分拣必填**：没带 `?` 的参数名塞进 `required` 列表

> 📌 JSON Schema 里「可选」不需要单独标记 —— **只要不在 `required` 里，就是可选**。

**数据怎么变形 —— 拿 `read` 这一行走一遍：**

```text
表里这一行
  {"path": "string", "offset": "number?", "limit": "number?"}
        │                │                   │
        │                └── 剥 ? ──────────┘
        │                        ↓
        │            offset: integer (不进 required)
        │            limit:  integer (不进 required)
        ↓
   path: string  →  进 required
        ↓
组装成一个工具定义
  {
    "name": "read",
    "description": "Read file with line numbers (file path, not directory)",
    "input_schema": {
      "type": "object",
      "properties": {
        "path":   {"type": "string"},
        "offset": {"type": "integer"},
        "limit":  {"type": "integer"}
      },
      "required": ["path"]
    }
  }
```

**注意 `number` → `integer` 这个映射略有偏差**：JSON Schema 里 `number` 本应允许小数，`integer` 只接受整数。这里为了 `offset` / `limit` 这种「行号/条数」参数，直接映射成 `integer` 刚好合适。如果哪天加一个需要小数的参数（比如 `timeout: 1.5`），就得改这个映射。

**为什么每次调用 API 都重新生成一遍？**

`call_api()` 里写的是 `"tools": make_schema()`，而不是启动时算一次存起来。因为只有六个工具、计算量可以忽略，**换来的是「改了 TOOLS 立刻生效」** —— 不用管缓存失效。

---

### 7.3 `run_tool()` — 唯一的分发口 + 唯一的异常出口

`nanocode.py:136-140`

```python
def run_tool(name, args):
    try:
        return TOOLS[name][2](args)
    except Exception as err:
        return f"error: {err}"
```

两行有信息量的代码：

```python
TOOLS[name][2]      # 用名字查表 → 取第 3 个元素（函数）→ 传 args 调用
except → "error: …" # 任何异常都变成字符串返回
```

**为什么这个 `try/except` 是 agent 设计里最关键的一招？**

对比两种设计：

| 设计 | 文件不存在时发生什么 | AI 能做什么 |
|---|---|---|
| 不兜异常 | 程序崩溃，会话结束 | 什么都做不了 |
| 兜成字符串 | 返回 `"error: [Errno 2] No such file..."` | 看到错误，换个路径重试 |

关键在于：**对 AI 来说，「成功的结果」和「失败的结果」长得一模一样，都是一个字符串。** 它必须把字符串读一遍，于是自然就学会了自我纠正。

所以 AI 看起来「很聪明」，很大一部分不是模型的功劳，而是这个机制把错误喂回去让它有第二次机会。

**它同时兜住了三类错误：**

| 错误来源 | 例子 |
|---|---|
| 参数缺失 | `read({})` → `KeyError: 'path'` |
| 参数类型不对 | `offset: "1"` → `TypeError` |
| 运行时失败 | 文件不存在、目录不可读、正则语法错、命令超时 |

**顺便还有一个好处：工具名不存在也不会崩。**

`TOOLS[name][2]` 是在 `try` 内部求值的，所以模型幻想出一个不存在的工具名（比如 `"mkdir"`）时，`TOOLS["mkdir"]` 抛的 `KeyError` 同样被兜住，返回 `error: 'mkdir'`。模型看到就知道「这个工具没有」，可以改用别的。

---

### 7.4 这三部分怎么串起来

```text
        ┌──────────────────────────────────────────────┐
        │  TOOLS（小表，程序里写死）                    │
        │  "read": ("描述", {"path": ...}, read)       │
        └───────────────┬──────────────────────────────┘
                        │
         ┌──────────────┴───────────────┐
         │                              │
    make_schema()                  run_tool()
         │                              │
    JSON Schema                    TOOLS[name][2](args)
         │                              │
         ↓                              ↓
   call_api() 发给 AI            本地执行，结果变字符串
         │                              │
         └──────────→ AI ←──────────────┘
                   （说要用哪个工具）      （拿到结果）
```

**一个「加新工具」的完整例子：**

比如加一个 `mkdir`：

```python
# 1. 写函数（入参 dict，出参 str，不抛异常）
def mkdir(args):
    os.makedirs(args["path"], exist_ok=True)
    return "ok"

# 2. 加一行注册
TOOLS["mkdir"] = ("Create a directory", {"path": "string"}, mkdir)
```

**就这两步。** `make_schema()` 会自动把它翻译成 JSON Schema 发给 AI，`run_tool()` 会自动能找到它。不用改 `call_api()`、不用改 `main()`、不用手写 JSON。

这就是「写个小表 + 自动生成」这个设计的全部价值 —— **单一事实来源（single source of truth）**：工具的名字、描述、参数只在 `TOOLS` 里写一次。

> ⚠️ 但要注意「自动」的边界：`make_schema()` 只负责把 `TOOLS` 翻译成 API 认识的结构，**它不会检查你写的类型名对不对**。写成 `{"path": "strin"}` 这种笔误，会原样发给 API，然后在调用时被模型误解或直接报错。所以加工具时，类型名只能是 `string` / `number` / `boolean`（可选加 `?`）。

---

### 7.5 定义与执行的分界点

这三部分在 `nanocode.py` 里只有三个落地点：

| 位置 | 用了什么 | 干什么 |
|---|---|---|
| `call_api()` L179 | `make_schema()` | 把菜单塞进请求体的 `"tools"` 字段 |
| `main()` L239 | `run_tool(name, args)` | 模型说要用工具时，真正去执行 |
| `main()` L234 | `tool_args.values()` | 打印工具调用时取第一个参数做预览 |

**`call_api()` L170-189 里就这一句：**

```python
"tools": make_schema(),          # make_schema() 生成的菜单
```

**`main()` L239 附近这一段：**

```python
result = run_tool(tool_name, tool_args)      # 干活，永不抛异常
tool_results.append(
    {
        "type": "tool_result",
        "tool_use_id": block["id"],          # 对号：回应的是哪一次 tool_use
        "content": result,                   # 结果字符串，成功失败同一个字段
    }
)
```

**这两处就是「定义」和「执行」的分界点：**

- `make_schema()` **只往外出**：告诉 AI 有这些工具
- `run_tool()` **只往里进**：AI 说要哪个，就执行哪个

中间隔着一次网络往返。**程序不预测 AI 会调什么，也不校验它调得对不对** —— 全靠 `run_tool` 的 `try/except` 兜底，把错误当成普通消息再发回去。

---

## 附：测试目录

```text
tests/
├── test_read.py    test_write.py   test_edit.py
├── test_glob.py    test_grep.py    test_bash.py
└── fixtures/
    ├── read_sample.py        # read / grep 的输入
    ├── write_sample.py       # write 的输入
    ├── edit_sample.py        # edit 的输入
    ├── glob_sample_new.py    # glob 排序对比（新）
    └── glob_sample_old.py    # glob 排序对比（旧）
```

全部是纯 Python，不依赖 `pytest` / `unittest`。每个测试文件都能直接跑：

```powershell
python tests/test_read.py
python tests/test_bash.py
```

只有一个测试函数的文件跑完打印一行 `[PASS]`；有多个测试函数的文件会用 `banner()` 打印分隔线，方便看清每个用例的边界。
