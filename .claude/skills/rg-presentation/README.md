# rg-presentation skill

Generates the monthly IT department KPI email and PowerPoint for CaribeTrans board meetings.

## Setup

```bash
pip install python-pptx
```

## How to use

Say: **"Let's work on my RG presentation, meeting is DD.MM.YYYY"** and attach the dashboard screenshot.

Claude will:
1. Read KPI numbers from your screenshot
2. Print the ready-to-copy audit email
3. Create the PPTX in the correct `RG/{year}/{month}/` folder

## Output locations

- **Email**: printed in conversation (copy-paste to send)
- **PPTX**: `RG/{meeting_year}/{m}. {Month}/9. RG. {DD.MM.YYYY} Sistemas {mm} - {yyyy}.pptx`

## PPTX file naming

| Part | Example | Meaning |
|---|---|---|
| `9. RG.` | fixed | Meeting series prefix |
| `21.05.2026` | meeting date | Date you provide in trigger phrase |
| `Sistemas` | fixed | Your department |
| `04 - 2026` | report period | Last month (April if meeting is in May) |

## Script reference

```bash
python .claude/skills/rg-presentation/scripts/generate_pptx.py \
  --reference "RG/.../last_month.pptx" \
  --output    "RG/.../new_month.pptx"  \
  --new-date  "21.05.2026"             \
  --new-period "04 - 2026"             \
  --resueltos 1 --cerrados 38 --abiertos 11 --total 50 \
  --tiempo-horas 105 --pct-resolucion 78 --dias-promedio 4.4 \
  [--find-replace "OLD TEXT" "NEW TEXT"]  # repeat for manual overrides
```
