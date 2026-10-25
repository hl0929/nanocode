# -*- coding: utf-8 -*-
"""Build the standalone HTML edition of docs/nanocode-explained.md.

    python docs/assets/build_html.py             # self-contained (SVG inlined)
    python docs/assets/build_html.py --external  # keep <img src="assets/..."> links

Output: docs/index.html

The Markdown stays the single source of truth; this script only changes the
presentation.  The HTML edition deliberately breaks away from the Markdown look:

* editorial grid — narrow text measure, full-bleed "plates" for the diagrams
* outlined chapter numerals in the gutter, mono index badges on subsections
* the six tool subsections and the seven issues become cards
* callouts become labelled panels (KEY / TIP / WARN / ...), emoji dropped
* always-dark "terminal" code blocks, dark-first theme, chapter rail + overlay TOC
"""

from __future__ import annotations

import html as htmllib
import os
import re
import sys
import urllib.parse

import mistune
from mistune.renderers.html import HTMLRenderer
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer, MarkdownLexer, PythonLexer, TextLexer, get_lexer_by_name

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # docs/
SRC = os.path.join(ROOT, "nanocode-explained.md")
OUT = os.path.join(ROOT, "index.html")

# ---------------------------------------------------------------------------
# figure captions (better than the terse alt="" in the Markdown)
# ---------------------------------------------------------------------------
CAPTIONS = {
    "01-roles.svg": "谁碰得到硬盘，谁碰不到",
    "02-main-loop.svg": "那个「圈」到底怎么转",
    "03-block-dispatch.svg": "一个 response 怎么被拆开处理",
    "04-tool-use-id-pairing.svg": "为什么 <code>tool_use_id</code> 必须对上",
    "05-history-resend.svg": "为什么每轮都要整个重发",
    "06-tool-contract.svg": "六个工具的共同形状",
    "07-read-slice.svg": "<code>offset</code> / <code>limit</code> 到底切哪几行",
    "08-edit-decision.svg": "只有一条路能走到写盘",
    "09-schema-pipeline.svg": "小表怎么变成 JSON",
    "10-backend-switch.svg": "一个环境变量决定整条链路",
    "11-nested-loops.svg": "三个 while / for 谁管谁",
    "12-full-sequence.svg": "一次提问的完整来回",
    "13-bash-timeout-bug.svg": "<code>readline()</code> 把超时卡死",
}

LEXERS = {
    "python": PythonLexer,
    "py": PythonLexer,
    "json": JsonLexer,
    "markdown": MarkdownLexer,
    "md": MarkdownLexer,
}

# blockquote markers -> (callout kind, english label)
MARKERS = [
    ("🔑", "key", "KEY"),
    ("💡", "tip", "TIP"),
    ("⚠", "warn", "WARN"),
    ("📌", "pin", "NOTE"),
    ("🔍", "hint", "HINT"),
    ("🧠", "key", "KEY"),
]
MARKER_CHARS = "".join(m[0] for m in MARKERS)

SEVERITY = {"🔴": ("high", "严重"), "🟡": ("med", "中等"), "🟢": ("low", "轻微")}

H2_GLYPH = {"附录": "§", "最后": "→", "一句话": "★", "目录": "≡"}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def slugify(text: str) -> str:
    """GitHub-flavoured anchor slug (keeps CJK, drops punctuation)."""
    out = []
    for ch in text.strip().lower():
        if ch.isalnum() or ch in "-_":
            out.append(ch)
        elif ch in " \t":
            out.append("-")
    return "".join(out)


def plain(fragment: str) -> str:
    txt = re.sub(r"<[^>]+>", "", fragment)
    return htmllib.unescape(txt).strip()


NUM_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+")


def split_number(label: str) -> tuple[str, str]:
    """'2.1 read' -> ('2.1', 'read'); '1. 核心机制：一个圈' -> ('1', '核心机制：一个圈')"""
    m = NUM_RE.match(label)
    if not m:
        return "", label
    return m.group(1), label[m.end():].strip()


