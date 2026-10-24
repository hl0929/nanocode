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

## 设计约定

- **语义配色**：蓝 = 你，青 = 程序（nanocode.py），紫 = AI，绿 = 文件系统 / 工具执行，红 = 坑 / 错误路径，琥珀 = 强调。
- **等宽字体**只用于代码、字段名、函数名，中文说明用系统黑体。
- **流动虚线**表示"数据实际往这边流"，静态箭头表示控制流。
- 每张图 `<title>` / `<desc>` 齐全，动画有 `prefers-reduced-motion` 兜底。
- 纯白背景 + 点阵网格，深浅色阅读器下都看得清。
