"""Builders for every picture on the profile. Each returns an SVG string.

The look follows the hand-made preview.html mockup (Windows Terminal + Catppuccin).
"""
from __future__ import annotations

import math
from datetime import date

import ascii_art as art
from svgkit import Canvas
from svgkit import frames_css
from term import Term, cells, plain, resolve

W = 840  # every card is 840 px wide; GitHub scales it to the column width
MARGIN = 10  # room for the window shadow
TITLE_H = 34
PAD = 24

# preview.html terminal icon (24x24 viewBox)
TERM_ICON = ("M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zm4 7.5L5 9v1.5l2 1.5-2 1.5V15"
             "l3-2.5v-1zm4 3.5h5v-1.5h-5V15z")


# ----------------------------------------------------------------- helpers

class Clock:
    """Turns time windows inside one looping animation into CSS classes."""

    def __init__(self, c: Canvas, total: float, name: str):
        self.c, self.total, self.name = c, total, name
        self._cache: dict[tuple, str] = {}

    def show(self, start: float, end: float, static: bool = False) -> str:
        """Class that is visible from `start` to `end` seconds of every loop.

        static: whether the element shows when animations are turned off.
        """
        key = (round(start, 3), round(end, 3), static)
        if key in self._cache:
            return self._cache[key]
        cls = f"{self.name}{len(self._cache)}"
        a = max(0.0, start) / self.total * 100
        b = min(end, self.total) / self.total * 100
        kf = ["0%{opacity:0}"] if a > 0 else []
        kf.append(f"{a:.3f}%{{opacity:1}}")
        if b < 100:
            kf.append(f"{b:.3f}%{{opacity:0}}")
            kf.append("100%{opacity:0}")
        self.c.style(
            f".{cls}{{opacity:{1 if static else 0};animation:{cls}k {self.total:.2f}s step-end infinite}}"
            f"@keyframes {cls}k{{{''.join(kf)}}}"
        )
        self._cache[key] = cls
        return cls