# ---------------------------------------------------------------------------
# renderer
# ---------------------------------------------------------------------------
class DocRenderer(HTMLRenderer):
    def __init__(self, inline_svg: bool):
        super().__init__()
        self.headings: list[dict] = []
        self.slugs: dict[str, int] = {}
        self.quote_count = 0
        self.figs: list[str] = []
        self.inline_svg = inline_svg

    # -- headings ---------------------------------------------------------
    def heading(self, text: str, level: int, **attrs) -> str:
        label = plain(text)
        base = slugify(label) or "section"
        n = self.slugs.get(base, 0)
        self.slugs[base] = n + 1
        slug = base if n == 0 else f"{base}-{n}"

        # strip a leading emoji (🔴 …) but keep it as a coloured marker
        marker = ""
        for emoji, (kind, _word) in SEVERITY.items():
            if label.startswith(emoji):
                marker = emoji
                label_clean = label[len(emoji):].strip()
                text_clean = re.sub(r"^\s*" + re.escape(emoji) + r"\s*", "", text, count=1)
                break
        else:
            label_clean, text_clean = label, text

        num, rest = split_number(label_clean)
        if marker:
            num = "●"
        elif not num:
            num = "·" if level >= 3 else next(
                (g for k, g in H2_GLYPH.items() if label_clean.startswith(k)), "§"
            )
        if num != "●" and rest:
            # drop "1. " / "2.1 " from the rendered inline HTML too
            text_clean = re.sub(r"^\s*\d+(?:\.\d+)*\.?\s+", "", text_clean, count=1)
        elif num == "●":
            text_clean = label_clean

        kind = ""
        if marker:
            kind = f" sev-{SEVERITY[marker][0]}"
        self.headings.append(
            {"level": level, "num": num, "text": rest or label_clean, "slug": slug}
        )
        if level >= 3:
            return (
                f'<h{level} id="{slug}" class="h-sub{kind}">'
                f'<span class="h-num">{num}</span>'
                f'<span class="h-text">{text_clean}</span>'
                f'<a class="h-anchor" href="#{slug}" aria-hidden="true">#</a></h{level}>\n'
            )
        return (
            f'<h{level} id="{slug}" class="h-chap{kind}">'
            f'<span class="h-num" aria-hidden="true">{num}</span>'
            f'<span class="h-text">{text_clean}</span>'
            f'<a class="h-anchor" href="#{slug}" aria-hidden="true">#</a></h{level}>\n'
        )

    # -- blockquote -> labelled panels -----------------------------------
    def block_quote(self, text: str) -> str:
        self.quote_count += 1
        lede = self.quote_count == 1
        chunks = [c for c in re.split(r"(?=<p>)", text.strip()) if c.strip()] or [text.strip()]

        groups: list[tuple[str | None, list[str]]] = []
        for chunk in chunks:
            kind = self._marker(chunk) or (groups[-1][0] if groups else None)
            if groups and groups[-1][0] == kind:
                groups[-1][1].append(chunk)
            else:
                groups.append((kind, [chunk]))

        out = []
        for kind, parts in groups:
            inner = "".join(parts).replace(' data-m="', ' data-x="')
            if kind is None:
                if lede:
                    out.append(
                        '<aside class="preface" data-label="PREFACE">'
                        '<div class="preface-body">%s</div></aside>\n' % inner
                    )
                else:
                    out.append('<aside class="note">%s</aside>\n' % inner)
                continue
            label = dict((k, l) for _e, k, l in MARKERS)[kind]
            out.append(
                f'<aside class="callout c-{kind}" data-label="{label}">'
                f'<div class="callout-body">{inner}</div></aside>\n'
            )
        return "".join(out)

    @staticmethod
    def _marker(chunk: str) -> str | None:
        m = re.match(r'<p data-m="(\w+)"', chunk)
        return m.group(1) if m else None

    def paragraph(self, text: str) -> str:
        # Keep the emoji out of the flow but remember it: block_quote turns it
        # into a labelled panel, and that label replaces the emoji.
        m = re.match(r"^\s*([" + re.escape(MARKER_CHARS) + r"])\ufe0f?\s*", text)
        if not m:
            return f"<p>{text}</p>\n"
        kind = {e: k for e, k, _l in MARKERS}[m.group(1)]
        return f'<p data-m="{kind}">{text[m.end():]}</p>\n'

    # -- code -------------------------------------------------------------
    def block_code(self, code: str, info: str | None = None) -> str:
        lang = (info or "").strip().split()[0].lower() if info else ""
        lexer_cls = LEXERS.get(lang)
        if lexer_cls is not None:
            lexer = lexer_cls(stripnl=False)
        elif lang:
            try:
                lexer = get_lexer_by_name(lang, stripnl=False)
            except Exception:
                lexer = TextLexer(stripnl=False)
        else:
            lexer = TextLexer(stripnl=False)

        body = highlight(code, lexer, HtmlFormatter(nowrap=True)).rstrip("\n")
        label = lang or "text"
        return (
            '<div class="code-card" data-lang="%s">'
            '<div class="code-head"><span class="dots"><i></i><i></i><i></i></span>'
            '<span class="code-lang">%s</span>'
            '<button class="code-copy" type="button" data-copy>复制</button></div>'
            '<pre class="hl"><code>%s</code></pre></div>\n'
            % (htmllib.escape(label), htmllib.escape(label), body)
        )

    # -- inline -----------------------------------------------------------
    def codespan(self, text: str) -> str:
        # mistune hands us the raw span; `\|` is markdown's table-cell escape
        return "<code>%s</code>" % htmllib.escape(text.replace("\\|", "|"))

    def inline_html(self, html_text: str) -> str:
        return html_text

    def block_html(self, html_text: str) -> str:
        return self._figure(html_text)

    # -- figures ----------------------------------------------------------
    def _figure(self, raw: str) -> str:
        m = re.search(
            r'<img\s+src="assets/([\w.\-]+\.svg)"[^>]*?width="(\d+)"[^>]*?alt="([^"]*)"', raw
        )
        if not m:
            return raw
        name, width, alt = m.group(1), m.group(2), m.group(3)
        self.figs.append(name)
        idx = len(self.figs)
        caption = CAPTIONS.get(name, htmllib.escape(alt))
        media = (
            self._inline(name, idx, width, alt)
            if self.inline_svg
            else f'<img src="assets/{name}" alt="{htmllib.escape(alt)}" '
            f'width="{width}" loading="lazy" decoding="async">'
        )
        return (
            f'<figure class="plate" id="fig-{idx}" data-fig="{name}">'
            f'<div class="plate-frame" data-zoom>{media}'
            f'<span class="plate-zoom" aria-hidden="true">⤢</span></div>'
            f'<figcaption><span class="plate-num">PLATE {idx:02d}</span>'
            f'<span class="plate-cap">{caption}</span></figcaption></figure>\n'
        )

    @staticmethod
    def _inline(name: str, idx: int, width: str, alt: str) -> str:
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            svg = f.read()
        prefix = f"f{idx}-"
        for ident in set(re.findall(r'id="([^"]+)"', svg)):
            svg = svg.replace(f'id="{ident}"', f'id="{prefix}{ident}"')
            svg = svg.replace(f"url(#{ident})", f"url(#{prefix}{ident})")
            svg = svg.replace(f'href="#{ident}"', f'href="#{prefix}{ident}"')
        # let CSS drive the size: keep viewBox, drop fixed pixel box
        svg = svg.replace(' style="background:#ffffff;max-width:100%;height:auto"', "")
        svg = re.sub(r'(<svg[^>]*?)\swidth="\d+"\s+height="\d+"', r"\1", svg, count=1)
        svg = re.sub(r'\s+role="img"', "", svg)
        svg = re.sub(r'\s+aria-label="[^"]*"', "", svg, count=1)
        svg = svg.replace("<svg ", f'<svg class="plate-svg" role="img" aria-label="{htmllib.escape(alt)}" ', 1)
        return svg.strip()


# ---------------------------------------------------------------------------
# markdown pre-processing
# ---------------------------------------------------------------------------
def merge_blockquotes(src: str) -> str:
    """Normalise `>` blocks so each callout gets its own blockquote.

    1. a blank line between two `>` blocks still means one quote
    2. a new marker line (💡 / ⚠ / ...) starts a fresh paragraph so it can
       become its own labelled panel
    """
    lines = src.split("\n")
    out: list[str] = []
    fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fence = not fence
        if not fence and not line.strip() and out and out[-1].lstrip().startswith(">"):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].lstrip().startswith(">"):
                continue
        if not fence and line.lstrip().startswith(">"):
            content = line.lstrip()[1:].lstrip()
            prev = out[-1].lstrip()[1:].lstrip() if out and out[-1].lstrip().startswith(">") else None
            if content and content[0] in MARKER_CHARS and prev:
                out.append(">")
        out.append(line)
    return "\n".join(out)


def demote_h1(src: str) -> str:
    return re.sub(r"\A# .*\n", "", src, count=1)


# ---------------------------------------------------------------------------
# post-processing: turn flat h3 runs into cards
# ---------------------------------------------------------------------------
def _split_at_headings(body: str) -> list[str]:
    return [p for p in re.split(r"(?=<(?:h2|h3) )", body) if p]


H3_ID = re.compile(r'^<h3 id="([^"]+)" class="h-sub(?: (sev-\w+))?"')


def _card_kind(part: str) -> tuple[str, str] | None:
    """Classify a section chunk: ('tool'|'issue', key) or None."""
    m = H3_ID.match(part)
    if not m:
        return None
    if m.group(2):                              # severity class -> issue card
        return ("issue", m.group(2))
    if re.match(r"^2\d-", m.group(1)):         # 2.x -> tool card
        return ("tool", m.group(1).split("-", 1)[1])
    return None


def group_cards(body: str) -> str:
    """Wrap each tool (2.x) and each severity-tagged issue in its own card.

    `_split_at_headings` yields one chunk per heading (heading + its body), so a
    card == a chunk; no run-grouping needed.
    """
    out: list[str] = []
    for part in _split_at_headings(body):
        hit = _card_kind(part)
        if not hit:
            out.append(part)
            continue
        kind, key = hit
        if kind == "tool":
            out.append(f'<section class="tool" data-tool="{htmllib.escape(key)}">')
        else:
            out.append(f'<section class="issue {key}">')
        out.append(part)
        out.append("</section>")
    return "".join(out)


