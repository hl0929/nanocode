# -*- coding: utf-8 -*-
"""Drawing primitives shared by figures.py.

See figures.py for the actual diagrams; run `python docs/assets/figures.py` to
regenerate every SVG in this folder.  The diagrams are hand-laid-out (no
Mermaid) so they share one design system: rounded cards, semantic colours,
monospace for code, and a subtle animated "data flow" on the important edges.
"""

import os

OUT = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------
# design system
# --------------------------------------------------------------------------

# name -> (stroke, fill, strong text)
CO = {
    "ink":   ("#64748b", "#ffffff", "#0f172a"),
    "user":  ("#2563eb", "#eff6ff", "#1d4ed8"),
    "proc":  ("#0891b2", "#ecfeff", "#0e7490"),
    "ai":    ("#7c3aed", "#f5f3ff", "#6d28d9"),
    "fs":    ("#059669", "#ecfdf5", "#047857"),
    "warn":  ("#dc2626", "#fef2f2", "#b91c1c"),
    "amber": ("#d97706", "#fffbeb", "#b45309"),
    "muted": ("#cbd5e1", "#f8fafc", "#64748b"),
}

FONT = "-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Courier New',monospace"

CSS = """
text { font-family: %s; fill: #0f172a; }
.mono { font-family: %s; }
.node rect.box, .node ellipse, .node polygon { filter: url(#soft); }
.flow { stroke-dasharray: 4 16; animation: flow 1.1s linear infinite; }
@keyframes flow { to { stroke-dashoffset: -20; } }
@media (prefers-reduced-motion: reduce) {
  .flow { animation: none; }
}
""" % (FONT, MONO)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tw(s, fs):
    """rough text width: CJK is ~1em, latin ~0.55em"""
    w = 0.0
    for ch in s:
        w += fs * (1.0 if ord(ch) > 0x2E7F else 0.56)
    return w