def glow(c: Canvas, P: dict, color: str, std: float = 6, op: float = .35) -> str:
    """filter attribute for a soft neon glow (like CSS drop-shadow 0 0 Npx)."""
    fid = f"glow-{color}-{std:g}"
    op = op if P["name"] == "dark" else op * .6
    c.define(fid, f'<filter id="{fid}" x="-30%" y="-40%" width="160%" height="180%">'
                  f'<feGaussianBlur in="SourceAlpha" stdDeviation="{std:g}" result="b"/>'
                  f'<feFlood flood-color="{P[color]}" flood-opacity="{op:.2f}"/>'
                  f'<feComposite in2="b" operator="in"/>'
                  f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    return f'filter="url(#{fid})"'


def text_w(t: Term, s: str) -> float:
    return cells(plain(s)) * t.cw


def window(c: Canvas, P: dict, h: float, title: str, dot: str | None = None, tabs: bool = False) -> tuple[float, float]:
    """Draw a terminal window filling the canvas. Returns the content origin.

    tabs: Windows Terminal tab strip (active tab, notes.txt, +); otherwise a "● title" bar.
    """
    x, y, w = MARGIN, MARGIN, c.w - 2 * MARGIN
    wh = h - 2 * MARGIN
    dark = P["name"] == "dark"
    c.define(
        "shadow",
        '<filter id="shadow" x="-6%" y="-8%" width="112%" height="130%">'
        f'<feDropShadow dx="0" dy="6" stdDeviation="7" flood-color="{P["shadow"]}" '
        f'flood-opacity="{0.6 if dark else 0.13}"/></filter>',
    )
    bar = P["crust"] if tabs else P["mantle"]
    c.add(
        f'<rect x="{x}" y="{y}" width="{w}" height="{wh}" rx="12" fill="{P["base"]}" filter="url(#shadow)"/>',
        f'<path d="M{x},{y + TITLE_H} V{y + 12} a12,12 0 0 1 12,-12 H{x + w - 12} a12,12 0 0 1 12,12 V{y + TITLE_H} Z" '
        f'fill="{bar}"/>',
        f'<path d="M{x},{y + TITLE_H} H{x + w}" stroke="{P["surface0"]}" stroke-width="1"/>',
    )
    # Windows Terminal caption controls: ─ □ ✕
    rx = x + w - 70
    cy = y + TITLE_H / 2
    ink = P["subtext0" if tabs else "overlay1"]
    c.add(
        f'<line x1="{rx:.1f}" y1="{cy:.1f}" x2="{rx + 10:.1f}" y2="{cy:.1f}" stroke="{ink}" stroke-width="1.2"/>',
        f'<rect x="{rx + 24:.1f}" y="{cy - 5:.1f}" width="10" height="10" fill="none" stroke="{ink}" stroke-width="1.2"/>',
        f'<path d="M{rx + 48:.1f},{cy - 5:.1f} l10,10 M{rx + 58:.1f},{cy - 5:.1f} l-10,10" stroke="{ink}" stroke-width="1.2"/>',
    )
    if tabs:
        ty, bot = y + 7, y + TITLE_H + .5
        tt = Term(c, P, 0, ty + (TITLE_H - 7 - 12 * 1.4) / 2, size=12, lh=1.4)
        tx = x + 12
        tw = 14 + 13 + 8 + text_w(tt, title) + 10 + tt.cw + 14
        c.add(f'<path d="M{tx},{bot} V{ty + 8} a8,8 0 0 1 8,-8 H{tx + tw - 8} a8,8 0 0 1 8,8 V{bot} Z" fill="{P["base"]}"/>',
              f'<path d="M{tx + 1},{ty + 7} a7,7 0 0 1 7,-7 H{tx + tw - 8} a7,7 0 0 1 7,7" fill="none" '
              f'stroke="{P["pink"]}" stroke-width="2"/>',
              f'<path transform="translate({tx + 14:.1f} {cy + 3.5 - 6.5:.1f}) scale(.55)" d="{TERM_ICON}" fill="{P["blue"]}"/>')
        tt.x = tx + 14 + 13 + 8
        c.add(tt.text(0, 0, title, "text"))
        c.add(tt.text(cells(title) + 1.4, 0, "×", "overlay1"))
        nx = tx + tw + 4
        nw = 24 + text_w(tt, "notes.txt")
        c.add(f'<path d="M{nx},{bot - .5} V{ty + 8} a8,8 0 0 1 8,-8 H{nx + nw - 8} a8,8 0 0 1 8,8 V{bot - .5} Z" '
              f'fill="{P["mantle"]}" fill-opacity=".6"/>')
        tt.x = nx + 12
        c.add(tt.text(0, 0, "notes.txt", "overlay1"))
        tt.x = nx + nw + 12
        c.add(tt.text(0, 0, "+", "overlay1"))
    else:
        t = Term(c, P, x + 18, y + (TITLE_H - 12 * 1.4) / 2, size=12, lh=1.4)
        if dot:
            c.add(t.text(0, 0, "●", dot, bold=True))
        c.add(t.text(2 if dot else 0, 0, title, "subtext0"))
    c.add(f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{wh - 1}" rx="11.5" fill="none" '
          f'stroke="{P["surface0"]}" stroke-opacity=".6"/>')
    return x + PAD, y + TITLE_H + 20


def prompt(cfg: dict) -> str:
    user = cfg["profile"]["user"]
    return f"[blue b]PS[/] [teal]C:\\Users\\{user}[/][overlay1]>[/] "


def cursor(c: Canvas, P: dict, t: Term, col: float, row: float, cls: str = "") -> str:
    c.style(".blink{animation:blink 1.06s step-end infinite}@keyframes blink{50%{opacity:0}}", key="blink")
    x, y = t.col_x(col), t.row_y(row) + (t.lh - t.size * 1.3) / 2
    k = f' class="{cls}"' if cls else ""
    return (
        f'<g{k}><rect class="blink" x="{x:.1f}" y="{y:.1f}" width="2" height="{t.size * 1.3:.1f}" '
        f'fill="{P["pink"]}"/></g>'
    )


# ----------------------------------------------------------------- header

def header(cfg: dict, P: dict, stats: dict | None = None) -> str:
    rows = art.banner(cfg["profile"]["banner"])
    bw = max(len(r) for r in rows)
    cmds = [dict(c) for c in cfg["header"]["commands"]]
    if stats and stats.get("latest_commit"):
        lc = stats["latest_commit"]
        msg = lc["message"]
        msg_disp = (msg[:40] + "…") if len(msg) > 42 else msg
        safe_msg = msg_disp.replace('"', '\\"')
        cmd_str = f'git commit -m "{safe_msg}"'
        branch = lc.get("branch", "main")
        sha = lc.get("sha", "0000000")
        adds = lc.get("additions", 0)
        dels = lc.get("deletions", 0)
        out_str = f"[[{branch} [yellow]{sha}[/]] {msg_disp} · [green]+{adds:,}[/] / [red]-{dels:,}[/]"
        idx = next((i for i, c in enumerate(cmds) if c["cmd"].startswith("git commit")), len(cmds) - 1)
        cmds[idx] = {"cmd": cmd_str, "output": [out_str]}

    bsize, blh = 15, 1.05
    size, lh = 14, 1.6
    oy = MARGIN + TITLE_H + 20
    y_b = oy + 4
    y_sub = y_b + len(rows) * bsize * blh + 18
    y_sep = y_sub + size * 1.5 + 14
    y_cmd = y_sep + 16
    n_rows = sum(1 + len(x["output"]) for x in cmds)
    H = y_cmd + n_rows * size * lh + 8 * (len(cmds) - 1) + 20 + MARGIN
    c = Canvas(W, H)
    ox, _ = window(c, P, H, cfg["header"]["title"], tabs=True)

    # faint pink radial light behind the body
    c.define("rg", f'<radialGradient id="rg" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{P["pink"]}" '
                   f'stop-opacity=".07"/><stop offset=".7" stop-color="{P["pink"]}" stop-opacity="0"/></radialGradient>')
    c.add(f'<rect x="{MARGIN}" y="{MARGIN + TITLE_H + 1}" width="{W - 2 * MARGIN}" height="{H - 2 * MARGIN - TITLE_H - 12}" '
          f'fill="url(#rg)"/>')

    # banner: solid pink blocks with a neon glow
    bt = Term(c, P, 0, y_b, size=bsize, lh=blh)
    bt.x = (W - bw * bt.cw) / 2
    c.add(f'<g {glow(c, P, "pink", 7)}>' + "".join(bt.text(0, r, line, "pink", bold=True)
                                                    for r, line in enumerate(rows)) + "</g>")

    st = Term(c, P, 0, y_sub, size=size, lh=1.5)
    m = cfg["header"]["subtitle"]
    st.x = (W - text_w(st, m)) / 2
    c.add(st.markup(0, 0, m, default="subtext0")[0])
    c.add(f'<path d="M{ox},{y_sep} H{W - MARGIN - PAD}" stroke="{P["surface0"]}" stroke-opacity=".6"/>')

    # commands; the last one types itself out on a loop
    pm = prompt(cfg)
    pcols = cells(plain(pm))
    y = y_cmd
    for k, item in enumerate(cmds):
        tt = Term(c, P, ox, y, size=size, lh=lh)
        c.add(tt.markup(0, 0, pm)[0])
        cmd = item["cmd"]
        last = k == len(cmds) - 1
        out_cls = ""
        if last:
            per, t0 = 0.055, 0.6
            t_typed = t0 + len(cmd) * per
            total = t_typed + 4.5
            clock = Clock(c, total, "ty")
            c.add(tt.text(pcols, 0, cmd, "text", cls=lambda i: clock.show(t0 + (i + 1) * per, total, static=True)))
            out_cls = clock.show(t_typed + .3, total, static=True)
            moves, col = [(0, pcols)], pcols
            for i, ch in enumerate(cmd):
                col += 1 if ch == " " else resolve(ch)[3]
                moves.append((t0 + (i + 1) * per, col))
            kf = "".join(f"{tm / total * 100:.3f}%{{transform:translateX({(cl - pcols) * tt.cw:.1f}px)}}" for tm, cl in moves)
            c.style(f"@keyframes curmove{{{kf}}}"
                    f".curmove{{animation:curmove {total:.2f}s step-end infinite;"
                    f"transform:translateX({(col - pcols) * tt.cw:.1f}px)}}")
            c.add(cursor(c, P, tt, pcols, 0, "curmove"))
        else:
            c.add(tt.text(pcols, 0, cmd, "text"))
        for j, out in enumerate(item["output"]):
            g = tt.markup(1.5, 1 + j, out, default="overlay1")[0]
            if item.get("bar"):
                g = (f'<rect x="{ox:.1f}" y="{tt.row_y(1 + j) + 2:.1f}" width="2" height="{tt.lh - 4:.1f}" '
                     f'fill="{P[item["bar"]]}" fill-opacity=".5"/>') + g
            c.add(f'<g class="{out_cls}">{g}</g>' if out_cls else g)
        y += (1 + len(item["output"])) * tt.lh + 8
    return c.svg(cfg["header"]["alt"])


# ----------------------------------------------------------------- fastfetch

def neofetch(cfg: dict, P: dict, stats: dict) -> str:
    nf = cfg["neofetch"]
    size, lh = 13, 1.6
    rows = [(k, v) for k, v in nf["about"]] + [
        ("Commits", f"[peach b]{stats['commits']:,}[/] [subtext0]in {stats['year_label']}[/]"),
        ("Activity", f"[peach b]{stats['contributions']:,}[/] [subtext0]total contributions[/]"),
    ]
    oy = MARGIN + TITLE_H + 20
    y0 = oy + size * lh + 14
    y_rows = y0 + 30
    y_lang = y_rows + len(rows) * size * lh + 10
    y_bar = y_lang + 20
    y_pal = y_bar + 18
    y_end = y_pal + 14
    H = y_end + 24 + MARGIN
    c = Canvas(W, H)
    ox, _ = window(c, P, H, "fastfetch — Kimina@KiminaOS-Windows", dot="blue")
    t = Term(c, P, ox, oy, size=size, lh=lh)
    c.add(t.markup(0, 0, prompt(cfg) + "fastfetch")[0])

    # Windows logo card
    cw_, gap = 232, 24
    c.add(f'<rect x="{ox}" y="{y0}" width="{cw_}" height="{y_end - y0}" rx="12" fill="{P["mantle"]}" '
          f'fill-opacity=".8" stroke="{P["surface0"]}" stroke-opacity=".6"/>')
    cx, cy = ox + cw_ / 2, y0 + (y_end - y0) / 2 - 22
    sz, g2 = 46, 7
    tiles = "".join(f'<rect x="{tx:.1f}" y="{ty:.1f}" width="{sz}" height="{sz}" rx="2"/>'
                    for tx in (cx - sz - g2 / 2, cx + g2 / 2) for ty in (cy - sz - g2 / 2, cy + g2 / 2))
    c.add(f'<g fill="{P["blue"]}" {glow(c, P, "blue", 6)}>{tiles}</g>')
    for txt, s, col, b, dy in (("KiminaOS-Windows", 11.5, "subtext0", True, sz + 18), ("Build 26100.9711", 10.5, "overlay1", False, sz + 36)):
        lt = Term(c, P, 0, cy + dy, size=s, lh=1.4)
        lt.x = cx - text_w(lt, txt) / 2
        c.add(lt.text(0, 0, txt, col, bold=b))

    # info column
    ix = ox + cw_ + gap
    right = W - MARGIN - PAD
    it = Term(c, P, ix, y0, size=size, lh=lh)
    c.add(it.markup(0, 0, f"[pink b]{cfg['profile']['user']}[/][overlay1]@[/][mauve b]KiminaOS-Windows[/]")[0])
    up = f"up {(date.today() - nf['installed']).days} days"
    pt = Term(c, P, 0, y0 + 2, size=10.5, lh=1.6)
    pw = text_w(pt, up) + 16
    pt.x = right - pw + 8
    c.add(f'<rect x="{right - pw:.1f}" y="{y0 + 2:.1f}" width="{pw:.1f}" height="{pt.lh:.1f}" rx="4" fill="{P["surface0"]}"/>',
          pt.text(0, 0, up, "subtext0"))
    c.add(f'<path d="M{ix},{y0 + 26} H{right}" stroke="{P["surface0"]}"/>')
    rt = Term(c, P, ix, y_rows, size=size, lh=lh)
    for r, (k, v) in enumerate(rows):
        c.add(rt.text(0, r, k, "mauve", bold=True), rt.markup(11, r, v)[0])

    # languages: label + legend, then one rounded bar
    total_size = sum(v for _, v in stats["languages"]) or 1
    langs = [(n, v) for n, v in stats["languages"] if v / total_size >= 0.01][:4]  # hide slivers under 1%
    accents = ["blue", "yellow", "red", "teal"]
    lt = Term(c, P, ix, y_lang, size=11.5, lh=1.4)
    c.add(lt.text(0, 0, "Languages", "mauve", bold=True))
    tot = sum(v for _, v in langs) or 1
    legend = " · ".join(f"{n} {v / tot * 100:.0f}%" for n, v in langs) or "no public code yet"
    lt2 = Term(c, P, right - text_w(lt, legend), y_lang, size=11.5, lh=1.4)
    c.add(lt2.text(0, 0, legend, "overlay1"))
    bw = right - ix
    c.define("barclip", f'<clipPath id="barclip"><rect x="{ix}" y="{y_bar}" width="{bw}" height="8" rx="4"/></clipPath>')
    segs, x = [], ix
    for (n, v), a in zip(langs, accents):
        w = v / tot * bw
        segs.append(f'<rect x="{x:.1f}" y="{y_bar}" width="{w + .5:.1f}" height="8" fill="{P[a]}"/>')
        x += w
    c.add(f'<g clip-path="url(#barclip)"><rect x="{ix}" y="{y_bar}" width="{bw}" height="8" fill="{P["surface0"]}"/>'
          + "".join(segs) + "</g>")

    # palette swatches
    for i, a in enumerate(["pink", "peach", "yellow", "green", "teal", "blue", "mauve"]):
        c.add(f'<rect x="{ix + i * 26}" y="{y_pal}" width="20" height="14" rx="2" fill="{P[a]}"/>')
    ct = Term(c, P, 0, y_pal, size=10, lh=1.4)
    ct.x = right - text_w(ct, "Catppuccin Mocha")
    c.add(ct.text(0, 0, "Catppuccin Mocha", "overlay1"))
    return c.svg("fastfetch: Kimina@KiminaOS-Windows")


# ----------------------------------------------------------------- activity heatmap

MONTHS_JA = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]


