---
name: bang-motion
description: Directivas de animación y diseño para estilo Bang Motion — motion graphics de alto impacto cinético, inspirados en anime de acción (Studio Trigger), cortes rápidos, líneas de velocidad (speed lines), temblor de cámara (screen shake), destellos de impacto (impact flashes) y tipografía hipercinética. Activa esta skill para hooks virales, momentos de máxima tensión técnica, alertas de seguridad críticas y revelaciones explosivas en videos cortos (Reels/TikTok/Shorts).
---

# BANG MOTION — Protocolo de Animación Hipercinética

El estilo **Bang Motion** prioriza impacto visual instantáneo, energía cinética pura y retención visceral del espectador en los primeros 1-3 segundos o en momentos clímax.

## 1. Principios Visuales Clave
1. **Frames de Impacto (Inverted Flash)**:
   - 1 a 2 fotogramas monocromáticos o invertidos (blanco/negro absoluto o neón sólido) justo en el impacto sonoro o visual.
   - Crea una sensación física de golpe en la retina.
2. **Líneas de Velocidad Radiales (Anime Speed Lines)**:
   - Rayos dinámicos que convergen hacia el punto focal (el rostro o el texto clave).
   - Generación paramétrica con ángulos pseudoaleatorios y opacidad parpadeante (strobe 24fps).
3. **Temblor de Cámara Decrescente (Exponential Screen Shake)**:
   - Fórmula: `offset_x = sin(t * 50) * amplitude * exp(-k * t)`
   - Amplitud inicial: 20-35px, disipación en 0.25 - 0.35s.
4. **Tipografía PUNCH-IN**:
   - Escala de entrada: Empieza en 2.5x con blur direccional y cae a 1.0x con rebote elástico (`elastic bounce out`).
   - Colores: Blanco puro `#FFFFFF` con borde negro grueso (stroke 6-8px) y sombra neón dura (magenta/cian/naranja).
   - RGB Split / Aberración Cromática en los bordes durante los primeros 4 frames de la aparición.

## 2. Paleta de Color Bang
- **Fondo Impacto**: `#0A0714` (Negro abisal púrpura)
- **Acento Primario**: `#FF0055` (Crimson Neon)
- **Acento Eléctrico**: `#FFE600` (Volt Yellow)
- **Flash / Chispas**: `#00F0FF` (Cyan Blast) y `#FFFFFF` (Strobe Puro)

## 3. Fórmulas Matemáticas de Movimiento
```python
import math

def bang_elastic_scale(rel_t, dur=0.4):
    """Rebote hipercinético de entrada rápida (overshoot snap)."""
    if rel_t <= 0: return 2.2
    p = min(1.0, rel_t / dur)
    # Easing elástico tenso
    return 1.0 + 1.2 * math.exp(-8.0 * p) * math.cos(12.0 * p)

def screen_shake(rel_t, max_amp=25, decay=9.0):
    """Vibración sísmica de pantalla post-impacto."""
    amp = max_amp * math.exp(-decay * rel_t)
    dx = int(math.sin(rel_t * 62.0) * amp)
    dy = int(math.cos(rel_t * 47.0) * amp)
    return dx, dy
```

## 4. Estructura de Cadencia Rápida
- **Duración máxima por elemento**: 1.5 a 3.5 segundos.
- **Transición**: Smash cut o wipe direccional acelerado.
- **Audio Sync**: Golpes sincronizados con transitorios de audio (kick, snare, bass drop o riser cortado en seco).