class Fig:
    def __init__(self, w, h, title, desc="", grid=True):
        self.w, self.h = w, h
        self.title, self.desc = title, desc
        self.body = []
        self.markers = set()
        self.grid = grid

    # -- primitives ------------------------------------------------------
    def add(self, s):
        self.body.append(s)

    def marker(self, color):
        if color in self.markers:
            return "arw-%s" % color
        self.markers.add(color)
        stroke = CO[color][0]
        self.body.append(
            '<marker id="arw-%s" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="%s"/></marker>' % (color, stroke)
        )
        return "arw-%s" % color

    def node(self, x, y, w, h, lines, color="ink", r=12, fs=13.5, dashed=False,
             align="center", bold_first=True, shadow=True, fill=None, lh=1.5):
        stroke, fillc, strong = CO[color]
        if isinstance(lines, str):
            lines = [lines]
        lines = [l if isinstance(l, dict) else {"t": l} for l in lines]
        if fill is None:
            fill = fillc

        dash = ' stroke-dasharray="6 5"' if dashed else ""
        sh = ' filter="url(#soft)"' if shadow else ""
        fillattr = 'fill="%s"' % fill if fill != "none" else 'fill="none"'
        out = ['<g class="node"><rect class="box" x="%.1f" y="%.1f" width="%.1f" '
               'height="%.1f" rx="%d" %s stroke="%s" stroke-width="1.6"%s%s/>'
               % (x, y, w, h, r, fillattr, stroke, dash, sh)]

        n = len(lines)
        cx = x + w / 2 if align == "center" else x + 16
        anchor = "middle" if align == "center" else "start"
        first_baseline = y + h / 2 - (n - 1) * fs * lh / 2 + fs * 0.35
        for i, ln in enumerate(lines):
            f = ln.get("fs", fs)
            cls = ' class="%s"' % ln["cls"] if "cls" in ln else ""
            if ln.get("mono"):
                cls = ' class="mono"'
            c = ln.get("color", strong if (i == 0 and bold_first) else "#475569")
            weight = ln.get("weight", "600" if (i == 0 and bold_first) else "400")
            yy = first_baseline + sum(
                lines[j].get("fs", fs) * lh for j in range(i)
            )
            out.append(
                '<text x="%.1f" y="%.1f" text-anchor="%s" font-size="%.1f" '
                'font-weight="%s" fill="%s"%s>%s</text>'
                % (cx, yy, anchor, f, weight, c, cls, esc(ln["t"])))
        out.append("</g>")
        self.add("\n".join(out))

    def pill(self, x, y, w, h, lines, color="ink", fs=13.5):
        self.node(x, y, w, h, lines, color=color, r=h / 2, fs=fs)

    def diamond(self, cx, cy, hw, hh, lines, color="ink", fs=13.5):
        stroke, fillc, strong = CO[color]
        if isinstance(lines, str):
            lines = [lines]
        lines = [l if isinstance(l, dict) else {"t": l} for l in lines]
        out = ['<g class="node"><polygon class="box" points="%.1f,%.1f %.1f,%.1f '
               '%.1f,%.1f %.1f,%.1f" fill="%s" stroke="%s" stroke-width="1.6" '
               'filter="url(#soft)"/>'
               % (cx, cy - hh, cx + hw, cy, cx, cy + hh, cx - hw, cy, fillc, stroke)]
        n = len(lines)
        fb = cy - (n - 1) * fs * 1.45 / 2 + fs * 0.35
        for i, ln in enumerate(lines):
            f = ln.get("fs", fs)
            c = ln.get("color", strong if i == 0 else "#475569")
            cls = ' class="mono"' if ln.get("mono") else ""
            y = fb + sum(lines[j].get("fs", fs) * 1.45 for j in range(i))
            out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%.1f" '
                       'font-weight="%s" fill="%s"%s>%s</text>'
                       % (cx, y, f, ln.get("weight", "600" if i == 0 else "400"),
                          c, cls, esc(ln["t"])))
        out.append("</g>")
        self.add("\n".join(out))

    @staticmethod
    def _path(pts, r=12):
        d = "M %.1f %.1f" % pts[0]
        for i in range(1, len(pts) - 1):
            p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
            v1 = (p1[0] - p0[0], p1[1] - p0[1])
            v2 = (p2[0] - p1[0], p2[1] - p1[1])
            l1 = max((v1[0] ** 2 + v1[1] ** 2) ** .5, 0.001)
            l2 = max((v2[0] ** 2 + v2[1] ** 2) ** .5, 0.001)
            rr = min(r, l1 / 2, l2 / 2)
            a = (p1[0] - v1[0] / l1 * rr, p1[1] - v1[1] / l1 * rr)
            b = (p1[0] + v2[0] / l2 * rr, p1[1] + v2[1] / l2 * rr)
            d += " L %.1f %.1f Q %.1f %.1f %.1f %.1f" % (a[0], a[1], p1[0], p1[1], b[0], b[1])
        d += " L %.1f %.1f" % pts[-1]
        return d

    def arrow(self, pts, color="ink", dash=False, flow=False, head=True,
              w=1.7, opacity=1.0):
        """polyline with rounded corners; `flow` overlays an animated dash"""
        stroke = CO[color][0]
        if len(pts) == 2:
            d = "M %.1f %.1f L %.1f %.1f" % (pts[0][0], pts[0][1], pts[1][0], pts[1][1])
        else:
            d = self._path(pts)
        me = ' marker-end="url(#%s)"' % self.marker(color) if head else ""
        ds = ' stroke-dasharray="6 5"' if dash else ""
        self.add('<path d="%s" fill="none" stroke="%s" stroke-width="%.1f" '
                 'stroke-linejoin="round" stroke-linecap="round" opacity="%.2f"%s%s/>'
                 % (d, stroke, w, opacity, ds, me))
        if flow:
            light = CO[color][1] if color != "ink" else "#ffffff"
            self.add('<path d="%s" fill="none" stroke="%s" stroke-width="%.1f" '
                     'stroke-linecap="round" opacity=".95" class="flow"/>'
                     % (d, light, max(w - 0.6, 1.4)))
        return d

    def text(self, x, y, s, fs=13, color="#334155", anchor="start", weight="400",
             mono=False, opacity=1.0, rot=None):
        cls = ' class="mono"' if mono else ""
        tr = ' transform="rotate(%s %.1f %.1f)"' % (rot, x, y) if rot is not None else ""
        self.add('<text x="%.1f" y="%.1f" text-anchor="%s" font-size="%.1f" '
                 'font-weight="%s" fill="%s" opacity="%.2f"%s%s>%s</text>'
                 % (x, y, anchor, fs, weight, color, opacity, tr, cls, esc(s)))

    def tag(self, x, y, text, color="muted", anchor="middle", mono=False,
            fs=12, bg=True, weight="500", pad=4, rot=None):
        cls = ' class="mono"' if mono else ""
        stroke, fillc, strong = CO[color]
        tc = "#334155" if color == "muted" else strong
        out = []
        if bg and rot is None:
            wd = tw(text, fs) + pad * 2
            x0 = {"middle": x - wd / 2, "start": x - pad, "end": x - wd + pad}[anchor]
            out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="5" '
                       'fill="#ffffff" fill-opacity="0.92" stroke="none"/>'
                       % (x0, y - fs * 0.85, wd, fs * 1.7))
        tr = ' transform="rotate(%s %.1f %.1f)"' % (rot, x, y) if rot is not None else ""
        out.append('<text x="%.1f" y="%.1f" text-anchor="%s" font-size="%.1f" '
                   'font-weight="%s" fill="%s"%s%s>%s</text>'
                   % (x, y + fs * 0.34, anchor, fs, weight, tc, tr, cls, esc(text)))
        self.add("".join(out))

    def badge(self, cx, cy, num, color="ink", r=11, fs=12):
        stroke, fillc, strong = CO[color]
        self.add('<circle cx="%.1f" cy="%.1f" r="%d" fill="#ffffff" stroke="%s" '
                 'stroke-width="1.6"/><text x="%.1f" y="%.1f" text-anchor="middle" '
                 'font-size="%d" font-weight="700" fill="%s">%s</text>'
                 % (cx, cy, r + 1, stroke, cx, cy + r * 0.34, fs, strong, esc(num)))

    def card(self, x, y, w, h, title, color="ink"):
        """framed group; body text should start at y + 50"""
        stroke, fillc, strong = CO[color]
        self.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="12" '
                 'fill="%s" stroke="%s" stroke-width="1.3" stroke-dasharray="5 5" '
                 'fill-opacity="0.5"/>' % (x, y, w, h, fillc, stroke))
        if title:
            self.add('<circle cx="%.1f" cy="%.1f" r="3.2" fill="%s"/>'
                     % (x + 14, y + 20.5, stroke))
            self.add('<text x="%.1f" y="%.1f" font-size="12.5" font-weight="700" '
                     'fill="%s">%s</text>'
                     % (x + 24, y + 25, strong, esc(title)))

    def frame(self, x, y, w, h, title, color="ink", fs=12):
        """solid nested-loop frame, title sits inside the top-left corner"""
        stroke, fillc, strong = CO[color]
        self.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="16" '
                 'fill="%s" fill-opacity="0.45" stroke="%s" stroke-width="1.6"/>'
                 % (x, y, w, h, fillc, stroke))
        self.text(x + 16, y + 21, title, fs=fs, color=strong, weight="700")

    # -- output ----------------------------------------------------------
    def render(self):
        head = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'width="%d" height="%d" role="img" aria-label="%s" '
            'style="background:#ffffff;max-width:100%%;height:auto">\n'
            '<title>%s</title><desc>%s</desc>\n'
            % (self.w, self.h, self.w, self.h, esc(self.title), esc(self.title),
               esc(self.desc))
        )
        defs = ['<style>%s</style>' % CSS, "<defs>"]
        if self.grid:
            defs.append(
                '<pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse">'
                '<circle cx="1.4" cy="1.4" r="1.05" fill="#e2e8f0"/></pattern>'
            )
        defs.append(
            '<filter id="soft" x="-20%" y="-20%" width="140%" height="150%">'
            '<feDropShadow dx="0" dy="1.4" stdDeviation="1.9" flood-color="#0f172a" '
            'flood-opacity="0.10"/></filter>'
        )
        defs.append("</defs>")
        bg = ('<rect width="%d" height="%d" fill="#ffffff"/>' % (self.w, self.h))
        if self.grid:
            bg += '<rect width="%d" height="%d" fill="url(#dots)"/>' % (self.w, self.h)
        return (head + "\n".join(defs) + bg + "\n"
                + "\n".join(self.body) + "\n</svg>\n")

    def save(self, name):
        p = os.path.join(OUT, name)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(self.render())
        print("wrote", os.path.basename(p))
