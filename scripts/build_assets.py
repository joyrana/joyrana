#!/usr/bin/env python3
"""Build the Fluent 2 styled SVG assets used by the profile README.

GitHub READMEs cannot run JavaScript or load stylesheets, so the Fluent UI
React components cannot be used directly. Instead this script renders the
Fluent 2 design language -- design tokens, type ramp, corner radii, elevation
and Fluent System Icons -- into static SVGs, one light and one dark variant
of each, which README.md swaps with <picture> + prefers-color-scheme.

The README's content and section order live in the CONTENT block below;
edit it there and run:  python3 scripts/build_assets.py   (writes ./assets)

Icons:   Fluent System Icons, MIT, https://github.com/microsoft/fluentui-system-icons
Metrics: glyph advances from Selawik (Microsoft's open, Segoe UI metric
         compatible font, OFL) are used only to measure text for layout.
"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "scripts" / "fluent-icons"
OUT = ROOT / "assets"
METRICS = json.loads((ROOT / "scripts" / "selawik-metrics.json").read_text())

# ==========================================================================
# CONTENT — kept word for word from the original README.
# Text wrapped in **double asterisks** is rendered bold.
# ==========================================================================
NAME_LINE = "Hi there, I'm Joy Rana 👋"
TAGLINE = ("Vice President @Citi | Staff Software Engineer | AI Engineer | "
           "Educator | Open Source Enthusiast")
PARAGRAPHS = [
    "I am a **Vice President at Citi** with **14+ years of experience** building "
    "large-scale enterprise applications in the financial industry. My passion lies "
    "in **Artificial Intelligence, Agentic AI, Large Language Models (LLMs), "
    "Distributed Systems, and Software Engineering**.",
    "Beyond my professional work, I create educational content on **YouTube**, where "
    "I simplify complex software engineering and AI concepts through practical, "
    "project-based tutorials.",
]
HIGHLIGHTS = [
    ("briefcase", "Staff Software Engineer (Vice President) @ Citi"),
    ("bot", "Exploring Agentic AI, LLMs, MCP, LangGraph, RAG & AI Systems"),
    ("code", "Java • Spring Boot • Python • React • FastAPI • Distributed Systems"),
    ("target_arrow", "Building production-ready AI applications from scratch"),
    ("book_open", "Passionate about teaching Data Structures & Algorithms and AI Engineering"),
]
CONNECT_TITLE = "Connect with Me"
LINKS = [  # key, icon, label, url (shown and linked)
    ("linkedin", "person_circle", "LinkedIn", "https://www.linkedin.com/in/joyrana/"),
    ("website", "globe", "Website", "https://joyrana.in"),
    ("medium", "drafts", "Medium", "https://joyrana-dev.medium.com/"),
    ("youtube", "video", "YouTube", "https://www.youtube.com/@MrJoyRana"),
    ("github", "code", "GitHub", "https://github.com/joyrana"),
]
LETS_TITLE = "Let's Connect"
LETS_INTRO = "If you're interested in:"
INTERESTS = [
    ("bot", "AI Engineering"),
    ("brain_circuit", "Agentic AI"),
    ("flash", "Ultra Low Latency Systems"),
    ("building_bank", "Solution Architecture"),
    ("server", "Distributed Systems"),
    ("flowchart", "Data Structures and Algorithms"),
]
LETS_OUTRO = "feel free to connect with me on LinkedIn or subscribe to my YouTube channel."
STAR_LINE = "If you find my projects helpful, consider giving them a star!"

# ==========================================================================
# Fluent 2 web tokens (webLightTheme / webDarkTheme)
# ==========================================================================
FONT = ("'Segoe UI Variable Text','Segoe UI Variable','Segoe UI',Selawik,"
        "-apple-system,BlinkMacSystemFont,'Helvetica Neue',Roboto,Arial,sans-serif")
FONT_DISPLAY = FONT.replace("Variable Text", "Variable Display")

THEMES = {
    "light": dict(
        bg1="#FFFFFF", bg2="#FAFAFA", bg3="#F5F5F5",
        fg1="#242424", fg2="#424242", fg3="#616161",
        stroke1="#D1D1D1", stroke2="#E0E0E0", strokeCard="#E0E0E0",
        brandFg1="#0F6CBD", brandBg2="#EBF3FC", brandFg2="#115EA3",
        brandStroke2="#B4D6FA", star="#EAA300",
        shadowA=0.12, shadowB=0.14, blob=0.20,
    ),
    "dark": dict(
        bg1="#292929", bg2="#1F1F1F", bg3="#141414",
        fg1="#FFFFFF", fg2="#D6D6D6", fg3="#ADADAD",
        stroke1="#666666", stroke2="#525252", strokeCard="#3D3D3D",
        brandFg1="#479EF5", brandBg2="#082338", brandFg2="#62ABF5",
        brandStroke2="#0E4775", star="#FFC225",
        shadowA=0.28, shadowB=0.32, blob=0.38,
    ),
}
BLUE, LAVENDER, CYAN = "#0F6CBD", "#7160E8", "#0099BC"
W = 840          # every card shares this width so they scale together
PAD = 32
SLACK = 1.07     # headroom for system fonts wider than Segoe UI (e.g. SF Pro)


# ==========================================================================
# Primitives
# ==========================================================================
def text_width(text: str, size: float, bold=False) -> float:
    reg = sum(METRICS["Regular"].get(ch, 0.55) for ch in text)
    if bold:  # semibold sits between Regular and Bold
        reg = (reg + sum(METRICS["Bold"].get(ch, 0.58) for ch in text)) / 2
    emoji = sum(1 for ch in text if ord(ch) > 0x2000 and ch not in "•—–’·")
    return (reg * size + emoji * size * 0.7) * SLACK


def icon(name, x, y, size, fill, filled=False) -> str:
    src = (ICONS / f"{name}_20_{'filled' if filled else 'regular'}.svg").read_text()
    paths = "".join(re.findall(r"<path[^>]*/>", src))
    return (f'<g transform="translate({x:.2f} {y:.2f}) scale({size / 20:.4f})" '
            f'fill="{fill}">{paths}</g>')


def t(x, y, s, size, fill, weight=400, anchor="start", family=FONT, ls=None) -> str:
    extra = f' letter-spacing="{ls}"' if ls is not None else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>'
            f'{escape(s)}</text>')


def rich_lines(src: str, size: float, maxw: float):
    """Word-wrap text containing **bold** runs -> list of [(text, bold), ...]."""
    # (word, bold, glued) — glued words follow the previous one with no space,
    # e.g. the "." right after a bold run.
    words, prev_part = [], ""
    for i, part in enumerate(src.split("**")):
        for j, w in enumerate(part.split(" ")):
            if w:
                glued = (j == 0 and bool(words) and not part.startswith(" ")
                         and not prev_part.endswith(" "))
                words.append((w, i % 2 == 1, glued))
        prev_part = part
    lines, cur, curw = [], [], 0.0
    space = text_width(" ", size)
    for w, b, glued in words:
        ww = text_width(w, size, b)
        gap = 0 if (glued or not cur) else space
        if cur and not glued and curw + gap + ww > maxw:
            lines.append(cur)
            cur, curw, gap = [], 0.0, 0
        curw += gap + ww
        cur.append((w, b, glued))
    if cur:
        lines.append(cur)
    return lines


def rich_text(x, y, line, size, c) -> str:
    spans, prev = [], None
    for k, (w, b, glued) in enumerate(line):
        sep = "" if (k == 0 or glued) else " "
        if spans and prev == b:
            spans[-1][0] += sep + w
        else:
            spans.append([sep + w, b])
        prev = b
    inner = "".join(
        f'<tspan fill="{c["fg1"] if b else c["fg2"]}" font-weight="{600 if b else 400}">'
        f'{escape(s)}</tspan>' for s, b in spans)
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'xml:space="preserve">{inner}</text>')


def shadow_filter(c) -> str:  # Fluent shadow4: 0 0 2px, 0 2px 4px
    return ('<filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">'
            f'<feDropShadow dx="0" dy="0" stdDeviation="1" flood-color="#000" flood-opacity="{c["shadowA"]}"/>'
            f'<feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#000" flood-opacity="{c["shadowB"]}"/>'
            '</filter>')


def card(h, c, radius=12) -> str:
    return (f'<rect x="4" y="4" width="{W - 8}" height="{h - 8}" rx="{radius}" '
            f'fill="{c["bg1"]}" stroke="{c["strokeCard"]}" filter="url(#shadow)"/>')


def svg(h, body, label, c, extra_defs="", w=W) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">'
            f'<title>{escape(label)}</title><defs>{shadow_filter(c)}{extra_defs}</defs>'
            f'{body}</svg>\n')


def section_title(x, y, label, name, c, size=24) -> str:
    return (f'<rect x="{x}" y="{y - 26}" width="36" height="36" rx="8" fill="{c["brandBg2"]}"/>'
            + icon(name, x + 8, y - 18, 20, c["brandFg2"], filled=True)
            + t(x + 50, y, label, size, c["fg1"], 600, family=FONT_DISPLAY))


def plain(s: str) -> str:
    return s.replace("**", "")


# ==========================================================================
# Sections
# ==========================================================================
def intro(c) -> str:
    """Name, tagline, both paragraphs and the five highlights."""
    maxw = W - 2 * PAD - 16
    body, y = "", 0

    y = 76
    body += t(PAD + 8, y, NAME_LINE, 36, c["fg1"], 600, family=FONT_DISPLAY, ls=-0.4)

    # Tagline: rocket + the original pipe-separated roles as a brand line
    y += 22
    tag_lines = rich_lines(f"**{TAGLINE}**", 15, maxw - 30)
    for i, line in enumerate(tag_lines):
        ly = y + 20 + i * 22
        if i == 0:
            body += icon("rocket", PAD + 8, ly - 15, 20, c["brandFg1"], filled=True)
        body += t(PAD + 38, ly, " ".join(w for w, _, _ in line), 15, c["brandFg1"], 600)
    y += 20 + (len(tag_lines) - 1) * 22

    # Paragraphs (Body 2 size for readability), bold runs in fg1
    for para in PARAGRAPHS:
        y += 18
        for line in rich_lines(para, 15, maxw):
            y += 24
            body += rich_text(PAD + 8, y, line, 15, c)

    # Highlights list
    y += 26
    body += f'<line x1="{PAD + 8}" x2="{W - PAD - 8}" y1="{y}" y2="{y}" stroke="{c["stroke2"]}"/>'
    y += 18
    for name, label in HIGHLIGHTS:
        body += (f'<rect x="{PAD + 8}" y="{y}" width="32" height="32" rx="8" '
                 f'fill="{c["brandBg2"]}"/>')
        body += icon(name, PAD + 14, y + 6, 20, c["brandFg2"], filled=True)
        body += t(PAD + 54, y + 21, label, 15, c["fg1"])
        y += 42
    h = y + PAD - 10

    defs = (''.join(
        f'<radialGradient id="g{i}"><stop offset="0" stop-color="{col}" stop-opacity="{op}"/>'
        f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>'
        for i, (col, op) in enumerate(((BLUE, c["blob"]), (LAVENDER, c["blob"] * .8),
                                       (CYAN, c["blob"] * .7))))
        + f'<clipPath id="clip"><rect x="4" y="4" width="{W - 8}" height="{h - 8}" rx="12"/></clipPath>')
    glow = ('<g clip-path="url(#clip)">'
            '<circle cx="780" cy="20" r="260" fill="url(#g0)"/>'
            '<circle cx="560" cy="-40" r="200" fill="url(#g1)"/>'
            '<circle cx="860" cy="200" r="180" fill="url(#g2)"/></g>')
    label = (f"{NAME_LINE} {TAGLINE}. " + " ".join(plain(p) for p in PARAGRAPHS)
             + " " + "; ".join(l for _, l in HIGHLIGHTS) + ".")
    return svg(h, card(h, c) + glow + body, label, c, defs)


def heading(c, title, name) -> str:
    h = 56
    return svg(h, section_title(8, 38, title, name, c), title, c)


def link_row(c, name, label, url) -> str:
    h = 68
    body = (f'<rect x="4" y="4" width="{W - 8}" height="{h - 8}" rx="8" fill="{c["bg1"]}" '
            f'stroke="{c["strokeCard"]}" filter="url(#shadow)"/>')
    body += f'<rect x="20" y="16" width="36" height="36" rx="8" fill="{c["brandBg2"]}"/>'
    body += icon(name, 28, 24, 20, c["brandFg2"], filled=True)
    body += t(72, 40, label, 16, c["fg1"], 600)
    body += t(72 + 110, 40, url, 15, c["brandFg1"])
    body += icon("chevron_right", W - 44, 24, 20, c["fg3"])
    return svg(h, body, f"{label}: {url}", c)


def lets_connect(c) -> str:
    y = 58
    body = section_title(PAD, y, LETS_TITLE, "handshake", c)
    y += 38
    body += t(PAD, y, LETS_INTRO, 15, c["fg2"])
    y += 18
    colw = (W - 2 * PAD - 12) / 2
    for i, (name, label) in enumerate(INTERESTS):
        x = PAD + (i % 2) * (colw + 12)
        ry = y + (i // 2) * 56
        body += (f'<rect x="{x:.1f}" y="{ry}" width="{colw:.1f}" height="46" rx="8" '
                 f'fill="{c["bg2"]}" stroke="{c["stroke2"]}"/>')
        body += (f'<rect x="{x + 10:.1f}" y="{ry + 9}" width="28" height="28" rx="6" '
                 f'fill="{c["brandBg2"]}"/>')
        body += icon(name, x + 14, ry + 13, 20, c["brandFg2"], filled=True)
        body += t(x + 50, ry + 28, label, 15, c["fg1"], 600)
    y += ((len(INTERESTS) + 1) // 2) * 56 + 22
    body += t(PAD, y, LETS_OUTRO, 15, c["fg2"])
    h = y + PAD
    label = (f"{LETS_TITLE}. {LETS_INTRO} " + ", ".join(l for _, l in INTERESTS)
             + f" — {LETS_OUTRO}")
    return svg(h, card(h, c) + body, label, c)


def star(c) -> str:
    h = 64
    body = (f'<rect x="4" y="4" width="{W - 8}" height="{h - 8}" rx="8" fill="{c["bg2"]}" '
            f'stroke="{c["strokeCard"]}"/>')
    body += icon("star", 24, 22, 20, c["star"], filled=True)
    body += t(56, 38, STAR_LINE, 15, c["fg1"], 600)
    return svg(h, body, STAR_LINE, c)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    for mode, c in THEMES.items():
        files = {
            "intro": intro(c),
            "connect-heading": heading(c, CONNECT_TITLE, "globe"),
            "lets-connect": lets_connect(c),
            "star": star(c),
        }
        for key, name, label, url in LINKS:
            files[f"link-{key}"] = link_row(c, name, label, url)
        for stem, data in files.items():
            (OUT / f"{stem}-{mode}.svg").write_text(data)
    print("wrote", len(list(OUT.glob("*.svg"))), "assets to", OUT)


if __name__ == "__main__":
    main()