def dither_defs(c: Canvas, P: dict):
    """Fill patterns that look like the shade characters ░ ▒ ▓ (2 px dots on a 4 px grid)."""
    h = P["heat"]
    t = 1 / 3
    q = t / 2

    def pat(pid, bg, fg, squares):
        sq = "".join(f'<rect x="{x * q:.4f}" y="{y * q:.4f}" width="{q:.4f}" height="{q:.4f}" fill="{fg}"/>'
                     for x, y in squares)
        c.define(pid, f'<pattern id="{pid}" width="{t:.4f}" height="{t:.4f}" patternContentUnits="objectBoundingBox">'
                      f'<rect width="{t:.4f}" height="{t:.4f}" fill="{bg}"/>{sq}</pattern>')

    pat("d1", h[0], h[2], [(0, 0)])
    pat("d2", h[1], h[3], [(0, 0), (1, 1)])
    pat("d3", h[2], h[4], [(0, 0), (1, 0), (0, 1)])


def heat_cell(P: dict, x: float, y: float, size: float, level: int) -> str:
    if level == 0:  # an empty day is just a dot, like '·'
        return f'<circle cx="{x + size / 2:g}" cy="{y + size / 2:g}" r="1.4" fill="{P["surface2"]}"/>'
    fill = P["heat"][4] if level == 4 else f"url(#d{level})"
    return f'<rect x="{x:g}" y="{y:g}" width="{size:g}" height="{size:g}" rx="1.5" fill="{fill}"/>'


