# Lineamientos corporativos de presentaciones — Caribetrans

Fuente oficial: `RG/TEMPLATE/1.0.2 GC FORMATO PRESENTACIONES 21.7.2026 V1` (PDF y PPTX editable),
emitido por Presidencia / Auditoría Interna (Gobierno Corporativo). Estos lineamientos aplican a
**todas** las presentaciones de reuniones internas, incluida la RG de Sistemas.

`scripts/build_deck.py` implementa todo lo descrito aquí. No se debe generar una presentación RG
por otro medio (copiar decks viejos, temas de Google Slides, Calibri, fondos oscuros, etc.).

---

## 1. Tipografía

| Elemento | Fuente | Tamaño | Peso | Notas |
|---|---|---|---|---|
| Portada (título) | Helvetica | 48 pt | Negrita | Mayúsculas |
| Títulos de página | Helvetica | 32 pt | Negrita | "El color gris de los títulos debe ser resaltado en negritas" |
| Texto de página | Helvetica | 18 pt | Regular | Viñetas, párrafos, columnas |
| Subtítulos / kicker | Helvetica | 18 pt | Regular | Debajo del título |
| Texto denso (tablas, tarjetas KPI, notas, pies) | Helvetica | 10–14 pt | Regular | Excepción práctica: mínimo 10 pt, nunca menos |
| Valor KPI | Helvetica | 40 pt | Negrita | |

- Helvetica es la fuente obligatoria. Windows la sustituye por Arial en render; el nombre de fuente
  en el archivo debe seguir siendo `Helvetica`.
- Todo el texto va en **gris** (ver 2.1). No se usa negro ni azul oscuro para texto.

## 2. Color

### 2.1 Texto y fondo

| Uso | Nombre en paleta Office | Hex |
|---|---|---|
| Fondo de página | White, Background 1 | `FFFFFF` |
| Texto (todo) | White, Background 1, Darker 50% | `7F7F7F` |
| Barras de encabezado, año 2024 | White, Background 1, Darker 35% | `A6A6A6` |
| Bordes, pistas de progreso | White, Background 1, Darker 15% | `D9D9D9` |
| Relleno suave de tarjetas | White, Background 1, Darker 5% | `F2F2F2` |
| Texto sobre barras grises | White | `FFFFFF` |

### 2.2 Paleta para gráficos e información

Los colores representan categorías y periodos temporales. Se debe respetar en todo gráfico, tabla
o tarjeta que muestre datos operativos.

| Categoría | Nombre en paleta Office | Hex | Rol en `build_deck.py` |
|---|---|---|---|
| Presupuesto | Orange, Accent 2 | `ED7D31` | `budget` |
| Año actual (2026) | Blue, Accent 5 | `5B9BD5` | `current` |
| Año anterior (2025) | Green, Accent 6 | `70AD47` | `prev` |
| Dos años atrás (2024) | White, Background 1, Darker 35% | `A6A6A6` | `prev2` |

Acento adicional observado en el template oficial (flechas de variación, resaltado de periodo):

| Uso | Hex |
|---|---|
| Variación negativa / alerta / resaltado de texto | `C00000` (Dark Red) |
| Variación positiva | `70AD47` |

### 2.3 Estados de proyectos (derivado de la paleta)

| Estado | Hex |
|---|---|
| Completado / Culminado | `70AD47` |
| En progreso / A tiempo | `5B9BD5` |
| Desviado / Crítico | `C00000` |
| Planeado / En espera | `A6A6A6` |

## 3. Layout (16:9, 13.333 × 7.5 in)

| Elemento | Posición |
|---|---|
| Logo Caribetrans | Esquina superior izquierda: x 0.20 in, y 0.36 in, alto 0.78 in (siempre presente) |
| Título | x 1.35 in, y 0.30 in, 32 pt negrita, alineado a la izquierda |
| Subtítulo | Debajo del título, 18 pt regular |
| Área de contenido | y 1.65 in → 6.75 in, márgenes laterales 0.45 in |
| Pie de página | Centro: texto de unidad/periodo, 10 pt. Derecha: número de página, 10 pt |
| Portada | Logo arriba-izquierda; título 48 pt negrita centrado; fecha en negrita debajo |
| Separador de sección | Línea 1 regular + línea 2 negrita, 48 pt centrado; fecha al pie |
| Cierre | "GRACIAS / POR SU ATENCIÓN" centrado en gris |

## 4. Reglas de contenido

- Fondo siempre blanco, sin gradientes, sin imágenes de fondo, sin bloques oscuros.
- Un mensaje por slide. Título en mayúsculas.
- Gráficos nativos de PowerPoint (editables), con etiquetas de datos y leyenda inferior.
- Los datos operativos de la unidad se muestran con la paleta de la sección 2.2.
- Fechas en formato `DD/MM/YYYY`.