def prettify(body: str, n_ch: int = 0, n_sub: int = 0) -> str:
    """Small structural upgrades that CSS alone cannot do."""
    body = re.sub(r"<table>", '<div class="table-wrap"><table>', body)
    body = re.sub(r"</table>", "</table></div>", body)
    # mistune percent-encodes fragments; our ids are raw CJK
    body = re.sub(
        r'href="#([^"]+)"', lambda m: 'href="#%s"' % urllib.parse.unquote(m.group(1)), body
    )
    body = group_cards(body)
    # the in-page TOC list duplicates the overlay TOC; swap it for a trigger
    hint = (
        '<h2 id="目录" class="h-chap"><span class="h-num" aria-hidden="true">≡</span>'
        '<span class="h-text">目录</span></h2>'
        f'<div class="toc-hint"><span>共 <b>{n_ch}</b> 章 <b>{n_sub}</b> 节，'
        '也可以随时按 <code>T</code> 唤出浮动目录。</span>'
        '<button type="button" data-open-toc>打开目录</button></div>'
    )
    body = re.sub(
        r'<h2 id="目录" class="h-chap">.*?(?=<h2 )',
        lambda _m: hint + "\n",
        body,
        count=1,
        flags=re.S,
    )
    return body


# ---------------------------------------------------------------------------
# navigation payloads
# ---------------------------------------------------------------------------
def chapters(headings: list[dict]) -> list[dict]:
    """[[h2, [h3, ...]], ...] — the `目录` section itself is not a chapter."""
    out: list[dict] = []
    for h in headings:
        if h["level"] == 2:
            if h["text"].strip() == "目录":
                out.append({"skip": True})
                continue
            out.append({**h, "subs": []})
        elif out["ch" if False else -1] and h["level"] == 3:
            if not out[-1].get("skip"):
                out[-1]["subs"].append(h)
    return [c for c in out if not c.get("skip")]


def chapter_rail(chs: list[dict]) -> str:
    items = []
    for c in chs:
        num = c["num"]
        items.append(
            f'<a class="rail-dot" href="#{c["slug"]}" data-target="{c["slug"]}">'
            f'<span class="rail-num">{num}</span>'
            f'<span class="rail-label">{htmllib.escape(c["text"])}</span></a>'
        )
    return "".join(items)


def toc_overlay(chs: list[dict]) -> str:
    cards = []
    for c in chs:
        num = c["num"]
        label = f"{int(num):02d}" if num.isdigit() else num
        subs = "".join(
            f'<li><a href="#{sub["slug"]}">'
            f'<span class="toc-sub-num">{htmllib.escape(sub["num"])}</span>'
            f'<span>{htmllib.escape(sub["text"])}</span></a></li>'
            for sub in c["subs"]
        )
        subs_html = f'<ul class="toc-sub">{subs}</ul>' if subs else ""
        cards.append(
            f'<div class="toc-card"><a class="toc-card-head" href="#{c["slug"]}">'
            f'<span class="toc-card-num">{label}</span>'
            f'<span class="toc-card-title">{htmllib.escape(c["text"])}</span></a>'
            f"{subs_html}</div>"
        )
    return "".join(cards)


def hero_chips(chs: list[dict]) -> str:
    out = []
    for c in chs:
        num = c["num"]
        out.append(
            f'<a class="chip" href="#{c["slug"]}">'
            f'<b>{num}</b>{htmllib.escape(c["text"])}</a>'
        )
    return "".join(out)


def pygments_css() -> str:
    """One dark, always-on palette for the terminal-style code blocks."""
    css = HtmlFormatter(style="one-dark").get_style_defs(".hl")
    css = re.sub(r"^[^\n{]*\.hl \{\s*background:[^}]*\}\n?", "", css, flags=re.M)
    css = css.replace("#282C34", "transparent")
    return css


