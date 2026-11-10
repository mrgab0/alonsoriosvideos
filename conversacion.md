# conversacion.md — Contexto del proyecto hyperframes

Este archivo resume todo lo conversado y construido para que `antigravity cli` (o cualquier agente futuro) tenga el contexto completo del proyecto sin necesidad de releer el historial.

---

## 1. Objetivo del usuario

El usuario quiere agregar **motion graphics automáticos** a videos ya grabados, sincronizados con **palabras habladas** detectadas por voz (Speech-to-Text), sin tener que calcular tiempos a mano.

Flujo deseado (coloquial):
> "Cuando diga 'casa', coloca un icono de casa en ese momento del video."

Detalles del flujo:
1. Video grabado ya existe (`sample/input.mp4` o en Google Drive).
2. Se detecta una palabra clave hablada (ej. "storm", "casa", "trueno").
3. Se genera automáticamente `config/motions.json` con los timestamps exactos (`start`/`end`) de cada ocurrencia.
4. Se renderizan gráficos sobre esos momentos (flechas, círculos, lower thirds, callouts, comparaciones, etc.).
5. El resultado queda en `output/resultado.mp4` con el audio original conservado.

Requisitos de infraestructura:
- Ejecutar en **Google Colab** (GPU gratuita Tesla T4) porque su PC local tiene apenas 4 GB RAM y solo ~200 MB libres.
- Almacenamiento en **Google Drive** (subida lenta de internet, solo una vez).
- Exponer una **API REST** para consumir desde su terminal local con `curl`.
- Usar **faster-whisper** en CUDA (`int8`, modelo `tiny` o `base`) en la GTX 1060 3 GB si corre local.

---

## 2. Estado actual de la carpeta `hyperframes/`

```
C:/Users/gabo/Documents/codigo/hyperframes/
├── conversacion.md              <- este archivo
├── README.md                    <- documentacion general del motor
├── requirements.txt             <- dependencias Python (moviepy, Pillow, numpy)
├── config/
│   └── motions.json             <- JSON de efectos generado automaticamente
├── sample/
│   └── input.mp4                <- video de prueba (8s, vertical 720x1280, 24fps, con audio)
├── output/
│   └── resultado.mp4            <- video renderizado con graficos (ya generado una vez)
├── assets/                      <- PNGs con canal alfa (opcional, para After Effects)
└── scripts/
    ├── add_motion_graphics.py   <- motor principal: lee motions.json y renderiza overlays sobre el video
    ├── whisper_to_motions.py    <- detecta palabra clave con faster-whisper y genera motions.json
    ├── generate_assets.py       <- genera PNGs con transparencia (para AE/Premiere)
    ├── ffmpeg_overlay.sh        <- overlay estatico rapido con ffmpeg
    ├── install_deps.bat         <- instalador de dependencias (Windows)
    ├── run_pipeline.bat         <- pipeline todo-en-uno (Windows)
    ├── api_hyperframes.py       <- API REST (FastAPI) para consumo remoto desde terminal local
    └── hyperframes_colab.ipynb  <- NOTEBOOK para Google Colab (todo integrado: Drive, Whisper, render)
```

---

## 3. Componentes creados

### 3.1 `add_motion_graphics.py`
Motor de composición. Lee `config/motions.json` y superpone efectos frame-a-frame sobre el video base usando MoviePy + Pillow (sin depender de ImageMagick).

Efectos soportados:
- `lower_third`: texto animado en la parte inferior.
- `highlight`: círculo o rectángulo pulsante sobre una zona.
- `arrow`: flecha animada de un punto a otro (flujo).
- `comparison`: split-screen con etiquetas "ANTES / DESPUÉS".
- `callout`: texto con burbuja y flecha que apunta a un detalle.

Parche especial: convierte frames a RGBA internamente para permitir overlays con transparencia, luego vuelve a RGB antes de escribir el MP4.

### 3.2 `whisper_to_motions.py`
Detector de palabras clave. Usa `faster-whisper` con `word_timestamps=True` para obtener inicio y fin exactos de cada palabra. Filtra por palabra(s) clave y genera `config/motions.json`.

Requisitos críticos para su PC local:
- `device="cuda"`, `compute_type="int8"` (vital para GTX 1060 3 GB).
- `beam_size=1`, `vad_filter=True` (ahorro de VRAM/RAM).
- `nvidia-cublas-cu12` y `nvidia-cuda-runtime-cu12` instalados vía pip.
- RAM mínima recomendada: ≥1 GB libre (faster-whisper falla con `mkl_malloc` si hay poca RAM).

### 3.3 `api_hyperframes.py`
API REST con FastAPI. Endpoints:
- `GET /estado` — salud del servicio.
- `POST /procesar` — recibe JSON con `video_filename`, `keyword` (o lista), `language`, `model_size`, `effect`, `duration`; devuelve el video renderizado en Drive.

Levanta en Colab y se expone con `pyngrok` para acceso externo.

