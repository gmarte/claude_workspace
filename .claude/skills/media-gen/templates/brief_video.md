# Brief de video — {{ID}}

Eres un worker de generación de video. Trabajas en modo headless: no hagas preguntas, no pidas confirmación.

## Entrega
- Genera UN video y guárdalo exactamente en: `{{OUT_DIR}}\{{ID}}.mp4`
- Duración: 6–8 s. Relación de aspecto: 16:9. Sin audio salvo que se indique.
- No incluyas texto, subtítulos ni logotipos dentro del video.

## Contenido
<!-- Describe la toma: sujeto, acción, movimiento de cámara, entorno, estilo. -->
Sujeto:
Acción:
Cámara: plano fijo o travelling lento.
Estilo: corporativo, realista, iluminación natural.

## Restricciones
- Usa tu herramienta nativa de generación de video (Veo). No uses `curl` ni APIs externas.
- Si NO dispones de ninguna herramienta para generar video, no inventes ni compongas frames con código:
  responde exactamente `SIN_HERRAMIENTA_DE_MEDIA` y termina.

## Cierre
Cuando el archivo exista en la ruta indicada, imprime en una línea:
`=== MEDIA {{ID}} TERMINADA ===` seguido de la ruta absoluta del archivo.