def activity(cfg: dict, P: dict, stats: dict) -> str:
    weeks = stats["weeks"][-53:]  # list of weeks; each a list of (iso_date, level 0-4, count)
    nweeks = len(weeks)
    pitch, cell, label_w = 14, 12, 28
    y_grid = MARGIN + TITLE_H + 20 + 2 * 14 * 1.5
    y_cells = y_grid + 20
    y_run = y_cells + 7 * pitch + 10
    y_sum = y_run + 14 * 1.4 + 12
    H = y_sum + 14 * 1.5 + 18 + MARGIN
    c = Canvas(W, H)
    ox, oy = window(c, P, H, "git log — PowerShell", dot="green")
    dither_defs(c, P)
    t = Term(c, P, ox, oy, size=14, lh=1.5)
    c.add(t.markup(0, 0, prompt(cfg) + "git log --heatmap --since '1 year ago'")[0])

    grid_x0 = round(ox + label_w)
    lt = Term(c, P, grid_x0, y_grid, size=11.5, lh=1.4)
    last_month = date.fromisoformat(weeks[0][0][0]).month
    for wi, week in enumerate(weeks):
        d0 = date.fromisoformat(week[0][0])
        if d0.month != last_month and wi < nweeks - 2:
            c.add(lt.text(wi * pitch / lt.cw, 0, MONTHS_JA[d0.month - 1], "subtext0"))
        last_month = d0.month
    dt = Term(c, P, ox, y_cells, size=11.5, lh=pitch / 11.5)
    for r, lab in ((1, "月"), (3, "水"), (5, "金")):
        c.add(dt.text(0, r, lab, "overlay1"))

    # kaomoji cat running underneath; every column hops when it passes
    rt = Term(c, P, 0, y_run, size=14, lh=1.4)
    run_w = cells(art.RUNNER["a"]) * rt.cw
    face_off = (cells("ε=ε=┏(=^･") + 0.5) * rt.cw
    grid_x1 = grid_x0 + nweeks * pitch
    run_secs = 12.0
    v = (grid_x1 - grid_x0) / run_secs
    s0 = MARGIN - run_w - 10
    s1 = W - MARGIN + 10
    total = (s1 - s0) / v
    c.style(
        "@keyframes hop{0%{transform:translateY(0)}1.5%{transform:translateY(-4px)}"
        "3.2%,100%{transform:translateY(0)}}"
    )
    for wi, week in enumerate(weeks):
        x = grid_x0 + wi * pitch
        parts = []
        for iso, level, count in week:
            wd = (date.fromisoformat(iso).weekday() + 1) % 7  # Sunday = 0
            parts.append(heat_cell(P, x, round(y_cells + wd * pitch), cell, level))
        t_hit = (x + cell / 2 - face_off - s0) / v
        c.add(f'<g style="animation:hop {total:.2f}s ease-out {t_hit:.2f}s infinite">{"".join(parts)}</g>')
    c.style(
        f"@keyframes run{{0%{{transform:translateX({s0:.0f}px)}}100%{{transform:translateX({s1:.0f}px)}}}}"
        f".run{{animation:run {total:.2f}s linear infinite;transform:translateX({s0:.0f}px)}}"
    )
    cls = frames_css(c, "leg", [(0, .2), (1, .2)], 2)
    c.style(f".{cls[1]}{{opacity:0}}")
    legs = "".join(f'<g class="{cls[i]}">{rt.text(0, 0, art.RUNNER[k], "pink", bold=True)}</g>'
                   for i, k in enumerate("ab"))
    clip = c.uid("win")
    c.define(clip, f'<clipPath id="{clip}"><rect x="{MARGIN + 1}" y="{MARGIN}" width="{W - 2 * MARGIN - 2}" '
                   f'height="{H - 2 * MARGIN}"/></clipPath>')
    c.add(f'<g clip-path="url(#{clip})"><g class="run">{legs}</g></g>')

    # summary + legend
    bt = Term(c, P, ox, y_sum, size=14, lh=1.5)
    streak = stats["streak"]
    s = (f"[green b]{stats['contributions']:,}[/] contributions in the last year [overlay1]·[/] "
         f"streak [peach b]{streak}[/] day{'s' if streak != 1 else ''}")
    c.add(bt.markup(0, 0, s)[0])
    right = W - MARGIN - PAD
    lx = right - (2 * 2 + 5 * 16 + 2 * 8) * 1.0 - 8
    cy = bt.row_y(0) + (bt.lh - cell) / 2
    out = [Term(c, P, lx, y_sum, size=14, lh=1.5).text(0, 0, "少", "overlay1")]
    x = lx + 2 * bt.cw + 6
    for lv in range(5):
        out.append(heat_cell(P, round(x), round(cy), cell, lv))
        x += 16
    out.append(Term(c, P, x + 2, y_sum, size=14, lh=1.5).text(0, 0, "多", "overlay1"))
    c.add("".join(out))
    return c.svg("Contribution heatmap drawn with characters")


