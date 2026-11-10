# hyperframes

Motor ligero de **motion graphics** para superponer animaciones sobre videos ya grabados.

Ideal para:
- **Flujos:** flechas animadas que conectan puntos o pasos.
- **Comparaciones:** split-screen con etiquetas "Antes / Después".
- **Acentuaciones:** círculos/resaltados, lower thirds y callouts que apuntan a un detalle.

## Estructura

```
hyperframes/
├── README.md
├── requirements.txt
├── config/
│   └── motions.json          # Define qué gráficos van y en qué segundos
├── scripts/
│   ├── add_motion_graphics.py # Motor principal (MoviePy + Pillow)
│   ├── generate_assets.py     # Genera PNGs con transparencia (opcional, para AE)
│   └── ffmpeg_overlay.sh      # Alternativa rápida con FFmpeg (solo overlays estáticos)
├── assets/                    # Logos, fuentes, PNGs con canal alfa
├── output/                    # Aquí queda el video renderizado
└── sample/                    # Pon aquí tu video de entrada (input.mp4)
```

## Requisitos

Python 3.8+ y:

```bash
pip install -r requirements.txt
```

Dependencias:
- `moviepy==1.0.3`
- `Pillow`
- `numpy`

> Nota: este proyecto renderiza texto con **Pillow**, así que no necesitas instalar ImageMagick.

## Paso a paso

### 1. Coloca tu video
Copia tu video grabado a `sample/input.mp4` (o cambia la ruta en `config/motions.json`).

### 2. Edita los efectos
Abre `config/motions.json` y define cuántos gráficos quieres y en qué segundos aparecen.

Ejemplo de bloque:

```json
{
  "type": "lower_third",
  "start": 2.0,
  "end": 6.0,
  "text": "Esto es un acento",
  "position": ["center", "bottom"],
  "offset_y": 120
}
```

Tipos disponibles:
| type | Para qué sirve |
|------|----------------|
| `lower_third` | Texto animado en la parte inferior (leyendas, acentos). |
| `highlight` | Círculo o rectángulo que resalta una zona (pulsante). |
| `arrow` | Flecha animada de un punto a otro (flujos). |
| `comparison` | Mitad del video oscurecida con etiquetas Antes/Después. |
| `callout` | Texto con burbuja y flecha que apunta a un detalle. |

### 3. Ejecuta
```bash
python scripts/add_motion_graphics.py --config config/motions.json
```

El resultado queda en `output/resultado.mp4`.

### 4. (Opcional) Generar assets para After Effects
Si prefieres diseñar en After Effects y compponer después, usa:

```bash
python scripts/generate_assets.py
```

Esto crea PNGs con canal alfa (flechas, círculos, lower thirds) en `assets/`.

## Alternativa rápida con FFmpeg

Si solo necesitas poner una imagen transparente (logo, marca de agua) sin animación frame a frame:

```bash
bash scripts/ffmpeg_overlay.sh sample/input.mp4 assets/logo.png output/resultado.mp4
```

## Tips

- Usa **canal alfa** (transparencia) en cualquier PNG que superpongas; así no tapa el video.
- Los tiempos (`start` / `end`) van en **segundos**.
- Si el video es vertical (Reels/TikTok), ajusta `resolution` a `[1080, 1920]` en el JSON.
- No pongas más de 2-3 efectos simultáneos; el motion graphics debe apoyar, no distraer.
