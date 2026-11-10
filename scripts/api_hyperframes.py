"""
api_hyperframes.py
==================
API REST para consumir hyperframes desde cualquier terminal (curl, Postman, etc.)

Levanta en Google Colab y recibe peticiones para detectar una palabra hablada
y renderizar los gráficos automáticamente.

Endpoints:
  POST /procesar   -> recibe parámetros y devuelve el video con gráficos
  GET  /estado     -> salud de la API

Uso en Colab:
    python scripts/api_hyperframes.py

Luego expón con ngrok para llamarla desde tu PC local:
    !pip install pyngrok
    from pyngrok import ngrok
    url = ngrok.connect(8000)
    print("URL pública:", url)
"""

import os, sys, json, gc, tempfile, wave, subprocess
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import numpy as np
import imageio_ffmpeg
from faster_whisper import WhisperModel

# Rutas (ajusta si usas Drive montado en otro lugar)
DRIVE_ROOT = "/content/drive/MyDrive/hyperframes"
INPUT_DIR = os.path.join(DRIVE_ROOT, "input")
OUTPUT_DIR = os.path.join(DRIVE_ROOT, "output")
CONFIG_DIR = os.path.join(DRIVE_ROOT, "config")
SCRIPTS_DIR = "/content/hyperframes/scripts"

for d in [INPUT_DIR, OUTPUT_DIR, CONFIG_DIR, SCRIPTS_DIR]:
    os.makedirs(d, exist_ok=True)

sys.path.insert(0, SCRIPTS_DIR)

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

# ============================ MODELOS ============================

class ProcesarRequest(BaseModel):
    video_filename: str = "input.mp4"
    keyword: str = "casa"
    model_size: str = "tiny"
    language: str = "es"
    effect: str = "highlight"
    duration: float = 1.5

class ProcesarResponse(BaseModel):
    ok: bool
    keyword: str
    coincidencias: int
    video_entrada: str
    video_salida: str | None
    config: str | None
    mensaje: str

# ============================ FUNCIONES ============================

def extract_audio(video_path, wav_path):
    cmd = [FFMPEG_EXE, "-y", "-i", video_path,
           "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def load_wav_as_array(wav_path):
    with wave.open(wav_path, "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    dtype = np.int16 if sample_width == 2 else np.int32
    audio = np.frombuffer(raw, dtype=dtype)
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels)[:, 0]
    return audio.astype(np.float32) / 32768.0

def transcribe_words(audio_path, model_size="tiny", language=None):
    model = WhisperModel(model_size, device="cuda", compute_type="int8")
    audio_array = load_wav_as_array(audio_path)
    segments, info = model.transcribe(
        audio_array, word_timestamps=True, language=language,
        vad_filter=True, beam_size=1,
    )
    words = []
    for segment in segments:
        for w in segment.words:
            words.append({
                "word": w.word,
                "start": round(float(w.start), 3),
                "end": round(float(w.end), 3),
            })
    del model
    gc.collect()
    try:
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass
    return words, info

def build_motions(words, keywords, effect_type="highlight", duration=1.5):
    effects = []
    for w in words:
        palabra = w["word"].strip().lower()
        if any(k.lower() in palabra for k in keywords):
            effects.append({
                "type": effect_type,
                "start": w["start"],
                "end": round(w["start"] + duration, 3),
                "text": w["word"],
                "position": ["center", "bottom"],
                "offset_y": 140,
                "fontsize": 40,
                "color": "#FFFFFF",
                "bg_color": "#FF0000",
                "bg_opacity": 0.85,
                "animation": "pulse",
            })
    return effects

# Importar renderizador del motor existente
from add_motion_graphics import render_video

# ============================ APP ============================

app = FastAPI(title="HyperFrames API", version="1.0")

@app.get("/estado")
def estado():
    return {"ok": True, "servicio": "hyperframes", "gpu": "cuda"}

@app.post("/procesar", response_model=ProcesarResponse)
def procesar(req: ProcesarRequest):
    video_path = os.path.join(INPUT_DIR, req.video_filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"No se encontró: {video_path}")

    output_path = os.path.join(OUTPUT_DIR, f"resultado_{req.keyword}.mp4")
    tmp_fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(tmp_fd)

    try:
        extract_audio(video_path, wav_path)
        words, info = transcribe_words(wav_path, req.model_size, req.language)
        effects = build_motions(words, [req.keyword], req.effect, req.duration)

        if not effects:
            return ProcesarResponse(
                ok=False, keyword=req.keyword, coincidencias=0,
                video_entrada=video_path, video_salida=None,
                config=None, mensaje="No se encontró la palabra clave en el video."
            )

        config = {
            "input": video_path,
            "output": output_path,
            "fps": 24,
            "effects": effects,
        }
        os.makedirs(CONFIG_DIR, exist_ok=True)
        config_path = os.path.join(CONFIG_DIR, f"motions_{req.keyword}.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        render_video(video_path, output_path, effects, fps=24)

        return ProcesarResponse(
            ok=True, keyword=req.keyword, coincidencias=len(effects),
            video_entrada=video_path, video_salida=output_path,
            config=config_path,
            mensaje="Procesado correctamente."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)

if __name__ == "__main__":
    print("🚀 Iniciando API HyperFrames en puerto 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