# ----------------------------------------------------------------- skills

def skills(cfg: dict, P: dict) -> str:
    files = cfg["skills"]["files"]
    ncol, bh, gap = 3, 34, 12
    nrow = math.ceil(len(files) / ncol)
    oy = MARGIN + TITLE_H + 20
    y_grid = oy + 14 * 1.5 + 12
    H = y_grid + nrow * bh + (nrow - 1) * gap + 24 + MARGIN
    c = Canvas(W, H)
    ox, _ = window(c, P, H, "dir ~\\skills — PowerShell", dot="teal")
    t = Term(c, P, ox, oy, size=13, lh=1.6)
    c.add(t.markup(0, 0, prompt(cfg) + "Get-ChildItem -Path ~\\skills -Name")[0])
    gx = ox + 8
    bw = (W - MARGIN - PAD - gx - (ncol - 1) * gap) / ncol
    for i, (name, color, lang) in enumerate(files):
        x = gx + (i % ncol) * (bw + gap)
        y = y_grid + (i // ncol) * (bh + gap)
        c.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh}" rx="4" fill="{P["mantle"]}" '
              f'fill-opacity=".6" stroke="{P["surface0"]}" stroke-opacity=".6"/>')
        nt = Term(c, P, x + 10, y + (bh - 13 * 1.4) / 2, size=13, lh=1.4)
        c.add(nt.text(0, 0, name, color))
        lt = Term(c, P, 0, y + (bh - 10 * 1.4) / 2, size=10, lh=1.4)
        lt.x = x + bw - 10 - text_w(lt, lang)
        c.add(lt.text(0, 0, lang, "overlay1"))
    return c.svg("Skills: " + ", ".join(f[0] for f in files))


