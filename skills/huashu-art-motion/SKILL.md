---
name: huashu-art-motion
description: Directivas de animación y diseño para estilo Huashu Art Motion (画书) — motion graphics de micro-narrativa técnica de alta retención (popularizado en Douyin, Bilibili y reels técnicos virales). Combina elementos estilo boceto/pizarra animada, punteros de ratón interactivos haciendo clic en botones virtuales, barras de progreso segmentadas en bloques (■■■■□□□), micro-stickers con expresiones gestuales, viñetas de diagrama esquemático y retroalimentación visual continua en intervalos de 3 a 4 segundos. Activa esta skill para retención extrema de audiencia, desgloses paso a paso de código y tutoriales interactivos.
---

# HUASHU ART MOTION (画书) — Protocolo de Retención Extrema

El estilo **Huashu Art Motion** optimiza la neuroquímica de la atención (dopamina sostenida) dividiendo conceptos abstractos en micro-eventos visuales que se resuelven cada 2 a 4 segundos.

## 1. Patrones Visuales Distintivos
1. **Puntero de Ratón Interactivo (Virtual Clicker)**:
   - Cursor de flecha estilo píxel o macOS que viaja hacia un botón (`[Ejecutar]`, `[Parchear]`, `[Deploy]`).
   - Al llegar: escala el botón hacia abajo (0.92x click down), genera una onda expansiva de clic (`ripple ring`), y activa el siguiente estado.
2. **Barras de Progreso Segmentadas en Bloques**:
   - En lugar de barras continuas aburridas, usa bloques discretos: `[ ■ ■ ■ ■ ■ □ □ □ ] 62%`.
   - Cada bloque se ilumina con un sonido de `tick` y destello de color neón.
3. **Diagramas Esquemáticos Dibujados**:
   - Nodos rectangulares con esquinas redondeadas y líneas punteadas (`dash array`) que se van trazando como si una mano invisible las dibujara.
   - Flechas vectoriales con pulsación de energía brillante viajando por el cable.
4. **Micro-Cards de Notas Adhesivas / Stickers**:
   - Tarjetas flotantes con una ligera rotación orgánica (-2° a +3°) que simulan post-its digitales o fichas técnicas.

## 2. Paleta de Color Huashu
- **Lienzo / Darkboard**: `#0F172A` (Azul medianoche pizarra)
- **Activo / Aprobado**: `#10B981` (Esmeralda eléctrico)
- **Proceso / Advertencia**: `#F59E0B` (Ámbar brillante)
- **Error / Hacker**: `#EF4444` (Rojo carmesí)
- **Conectores y Nodos**: `#38BDF8` (Azul cielo)

## 3. Implementación de Barra de Bloques Huashu
```python
def draw_huashu_blocks(draw, box, progress, total_blocks=10, fill_color=(16, 185, 129), empty_color=(45, 55, 75)):
    """Renderiza barra de progreso segmentada en bloques discretos."""
    x0, y0, x1, y1 = box
    w = x1 - x0
    h = y1 - y0
    gap = 6
    block_w = (w - (total_blocks - 1) * gap) // total_blocks
    active_count = int(round(progress * total_blocks))
    
    for i in range(total_blocks):
        bx0 = x0 + i * (block_w + gap)
        bx1 = bx0 + block_w
        color = fill_color if i < active_count else empty_color
        draw.rounded_rectangle([bx0, y0, bx1, y1], radius=4, fill=color)
```

## 4. Ritmo y Cadencia
- **Ritmo de eventos**: Cada 3.0 a 4.0 segundos ocurre una acción física visual (clic de ratón, llenado de bloque, aparición de sello de aprobación).
- **Sensación**: Interactiva, lúdica, altamente estructurada y matemáticamente limpia.
