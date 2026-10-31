#!/usr/bin/env python3
"""Build the Fluent 2 styled SVG assets used by the profile README.

GitHub READMEs cannot run JavaScript or load stylesheets, so the Fluent UI
React components cannot be used directly. Instead this script renders the
Fluent 2 design language -- design tokens, type ramp, corner radii, elevation
and Fluent System Icons -- into static SVGs, one light and one dark variant
of each, which README.md swaps with <picture> + prefers-color-scheme.

Usage:  python3 scripts/build_assets.py      (writes into ./assets)

Icons:  Fluent System Icons, MIT, https://github.com/microsoft/fluentui-system-icons
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

FONT = ("'Segoe UI Variable Text','Segoe UI Variable','Segoe UI',Selawik,"
        "-apple-system,BlinkMacSystemFont,'Helvetica Neue',Roboto,Arial,sans-serif")
FONT_DISPLAY = FONT.replace("Variable Text", "Variable Display")

# --------------------------------------------------------------------------
# Fluent 2 web tokens (webLightTheme / webDarkTheme)
# --------------------------------------------------------------------------
THEMES = {
    "light": dict(
        bg1="#FFFFFF", bg2="#FAFAFA", bg3="#F5F5F5",
        fg1="#242424", fg2="#424242", fg3="#616161",
        stroke1="#D1D1D1", stroke2="#E0E0E0", strokeCard="#E0E0E0",
        brand="#0F6CBD", brandHover="#115EA3", brandFg1="#0F6CBD",
        brandBg2="#EBF3FC", brandFg2="#115EA3", brandStroke2="#B4D6FA",
        onBrand="#FFFFFF",
        shadowA=0.12, shadowB=0.14, blob=0.20,
    ),
    "dark": dict(
        bg1="#292929", bg2="#1F1F1F", bg3="#141414",
        fg1="#FFFFFF", fg2="#D6D6D6", fg3="#ADADAD",
        stroke1="#666666", stroke2="#525252", strokeCard="#3D3D3D",
        brand="#115EA3", brandHover="#0F6CBD", brandFg1="#479EF5",
        brandBg2="#082338", brandFg2="#62ABF5", brandStroke2="#0E4775",
        onBrand="#FFFFFF",
        shadowA=0.28, shadowB=0.32, blob=0.38,
    ),
}
# Fluent shared colours used for the decorative gradient
BLUE, LAVENDER, CYAN = "#0F6CBD", "#7160E8", "#0099BC"

SLACK = 1.07  # headroom for system fonts wider than Segoe UI (e.g. SF Pro)


def text_width(text: str, size: float, weight: str = "Regular") -> float:
    table = METRICS["Bold" if weight in ("Bold", "Semibold") else "Regular"]
    w = sum(table.get(ch, 0.55) for ch in text) * size
    if weight == "Semibold":  # between Regular and Bold
        w = (w + sum(METRICS["Regular"].get(ch, 0.55) for ch in text) * size) / 2
    return w * SLACK


def icon(name: str, x: float, y: float, size: float, fill: str, filled=False) -> str:
    variant = "filled" if filled else "regular"
    src = (ICONS / f"{name}_20_{variant}.svg").read_text()
    paths = "".join(re.findall(r"<path[^>]*/>", src))
    s = size / 20
    return (f'<g transform="translate({x:.2f} {y:.2f}) scale({s:.4f})" '
            f'fill="{fill}">{paths}</g>')


def t(x, y, s, size, fill, weight=400, anchor="start", family=FONT, ls=None) -> str:
    extra = f' letter-spacing="{ls}"' if ls is not None else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{extra}>{escape(s)}</text>')


def svg(w, h, body, title, defs="") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">'
            f'<title>{escape(title)}</title><defs>{defs}</defs>{body}</svg>\n')


def shadow_filter(c, fid="shadow") -> str:
    # Fluent shadow4: 0 0 2px a, 0 2px 4px b
    return (f'<filter id="{fid}" x="-10%" y="-10%" width="120%" height="130%">'
            f'<feDropShadow dx="0" dy="0" stdDeviation="1" flood-color="#000" flood-opacity="{c["shadowA"]}"/>'
            f'<feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#000" flood-opacity="{c["shadowB"]}"/>'
            f'</filter>')


def card(w, h, c, pad=4, radius=12) -> str:
    return (f'<rect x="{pad}" y="{pad}" width="{w - 2 * pad}" height="{h - 2 * pad}" '
            f'rx="{radius}" fill="{c["bg1"]}" stroke="{c["strokeCard"]}" '
            f'filter="url(#shadow)"/>')


def section_title(x, y, label, name, c) -> str:
    return (icon(name, x, y - 17, 20, c["brandFg1"], filled=True)
            + t(x + 30, y, label, 20, c["fg1"], 600))


# --------------------------------------------------------------------------
# Hero
# --------------------------------------------------------------------------
def hero(c, mode) -> str:
    W, H = 840, 288
    defs = shadow_filter(c) + (
        '<clipPath id="clip"><rect x="4" y="4" width="832" height="280" rx="12"/></clipPath>'
        + "".join(
            f'<radialGradient id="g{i}"><stop offset="0" stop-color="{col}" stop-opacity="{op}"/>'
            f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>'
            for i, (col, op) in enumerate(((BLUE, c["blob"]), (LAVENDER, c["blob"] * .8),
                                           (CYAN, c["blob"] * .7))))
        + (
        f'<linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{BLUE}"/>'
        f'<stop offset="1" stop-color="{LAVENDER}"/></linearGradient>'
        f'<linearGradient id="avatar" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="#5B4BD1"/></linearGradient>'
    ))
    body = card(W, H, c)
    body += ('<g clip-path="url(#clip)">'
             '<circle cx="760" cy="40" r="260" fill="url(#g0)"/>'
             '<circle cx="600" cy="280" r="220" fill="url(#g1)"/>'
             '<circle cx="850" cy="270" r="200" fill="url(#g2)"/>'
             '</g>')

    x = 48
    # Badge (Fluent Badge, tint, rounded)
    label = "Vice President · Citi"
    bw = 12 + 16 + 6 + text_width(label, 12, "Semibold") + 12
    body += (f'<rect x="{x}" y="44" width="{bw:.1f}" height="28" rx="14" '
             f'fill="{c["brandBg2"]}" stroke="{c["brandStroke2"]}"/>')
    body += icon("building_bank", x + 12, 50, 16, c["brandFg2"], filled=True)
    body += t(x + 34, 62.5, label, 12, c["brandFg2"], 600)

    # Large Title / Subtitle / Body
    body += t(x, 128, "Hi, I'm Joy Rana", 40, c["fg1"], 600, family=FONT_DISPLAY, ls=-0.5)
    body += t(x, 166, "Staff Software Engineer · AI Engineer · Educator", 20, c["fg2"], 400)
    body += t(x, 204, "14+ years building large-scale enterprise applications", 14, c["fg3"])
    body += t(x, 226, "in finance. Now focused on Agentic AI, LLMs and distributed systems.", 14, c["fg3"])

    # Tags row
    tx = x
    for name, lbl in (("sparkle", "Agentic AI"), ("server", "Distributed systems"),
                      ("video", "YouTube educator")):
        tw = 8 + 16 + 6 + text_width(lbl, 12) + 10
        body += (f'<rect x="{tx:.1f}" y="244" width="{tw:.1f}" height="24" rx="4" '
                 f'fill="{c["bg3"]}" stroke="{c["stroke2"]}"/>')
        body += icon(name, tx + 8, 248, 16, c["fg2"])
        body += t(tx + 30, 260.5, lbl, 12, c["fg2"])
        tx += tw + 8

    # Avatar with active ring (Fluent Avatar, size 128, ring)
    cx, cy = 708, 140
    body += f'<circle cx="{cx}" cy="{cy}" r="76" fill="none" stroke="url(#ring)" stroke-width="4"/>'
    body += f'<circle cx="{cx}" cy="{cy}" r="70" fill="{c["bg1"]}"/>'
    body += f'<circle cx="{cx}" cy="{cy}" r="66" fill="url(#avatar)"/>'
    body += t(cx, cy + 17, "JR", 48, "#FFFFFF", 600, anchor="middle", family=FONT_DISPLAY)

    return svg(W, H, body, "Hi, I'm Joy Rana — Vice President at Citi, Staff Software "
               "Engineer, AI Engineer and Educator", defs)


# --------------------------------------------------------------------------
# What I'm doing now — 2-column list of tiles
# --------------------------------------------------------------------------
NOW = [
    ("briefcase", "Staff Software Engineer", "Vice President at Citi"),
    ("bot", "Agentic AI & LLMs", "MCP, LangGraph, RAG and AI systems"),
    ("code", "Full-stack engineering", "Java, Spring Boot, Python, React, FastAPI"),
    ("rocket", "Production-ready AI", "Building AI applications from scratch"),
    ("book_open", "Teaching", "Data structures, algorithms, AI engineering"),
    ("video", "YouTube tutorials", "Project-based software and AI lessons"),
]


def now(c, mode) -> str:
    W, pad, gap, th = 840, 28, 12, 68
    cols, rows = 2, (len(NOW) + 1) // 2
    tw = (W - 2 * pad - gap) / cols
    top = 76
    H = top + rows * th + (rows - 1) * gap + pad
    body = card(W, H, c)
    body += section_title(pad, 48, "What I'm working on", "sparkle", c)
    for i, (name, title, desc) in enumerate(NOW):
        cx = pad + (i % cols) * (tw + gap)
        cy = top + (i // cols) * (th + gap)
        body += (f'<rect x="{cx:.1f}" y="{cy}" width="{tw:.1f}" height="{th}" rx="8" '
                 f'fill="{c["bg2"]}" stroke="{c["stroke2"]}"/>')
        body += (f'<rect x="{cx + 14:.1f}" y="{cy + 14}" width="40" height="40" rx="8" '
                 f'fill="{c["brandBg2"]}"/>')
        body += icon(name, cx + 24, cy + 24, 20, c["brandFg2"], filled=True)
        body += t(cx + 68, cy + 30, title, 14, c["fg1"], 600)
        body += t(cx + 68, cy + 50, desc, 12, c["fg3"])
    return svg(W, H, body, "What I'm working on: " +
               "; ".join(f"{a} — {b}" for _, a, b in NOW), shadow_filter(c))


# --------------------------------------------------------------------------
# Focus areas + toolbox — wrapping chips
# --------------------------------------------------------------------------
FOCUS = [
    ("brain_circuit", "AI Engineering"),
    ("bot", "Agentic AI"),
    ("flash", "Ultra-low-latency systems"),
    ("organization", "Solution architecture"),
    ("server", "Distributed systems"),
    ("flowchart", "Data structures & algorithms"),
]
STACK = ["Java", "Spring Boot", "Python", "FastAPI", "React", "LangGraph",
         "MCP", "RAG", "LLMs"]


def chips(items, x0, y0, maxw, c, brand, h=32):
    out, x, y = "", x0, y0
    for item in items:
        name, label = item if isinstance(item, tuple) else (None, item)
        w = 12 + (20 + 8 if name else 0) + text_width(label, 14) + 12
        if x + w > x0 + maxw:
            x, y = x0, y + h + 10
        fill, stroke, fg = ((c["brandBg2"], c["brandStroke2"], c["brandFg2"]) if brand
                            else (c["bg1"], c["stroke1"], c["fg1"]))
        out += (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" '
                f'fill="{fill}" stroke="{stroke}"/>')
        lx = x + 12
        if name:
            out += icon(name, lx, y + 6, 20, fg)
            lx += 28
        out += t(lx, y + 21, label, 14, fg)
        x += w + 10
    return out, y + h


def focus(c, mode) -> str:
    W, pad = 840, 28
    body_inner, y = chips(FOCUS, pad, 72, W - 2 * pad, c, brand=True)
    y += 40
    title2 = section_title(pad, y + 20, "Toolbox", "toolbox", c)
    stack, y2 = chips(STACK, pad, y + 40, W - 2 * pad, c, brand=False)
    H = y2 + pad
    body = card(W, H, c)
    body += section_title(pad, 48, "Focus areas", "brain_circuit", c)
    body += body_inner
    body += f'<line x1="{pad}" x2="{W - pad}" y1="{y - 16}" y2="{y - 16}" stroke="{c["stroke2"]}"/>'
    body += title2 + stack
    return svg(W, H, body, "Focus areas: " + ", ".join(l for _, l in FOCUS)
               + ". Toolbox: " + ", ".join(STACK), shadow_filter(c))


# --------------------------------------------------------------------------
# Connect — Fluent buttons (size large: 40px tall, 4px radius)
# --------------------------------------------------------------------------
LINKS = [
    ("linkedin", "person_circle", "LinkedIn", True),
    ("youtube", "video", "YouTube", False),
    ("website", "globe", "joyrana.in", False),
    ("medium", "drafts", "Medium", False),
]


def button(c, icon_name, label, primary) -> str:
    h, pad = 40, 16
    w = round(pad + 20 + 8 + text_width(label, 14, "Semibold") + pad + 4)
    W, H = w + 4, h + 6  # room for elevation
    if primary:
        bg, stroke, fg = c["brand"], "none", c["onBrand"]
    else:
        bg, stroke, fg = c["bg1"], c["stroke1"], c["fg1"]
    body = (f'<rect x="2" y="2" width="{w}" height="{h}" rx="4" fill="{bg}" '
            f'stroke="{stroke}" filter="url(#shadow)"/>')
    body += icon(icon_name, 2 + pad, 2 + 10, 20, fg, filled=primary)
    body += t(2 + pad + 28, 2 + 25, label, 14, fg, 600)
    return svg(W, H, body, label, shadow_filter(c))


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for mode, c in THEMES.items():
        (OUT / f"hero-{mode}.svg").write_text(hero(c, mode))
        (OUT / f"now-{mode}.svg").write_text(now(c, mode))
        (OUT / f"focus-{mode}.svg").write_text(focus(c, mode))
        for key, ic, label, primary in LINKS:
            (OUT / f"btn-{key}-{mode}.svg").write_text(button(c, ic, label, primary))
    print("wrote", len(list(OUT.glob("*.svg"))), "assets to", OUT)


if __name__ == "__main__":
    main()
