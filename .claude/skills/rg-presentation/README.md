# rg-presentation skill

Generates the monthly IT department KPI email and the PowerPoint deck for the CaribeTrans
Reunión Gerencial, following the corporate presentation standard published by Gobierno Corporativo
(`RG/TEMPLATE/1.0.2 GC FORMATO PRESENTACIONES 21.7.2026 V1`).

## Setup

```bash
pip install -r .claude/skills/rg-presentation/requirements.txt   # python-pptx, Pillow
```

PNG previews (`--render`) use the locally installed PowerPoint through COM — no extra install.

## How to use

Say: **"Let's work on my RG presentation, meeting is DD.MM.YYYY"** and attach the dashboard screenshot
(plus any project screenshots and this month's project updates).

Claude will:
1. Read KPI numbers from the screenshot and print the ready-to-copy email
2. Carry over last month's project narrative (`scan_pptx.py`) and ask for updates
3. Write `deck.json` in the meeting folder and build the PPTX with `build_deck.py`
4. Render PNG previews, inspect them and fix any overflow before handing over

## Files

```
SKILL.md                        workflow Claude follows
references/brand_guidelines.md  corporate standard: fonts, sizes, colors, layout (source: RG/TEMPLATE)
templates/deck_example.json     full example of every slide type — start here
scripts/build_deck.py           JSON → PPTX, enforces the standard
scripts/render_preview.ps1      PPTX → PNG per slide (PowerPoint COM)
scripts/scan_pptx.py            dump text/charts of an existing deck
assets/logo_caribetrans.png     logo extracted from the corporate template
```

## Slide types

| type | Use |
|---|---|
| `cover` | Portada: unidad, "Reporte Gerencial • Mes Año", fecha |
| `kpi` | Tarjetas KPI + gráfico de barras + lectura ejecutiva |
| `section` | Separador de sección |
| `table` | Tabla con barra de avance y chip de estado (portafolio) |
| `bullets` | Lead + viñetas, badge de estado, imagen opcional, bloque "Impacto" |
| `two_column` | "Puntos Bajos / Puntos Altos" (formato Noticias del mes) |
| `chart` | Gráfico comparativo Presupuesto / 2026 / 2025 / 2024 con callouts |
| `image` | Captura a ancho completo con caption y viñetas |
| `closing` | Gracias / Por su atención |

## Script reference

```bash
# build + preview
python .claude/skills/rg-presentation/scripts/build_deck.py --spec "RG/2026/9. Septiembre/deck.json" \
  --output "RG/2026/9. Septiembre/9. RG. 15.09.2026 Sistemas 08 - 2026.pptx" --render

# dump last month's deck
python .claude/skills/rg-presentation/scripts/scan_pptx.py "RG/2026/8. Agosto/9. RG. 25.08.2026 Sistemas 07 - 2026.pptx"

# render an existing pptx
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/skills/rg-presentation/scripts/render_preview.ps1 \
  -Pptx "deck.pptx" -OutDir "C:\TEMP\preview"
```

## Output locations

- **Email**: printed in conversation
- **deck.json**: `RG/{meeting_year}/{m}. {Month}/deck.json`
- **PPTX**: `RG/{meeting_year}/{m}. {Month}/9. RG. {DD.MM.YYYY} Sistemas {mm} - {yyyy}.pptx`
