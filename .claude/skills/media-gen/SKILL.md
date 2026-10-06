---
name: media-gen
description: |
  Genera imágenes o videos para presentaciones, contenido social o documentación delegando la
  generación a un sub-agente Gemini (Antigravity CLI `agy`, la misma técnica de despacho headless
  usada en C:\TEMP\pricing y en el módulo PMO de C:\TEMP\intranet), con fallback al MCP de Higgsfield.

  TRIGGER cuando el usuario diga:
  - "genera una imagen de…" / "necesito una imagen para el slide…"
  - "genera un video de…" / "hazme un clip de…"
  - "ilustración para la presentación" / "imagen de portada" / "banner"
  - "usa AGY para generar…" / "despacha a Gemini la imagen…"

  SKIP cuando:
  - El usuario pide capturas de pantalla reales de un sistema (usar Chrome / Read de PNG existentes).
  - El usuario pide gráficos de datos (usar el skill dataviz o el tipo `chart` de rg-presentation).
---

# media-gen — Imágenes y videos con sub-agente AGY

Base del skill: `.claude/skills/media-gen/`. Ejecuta los pasos en orden.

## Cómo funciona la técnica (igual que pricing e intranet/PMO)

El líder (esta sesión de Claude Code) **no genera el media**: redacta un brief Markdown, lo despacha a un
worker Gemini con `agy -p` en modo headless, y valida el resultado por centinela + archivo en disco.

```
brief (media/briefs/<id>.md)  →  scripts/despachar_media.ps1 <id>  →  media/out/<id>/<id>.png|mp4
                                       agy -p --new-project --dangerously-skip-permissions
```

Reglas heredadas de `C:\TEMP\pricing\plan\scripts\agentes\despachar.ps1`:
- `--new-project` es obligatorio (sin él agy escribe en el proyecto registrado, no en el cwd).
- `--dangerously-skip-permissions` es obligatorio en headless: sin él agy auto-deniega toda herramienta.
- Las comillas dobles del brief se escapan como `\"` (regla `CommandLineToArgvW`).
- Cada brief es independiente y escribe **un solo archivo**; el worker imprime `=== MEDIA <ID> TERMINADA ===`.
- Modelo por defecto `gemini-3.8-flash-high` (`$env:AGY_MODEL`), timeout 15 min (`$env:AGY_TIMEOUT`).

## Workflow

### Paso 1 — Definir el pedido

Extrae del mensaje: tipo (`img` | `vid`), propósito (slide, post, portada), sujeto, estilo, relación de aspecto
y carpeta destino final. Si falta el sujeto, pregunta. Todo lo demás toma un default:
16:9, PNG 1920×1080 para imagen; 6–8 s MP4 16:9 sin audio para video; estilo corporativo limpio.

Asigna un ID en kebab-case con prefijo de tipo: `img-camion-almacen`, `vid-portada-rg-septiembre`.

### Paso 2 — Escribir el brief

Copia `templates/brief_imagen.md` o `templates/brief_video.md` a `media/briefs/<id>.md` (relativo al proyecto,
o a `$env:MEDIA_ROOT`). Rellena la sección **Contenido** con 3–6 líneas concretas. No toques la sección
**Restricciones** ni **Cierre**: son las que permiten al script detectar éxito o falta de herramienta.
Los marcadores `{{ID}}` y `{{OUT_DIR}}` los sustituye el script.

### Paso 3 — Despachar al worker AGY

```powershell
.\.claude\skills\media-gen\scripts\despachar_media.ps1 <id>
```

Códigos de salida:
| Código | Significado | Acción |
|---|---|---|
| 0 | Centinela + archivo generado | Ir al Paso 5 |
| 2 | Sin centinela o sin archivo | Leer `media/out/logs/<id>.log`, ajustar brief, reintentar una vez |
| 3 | Worker respondió `SIN_HERRAMIENTA_DE_MEDIA` | Ir al Paso 4 (fallback) |

Primera vez en una máquina: correr `despachar_media.ps1 -Prueba` (humo) y `-Capacidades` (qué herramientas de
imagen/video expone agy con el modelo elegido). Guarda el resultado de `-Capacidades` en `media/CAPACIDADES.md`
para no repetirlo.

Nota de permisos: en sesiones de Claude Code en modo automático el clasificador puede bloquear el lanzamiento de
`agy --dangerously-skip-permissions`. En ese caso indica al usuario el comando exacto para que lo ejecute con el
prefijo `!` en el prompt, y continúa desde el Paso 5 cuando el archivo exista.

### Paso 4 — Fallback: MCP de Higgsfield

Si el worker no tiene herramienta de media (o agy no está disponible), usa las herramientas MCP
`mcp__claude_ai_higgsfield__generate_image` / `generate_video` (cargar con ToolSearch). Usa el mismo texto de la
sección **Contenido** del brief como prompt; para varias piezas usa `generate_image_batch` / `generate_video_batch`
con `jobs_wait`. Descarga el resultado a `media/out/<id>/<id>.png|mp4` para que el resto del flujo sea idéntico.

### Paso 5 — Verificar e integrar

1. Abre el archivo con `Read` (imagen) o revisa duración/tamaño con `ffprobe` (video) y confirma que cumple el brief:
   sin texto, sin logos, aspecto correcto. Si no cumple, ajusta el brief y repite el Paso 3 (máx. 2 iteraciones).
2. Copia el archivo a la carpeta destino del proyecto (p. ej. `RG/2026/9. Septiembre/img/`) con nombre descriptivo.
3. Si es para un deck RG, añade el slide (`image` o `bullets` con `image`) en `deck.json` y reconstruye con
   `rg-presentation`.

## Convenciones

- `media/briefs/`, `media/out/` y `media/CAPACIDADES.md` viven en el proyecto que pide el media; `media/out/`
  va en `.gitignore` (solo se versiona el archivo final copiado a su destino).
- Nunca pongas credenciales, datos personales ni capturas reales de clientes en un brief: el worker es un modelo externo.
- Un brief = un archivo. Para series (p. ej. 4 iconos) crea 4 briefs y despáchalos en paralelo con `Start-Job`.
