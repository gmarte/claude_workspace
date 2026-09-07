"""
build_deck.py — Build an RG PowerPoint that follows the Caribetrans corporate template
(RG/TEMPLATE/1.0.2 GC FORMATO PRESENTACIONES 21.7.2026 V1) from a JSON deck spec.

Standard implemented here (see ../references/brand_guidelines.md):
  - Helvetica everywhere. 48 pt cover, 32 pt bold titles, 18 pt body, >= 10 pt dense text.
  - White background, all text gray 7F7F7F (White, Background 1, Darker 50%).
  - Chart palette: Presupuesto ED7D31 | año actual 5B9BD5 | año anterior 70AD47 | 2 años atrás A6A6A6.
  - Logo top-left on every slide, footer with unit/period + slide number.

Usage:
  python build_deck.py --spec deck.json --output "RG/2026/9. Septiembre/9. RG. 15.09.2026 Sistemas 08 - 2026.pptx" [--render]

Slide types accepted in deck.json (see ../templates/deck_example.json for a full example):
  cover, section, kpi, table, bullets, two_column, chart, image, closing
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
LOGO = os.path.join(SKILL_DIR, "assets", "logo_caribetrans.png")
RENDER_PS1 = os.path.join(HERE, "render_preview.ps1")

# --------------------------------------------------------------------------- standard
FONT = "Helvetica"

COLOR = {
    "text": "7F7F7F",     # White, Background 1, Darker 50%
    "gray35": "A6A6A6",   # White, Background 1, Darker 35%  (headers, 2024)
    "gray15": "D9D9D9",   # borders, progress track
    "gray5": "F2F2F2",    # soft card fill
    "white": "FFFFFF",
    "orange": "ED7D31",   # Orange, Accent 2  -> Presupuesto
    "blue": "5B9BD5",     # Blue, Accent 5    -> año actual
    "green": "70AD47",    # Green, Accent 6   -> año anterior
    "red": "C00000",      # Dark Red          -> alerta / variación negativa
}
ROLE_COLOR = {"budget": "orange", "current": "blue", "prev": "green", "prev2": "gray35"}
STATUS_COLOR = {
    "completado": "green", "culminado": "green", "cerrado": "green", "producción": "green",
    "en progreso": "blue", "a tiempo": "blue", "en curso": "blue",
    "desviado": "red", "crítico": "red", "critico": "red", "atrasado": "red",
    "planeado": "gray35", "en espera": "gray35", "pausado": "gray35",
}

SIZE = {"cover": 48, "title": 32, "subtitle": 18, "body": 18, "small": 12, "tiny": 10, "kpi": 40}

SLIDE_W, SLIDE_H = 13.333, 7.5
MARGIN = 0.45
CONTENT_TOP = 1.65
CONTENT_BOTTOM = 6.75
FOOTER_Y = 6.95


def rgb(name_or_hex):
    return RGBColor.from_string(COLOR.get(name_or_hex, name_or_hex))


def est_lines(text, width_in, size, bold=False):
    """Rough line-count estimate for Helvetica/Arial text in a box of width_in inches."""
    factor = 0.56 if bold else 0.52
    if str(text).upper() == str(text):  # all-caps runs ~12% wider
        factor *= 1.12
    avg_char_in = size / 72 * factor
    cpl = max(int((width_in - 0.1) / avg_char_in), 1)
    lines = 0
    for para in str(text).split("\n"):
        lines += max(1, -(-len(para) // cpl))
    return lines


def fit_size(text, width_in, sizes, bold=False, max_lines=1):
    """First size in `sizes` that fits within max_lines; else the smallest."""
    for s in sizes:
        if est_lines(text, width_in, s, bold) <= max_lines:
            return s
    return sizes[-1]


# --------------------------------------------------------------------------- primitives
def _style_run(run, size, bold=False, color="text", italic=False):
    f = run.font
    f.name = FONT
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = rgb(color)


def add_text(slide, x, y, w, h, content, size=SIZE["body"], bold=False, color="text",
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=None, space_after=None,
             margin=0.05):
    """content: str (\\n = new paragraph) OR list of paragraphs, each a str or a list of run dicts
    {text, bold, color, size, italic}."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, Inches(margin))

    paragraphs = content.split("\n") if isinstance(content, str) else content
    for i, para in enumerate(paragraphs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if line_spacing:
            p.line_spacing = line_spacing
        if space_after is not None:
            p.space_after = Pt(space_after)
        runs = [{"text": para}] if isinstance(para, str) else para
        for rd in runs:
            r = p.add_run()
            r.text = rd.get("text", "")
            _style_run(r, rd.get("size", size), rd.get("bold", bold), rd.get("color", color),
                       rd.get("italic", False))
    return box


def add_rect(slide, x, y, w, h, fill=None, line=None, rounded=False, radius=0.08, line_w=0.75):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    shape.shadow.inherit = False
    if rounded:
        shape.adjustments[0] = radius
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill)
    else:
        shape.fill.background()
    if line:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(line_w)
    else:
        shape.line.fill.background()
    return shape


