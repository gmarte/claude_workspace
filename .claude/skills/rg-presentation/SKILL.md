---
name: rg-presentation
description: |
  Monthly RG (Reuniones de Gerencia) presentation skill for Giancarlo's IT department.
  Generates the audit team email and PowerPoint slide deck from a dashboard screenshot.

  TRIGGER when the user says any of:
  - "Let's work on my RG presentation"
  - "work on my RG presentation"
  - "RG presentation"

  SKIP when:
  - User is only asking a question about past presentations
  - User is not providing a dashboard image

version: 1.0.0
---

# RG Presentation — Execution Guide

You are generating Giancarlo's monthly IT KPI deliverables for CaribeTrans board meetings. Execute every step in order without skipping.

---

## Non-negotiable rules

1. **Reporting month is always last month.** If today is in May 2026, you are reporting April 2026 (04-2026).
2. **% de Resolución = (Resueltos + Cerrados) / Total × 100**, rounded to nearest integer.
3. **Días Promedio = Tiempo Promedio (hours) / 24**, rounded to 1 decimal.
4. **Never invent KPI numbers** — read everything from the provided dashboard image.
5. **Always create the output folder** if it does not exist before running the script.

---

## Month names (Spanish)

| # | Name |
|---|---|
| 1 | Enero |
| 2 | Febrero |
| 3 | Marzo |
| 4 | Abril |
| 5 | Mayo |
| 6 | Junio |
| 7 | Julio |
| 8 | Agosto |
| 9 | Septiembre |
| 10 | Octubre |
| 11 | Noviembre |
| 12 | Diciembre |

---

## Workflow — execute every step in order

### Step 1 — Extract meeting date

Search the user's message for a date matching pattern `DD.MM.YYYY` or `DD/MM/YYYY`.

If found: use it as `meeting_date` (normalize to `DD.MM.YYYY`).
If not found, ask: *"¿Cuál es la fecha de la reunión? (formato: DD.MM.YYYY)"*

Derive from `meeting_date`:
- `meeting_day`, `meeting_month_num` (zero-padded), `meeting_year` (4-digit)
- `meeting_month_name` = Spanish month name for `meeting_month_num`

### Step 2 — Determine reporting period

```
report_month_num = meeting_month_num - 1  (if meeting_month == 1, wrap to 12 and report_year = meeting_year - 1)
report_year = meeting_year
report_period = f"{report_month_num:02d} - {report_year}"   # e.g., "04 - 2026"
report_month_name = Spanish name for report_month_num
```

### Step 3 — Analyze the dashboard image

Read the following from the screenshot the user provided. Look in the **lower KPI row** (second row of metric cards, which shows period-specific stats):

| Variable | Label in image |
|---|---|
| `total_tickets` | "Total Tickets" (in period section, smaller number) |
| `resueltos` | "Tickets Resueltos" count |
| `cerrados` | "Tickets Cerrados" count |
| `abiertos` | "Tickets Abiertos" count |
| `tiempo_horas` | "Tiempo Promedio" number (strip "h" unit) |

**Calculate:**
```python
pct_resolucion = round((resueltos + cerrados) / total_tickets * 100)
dias_promedio  = round(tiempo_horas / 24, 1)
```

State the extracted values clearly before proceeding:
> Extracted: total=50, resueltos=1, cerrados=38, abiertos=11, tiempo=105h → % resolución=78%, días=4.4

### Step 4 — Output the audit email

Print this block to the user:

```
━━━ EMAIL PARA AUDITORÍA ━━━━━━━━━━━━━━━━━━━━━━━━━━
Asunto: Indicadores {report_month_num:02d}-{report_year}

% de Resolución de Tickets: {pct_resolucion}%
Promedio de Días de Resolución: {dias_promedio}

Saludos,
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 5 — Locate reference PPTX

Look for the previous month's main presentation file:
```
RG/{report_year}/{report_month_num}. {report_month_name}/9. RG.*.pptx
```

If it doesn't exist, search `RG/{report_year}/` for the most recent `9. RG.*.pptx`.

Store the result as `reference_pptx`.

### Step 6 — Determine output path

```
output_folder = f"RG/{meeting_year}/{meeting_month_num}. {meeting_month_name}"
output_filename = f"9. RG. {meeting_date} Sistemas {report_month_num:02d} - {report_year}.pptx"
output_path = f"{output_folder}/{output_filename}"
```

Example: `RG/2026/5. Mayo/9. RG. 21.05.2026 Sistemas 04 - 2026.pptx`

### Step 7 — Scan the reference PPTX

```bash
python .claude/skills/rg-presentation/scripts/generate_pptx.py \
  --reference "{reference_pptx}" \
  --scan
```

Read the output carefully. Note the exact text strings for:
- The period label (e.g., "Marzo 2026") — appears on slides 1 and 2
- The written meeting date (e.g., "21 de Abril, 2026") — appears on slide 1
- KPI numbers on slide 2: total tickets, cerrados count, % del total strings, abiertos count, % resolución, tiempo promedio

### Step 8 — Build the replacement map

From scan output, construct --find-replace pairs:

| Old (from scan) | New (from your data) |
|---|---|
| `"{old_period_name} {old_year}"` | `"{report_month_name} {report_year}"` |
| `"21 de {old_month_name}, {old_year}"` | `"{meeting_day} de {meeting_month_name}, {meeting_year}"` |
| `"{old_total}"` | `"{total_tickets}"` |
| `"{old_cerrados}"` | `"{cerrados}"` |
| `"{old_pct_cerrados}% del total"` (cerrados %) | `"{cerrados_pct}% del total"` |
| `"{old_abiertos}"` | `"{abiertos}"` |
| `"{old_pct_abiertos}% del total"` (abiertos %) | `"{abiertos_pct}% del total"` |
| `"{old_pct_resolucion}%"` | `"{pct_resolucion}%"` |
| `"{old_dias} días"` | `"{dias_promedio} días"` |

Where:
- `cerrados_pct = round(cerrados / total_tickets * 100)`
- `abiertos_pct = round(abiertos / total_tickets * 100)`

### Step 9 — Generate the PPTX

```bash
python .claude/skills/rg-presentation/scripts/generate_pptx.py \
  --reference "{reference_pptx}" \
  --output    "{output_path}"    \
  --find-replace "Marzo 2026" "Abril 2026" \
  --find-replace "21 de Abril, 2026" "21 de Mayo, 2026" \
  --find-replace "68" "50" \
  --find-replace "54" "38" \
  ... (all pairs from the replacement map above)
```

If the AFTER output still shows any old value, run again with the corrected --find-replace pair.

### Step 10 — Confirm to user

Report:
- Email is ready to copy above
- PPTX saved to: `{output_path}`
- Which values were updated on slides 1 and 2
- Reminder: *"The remaining slides are copied from last month — add your content when ready."*
