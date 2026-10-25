# docs/assets

`nanocode-explained.md` 里的 13 张图。全部是手写 SVG，**不依赖 Mermaid、不需要任何插件**。

## 文件

| 文件 | 对应章节 |
|---|---|
| `01-roles.svg` | 0. 三方关系 |
| `02-main-loop.svg` | 1.1 主循环 |
| `03-block-dispatch.svg` | 1.2 块分拣 |
| `04-tool-use-id-pairing.svg` | 1.4 id 配对 |
| `05-history-resend.svg` | 1.5 历史重发 |
| `06-tool-contract.svg` | 2. 工具契约 |
| `07-read-slice.svg` | 2.1 read 切片 |
| `08-edit-decision.svg` | 2.3 edit 决策树 |
| `09-schema-pipeline.svg` | 3.2 schema 流水线 |
| `10-backend-switch.svg` | 4. 后端切换 |
| `11-nested-loops.svg` | 5. 三层嵌套 |
| `12-full-sequence.svg` | 6.1 全流程泳道 |
| `13-bash-timeout-bug.svg` | 7. bash 超时 bug |

## 改图

图是代码生成的，别手改 `.svg`（重新生成会覆盖）：

```bash
python docs/assets/figures.py
```

- `build.py` —— 绘图底座：配色表 `CO`、`Fig` 类的 `node / diamond / pill / arrow / tag / badge / card / frame`、以及共享 `<style>`。
- `figures.py` —— 每张图一个函数，里面就是坐标和文案，改数字就能挪框。

## 生成 HTML 版

`docs/index.html` 是从 Markdown 自动生成的，不要手改：

```bash
python docs/assets/build_html.py              # 默认：SVG 内联，单文件可离线/可发邮件
python docs/assets/build_html.py --external   # 图仍用 assets/*.svg 外链，文件小很多
```

- 依赖：`mistune`（Markdown 解析）+ `pygments`（代码高亮）。
- 图注、章节锚点、目录、阅读时长都是脚本自动算的；图注文案在 `build_html.py` 顶部的 `CAPTIONS`。
- `> 🔑 / 💡 / ⚠️ / 📌 / 🔍` 开头的引用块会自动变成带英文标签的 callout（KEY / TIP / WARN / NOTE / HINT），emoji 被标签替代。

### HTML 版的设计与 md 不同

它不是「给 Markdown 加样式」，而是一套独立的编辑型排版：

| 元素 | 做法 |
|---|---|
| 版心 | 居中 700px 正文，代码/表格向两侧各外溢 130px，图版外溢 230px |
| 章节号 | 巨大的描边数字挂在正文左侧空白里；小节号是 mono 小胶囊 |
| 目录 | 顶栏按钮或按 `T` 唤出全屏卡片式目录（不再是侧边栏） |
| 章节导航 | 左侧竖排刻度（rail），悬停显示章名；顶栏中央显示「当前在哪」 |
| 工具/问题 | 6 个工具与 6 条问题各自成卡片，问题卡按 🔴/🟡/🟢 上色边条 |
| 代码 | 永远是深色终端风（红黄绿三点 + 语言标签 + 复制） |
| 图 | 「PLATE 01」编号 + 说明，点击全屏放大 |
| 主题 | 默认深色，可切浅色，localStorage 记忆，无闪白 |
| 打印 | 强制浅色单栏，卡片/代码/图不跨页 |

内部实现要点（改样式时容易踩的）：

- `prettify` 之前的构建阶段分两步：先 `md()` 渲染（填充 `renderer.headings`），再 `prettify()`（包卡片、生成 hint），顺序不能反。
- `group_cards()` 给每个 `h3` 块单独包一个 `<section>`，不要改成「连续块包一个」——工具与问题两段 `h3` 在文档里是连着的，一改动就会互相吞掉。

## 设计约定

- **语义配色**：蓝 = 你，青 = 程序（nanocode.py），紫 = AI，绿 = 文件系统 / 工具执行，红 = 坑 / 错误路径，琥珀 = 强调。
- **等宽字体**只用于代码、字段名、函数名，中文说明用系统黑体。
- **流动虚线**表示"数据实际往这边流"，静态箭头表示控制流。
- 每张图 `<title>` / `<desc>` 齐全，动画有 `prefers-reduced-motion` 兜底。
- 纯白背景 + 点阵网格，深浅色阅读器下都看得清。
