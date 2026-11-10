---
name: claude-drawing
description: Directivas de animación y diseño para estilo Claude Drawing — animación vectorial de trazo progresivo (stroke-by-stroke drawing), esquemas de arquitectura técnica dibujados en tiempo real, diagramas de pizarra digital (whiteboard canvas), gráficos matemáticos y líneas con interpolación suave. Activa esta skill para ilustrar arquitecturas de nube, flujos de datos entre APIs, estructuras de datos y conceptos abstractos mediante dibujo progresivo generado por código.
---

# CLAUDE DRAWING — Protocolo de Animación Vectorial de Trazo Progresivo

El estilo **Claude Drawing** transforma diagramas estáticos en una experiencia visual hipnótica donde cada caja, conector, flecha y etiqueta se dibuja de forma continua en pantalla como si un arquitecto lo trazara en tiempo real.

## 1. Principios de Animación de Trazo
1. **Animación de Longitud de Trazo (Path Tracing)**:
   - Todo vector se interpola desde longitud 0 hasta longitud total: `t_progress = clamp((t - start) / dur, 0.0, 1.0)`.
   - La punta del trazo tiene un sutil punto brillante o marcador (`glow tip`) que guía la mirada del espectador.
2. **Jerarquía Secuencial de Dibujo**:
   - **Paso 1 (0.0s - 1.2s)**: Dibuja los contenedores principales (rectángulos y límites de servicio).
   - **Paso 2 (1.2s - 2.5s)**: Trazado de flechas y cables conectores entre componentes.
   - **Paso 3 (2.5s - 3.8s)**: Aparición de etiquetas tipográficas y métricas con efecto fade-in suave.
3. **Estilo Pizarra de Ingeniería**:
   - Líneas nítidas de 2 a 4 píxeles de grosor.
   - Esquinas suavemente redondeadas (`border-radius: 8px`).
   - Conectores ortogonales (estilo cableado PCB o diagrama eléctrico, no líneas diagonales caóticas).

## 2. Paleta de Color Claude Drawing
- **Lienzo**: `#0B0F17` (Negro plano técnico con cuadrícula milimétrica tenue al 5% de opacidad)
- **Trazo Principal**: `#E2E8F0` (Blanco tiza suave)
- **Flujo de Datos A (Entrada)**: `#38BDF8` (Cian eléctrico)
- **Flujo de Datos B (Procesamiento)**: `#A78BFA` (Lavanda / Púrpura Claude)
- **Resultado / Salida**: `#34D399` (Menta brillante)

## 3. Función de Trazado Progresivo en Python
```python
def draw_progressive_polyline(draw, points, progress, color=(226, 232, 240), width=3):
    """Dibuja una polilínea continua progresivamente según el porcentaje completado."""
    if len(points) < 2 or progress <= 0:
        return
    
    # Calcular longitud total
    lengths = []
    total_len = 0.0
    for i in range(len(points) - 1):
        seg_len = math.hypot(points[i+1][0] - points[i][0], points[i+1][1] - points[i][1])
        lengths.append(seg_len)
        total_len += seg_len
        
    target_dist = total_len * min(1.0, progress)
    accum = 0.0
    
    for i in range(len(points) - 1):
        p0 = points[i]
        p1 = points[i+1]
        seg_len = lengths[i]
        if accum + seg_len <= target_dist:
            draw.line([p0, p1], fill=color, width=width)
            accum += seg_len
        else:
            rem = target_dist - accum
            ratio = rem / seg_len if seg_len > 0 else 0
            cur_end = (int(p0[0] + (p1[0] - p0[0]) * ratio), int(p0[1] + (p1[1] - p0[1]) * ratio))
            draw.line([p0, cur_end], fill=color, width=width)
            # Dibujar cabezal de trazo luminoso
            draw.ellipse([cur_end[0]-4, cur_end[1]-4, cur_end[0]+4, cur_end[1]+4], fill=(255, 255, 255))
            break
```

## 4. Cadencia de Integración
- **Duración ideal**: 3.5 a 4.5 segundos por esquema.
- **Audio Sync**: Sincronizado con sonido suave de tiza o lápiz digital sobre tableta (`pencil_sketch.mp3`).
