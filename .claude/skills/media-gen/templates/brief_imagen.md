# Brief de imagen — {{ID}}

Eres un worker de generación de imágenes. Trabajas en modo headless: no hagas preguntas, no pidas confirmación.

## Entrega
- Genera UNA imagen y guárdala exactamente en: `{{OUT_DIR}}\{{ID}}.png`
- Formato: PNG. Relación de aspecto: 16:9. Resolución mínima: 1920×1080.
- No incluyas texto, marcas de agua ni logotipos dentro de la imagen.

## Contenido
<!-- Describe la escena en 3–6 líneas: sujeto, entorno, iluminación, estilo, paleta. -->
Sujeto:
Entorno:
Estilo: fotográfico corporativo, limpio, luz natural, sin saturación excesiva.
Paleta: predominio de blancos y grises; acento rojo Caribetrans solo si aplica.

## Restricciones
- Usa tu herramienta nativa de generación de imágenes (Gemini image / Nano Banana). No uses `curl` ni APIs externas.
- Si NO dispones de ninguna herramienta para generar imágenes, no inventes ni dibujes con código:
  responde exactamente `SIN_HERRAMIENTA_DE_MEDIA` y termina.

## Cierre
Cuando el archivo exista en la ruta indicada, imprime en una línea:
`=== MEDIA {{ID}} TERMINADA ===` seguido de la ruta absoluta del archivo.
