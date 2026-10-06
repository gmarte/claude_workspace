# media-gen

Skill de Claude Code para generar imágenes y videos delegando la generación a un sub-agente Gemini
(Antigravity CLI `agy`) con la misma técnica de despacho headless usada en `C:\TEMP\pricing` y en el
módulo PMO de `C:\TEMP\intranet`. Fallback: MCP de Higgsfield.

```
SKILL.md                      instrucciones para Claude (workflow de 5 pasos)
scripts/despachar_media.ps1   despacha un brief a agy y valida centinela + archivo
templates/brief_imagen.md     plantilla de brief para imagen (PNG 16:9)
templates/brief_video.md      plantilla de brief para video (MP4 6–8 s)
```

Uso rápido desde PowerShell:

```powershell
.\.claude\skills\media-gen\scripts\despachar_media.ps1 -Prueba         # humo
.\.claude\skills\media-gen\scripts\despachar_media.ps1 -Capacidades    # qué herramientas de media tiene agy
.\.claude\skills\media-gen\scripts\despachar_media.ps1 img-mi-imagen   # despacha media\briefs\img-mi-imagen.md
```

Variables opcionales: `MEDIA_ROOT`, `MEDIA_BRIEFS`, `MEDIA_OUT`, `AGY_MODEL` (default `gemini-3.8-flash-high`),
`AGY_TIMEOUT` (default `15m`).