### 3.4 `hyperframes_colab.ipynb`
Notebook listo para Google Colab. Contiene:
- Montaje de Google Drive.
- Instalación de dependencias.
- Creación automática de `add_motion_graphics.py`.
- Función `pipeline_hyperframes()` que une transcripción + render.
- Celda de ejecución con parámetros configurables (`VIDEO_FILENAME`, `KEYWORD`, `LANGUAGE`, `MODEL`, `EFFECT`, `DURATION`).
- Guardado directo en Drive: `MiDrive/hyperframes/input/` → `MiDrive/hyperframes/output/`.

---

## 4. Flujo de uso completo (usuario)

### Opción A: Google Colab (recomendada para su PC con poca RAM)
1. Subir `hyperframes_colab.ipynb` a Colab.
2. Runtime → Cambiar tipo de runtime → **GPU (T4)**.
3. Subir video una sola vez a Drive: `MiDrive/hyperframes/input/input.mp4`.
4. Ejecutar celdas en orden.
5. Cambiar `KEYWORD` por la palabra deseada (`casa`, `storm`, etc.).
6. Resultado en Drive: `MiDrive/hyperframes/output/resultado.mp4`.

### Opción B: API desde terminal local
1. En Colab, levantar `api_hyperframes.py` y exponer con `ngrok`.
2. Desde terminal local:
   ```bash
   curl -X POST https://<ngrok-url>/procesar \
     -H "Content-Type: application/json" \
     -d '{"video_filename":"input.mp4","keyword":"casa","language":"es","model_size":"tiny","effect":"highlight","duration":1.5}'
   ```

### Opción C: Local (si libera RAM e instala cuBLAS)
```bash
"C:\Program Files\Python314\python.exe" scripts/whisper_to_motions.py \
  --video sample/input.mp4 \
  --keyword casa \
  --model tiny \
  --language es \
  --effect highlight \
  --duration 1.5 \
  --render
```

---

## 5. Múltiples palabras con efectos distintos (pendiente de implementar completa)

Actualmente `build_motions` aplica un mismo efecto a todas las palabras. El usuario quiere:

```json
[
  {"keyword": "casa",      "effect": "highlight", "bg_color": "#FF0000", "duration": 1.5},
  {"keyword": "storm",     "effect": "arrow",     "color": "#0000FF",   "duration": 2.0},
  {"keyword": "trueno",    "effect": "callout",   "bg_color": "#FFA500", "duration": 1.2}
]
```

Esto requiere modificar `build_motions(words, keyword_configs)` para aceptar una lista de configuraciones por palabra, y actualizar el modelo `ProcesarRequest` de la API para aceptar `keywords` como lista en lugar de string único.

---

## 6. Problemas encontrados y soluciones aplicadas

| Problema | Solución |
|----------|----------|
| Python 3.14 incompatible con numpy/moviepy | Se instaló `numpy==1.26.4` (aún con warnings de MINGW-W64, pero funciona). |
| `PIL.Image.ANTIALIAS` no existe en Pillow nueva | Se removió `resolution` del config (video ya es 720x1280) para evitar `resize`. |
| MoviePy no mezcla RGB (video) con RGBA (overlays) | Se parcheó `add_motion_graphics.py` para composición manual frame-a-frame con canal alfa. |
| `faster-whisper` fallaba con PyAV `metadata_errors` | Se reemplazó lectura de audio por `wave` + array numpy directo al modelo. |
| `cublas64_12.dll` no encontrada | Se instaló `nvidia-cublas-cu12` y `nvidia-cuda-runtime-cu12` vía pip; se agregó ruta al PATH dentro del script. |
| `mkl_malloc: failed to allocate memory` (RAM insuficiente) | Solución: usar Google Colab (GPU T4 + RAM suficiente). Local requiere liberar RAM (≥1 GB libre). |
| Drivers de NVIDIA | **Nunca se tocaron.** cuBLAS se instala solo en `site-packages` de Python, no modifica el driver del sistema. |

---

## 7. Próximos pasos sugeridos

1. **Finalizar multi-palabra con efectos distintos** en `whisper_to_motions.py` y `api_hyperframes.py`.
2. **Probar el notebook en Colab** con el video de Drive y validar el render completo.
3. **Exponer la API con ngrok** y probar `curl` desde terminal local.
4. **Agregar más efectos**: barras de progreso, títulos animados, transiciones entre escenas.
5. **Crear script `.bat`/.sh** para llamar a la API sin escribir `curl` manualmente.

---

## 8. Comandos clave para referencia rápida

```bash
# Local: detectar palabra y renderizar
python scripts/whisper_to_motions.py --video sample/input.mp4 --keyword casa --model tiny --language es --effect highlight --duration 1.5 --render

# Local: solo generar JSON (sin render)
python scripts/whisper_to_motions.py --video sample/input.mp4 --keyword storm --model tiny --language en

# Colab: levantar API
!python /content/hyperframes/scripts/api_hyperframes.py &

# Terminal local: consumir API
curl -X POST https://<ngrok>/procesar -H "Content-Type: application/json" -d '{"video_filename":"input.mp4","keyword":"casa","language":"es"}'
```

---

**Fin del contexto.** Todo está listo para continuar en Colab o en local una vez que se libere RAM e instalen `nvidia-cublas-cu12`.