# ---------------------------------------------------------------------------
# page CSS
# ---------------------------------------------------------------------------
CSS = r"""
/* ============================================================== tokens */
:root{
  --font-sans:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB",
    "Microsoft YaHei","Noto Sans SC",sans-serif;
  --font-mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
  --rail:92px;
  --measure:700px;
  --gutter:82px;          /* hanging numeral column, sits left of the text */
  --spill:130px;          /* how far code/tables may grow on both sides */
  --spill-wide:230px;     /* … and full plates */
  --pad:clamp(20px,3.4vw,52px);
  --ease:cubic-bezier(.2,.7,.3,1);
}
:root[data-theme="light"]{
  --bg:#f6f5f1; --bg-elev:#fbfaf7; --panel:#ffffff; --panel-2:#f2f1ec;
  --ink:#14161b; --ink-2:#3b4250; --ink-3:#787f8d; --ink-4:#a3a8b3;
  --line:#e3e1d8; --line-2:#eeece5;
  --accent:#a15c07; --accent-soft:#f6ecdb; --accent-ink:#7b4405;
  --teal:#0d7268; --indigo:#3f51b5; --violet:#6d3fa8; --red:#b4382f; --amber:#a15c07;
  --ghost:rgba(20,22,27,.17);
  --shadow:0 1px 2px rgba(20,22,27,.05),0 18px 44px -34px rgba(20,22,27,.45);
  --shadow-lg:0 30px 90px -40px rgba(20,22,27,.5);
  --code-bg:#0f1319; --code-ink:#d9e0ec; --glow:rgba(161,92,7,.10);
}
:root[data-theme="dark"]{
  --bg:#0a0b0e; --bg-elev:#101217; --panel:#13161c; --panel-2:#171b22;
  --ink:#eef0f4; --ink-2:#b7bfcc; --ink-3:#7e8695; --ink-4:#5a626f;
  --line:#232833; --line-2:#1a1e26;
  --accent:#f2b74b; --accent-soft:#241d0f; --accent-ink:#f2b74b;
  --teal:#5eead4; --indigo:#8b9cff; --violet:#c4a4ff; --red:#ff7b72; --amber:#f2b74b;
  --ghost:rgba(238,240,244,.15);
  --shadow:0 1px 2px rgba(0,0,0,.4),0 24px 60px -40px rgba(0,0,0,.9);
  --shadow-lg:0 40px 120px -50px rgba(0,0,0,1);
  --code-bg:#0b0e13; --code-ink:#d9e0ec; --glow:rgba(242,183,75,.10);
}

*{box-sizing:border-box}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *{animation:none!important;transition:none!important}
}
body{
  margin:0;background:var(--bg);color:var(--ink-2);
  font-family:var(--font-sans);font-size:16.5px;line-height:1.9;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
  font-feature-settings:"kern" 1,"liga" 1;
  overflow-x:hidden;
}
body::before{                       /* ambient light behind the top of the page */
  content:"";position:fixed;inset:-20vh 0 auto 0;height:70vh;pointer-events:none;z-index:0;
  background:radial-gradient(60% 100% at 62% 0%,var(--glow),transparent 70%);
}
::selection{background:var(--accent-soft);color:var(--ink)}
a{color:inherit}
img,svg{max-width:100%}

/* ============================================================== chrome */
.topbar{
  position:fixed;inset:0 0 auto 0;height:56px;z-index:60;
  display:flex;align-items:center;gap:16px;padding:0 22px;
  background:color-mix(in srgb,var(--bg) 82%,transparent);
  backdrop-filter:saturate(150%) blur(14px);
  border-bottom:1px solid transparent;transition:border-color .2s,background .2s;
}
.topbar.stuck{border-bottom-color:var(--line)}
.brand{display:flex;align-items:center;gap:9px;font-family:var(--font-mono);
  font-size:13.5px;font-weight:700;color:var(--ink);letter-spacing:-.01em;flex:none}
.brand-mark{width:22px;height:22px;border-radius:7px;display:grid;place-items:center;
  background:linear-gradient(140deg,var(--accent),color-mix(in srgb,var(--accent) 45%,var(--violet)));
  color:#12141a;font-size:12px;font-weight:800}
.brand-sep{color:var(--ink-4);font-weight:400}
.brand-sub{color:var(--ink-3);font-weight:500;font-size:12.5px}
.now{flex:1;min-width:0;text-align:center;font-size:12.5px;color:var(--ink-3);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:var(--font-mono)}
.now b{color:var(--accent);font-weight:700}
.actions{display:flex;align-items:center;gap:8px;flex:none}
.iconbtn{
  appearance:none;border:1px solid var(--line);background:var(--panel);color:var(--ink-2);
  font:inherit;font-size:12.5px;padding:7px 11px;border-radius:9px;cursor:pointer;
  display:inline-flex;align-items:center;gap:6px;transition:background .15s,color .15s,border-color .15s;
}
.iconbtn:hover{background:var(--panel-2);color:var(--ink)}
.iconbtn kbd{font-family:var(--font-mono);font-size:10.5px;color:var(--ink-4);
  border:1px solid var(--line);border-bottom-width:2px;border-radius:4px;padding:0 4px}
.progress{position:fixed;top:0;left:0;height:2px;width:0;z-index:70;
  background:linear-gradient(90deg,var(--accent),var(--violet));transition:width .08s linear}

/* ============================================================== chapter rail */
.rail{
  position:fixed;left:0;top:56px;bottom:0;width:var(--rail);z-index:40;
  display:flex;flex-direction:column;justify-content:center;gap:2px;
  padding:20px 0 32px;border-right:1px solid transparent;
}
.rail-dot{
  display:flex;align-items:center;gap:10px;height:30px;padding-left:26px;
  text-decoration:none;color:var(--ink-4);position:relative;
}
.rail-dot::before{                       /* tick */
  content:"";width:14px;height:1px;background:currentColor;flex:none;
  transition:width .25s var(--ease),background .25s,color .25s;
}
.rail-num{font-family:var(--font-mono);font-size:11.5px;font-weight:700;letter-spacing:.04em}
.rail-label{
  position:absolute;left:calc(var(--rail) + 6px);top:50%;translate:0 -50%;
  white-space:nowrap;font-size:12px;color:var(--ink-2);background:var(--panel);
  border:1px solid var(--line);border-radius:8px;padding:3px 10px;
  opacity:0;pointer-events:none;transition:opacity .18s,translate .18s;box-shadow:var(--shadow);
  max-width:46vw;overflow:hidden;text-overflow:ellipsis;
}
.rail-dot:hover{color:var(--ink-2)}
.rail-dot:hover .rail-label{opacity:1;translate:4px -50%}
.rail-dot.active{color:var(--accent)}
.rail-dot.active::before{width:26px;background:var(--accent)}
.rail-dot.active .rail-num{font-size:12.5px}

/* ============================================================== shell */
.wrap{position:relative;z-index:1;padding-left:var(--rail)}
.shell{max-width:calc(var(--measure) + 2 * var(--spill-wide));
  margin:0 auto;padding:0 var(--pad)}

/* ============================================================== hero */
.hero{padding:126px 0 58px;position:relative;
  max-width:var(--measure);margin-inline:auto}

.hero-eyebrow{display:inline-flex;align-items:center;gap:9px;
  font-family:var(--font-mono);font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--accent);margin-bottom:26px}
.hero-eyebrow::before{content:"";width:26px;height:1px;background:currentColor}
.hero h1{
  margin:0 0 26px;font-size:clamp(40px,5.6vw,74px);line-height:1.04;font-weight:850;
  letter-spacing:-.04em;color:var(--ink);
  margin-right:calc(-1 * var(--spill));max-width:none;
}
.hero h1 em{
  font-style:normal;color:transparent;
  background:linear-gradient(120deg,var(--accent),var(--violet) 65%,var(--teal));
  -webkit-background-clip:text;background-clip:text;
}
.hero .standfirst{
  margin:0 0 34px;max-width:60ch;font-size:clamp(16px,1.5vw,19px);line-height:1.75;
  color:var(--ink-2);
}
.stats{display:flex;flex-wrap:wrap;gap:34px;padding:22px 0;border-top:1px solid var(--line);
  border-bottom:1px solid var(--line);margin-bottom:30px}
.stat{display:flex;flex-direction:column;gap:2px}
.stat b{font-family:var(--font-mono);font-size:22px;font-weight:700;color:var(--ink);
  letter-spacing:-.02em;line-height:1.2}
.stat span{font-size:11.5px;color:var(--ink-3);letter-spacing:.08em;text-transform:uppercase}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{
  display:inline-flex;align-items:center;gap:8px;text-decoration:none;
  font-size:13px;color:var(--ink-2);background:var(--panel);border:1px solid var(--line);
  border-radius:999px;padding:6px 14px 6px 7px;transition:border-color .15s,color .15s,background .15s;
}
.chip b{font-family:var(--font-mono);font-size:11px;font-weight:700;color:var(--accent);
  background:var(--accent-soft);border-radius:999px;min-width:20px;height:20px;
  display:grid;place-items:center;padding:0 5px}
.chip:hover{border-color:var(--accent);color:var(--ink)}

/* ============================================================== grid */
/* Centred measure + symmetric spill. The text column is optically centred in
   the viewport; code/tables grow both ways, plates grow more, chapter numerals
   hang into the left margin so the text edge stays flush. */
.reading{
  max-width:var(--measure);
  margin-inline:auto;
  padding-bottom:130px;
}
.reading>*{min-width:0}
.reading>.code-card,
.reading>.table-wrap,
.reading>.tool,
.reading>.issue,
.reading>.callout,
.reading>.note,
.reading>.preface,
.reading>.toc-hint{
  margin-inline:calc(-1 * var(--spill));
}
.reading>figure.plate,
.reading>hr{
  margin-inline:calc(-1 * var(--spill-wide));
}
/* the markdown TOC list is replaced by .toc-hint in the builder */
.reading>h2#目录+ul{display:none}

.toc-hint{
  display:flex;align-items:center;gap:14px;flex-wrap:wrap;
  padding:18px 22px;border-radius:16px;background:var(--panel);
  border:1px dashed color-mix(in srgb,var(--accent) 40%,var(--line));
  font-size:14px;color:var(--ink-3);margin-block:0 8px;
}
.toc-hint b{color:var(--ink);font-weight:650}
.toc-hint button{
  margin-left:auto;appearance:none;border:1px solid var(--line);background:var(--panel-2);
  color:var(--ink-2);font:inherit;font-size:12.5px;padding:7px 14px;border-radius:9px;
  cursor:pointer;transition:border-color .15s,color .15s;
}
.toc-hint button:hover{border-color:var(--accent);color:var(--accent)}

/* ============================================================== headings */
.h-chap{
  position:relative;
  margin:106px 0 26px;padding-top:26px;border-top:1px solid var(--line);
  font-size:clamp(25px,2.7vw,33px);line-height:1.28;font-weight:800;letter-spacing:-.028em;
  color:var(--ink);scroll-margin-top:84px;
}
.h-chap:first-of-type{margin-top:24px;border-top:none;padding-top:0}
.h-chap .h-num{
  position:absolute;right:100%;bottom:.06em;padding-right:.4em;
  font-family:var(--font-mono);font-size:clamp(30px,3.2vw,46px);
  font-weight:800;line-height:.8;color:var(--ghost);letter-spacing:-.05em;
  user-select:none;white-space:nowrap;
}
.h-sub{
  position:relative;
  margin:48px 0 14px;font-size:clamp(17px,1.5vw,19px);line-height:1.55;
  font-weight:700;color:var(--ink);letter-spacing:-.012em;scroll-margin-top:82px;
}
.h-sub .h-num{
  position:absolute;right:100%;top:.14em;margin-right:.5em;
  font-family:var(--font-mono);font-size:10.5px;font-weight:700;
  color:var(--accent);border:1px solid color-mix(in srgb,var(--accent) 38%,transparent);
  border-radius:5px;padding:1px 6px;line-height:1.6;user-select:none;white-space:nowrap;
}
.h-sub.sev-high,.h-sub.sev-med,.h-sub.sev-low{color:var(--ink)}
.h-sub.sev-high .h-num,.h-sub.sev-med .h-num,.h-sub.sev-low .h-num{
  border:none;background:none;padding:0;font-size:15px;line-height:1;top:.1em;
  margin-right:.62em;
}
.h-sub.sev-high .h-num{color:var(--red)}
.h-sub.sev-med .h-num{color:var(--amber)}
.h-sub.sev-low .h-num{color:var(--teal)}
.h-sub code,.h-chap code{font-size:.92em}
.h-anchor{
  position:relative;display:inline-block;margin-left:.3em;text-decoration:none;
  color:var(--line);font-weight:600;opacity:0;transition:opacity .15s,color .15s;
}
.h-chap:hover .h-anchor,.h-sub:hover .h-anchor{opacity:1;color:var(--ink-4)}

/* ============================================================== standfirst & panels */
.preface{
  position:relative;margin:0 0 40px;padding:26px 28px 22px;border-radius:18px;
  background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);
}
.preface::before{
  content:attr(data-label);position:absolute;top:-9px;left:22px;
  font-family:var(--font-mono);font-size:10px;font-weight:800;letter-spacing:.16em;
  padding:2px 9px;border-radius:999px;background:var(--bg);color:var(--ink-3);
  border:1px solid var(--line);
}
.preface-body>*:first-child{margin-top:0}
.preface-body>*:last-child{margin-bottom:0}
.preface-body p{margin:.6em 0;font-size:15.5px;line-height:1.85}
.preface-body p:first-child{color:var(--ink);font-size:16.5px}
.callout,.note{
  position:relative;margin:34px 0;padding:24px 24px 20px;border-radius:16px;
  background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);
}
.callout::before{
  content:attr(data-label);position:absolute;top:-9px;left:20px;
  font-family:var(--font-mono);font-size:10px;font-weight:800;letter-spacing:.14em;
  padding:2px 9px;border-radius:999px;background:var(--bg);
  color:var(--c,var(--ink-3));border:1px solid color-mix(in srgb,var(--c,var(--ink-3)) 45%,transparent);
}
.callout-body>*:first-child{margin-top:0}
.callout-body>*:last-child{margin-bottom:0}
.callout-body p{font-size:15.5px;line-height:1.85;color:var(--ink-2);margin:.5em 0}
.callout-body p>strong:first-child{color:var(--ink)}
.c-key{--c:var(--amber)}
.c-tip{--c:var(--teal)}
.c-warn{--c:var(--red)}
.c-pin{--c:var(--indigo)}
.c-hint{--c:var(--violet)}
.callout{background:color-mix(in srgb,var(--c) 5%,var(--panel))}
.note{background:var(--panel-2);padding:18px 22px}
.note p{font-size:14.5px;color:var(--ink-3);margin:.4em 0}

/* ============================================================== code */
.code-card{
  position:relative;margin:32px 0;border-radius:16px;overflow:hidden;
  background:var(--code-bg);box-shadow:var(--shadow),inset 0 0 0 1px rgba(255,255,255,.05);
}
.code-head{
  display:flex;align-items:center;gap:12px;padding:10px 14px;
  border-bottom:1px solid rgba(255,255,255,.07);
  background:linear-gradient(180deg,rgba(255,255,255,.04),transparent);
}
.dots{display:flex;gap:5px}
.dots i{width:9px;height:9px;border-radius:50%;background:rgba(255,255,255,.14);display:block}
.dots i:nth-child(1){background:#e05252}
.dots i:nth-child(2){background:#db9d3f}
.dots i:nth-child(3){background:#3fa06a}
.code-lang{font-family:var(--font-mono);font-size:10.5px;letter-spacing:.16em;
  text-transform:uppercase;color:rgba(233,240,252,.42);font-weight:700}
.code-copy{
  margin-left:auto;appearance:none;border:1px solid rgba(255,255,255,.12);
  background:transparent;color:rgba(233,240,252,.55);font:inherit;font-size:11px;
  padding:3px 9px;border-radius:6px;cursor:pointer;
  transition:background .15s,color .15s,border-color .15s;
}
.code-copy:hover{background:rgba(255,255,255,.07);color:#fff}
.code-copy.done{color:#7ee2b8;border-color:rgba(126,226,184,.5)}
.code-card pre{
  margin:0;padding:16px 18px 18px;overflow-x:auto;background:transparent;
  font-family:var(--font-mono);font-size:13.2px;line-height:1.75;color:var(--code-ink);
  tab-size:4;
}
.code-card pre code{background:none;border:none;padding:0;font-size:inherit;color:inherit;
  font-family:inherit;white-space:pre}
.code-card pre::-webkit-scrollbar{height:8px}
.code-card pre::-webkit-scrollbar-thumb{background:rgba(255,255,255,.14);border-radius:8px}

/* ============================================================== tables */
.table-wrap{
  margin:32px 0;border:1px solid var(--line);border-radius:16px;overflow:hidden;
  background:var(--panel);box-shadow:var(--shadow);
}
.table-wrap table{border-collapse:collapse;width:100%;font-size:14.5px}
.table-wrap th,.table-wrap td{padding:11px 16px;text-align:left;vertical-align:top;
  border-bottom:1px solid var(--line-2)}
.table-wrap th{background:var(--panel-2);color:var(--ink);font-weight:700;font-size:12px;
  letter-spacing:.06em;text-transform:uppercase;white-space:nowrap}
.table-wrap tbody tr:last-child td{border-bottom:none}
.table-wrap tbody tr:hover{background:color-mix(in srgb,var(--accent) 4%,transparent)}
.table-wrap td code{white-space:nowrap}

/* ============================================================== plates (figures) */
.plate{margin:52px 0}
.plate-frame{
  position:relative;padding:16px;border-radius:20px;
  background:#fff;border:1px solid var(--line);
  box-shadow:0 1px 2px rgba(15,23,42,.05),0 30px 70px -50px rgba(15,23,42,.5);
  cursor:zoom-in;overflow:hidden;
}
.plate-frame::after{
  content:"";position:absolute;inset:0;border-radius:20px;pointer-events:none;
  box-shadow:inset 0 0 0 1px rgba(15,23,42,.06);
}
.plate-frame:hover .plate-zoom{opacity:1;translate:0 0}
.plate-svg,.plate-frame img{display:block;width:100%;height:auto;border-radius:9px}
.plate-svg text{fill:#0f172a}
.plate-zoom{
  position:absolute;right:16px;bottom:16px;width:32px;height:32px;border-radius:9px;
  background:rgba(15,23,42,.72);color:#fff;display:grid;place-items:center;font-size:15px;
  opacity:0;translate:0 6px;transition:opacity .18s,translate .18s;pointer-events:none;
}
.plate figcaption{
  display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;
  margin:16px 0 0;padding-left:2px;font-size:13.5px;color:var(--ink-3);
}
.plate-num{
  font-family:var(--font-mono);font-size:10px;font-weight:800;letter-spacing:.18em;
  color:var(--accent);border-top:1px solid color-mix(in srgb,var(--accent) 45%,transparent);
  padding-top:2px;
}
.plate-cap{color:var(--ink-2)}

/* lightbox */
.lightbox{position:fixed;inset:0;z-index:90;display:none;place-items:center;padding:3vmin;
  background:rgba(6,8,12,.9);backdrop-filter:blur(6px);cursor:zoom-out}
.lightbox.on{display:grid}
.lightbox-inner{background:#fff;border-radius:18px;padding:16px;max-width:96vw;max-height:92vh;
  overflow:auto;box-shadow:0 50px 140px -30px rgba(0,0,0,.85)}
.lightbox-inner svg,.lightbox-inner img{display:block;width:min(1500px,92vw);height:auto}

/* ============================================================== tool cards */
.tool{
  position:relative;margin:22px 0;padding:4px 26px 22px;border-radius:20px;
  background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);
  overflow:hidden;
}
.tool::before{
  content:"";position:absolute;left:0;top:0;bottom:0;width:3px;
  background:linear-gradient(180deg,var(--accent),color-mix(in srgb,var(--accent) 15%,transparent));
}
.tool .h-sub{margin-top:26px}
.tool .h-sub .h-num{position:static;margin-right:10px;font-size:11px;
  border:none;background:var(--accent-soft);color:var(--accent-ink);padding:1px 7px;border-radius:5px}
.tool .h-sub .h-num::before{content:"tool "}
.tool .h-anchor{right:0}
.tool p,.tool li{font-size:15.5px;line-height:1.85}
.tool>.code-card{margin:18px 0}
.tool table{font-size:13.5px}
.tool>.table-wrap{grid-column:auto}
.tool code{background:var(--panel-2)}

/* ============================================================== issue cards */
.issue{
  margin:20px 0;padding:6px 24px 18px;border-radius:16px;
  background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--c,var(--line));
  box-shadow:var(--shadow);
}
.issue.sev-high{--c:var(--red)}
.issue.sev-med{--c:var(--amber)}
.issue.sev-low{--c:var(--teal)}
.issue .h-sub{margin-top:22px}
.issue .h-sub .h-num{position:static;border:none;background:none;padding:0;
  margin-right:9px;font-size:13px;color:var(--c)}
.issue .h-sub .h-num::before{content:""}
.issue .h-anchor{right:0}
.issue p,.issue li{font-size:15.5px;line-height:1.85}
.issue>.code-card{margin:18px 0}
.issue>.table-wrap{grid-column:auto;margin:16px 0}

/* ============================================================== overlay TOC */
.toc-overlay{
  position:fixed;inset:0;z-index:80;display:none;
  background:color-mix(in srgb,var(--bg) 72%,#000 28%);
  backdrop-filter:blur(10px) saturate(140%);
  overflow-y:auto;padding:86px 24px 60px;
}
.toc-overlay.on{display:block;animation:fadeIn .2s var(--ease)}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.toc-sheet{max-width:1120px;margin:0 auto}
.toc-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:34px}
.toc-top h2{margin:0;font-family:var(--font-mono);font-size:12px;letter-spacing:.22em;
  text-transform:uppercase;color:var(--ink-3);font-weight:700}
.toc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;
  align-items:start}
.toc-card{
  background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px 20px;
  box-shadow:var(--shadow);transition:border-color .15s,transform .15s;
}
.toc-card:hover{border-color:color-mix(in srgb,var(--accent) 55%,var(--line));transform:translateY(-2px)}
.toc-card-head{display:flex;align-items:baseline;gap:11px;text-decoration:none;color:var(--ink)}
.toc-card-num{font-family:var(--font-mono);font-size:12px;font-weight:800;color:var(--accent);flex:none}
.toc-card-title{font-size:16px;font-weight:700;letter-spacing:-.01em}
.toc-sub{list-style:none;margin:12px 0 0;padding:0;display:flex;flex-direction:column;gap:2px}
.toc-sub a{display:flex;gap:9px;font-size:12.5px;line-height:1.5;color:var(--ink-3);
  text-decoration:none;padding:3px 8px;border-radius:7px;
  transition:background .15s,color .15s}
.toc-sub a:hover{color:var(--accent);background:var(--accent-soft)}
.toc-sub-num{font-family:var(--font-mono);font-size:10.5px;font-weight:700;flex:none;
  min-width:2.1em;color:var(--ink-4);padding-top:.15em}
.toc-sub a:hover .toc-sub-num{color:var(--accent)}

/* ============================================================== footer */
.foot{
  grid-column:1 / -1;margin-top:80px;padding-top:26px;border-top:1px solid var(--line);
  display:flex;flex-wrap:wrap;gap:14px 24px;align-items:center;justify-content:space-between;
  font-size:12.5px;color:var(--ink-3);
}
.foot code{font-size:.95em}
.foot a{color:var(--accent);text-decoration:none}
.foot a:hover{text-decoration:underline}

.to-top{position:fixed;right:24px;bottom:24px;z-index:55;width:42px;height:42px;
  border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--ink-2);
  font-size:15px;cursor:pointer;box-shadow:var(--shadow);opacity:0;pointer-events:none;
  transition:opacity .2s,transform .2s,color .2s}
.to-top.on{opacity:1;pointer-events:auto}
.to-top:hover{transform:translateY(-2px);color:var(--accent)}

/* ============================================================== responsive */
@media (max-width:1360px){
  :root{--measure:660px;--spill:90px;--spill-wide:150px;--gutter:72px}
}
@media (max-width:1080px){
  .rail{display:none}
  .wrap{padding-left:0}
}
@media (max-width:940px){
  :root{--measure:100%;--spill:0px;--spill-wide:var(--pad)}
  .reading>.code-card,.reading>.table-wrap,.reading>.tool,.reading>.issue,
  .reading>.callout,.reading>.note,.reading>.preface{margin-inline:0}
  .h-chap .h-num,.h-sub .h-num{position:static;display:inline-block;margin:0 .5em 0 0;
    vertical-align:baseline}
  .h-chap .h-num{font-size:13px;color:var(--accent);letter-spacing:.06em;font-weight:800}
  .h-sub .h-num{font-size:10.5px;position:static;border:1px solid var(--line);padding:1px 6px}
  .h-sub.sev-high .h-num,.h-sub.sev-med .h-num,.h-sub.sev-low .h-num{
    border:none;background:none;padding:0;font-size:13px}
  .reading>h2#目录+ul{columns:1}
  .hero{padding-top:104px}
  .now{display:none}
}
@media (max-width:600px){
  body{font-size:16px}
  .reading p,.callout-body p,.preface-body p{font-size:15.5px;line-height:1.85}
  .hero{padding-top:94px;padding-bottom:30px}
  .hero h1{font-size:33px}
  .stats{gap:20px;padding:15px 0}
  .stat b{font-size:18px}
  .h-chap{margin-top:62px;font-size:22px}
  .h-sub{font-size:16.5px;margin-top:34px}
  .code-card pre{font-size:12.2px;padding:13px 14px 15px}
  .plate{margin:34px 0}
  .plate-frame{padding:8px;border-radius:14px}
  .table-wrap{font-size:13px}
  .table-wrap th,.table-wrap td{padding:9px 11px}
  .table-wrap th{white-space:normal}
  .table-wrap td code{white-space:normal}
  .tool,.issue{padding-left:16px;padding-right:16px;border-radius:16px}
  .topbar{padding:0 14px;gap:10px}
  .brand-sub{display:none}
  .iconbtn kbd{display:none}
  .toc-overlay{padding:74px 16px 40px}
}

/* ============================================================== print */
@media print{
  @page{margin:15mm 13mm}
  /* beat both [data-theme] token blocks: print is always light */
  :root,:root[data-theme="dark"],:root[data-theme="light"]{
    --bg:#fff;--bg-elev:#fff;--panel:#fff;--panel-2:#f7f7f5;
    --ink:#111;--ink-2:#222;--ink-3:#555;--ink-4:#777;
    --line:#ddd;--line-2:#eee;--ghost:transparent;
    --accent:#8a4d05;--accent-soft:#f4ecdf;--accent-ink:#8a4d05;
    --shadow:none;--shadow-lg:none;--glow:transparent;
  }
  body{background:#fff!important;color:#222;font-size:10.5pt;line-height:1.7}
  body::before{display:none}
  .topbar,.rail,.to-top,.progress,.code-copy,.lightbox,.toc-overlay,.plate-zoom,
  .toc-hint,.hero .chips{display:none!important}
  .wrap{padding-left:0}
  .reading{max-width:none;margin:0;padding-bottom:0}
  .reading>.code-card,.reading>.table-wrap,.reading>.tool,.reading>.issue,
  .reading>.callout,.reading>.note,.reading>.preface,
  .reading>figure.plate,.reading>hr{margin-inline:0}
  .hero{padding-top:0;max-width:none}
  .hero h1{font-size:25pt;margin-right:0}
  .hero h1 em{-webkit-text-fill-color:#111;color:#111;background:none}
  .hero .standfirst{font-size:11pt}
  .stats{border-color:#ddd}
  .h-chap,.h-sub{display:block;margin-top:20pt;padding-top:14pt}
  .h-chap .h-num,.h-sub .h-num{position:static;display:inline;margin:0 8px 0 0;
    color:#777;font-size:.85em;border:none;background:none;padding:0;letter-spacing:0}
  .h-sub.sev-high .h-num{color:#b4382f}
  .h-sub.sev-med .h-num{color:#a15c07}
  .h-sub.sev-low .h-num{color:#0d7268}
  .h-chap{page-break-after:avoid}
  .h-sub{page-break-after:avoid}
  .code-card{break-inside:avoid;box-shadow:none}
  .code-card pre{font-size:8.2pt}
  .plate,.callout,.note,.preface,.tool,.issue,.table-wrap{break-inside:avoid;box-shadow:none}
  .plate-frame{padding:6px;box-shadow:none}
  .toc-overlay{display:none!important}
  .reading a{color:#111;background:none!important}
  .foot{page-break-before:avoid}
}
"""