def add_picture_fit(slide, path, x, y, w, h, align="center"):
    """Insert an image scaled to fit inside the (x, y, w, h) box, preserving aspect ratio."""
    from PIL import Image

    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    px = x + (w - pw) / 2 if align == "center" else x
    py = y + (h - ph) / 2 if align == "center" else y
    return slide.shapes.add_picture(path, Inches(px), Inches(py), Inches(pw), Inches(ph))


def add_logo(slide):
    # Template position: x 181480 EMU, y 333367 EMU, h 717748 EMU
    add_picture_fit(slide, LOGO, 0.20, 0.36, 0.90, 0.78, align="left")


def add_header(slide, title, subtitle=None, right_reserve=0.0):
    """Logo + 32 pt bold title + 18 pt subtitle. Title shrinks to 28/24 pt if it would wrap."""
    add_logo(slide)
    title = (title or "").upper()
    tw = SLIDE_W - 1.35 - MARGIN - right_reserve
    size = fit_size(title, tw, [SIZE["title"], 28, 24], bold=True)
    if size != SIZE["title"]:
        print(f"  ! título largo ({len(title)} chars) reducido a {size} pt — considera acortarlo: {title[:50]}")
    add_text(slide, 1.35, 0.30, tw, 0.65, title, size=size, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    if subtitle:
        add_text(slide, 1.35, 0.95, tw, 0.45, subtitle, size=SIZE["subtitle"], anchor=MSO_ANCHOR.TOP)


def add_footer(slide, meta, n):
    footer = meta.get("footer", "")
    if meta.get("draft"):
        footer = (footer + "   •   DRAFT").strip(" •")
    add_text(slide, 3.5, FOOTER_Y, SLIDE_W - 7.0, 0.35, footer, size=SIZE["tiny"],
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, SLIDE_W - MARGIN - 1.0, FOOTER_Y, 1.0, 0.35, str(n), size=SIZE["tiny"],
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)


def bullet_paragraphs(items, size=SIZE["body"], bold=False, bullet="○"):
    """Return paragraph list with the template's red hollow bullet."""
    paras = []
    for it in items:
        if isinstance(it, str):
            paras.append([{"text": f"{bullet}  ", "color": "red", "size": size},
                          {"text": it, "size": size, "bold": bold}])
        else:  # already a run list
            paras.append([{"text": f"{bullet}  ", "color": "red", "size": size}] + it)
    return paras


def add_bullets(slide, x, y, w, h, items, size=SIZE["body"], bold=False, space_after=8):
    return add_text(slide, x, y, w, h, bullet_paragraphs(items, size, bold), size=size,
                    space_after=space_after, line_spacing=1.05)


def add_card(slide, x, y, w, h, label, value, note=None, note_color="text", value_size=None):
    """KPI card: label (top, up to 2 lines) / value (middle, auto-sized) / note (bottom)."""
    add_rect(slide, x, y, w, h, fill="gray5", rounded=True, radius=0.06)
    inner_w = w - 0.3
    label = (label or "").upper()
    label_size = 12 if est_lines(label, inner_w, 12, bold=True) == 1 else 10
    label_h = 0.42
    note_h = 0.36 if note else 0.1
    value_h = h - label_h - note_h
    value = str(value)
    # largest size whose line height fits value_h and whose text fits on one line
    candidates = [s for s in (value_size or SIZE["kpi"], 36, 32, 28, 24, 20) if s <= (value_size or SIZE["kpi"])]
    vsize = next((s for s in candidates
                  if s / 72 * 1.15 <= value_h and est_lines(value, inner_w, s, bold=True) == 1), candidates[-1])
    add_text(slide, x + 0.15, y + 0.06, inner_w, label_h, label, size=label_size, bold=True,
             anchor=MSO_ANCHOR.MIDDLE, line_spacing=0.95)
    add_text(slide, x + 0.15, y + label_h, inner_w, value_h, value, size=vsize, bold=True,
             anchor=MSO_ANCHOR.MIDDLE)
    if note:
        nsize = 12 if est_lines(note, inner_w, 12) == 1 else 10
        add_text(slide, x + 0.15, y + h - note_h - 0.04, inner_w, note_h, note, size=nsize,
                 color=note_color, anchor=MSO_ANCHOR.MIDDLE, line_spacing=0.95)


def add_cards_row(slide, cards, y, h=1.6, x=MARGIN, w=SLIDE_W - 2 * MARGIN, gap=0.15):
    n = max(len(cards), 1)
    cw = (w - gap * (n - 1)) / n
    for i, c in enumerate(cards):
        add_card(slide, x + i * (cw + gap), y, cw, h, c.get("label", ""), c.get("value", ""),
                 c.get("note"), c.get("note_color", "text"),
                 value_size=c.get("value_size", SIZE["kpi"] if n <= 5 else 32))
    return y + h


def add_chip(slide, x, y, w, h, text, color):
    add_rect(slide, x, y, w, h, fill=color, rounded=True, radius=0.5)
    add_text(slide, x, y, w, h, text, size=SIZE["tiny"], bold=True, color="white",
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, margin=0.02)


def add_progress(slide, x, y, w, pct, color="blue", h=0.16, label=True):
    pct = max(0.0, min(100.0, float(pct)))
    bar_w = w - (0.75 if label else 0)
    add_rect(slide, x, y, bar_w, h, fill="gray15", rounded=True, radius=0.5)
    if pct > 0:
        add_rect(slide, x, y, max(bar_w * pct / 100, h), h, fill=color, rounded=True, radius=0.5)
    if label:
        add_text(slide, x + bar_w + 0.05, y - 0.13, 0.7, h + 0.26, f"{pct:.0f}%", size=SIZE["small"],
                 bold=True, anchor=MSO_ANCHOR.MIDDLE, margin=0.02)


def status_color(text):
    t = (text or "").strip().lower()
    for key, col in STATUS_COLOR.items():
        if key in t:
            return col
    return "gray35"


def parse_pct(v):
    if isinstance(v, (int, float)):
        return float(v)
    return float(str(v).replace("%", "").replace(",", ".").strip() or 0)


def add_chart(slide, x, y, w, h, spec):
    """Native chart with the corporate palette.
    spec: {"kind": "column|bar", "categories": [...], "series": [{"name", "values", "role"|"color"}],
           "legend": true, "number_format": "0", "gap_width": 60}"""
    kind = spec.get("kind", "column")
    cd = CategoryChartData()
    cd.categories = spec["categories"]
    for s in spec["series"]:
        cd.add_series(s.get("name", ""), s["values"])

    ctype = XL_CHART_TYPE.BAR_CLUSTERED if kind == "bar" else XL_CHART_TYPE.COLUMN_CLUSTERED
    gf = slide.shapes.add_chart(ctype, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    chart = gf.chart
    chart.has_title = False
    chart.font.name = FONT
    chart.font.size = Pt(10)
    chart.font.color.rgb = rgb("text")

    plot = chart.plots[0]
    plot.gap_width = spec.get("gap_width", 60)
    plot.overlap = spec.get("overlap", -10)
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.font.size = Pt(10)
    dl.font.color.rgb = rgb("text")
    dl.number_format = spec.get("number_format", "0")
    dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END

    for s, sd in zip(plot.series, spec["series"]):
        col = sd.get("color") or ROLE_COLOR.get(sd.get("role", ""), "blue")
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = rgb(col)
        s.format.line.fill.background()

    va = chart.value_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb("gray15")
    va.format.line.fill.background()
    va.tick_labels.font.size = Pt(10)
    va.tick_labels.font.color.rgb = rgb("text")
    if spec.get("hide_value_axis", kind == "bar"):
        va.visible = False
        va.has_major_gridlines = False

    ca = chart.category_axis
    ca.format.line.color.rgb = rgb("gray15")
    ca.tick_labels.font.size = Pt(10)
    ca.tick_labels.font.color.rgb = rgb("text")
    if kind == "bar":
        ca.reverse_order = True

    show_legend = spec.get("legend", len(spec["series"]) > 1)
    chart.has_legend = bool(show_legend)
    if show_legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(10)
        chart.legend.font.color.rgb = rgb("text")
    return gf


def add_callouts(slide, callouts, x, y, w=2.6):
    """Right-aligned variation lines like the template: '+6 2026' (green) / '-2% vs. 2025' (red).
    callouts: [{"value": "+6", "text": "2026", "color": "green"}, ...]"""
    paras = []
    for c in callouts:
        paras.append([{"text": c.get("value", "") + " ", "bold": True, "color": c.get("color", "text"),
                       "size": 16},
                      {"text": c.get("text", ""), "bold": True, "size": 14}])
    add_text(slide, x, y, w, 0.4 * len(paras) + 0.1, paras, align=PP_ALIGN.RIGHT, space_after=2)


# --------------------------------------------------------------------------- slide builders
def slide_cover(prs, s, meta, n):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_logo(slide)
    add_text(slide, 0.6, 2.15, SLIDE_W - 1.2, 1.7, (s.get("title", "")).upper(), size=SIZE["cover"],
             bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.05)
    if s.get("subtitle"):
        add_text(slide, 0.6, 3.95, SLIDE_W - 1.2, 0.7, s["subtitle"].upper(), size=24,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if s.get("date"):
        add_text(slide, 0.6, 5.55, SLIDE_W - 1.2, 0.5, s["date"], size=SIZE["subtitle"], bold=True,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if s.get("presenter"):
        add_text(slide, 0.6, 6.05, SLIDE_W - 1.2, 0.45, s["presenter"], size=14,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    return slide


def slide_section(prs, s, meta, n):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_logo(slide)
    kicker = (s.get("kicker") or "").upper()
    title = (s.get("title") or "").upper()
    paras = []
    if kicker:
        paras.append([{"text": kicker, "size": SIZE["cover"] if len(kicker) <= 26 else 36, "bold": False}])
    paras.append([{"text": title, "size": SIZE["cover"] if len(title) <= 26 else 36, "bold": True}])
    add_text(slide, 0.8, 2.3, SLIDE_W - 1.6, 2.0, paras, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.05)
    if s.get("subtitle"):
        add_text(slide, 0.8, 4.4, SLIDE_W - 1.6, 0.6, s["subtitle"], size=SIZE["subtitle"],
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    date = s.get("date") or meta.get("meeting_date")
    if date:
        add_text(slide, 0.6, 6.4, SLIDE_W - 1.2, 0.4, date, size=14, bold=True,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_footer(slide, meta, n)
    return slide


def slide_kpi(prs, s, meta, n):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, s.get("title"), s.get("subtitle"))
    y = CONTENT_TOP
    if s.get("cards"):
        y = add_cards_row(slide, s["cards"], y, h=1.6) + 0.2

    chart = s.get("chart")
    bullets = s.get("bullets")
    avail_h = CONTENT_BOTTOM - y
    full_w = SLIDE_W - 2 * MARGIN
    chart_w = full_w * 0.6 if bullets else full_w
    if chart:
        if chart.get("title"):
            add_text(slide, MARGIN, y, chart_w, 0.3, chart["title"].upper(), size=SIZE["small"], bold=True)
            if chart.get("subtitle"):
                add_text(slide, MARGIN, y + 0.28, chart_w, 0.3, chart["subtitle"], size=SIZE["tiny"])
        add_chart(slide, MARGIN, y + 0.55, chart_w - 0.2, avail_h - 0.55, chart)
    if bullets:
        bx = MARGIN + chart_w if chart else MARGIN
        bw = full_w - chart_w if chart else full_w
        add_rect(slide, bx, y, bw, avail_h, fill="gray5", rounded=True, radius=0.04)
        add_text(slide, bx + 0.2, y + 0.12, bw - 0.4, 0.35, (s.get("bullets_title") or "LECTURA EJECUTIVA").upper(),
                 size=SIZE["small"], bold=True)
        add_bullets(slide, bx + 0.2, y + 0.5, bw - 0.4, avail_h - 0.6, bullets,
                    size=s.get("bullets_size", 14), space_after=6)
    add_footer(slide, meta, n)
    return slide


def slide_table(prs, s, meta, n):
    """columns: [{"header","width"(in),"kind": "text|progress|status|center"}], rows: [[...]]"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, s.get("title"), s.get("subtitle"))
    y = CONTENT_TOP
    if s.get("cards"):
        y = add_cards_row(slide, s["cards"], y, h=1.3) + 0.2
    if s.get("caption"):
        add_text(slide, MARGIN, y, SLIDE_W - 2 * MARGIN, 0.3, s["caption"].upper(), size=SIZE["small"], bold=True)
        y += 0.35

    cols = s["columns"]
    rows = s["rows"]
    total_w = SLIDE_W - 2 * MARGIN
    widths = [c.get("width") for c in cols]
    fixed = sum(w for w in widths if w)
    flex = [i for i, w in enumerate(widths) if not w]
    for i in flex:
        widths[i] = max((total_w - fixed) / len(flex), 0.8)
    scale = total_w / sum(widths)
    widths = [w * scale for w in widths]

    header_h = 0.42
    avail = CONTENT_BOTTOM - y - header_h
    row_h = min(0.55, avail / max(len(rows), 1))
    font_size = 14 if row_h >= 0.5 else (12 if row_h >= 0.4 else 10)

    # header bar (template style: gray 35% with white bold text)
    add_rect(slide, MARGIN, y, total_w, header_h, fill="gray35")
    cx = MARGIN
    for c, w in zip(cols, widths):
        add_text(slide, cx, y, w, header_h, c.get("header", ""), size=SIZE["small"], bold=True,
                 color="white", anchor=MSO_ANCHOR.MIDDLE,
                 align=PP_ALIGN.CENTER if c.get("kind") in ("progress", "status", "center") else PP_ALIGN.LEFT,
                 margin=0.08)
        cx += w
    y += header_h

    for ri, row in enumerate(rows):
        if ri % 2 == 1:
            add_rect(slide, MARGIN, y, total_w, row_h, fill="gray5")
        cx = MARGIN
        for c, w, val in zip(cols, widths, row):
            kind = c.get("kind", "text")
            if kind == "progress":
                pct = parse_pct(val)
                add_progress(slide, cx + 0.15, y + row_h / 2 - 0.08, w - 0.3, pct,
                             color=c.get("color", "blue"))
            elif kind == "status":
                chip_w = min(w - 0.2, 1.4)
                add_chip(slide, cx + (w - chip_w) / 2, y + row_h / 2 - 0.14, chip_w, 0.28,
                         str(val).upper(), status_color(str(val)))
            else:
                add_text(slide, cx, y, w, row_h, str(val), size=font_size,
                         bold=bool(c.get("bold")), anchor=MSO_ANCHOR.MIDDLE,
                         align=PP_ALIGN.CENTER if kind == "center" else PP_ALIGN.LEFT, margin=0.08)
            cx += w
        y += row_h
    add_rect(slide, MARGIN, y, total_w, 0.01, fill="gray15")
    add_footer(slide, meta, n)
    return slide


def slide_bullets(prs, s, meta, n):
    """title, subtitle, badge, lead, bullets, image, image_caption, impact_label, impact, callouts"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, s.get("title"), s.get("subtitle"), right_reserve=2.4 if s.get("badge") else 0)
    if s.get("badge"):
        add_chip(slide, SLIDE_W - MARGIN - 2.2, 0.42, 2.2, 0.36, s["badge"].upper(),
                 s.get("badge_color") or status_color(s["badge"]))

    y = CONTENT_TOP
    full_w = SLIDE_W - 2 * MARGIN
    image = s.get("image")
    text_w = full_w * 0.55 if image else full_w
    bottom = CONTENT_BOTTOM
    if s.get("impact"):
        bottom -= 1.0

    if s.get("lead"):
        lines = est_lines(s["lead"], text_w - 0.2, SIZE["body"], bold=True)
        lead_h = lines * SIZE["body"] * 1.25 / 72 + 0.15
        add_text(slide, MARGIN, y, text_w - 0.2, lead_h, s["lead"], size=SIZE["body"], bold=True,
                 line_spacing=1.05)
        y += lead_h + 0.15
    if s.get("bullets"):
        add_bullets(slide, MARGIN, y, text_w - 0.2, bottom - y, s["bullets"],
                    size=s.get("bullets_size", SIZE["body"]))
    if image:
        ix = MARGIN + text_w
        iw = full_w - text_w
        cap_h = 0.35 if s.get("image_caption") else 0
        pic = add_picture_fit(slide, image, ix, CONTENT_TOP, iw, bottom - CONTENT_TOP - cap_h)
        pic.line.color.rgb = rgb("gray15")
        pic.line.width = Pt(0.75)
        if s.get("image_caption"):
            add_text(slide, ix, bottom - cap_h, iw, cap_h, s["image_caption"], size=SIZE["tiny"],
                     align=PP_ALIGN.CENTER)
    if s.get("impact"):
        iy = CONTENT_BOTTOM - 0.85
        add_rect(slide, MARGIN, iy, full_w, 0.85, fill="gray5", rounded=True, radius=0.06)
        add_text(slide, MARGIN + 0.2, iy + 0.08, 1.6, 0.3, (s.get("impact_label") or "IMPACTO").upper(),
                 size=SIZE["small"], bold=True)
        add_text(slide, MARGIN + 0.2, iy + 0.35, full_w - 0.4, 0.45, s["impact"], size=14,
                 anchor=MSO_ANCHOR.MIDDLE)
    add_footer(slide, meta, n)
    return slide


def slide_two_column(prs, s, meta, n):
    """left/right: {"header": "...", "items": [...]} — template 'Noticias del mes' layout."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, s.get("title"), s.get("subtitle"))
    y = CONTENT_TOP
    full_w = SLIDE_W - 2 * MARGIN
    gap = 0.6
    col_w = (full_w - gap) / 2
    h = CONTENT_BOTTOM - y
    for i, col in enumerate((s.get("left", {}), s.get("right", {}))):
        x = MARGIN + i * (col_w + gap)
        add_rect(slide, x, y, col_w, h, fill="white", line="gray15")
        add_rect(slide, x, y, col_w, 0.5, fill="gray35")
        add_text(slide, x, y, col_w, 0.5, col.get("header", ""), size=SIZE["subtitle"], bold=True,
                 color="white", align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        add_bullets(slide, x + 0.2, y + 0.7, col_w - 0.4, h - 0.9, col.get("items", []),
                    size=s.get("bullets_size", SIZE["body"]), bold=col.get("bold", False))
    add_footer(slide, meta, n)
    return slide


def slide_chart(prs, s, meta, n):
    """Full-width chart slide, template 'Reportes de volumen' style, with optional callouts."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, s.get("title"), s.get("subtitle"))
    if s.get("tag"):  # small square tag top-right like 'M' / 'Q' / 'H1'
        add_rect(slide, SLIDE_W - MARGIN - 0.7, 0.2, 0.7, 0.55, fill="white", line="gray35")
        add_text(slide, SLIDE_W - MARGIN - 0.7, 0.2, 0.7, 0.55, s["tag"], size=20, bold=True,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    y = CONTENT_TOP
    if s.get("callouts"):
        add_callouts(slide, s["callouts"], SLIDE_W - MARGIN - 2.8, 1.0)
        y += 0.35
    add_chart(slide, MARGIN, y, SLIDE_W - 2 * MARGIN, CONTENT_BOTTOM - y - (0.5 if s.get("note") else 0), s)
    if s.get("note"):
        add_text(slide, MARGIN, CONTENT_BOTTOM - 0.45, SLIDE_W - 2 * MARGIN, 0.4, s["note"],
                 size=SIZE["small"], align=PP_ALIGN.CENTER)
    add_footer(slide, meta, n)
    return slide


def slide_image(prs, s, meta, n):
    """Full-width screenshot with optional caption and bullets underneath."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, s.get("title"), s.get("subtitle"))
    y = CONTENT_TOP
    full_w = SLIDE_W - 2 * MARGIN
    bullets = s.get("bullets")
    cap_h = 0.35 if s.get("image_caption") else 0
    bullets_h = 1.2 if bullets else 0
    img_h = CONTENT_BOTTOM - y - cap_h - bullets_h
    pic = add_picture_fit(slide, s["image"], MARGIN, y, full_w, img_h)
    pic.line.color.rgb = rgb("gray15")
    pic.line.width = Pt(0.75)
    y += img_h
    if cap_h:
        add_text(slide, MARGIN, y, full_w, cap_h, s["image_caption"], size=SIZE["tiny"], align=PP_ALIGN.CENTER)
        y += cap_h
    if bullets:
        add_bullets(slide, MARGIN, y + 0.05, full_w, bullets_h, bullets, size=14, space_after=4)
    add_footer(slide, meta, n)
    return slide


def slide_closing(prs, s, meta, n):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_logo(slide)
    paras = [[{"text": (s.get("title") or "GRACIAS").upper(), "size": SIZE["cover"], "bold": True}],
             [{"text": (s.get("subtitle") or "POR SU ATENCIÓN").upper(), "size": 40, "bold": False}]]
    add_text(slide, 0.8, 2.3, SLIDE_W - 1.6, 2.0, paras, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.05)
    name = s.get("name") or meta.get("author")
    role = s.get("role") or meta.get("role")
    if name:
        add_text(slide, 0.8, 5.0, SLIDE_W - 1.6, 0.45, name, size=SIZE["subtitle"], bold=True,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if role:
        add_text(slide, 0.8, 5.45, SLIDE_W - 1.6, 0.4, role, size=14, align=PP_ALIGN.CENTER,
                 anchor=MSO_ANCHOR.MIDDLE)
    add_footer(slide, meta, n)
    return slide


BUILDERS = {
    "cover": slide_cover,
    "section": slide_section,
    "kpi": slide_kpi,
    "table": slide_table,
    "bullets": slide_bullets,
    "two_column": slide_two_column,
    "chart": slide_chart,
    "image": slide_image,
    "closing": slide_closing,
}


# --------------------------------------------------------------------------- main
def build(spec, output):
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)
    meta = spec.get("meta", {})
    for i, s in enumerate(spec["slides"], start=1):
        kind = s.get("type")
        if kind not in BUILDERS:
            raise ValueError(f"Slide {i}: unknown type '{kind}'. Valid: {', '.join(BUILDERS)}")
        BUILDERS[kind](prs, s, meta, i)
        print(f"  slide {i:02d}  {kind:<10} {str(s.get('title', ''))[:60]}")
    out_dir = os.path.dirname(output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    prs.save(output)
    return output


def render(pptx_path, out_dir=None):
    if not out_dir:
        stem = os.path.splitext(os.path.basename(pptx_path))[0]
        out_dir = os.path.join(tempfile.gettempdir(), "rg_preview", stem)
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", RENDER_PS1,
           "-Pptx", os.path.abspath(pptx_path), "-OutDir", out_dir]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Render failed:\n" + res.stderr, file=sys.stderr)
        return None
    print(f"\nPreview PNGs ({out_dir}):")
    print(res.stdout.strip())
    return out_dir


def main():
    ap = argparse.ArgumentParser(description="Build corporate-standard RG PPTX from a JSON spec")
    ap.add_argument("--spec", required=True, help="Path to deck.json")
    ap.add_argument("--output", required=True, help="Output .pptx path")
    ap.add_argument("--render", action="store_true", help="Export PNG previews via PowerPoint after building")
    ap.add_argument("--preview-dir", help="Where to write PNG previews (default: %%TEMP%%/rg_preview/<name>)")
    args = ap.parse_args()

    with open(args.spec, encoding="utf-8") as fh:
        spec = json.load(fh)

    # resolve relative image paths against the spec file location
    base = os.path.dirname(os.path.abspath(args.spec))
    for s in spec["slides"]:
        if s.get("image") and not os.path.isabs(s["image"]):
            cand = os.path.join(base, s["image"])
            s["image"] = cand if os.path.exists(cand) else s["image"]
        if s.get("image") and not os.path.exists(s["image"]):
            print(f"ERROR: image not found: {s['image']}", file=sys.stderr)
            sys.exit(1)

    print(f"Building {len(spec['slides'])} slides -> {args.output}")
    build(spec, args.output)
    print(f"\nSaved: {args.output}")
    if args.render:
        render(args.output, args.preview_dir)


if __name__ == "__main__":
    main()
