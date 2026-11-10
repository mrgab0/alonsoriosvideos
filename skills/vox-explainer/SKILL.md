---
name: vox-explainer
description: Directivas de animación y diseño para estilo Vox Explainer — motion graphics estilo periodismo documental contemporáneo (Vox, Johnny Harris, PolyMatter). Incluye texturas de papel periódico/kraft, resaltador de texto animado (highlighter marker amarillo/cian), fotos estilo collage con bordes rasgados, líneas topográficas y mapas sutiles, tipografía editorial refinada (serif clásico + monospace técnico) y paneos de cámara ortogonales suaves. Activa esta skill para explicaciones técnicas profundas, contexto histórico de tecnología, desgloses de vulnerabilidades y lecciones educativas de alta credibilidad.
---

# VOX EXPLAINER — Protocolo de Diseño Periodístico y Educativo

El estilo **Vox Explainer** prioriza claridad intelectual, elegancia táctil y ritmo narrativo pausado pero visualmente magnético mediante metáforas físicas (papel, cinta adhesiva, resaltadores).

## 1. Elementos Visuales Esenciales
1. **Resaltador Fluorescente Animado (Highlighter Reveal)**:
   - Trazo de marcador que se desliza de izquierda a derecha sobre el texto clave (duración 0.35s).
   - Modo de fusión multiply o semitransparente (`rgba(255, 230, 0, 0.45)` o cian `#00F2FE`), bordes ligeramente irregulares con ángulo biselado (chisel tip).
2. **Fotografía y Recortes de Collage (Paper Cutout)**:
   - Imágenes con borde blanco irregular (2-4px) y sombra proyectada difusa (`drop shadow` offset y=12px, blur 25px).
   - Sutil animación de stop-motion o frame-rate reducido (12fps simulado) para acentuar el aspecto táctil analógico.
3. **Textura de Grano y Papel Orgánico**:
   - Superposición sutil de ruido perlin / grano de película (3-5% de opacidad) que elimina la esterilidad digital.
4. **Tipografía Híbrida Editorial**:
   - **Títulos**: Serif moderno con autoridad (Playfair, Georgia, o Liberation Serif).
   - **Subtítulos y Citas**: Sans-serif neutral limpio (Inter, Helvetica, Liberation Sans).
   - **Datos Técnicos y Métricas**: Monospace estricto (JetBrains Mono, Courier).

## 2. Paleta de Color Vox
- **Fondo Táctil**: `#121316` (Gris grafito profundo con subtono cálido) o `#F4F0E8` (Papel crema antiguo en modo claro)
- **Resaltador Amarillo**: `#FFE500` (Canary Highlighter)
- **Resaltador Cian**: `#00F0FF` (Cyan Aqua)
- **Tinta / Tipografía**: `#FFFFFF` y `#E2E2E6`
- **Acento Crítico**: `#FF3B30` (Sello de confidencial o alerta)

## 3. Lógica de Marcador Resaltador en Python/MoviePy
```python
def draw_vox_highlighter(draw, text_bbox, rel_t, dur=0.4, color=(255, 230, 0, 115)):
    """Trazo de resaltador que se descubre progresivamente sobre el texto."""
    x0, y0, x1, y1 = text_bbox
    progress = min(1.0, rel_t / dur)
    # Easing cuadrático suave (aceleración y desaceleración orgánica)
    ease = 1.0 - (1.0 - progress) ** 2
    cur_x1 = x0 + int((x1 - x0) * ease)
    # Rectángulo biselado con ligeras irregularidades
    draw.rectangle([x0, y0 + 6, cur_x1, y1 + 2], fill=color)
```

## 4. Cadencia y Ritmo
- **Duración por escena**: 3.5 a 5.0 segundos.
- **Movimiento de cámara**: Slow pan continuo (zoom ultra lento de 1.0x a 1.04x).
- **SFX característico**: Sonido de papel deslizándose (`paper_slide.mp3`), clic de máquina de escribir y trazo de plumón sobre papel (`marker_stroke.mp3`).