THEME_JS = """
(function(){
  var k='nanocode-theme', s=null;
  try{s=localStorage.getItem(k)}catch(e){}
  var t=s||'dark';
  document.documentElement.setAttribute('data-theme',t);
})();
"""

APP_JS = r"""
(function(){
  var k='nanocode-theme', root=document.documentElement;

  /* ---- theme ---- */
  var tbtn=document.getElementById('theme-btn');
  function paintTheme(){ tbtn.textContent = root.getAttribute('data-theme')==='dark' ? '☀ 浅色' : '☾ 深色'; }
  paintTheme();
  tbtn.addEventListener('click',function(){
    var next = root.getAttribute('data-theme')==='dark' ? 'light':'dark';
    root.setAttribute('data-theme',next);
    try{localStorage.setItem(k,next)}catch(e){}
    paintTheme();
  });

  /* ---- scroll state: progress, sticky shadow, rail, "now" label ---- */
  var bar=document.getElementById('progress');
  var toTop=document.getElementById('to-top');
  var topbar=document.querySelector('.topbar');
  var now=document.getElementById('now');
  var railDots=[].slice.call(document.querySelectorAll('.rail-dot'));
  var railBySlug={};
  railDots.forEach(function(d){ railBySlug[d.dataset.target]=d; });
  /* every chapter heading, in document order, paired with its rail dot */
  var heads=[].slice.call(document.querySelectorAll('.h-chap'))
    .filter(function(h){ return !!railBySlug[h.id]; });
  var hy=[];
  var ticking=false;

  function layout(){
    hy=heads.map(function(h){ return h.getBoundingClientRect().top+window.scrollY; });
  }

  function onScroll(){
    var y=window.scrollY||document.documentElement.scrollTop;
    var h=document.documentElement.scrollHeight-window.innerHeight;
    bar.style.width=(h>0?Math.min(100,(y/h)*100):0)+'%';
    toTop.classList.toggle('on', y>700);
    topbar.classList.toggle('stuck', y>8);

    var idx=-1;
    for(var i=0;i<hy.length;i++){ if(hy[i]-150<=y) idx=i; else break; }
    railDots.forEach(function(d){ d.classList.remove('active'); });
    var active = idx>=0 ? railBySlug[heads[idx].id] : null;
    if(active){
      active.classList.add('active');
      if(now){
        now.innerHTML='<b>'+active.querySelector('.rail-num').textContent+'</b> '+
          active.querySelector('.rail-label').textContent;
      }
    }
    ticking=false;
  }
  window.addEventListener('scroll',function(){
    if(!ticking){ ticking=true; requestAnimationFrame(onScroll); }
  },{passive:true});
  window.addEventListener('resize',function(){ layout(); onScroll(); });
  layout(); onScroll();

  toTop.addEventListener('click',function(){ window.scrollTo({top:0,behavior:'smooth'}); });

  /* ---- overlay TOC ---- */
  var toc=document.getElementById('toc');
  function openToc(v){ toc.classList.toggle('on', v); document.body.style.overflow = v?'hidden':''; }
  document.getElementById('toc-btn').addEventListener('click',function(){ openToc(!toc.classList.contains('on')); });
  document.getElementById('toc-close').addEventListener('click',function(){ openToc(false); });
  document.querySelectorAll('[data-open-toc]').forEach(function(b){
    b.addEventListener('click',function(){ openToc(true); });
  });
  toc.addEventListener('click',function(e){
    if(e.target===toc) openToc(false);
    if(e.target.closest('a')) openToc(false);
  });
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape'){ openToc(false); closeBox(); }
    if((e.key==='t'||e.key==='T') && !e.metaKey && !e.ctrlKey && !/input|textarea/i.test(document.activeElement.tagName)) openToc(true);
  });

  /* ---- copy ---- */
  document.querySelectorAll('.code-copy').forEach(function(btn){
    btn.addEventListener('click',function(){
      var txt=btn.closest('.code-card').querySelector('pre code').innerText;
      var done=function(){ btn.textContent='已复制'; btn.classList.add('done');
        setTimeout(function(){ btn.textContent='复制'; btn.classList.remove('done'); },1400); };
      function fallback(){
        var ta=document.createElement('textarea');
        ta.value=txt; ta.style.position='fixed'; ta.style.opacity='0';
        document.body.appendChild(ta); ta.select();
        try{document.execCommand('copy'); done();}catch(e){}
        document.body.removeChild(ta);
      }
      if(navigator.clipboard&&navigator.clipboard.writeText){
        navigator.clipboard.writeText(txt).then(done,fallback);
      } else { fallback(); }
    });
  });

  /* ---- lightbox ---- */
  var box=document.getElementById('lightbox');
  var inner=box.querySelector('.lightbox-inner');
  function closeBox(){ box.classList.remove('on'); inner.innerHTML=''; }
  document.querySelectorAll('.plate-frame').forEach(function(fr){
    fr.addEventListener('click',function(){
      inner.innerHTML='';
      inner.appendChild(fr.firstElementChild.cloneNode(true));
      box.classList.add('on');
    });
  });
  box.addEventListener('click',closeBox);
})();
"""


