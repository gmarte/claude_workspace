---
name: rg-presentation
description: |
  Monthly RG (Reuniones de Gerencia) presentation skill for Giancarlo's IT department.
  Generates the Sistema de Gestión indicators email and a PowerPoint deck that follows the
  Caribetrans corporate presentation standard (Gobierno Corporativo template, 21.7.2026).

  TRIGGER when the user says any of:
  - "Let's work on my RG presentation"
  - "work on my RG presentation"
  - "RG presentation"
  - "presentación gerencial" / "presentación RG"

  SKIP when:
  - User is only asking a question about past presentations
  - User is not providing a dashboard image

version: 2.0.0
---

# RG Presentation — Execution Guide

You are generating Giancarlo's monthly IT KPI deliverables for the CaribeTrans management meeting
(Reunión Gerencial). Execute every step in order without skipping.

**Every slide must follow the corporate standard** in `references/brand_guidelines.md`
(Helvetica, gray text `7F7F7F`, white background, 48/32/18 pt, corporate chart palette, logo
top-left). `scripts/build_deck.py` enforces it — never build the deck any other way and never
copy an old deck as a base.

---

## Non-negotiable rules

1. **Reporting month is always last month.** If the meeting is in May 2026, you report April 2026 (04-2026).
2. **% de Resolución = (Resueltos + Cerrados) / Total × 100** — 2 decimals in the email (84.72%), nearest integer on slides.
3. **Días Promedio = Tiempo Promedio (hours) / 24** — 2 decimals in the email (6.67), 1 decimal on slides.
4. **Never invent KPI numbers** — read everything from the provided dashboard image.
5. **Corporate standard is mandatory** — fonts, colors and layout come from `build_deck.py`; do not add colored backgrounds, other fonts or off-palette colors in the JSON.
6. **Always render and inspect** the PNG previews before reporting done. Fix overflows in the JSON (shorten text, split slide) and rebuild.

---

## Month names (Spanish)

| # | Name | # | Name |
|---|---|---|---|
| 1 | Enero | 7 | Julio |
| 2 | Febrero | 8 | Agosto |
| 3 | Marzo | 9 | Septiembre |
| 4 | Abril | 10 | Octubre |
| 5 | Mayo | 11 | Noviembre |
| 6 | Junio | 12 | Diciembre |

---

## Workflow — execute every step in order

### Step 1 — Extract meeting date

Search the user's message for `DD.MM.YYYY` or `DD/MM/YYYY`. If found, normalize to `meeting_date = DD.MM.YYYY`
and `meeting_date_slash = DD/MM/YYYY`. If not found, ask: *"¿Cuál es la fecha de la reunión? (formato: DD.MM.YYYY)"*

Derive `meeting_day`, `meeting_month_num` (zero-padded), `meeting_year`, `meeting_month_name`.

### Step 2 — Determine reporting period

```
report_month_num  = meeting_month_num - 1   (January → 12 of previous year)
report_year       = meeting_year (or meeting_year - 1 when wrapping)
report_period     = f"{report_month_num:02d} - {report_year}"     # "07 - 2026"
report_month_name = Spanish month name
period_label      = f"{report_month_name} {report_year}"          # "Julio 2026"
```

### Step 3 — Analyze the dashboard image

Read from the **lower KPI row** (period-specific cards) of the screenshot:

| Variable | Label in image |
|---|---|
| `total_tickets` | "Total Tickets" |
| `resueltos` | "Tickets Resueltos" |
| `cerrados` | "Tickets Cerrados" |
| `abiertos` | "Tickets Abiertos" |
| `tiempo_horas` | "Tiempo Promedio" (strip "h") |

Also read the **department distribution** (bar chart or table in the image): department names and ticket counts, top 7.

```python
pct_resolucion_email = (resueltos + cerrados) / total_tickets * 100   # f"{x:.2f}"
dias_promedio_email  = tiempo_horas / 24                              # f"{x:.2f}"
pct_resolucion = round(pct_resolucion_email)                          # slides
dias_promedio  = round(dias_promedio_email, 1)                        # slides
cerrados_pct   = round(cerrados / total_tickets * 100)
abiertos_pct   = round(abiertos / total_tickets * 100)
```

State the extracted values before proceeding:
> Extracted: total=50, resueltos=1, cerrados=38, abiertos=11, tiempo=105h → email: 78.00% / 4.38 días — slides: 78% / 4.4 días