# ----------------------------------------------------------------- footer

def footer(cfg: dict, P: dict) -> str:
    """Two centred lines, no window, like the bottom of preview.html."""
    c = Canvas(W, 60)
    for r, (m, s) in enumerate(zip(cfg["footer"]["lines"], (13, 11))):
        t = Term(c, P, 0, 6 + r * 26, size=s, lh=1.5)
        m = m.format(date=date.today().isoformat())
        t.x = (W - text_w(t, m)) / 2
        c.add(t.markup(0, 0, m, default="overlay1" if r == 0 else "overlay0")[0])
    return c.svg(cfg["footer"]["alt"])


# ----------------------------------------------------------------- badges

def badge(label: str, value: str, color: str, P: dict) -> str:
    """Floating rounded pill: bold label · value, tinted with one accent."""
    size, h, pad = 12, 28, 8
    m = f"[{color} b]{label}[/] [overlay1]·[/] [{color}]{value}[/]"
    probe = Term(Canvas(1, 1), P, 0, 0, size=size)
    w = text_w(probe, m) + 28
    c = Canvas(round(w + 2 * pad), h + 2 * pad)
    delay = {"pink": 0, "blue": .6, "teal": 1.2}.get(color, 0)
    c.style("@keyframes fl{0%,100%{transform:translateY(0)}50%{transform:translateY(-2px)}}"
            f".fl{{animation:fl 4s ease-in-out {delay}s infinite}}")
    t = Term(c, P, pad + 14, pad + (h - size * 1.4) / 2, size=size, lh=1.4)
    c.add(f'<g class="fl"><rect x="{pad}" y="{pad}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{P[color]}" '
          f'fill-opacity=".1" stroke="{P[color]}" stroke-opacity=".3" {glow(c, P, color, 5, .2)}/>'
          + t.markup(0, 0, m)[0] + "</g>")
    return c.svg(f"{label}: {value}")