def reading_minutes(text: str) -> int:
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z0-9_]+", text))
    return max(1, round(cjk / 380 + latin / 220))


def build(inline_svg: bool = True) -> str:
    with open(SRC, encoding="utf-8") as f:
        raw = f.read()

    title_m = re.search(r"^#\s+(.+)$", raw, re.M)
    title = title_m.group(1).strip() if title_m else "nanocode"
    title_main, _, title_sub = title.partition(" ")

    src = merge_blockquotes(raw)
    src = demote_h1(src)

    renderer = DocRenderer(inline_svg=inline_svg)
    md = mistune.create_markdown(
        renderer=renderer, escape=False, plugins=["table", "strikethrough", "url"]
    )
    body = md(src)                      # populates renderer.headings
    chs = chapters(renderer.headings)
    body = prettify(
        body,
        n_ch=len(chs),
        n_sub=sum(len(c["subs"]) for c in chs),
    )
    n_figs = len(renderer.figs)
    minutes = reading_minutes(raw)
    n_lines = 270

    meta = (
        f'<div class="stat"><b>{n_figs}</b><span>手绘 SVG</span></div>'
        f'<div class="stat"><b>{minutes}</b><span>分钟读完</span></div>'
        f'<div class="stat"><b>{len(chs)}</b><span>章节</span></div>'
        f'<div class="stat"><b>{n_lines}</b><span>行源码</span></div>'
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{htmllib.escape(title)}</title>
<meta name="description" content="面向零基础的 nanocode.py 逐行源码解读：agentic loop、六个工具、schema 生成、已知问题。">
<meta name="color-scheme" content="dark light">
<meta name="theme-color" content="#0a0b0e">
<script>{THEME_JS}</script>
<style>
{CSS}
{pygments_css()}
</style>
</head>
<body id="top">
<div class="progress" id="progress"></div>

<header class="topbar">
  <div class="brand">
    <span class="brand-mark">n</span>{htmllib.escape(title_main)}
    <span class="brand-sep">/</span><span class="brand-sub">{htmllib.escape(title_sub)}</span>
  </div>
  <div class="now" id="now"></div>
  <div class="actions">
    <button class="iconbtn" id="toc-btn" type="button">目录 <kbd>T</kbd></button>
    <button class="iconbtn" id="theme-btn" type="button">☀ 浅色</button>
  </div>
</header>

<nav class="rail" aria-label="章节导航">{chapter_rail(chs)}</nav>

<div class="wrap">
  <div class="shell">
    <header class="hero">
      <div class="hero-eyebrow">行级精读 · 零基础 · {n_lines} 行</div>
      <h1>一个 <em>agent</em> 是怎么转起来的</h1>
      <p class="standfirst">
        {htmllib.escape(title)} —— 把 <code>nanocode.py</code> 拆到不能再拆：主循环、六个工具、
        schema 生成、网络层，以及那些不得不说的坑。全文不假设你懂 LLM。
      </p>
      <div class="stats">{meta}</div>
      <div class="chips">{hero_chips(chs)}</div>
    </header>

    <main class="reading">
{body}
      <footer class="foot">
        <span>由 <code>docs/nanocode-explained.md</code> 自动生成 ·
          <code>python docs/assets/build_html.py</code></span>
        <span><a href="#{chs[0]["slug"]}">回到开头 ↑</a></span>
      </footer>
    </main>
  </div>
</div>

<button class="to-top" id="to-top" type="button" aria-label="回到顶部">↑</button>

<div class="toc-overlay" id="toc" role="dialog" aria-label="目录">
  <div class="toc-sheet">
    <div class="toc-top">
      <h2>Contents</h2>
      <button class="iconbtn" id="toc-close" type="button">✕ 关闭</button>
    </div>
    <div class="toc-grid">{toc_overlay(chs)}</div>
  </div>
</div>

<div class="lightbox" id="lightbox" role="dialog" aria-label="放大看图">
  <div class="lightbox-inner"></div>
</div>

<script>{APP_JS}</script>
</body>
</html>
"""


def main() -> None:
    inline = "--external" not in sys.argv
    out = build(inline_svg=inline)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    size = os.path.getsize(OUT) / 1024
    print(f"wrote {os.path.relpath(OUT)}  ({size:.0f} KB, "
          f"{'inline SVG' if inline else 'external SVG'})")


if __name__ == "__main__":
    main()