### Step 4 — Output the email for Sistema de Gestión

```
━━━ EMAIL PARA SISTEMA DE GESTIÓN ━━━━━━━━━━━━━━━━━
Asunto: Indicadores {report_month_num:02d}-{report_year}

% de Resolución de Tickets: {pct_resolucion_email:.2f}%
Promedio de Días de Resolución: {dias_promedio_email:.2f}
% de Avance de Proyectos: ver adjunto

Saludos,
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 5 — Carry over last month's narrative

Find the previous deck (most recent `RG/*/*/9. RG.*.pptx`, normally in the previous meeting's folder) and dump it:

```bash
python .claude/skills/rg-presentation/scripts/scan_pptx.py "RG/2026/8. Agosto/9. RG. 25.08.2026 Sistemas 07 - 2026.pptx"
```

From the dump collect: last month's `dias_promedio` (for the "vs." note), the project portfolio rows
(name, área, %, estado), project detail slides, and any "en espera / próximos pasos" text.
Ask the user for **this month's project updates** if they did not provide them. Do not invent progress.

If `PM.pdf` exists in the meeting folder, it is the Power BI project export — read it (`pymupdf`) for the
current portfolio (Descripción, Segmento, Porciento de avance, Estado).

### Step 6 — Determine output paths

```
output_folder = f"RG/{meeting_year}/{int(meeting_month_num)}. {meeting_month_name}"
deck_json     = f"{output_folder}/deck.json"
output_pptx   = f"{output_folder}/9. RG. {meeting_date} Sistemas {report_month_num:02d} - {report_year}.pptx"
```

Example: `RG/2026/9. Septiembre/9. RG. 15.09.2026 Sistemas 08 - 2026.pptx`

### Step 7 — Write `deck.json`

Start from `templates/deck_example.json` and keep this slide order:

| # | type | Content |
|---|---|---|
| 1 | `cover` | title "Unidad de Sistemas", subtitle "Reporte Gerencial • {period_label}", date `meeting_date_slash` |
| 2 | `kpi` | 5 cards (totales, cerrados, abiertos, % resolución, tiempo promedio), department `bar` chart, 2–3 "Lectura ejecutiva" bullets |
| 3 | `section` | kicker "01 • Portafolio", title "Seguimiento de Proyectos" |
| 4 | `table` | summary cards + portfolio rows (columns: Proyecto / Área / Avance `progress` / Estado `status`) |
| 5..n | `bullets` / `image` / `two_column` / `chart` | one slide per highlighted project or topic; screenshots via `image` |
| last | `closing` | "Gracias / Por su atención" (author/role from meta) |

Rules for the JSON:
- `meta.footer` = `"Unidad de Sistemas  •  Reporte Gerencial  •  {period_label}"`; `meta.draft` true only if the user says it is a borrador.
- KPI card 5 note: `"▲ vs. {prev} días {prev_month}"` with `note_color: "red"` when slower, `"▼ ..."` with `"green"` when faster.
- Chart series use `role`: `budget` (Presupuesto), `current` (año actual), `prev`, `prev2`. Never hardcode other colors.
- Titles ≤ 40 characters (the builder shrinks longer ones and warns). Bullets ≤ 110 characters, max 5 per slide, max 8 table rows per slide.
- Image paths relative to the workspace root or absolute. Copy user screenshots into `{output_folder}/img/` first.
- Text values are plain strings; the builder uppercases titles, labels and badges.

Full schema (all keys per slide type) is in `templates/deck_example.json`; `build_deck.py` docstring lists the types.

### Step 8 — Build and render

```bash
python .claude/skills/rg-presentation/scripts/build_deck.py --spec "{deck_json}" --output "{output_pptx}" --render
```

`--render` exports PNGs through the installed PowerPoint (`scripts/render_preview.ps1`) into `%TEMP%/rg_preview/<deck name>/`.
**Open every PNG with the Read tool** and check: no text overflow or overlap, no title reduced (see build warnings), values match Step 3.
Fix the JSON and rebuild until clean.

### Step 9 — Confirm to user

Report:
- The email is ready to copy (Step 4) — remind to attach the "% de Avance de Proyectos" file.
- PPTX path and slide list.
- Any content you carried over from last month that needs their confirmation (project % and status).
- That the deck follows the Gobierno Corporativo format (`RG/TEMPLATE`), so no manual restyling is needed.
