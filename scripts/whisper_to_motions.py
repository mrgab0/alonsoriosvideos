"""
whisper_to_motions.py
=====================
Detecta una palabra clave hablada en tu video con faster-whisper (CUDA int8)
y genera automáticamente config/motions.json para que hyperframes le ponga
gráficos en el momento exacto.

Uso básico (solo detección, genera el JSON):
    python scripts/whisper_to_motions.py --video sample/input.mp4 --keyword casa

Uso completo (detección + render inmediato):
    python scripts/whisper_to_motions.py --video sample/input.mp4 --keyword casa --render

Luego el resultado queda en output/resultado.mp4
"""

import argparse
import gc
import json
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np

# ---------------------------------------------------------------------------
# Windows: asegurar que cuBLAS DLL sea encontrada por faster-whisper
# (sin tocar nada del sistema, solo dentro de la carpeta de Python)
# ---------------------------------------------------------------------------

def _ensure_nvidia_dll_path():
    """Agrega al PATH todos los directorios bin de NVIDIA dentro de site-packages
    (sin tocar nada del sistema, solo dentro de la carpeta de Python)."""
    import site
    dll_dirs = []
    for sp in site.getsitepackages() + [site.getusersitepackages()]:
        nvidia_root = os.path.join(sp, "nvidia")
        if not os.path.isdir(nvidia_root):
            continue
        for pkg in os.listdir(nvidia_root):
            bin_dir = os.path.join(nvidia_root, pkg, "bin")
            if os.path.isdir(bin_dir):
                dll_dirs.append(bin_dir)
    if dll_dirs:
        # Poner primero los de cublas y cuda_runtime para prioridad
        dll_dirs.sort(key=lambda d: (0 if "cublas" in d or "cuda_runtime" in d else 1, d))
        os.environ["PATH"] = os.pathsep.join(dll_dirs) + os.pathsep + os.environ.get("PATH", "")
        for d in dll_dirs:
            try:
                os.add_dll_directory(d)
            except Exception:
                pass

_ensure_nvidia_dll_path()

# ---------------------------------------------------------------------------
# Dependencias opcionales (se instalan con install_deps.bat)
# ---------------------------------------------------------------------------

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_EXE = "ffmpeg"


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------

def extract_audio(video_path, wav_path):
    """Extrae audio mono 16kHz WAV usando el ffmpeg embebido de imageio."""
    cmd = [
        FFMPEG_EXE, "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        wav_path,
    ]
    subprocess.run(cmd, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------------------------------------------------------------------------
# Transcripción
# ---------------------------------------------------------------------------

def load_wav_as_array(wav_path):
    """Lee un WAV mono 16-bit y devuelve array numpy float32 [-1, 1]."""
    with wave.open(wav_path, "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    if sample_width == 2:
        dtype = np.int16
    elif sample_width == 4:
        dtype = np.int32
    else:
        dtype = np.int16

    audio = np.frombuffer(raw, dtype=dtype)
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels)[:, 0]  # canal 0
    audio = audio.astype(np.float32) / 32768.0
    return audio


def transcribe_words(audio_path, model_size="base", language=None):
    """
    Transcribe con faster-whisper en CUDA (int8).
    Lee el audio como array numpy para evitar problemas de PyAV.
    Devuelve lista de palabras con start/end y el idioma detectado.
    """
    if WhisperModel is None:
        raise RuntimeError(
            "faster-whisper no está instalado. Ejecuta primero:\n"
            "  pip install faster-whisper\n"
            "o usa scripts/install_deps.bat"
        )

    # int8 = vital para que quepa en GTX 1060 3GB
    model = WhisperModel(model_size, device="cuda", compute_type="int8")

    audio_array = load_wav_as_array(audio_path)

    segments, info = model.transcribe(
        audio_array,
        word_timestamps=True,
        language=language,          # None = auto-detectar
        vad_filter=True,            # elimina silencios, más rápido
        beam_size=1,                # menos RAM/VRAM
    )

    words = []
    for segment in segments:
        for w in segment.words:
            words.append({
                "word": w.word,
                "start": round(float(w.start), 3),
                "end": round(float(w.end), 3),
            })

    # Liberar VRAM y RAM inmediatamente
    del model
    gc.collect()
    try:
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass

    return words, info


# ---------------------------------------------------------------------------
# Construcción del JSON de motions
# ---------------------------------------------------------------------------

def build_motions(words, keywords, effect_type="highlight", duration=1.5):
    """Crea un efecto por cada ocurrencia de la palabra clave."""
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Detecta palabra clave hablada y genera motions.json para hyperframes"
    )
    parser.add_argument("--video", required=True, help="Video de entrada")
    parser.add_argument("--keyword", default=["storm"], nargs="+",
                        help="Palabra(s) clave a buscar (default: storm)")
    parser.add_argument("--model", default="base",
                        help="Modelo faster-whisper: tiny, base, small (default: base)")
    parser.add_argument("--language", default=None,
                        help="Idioma (es, en) o None para auto-detectar")
    parser.add_argument("--effect", default="highlight",
                        help="Tipo de efecto: highlight, lower_third, arrow, etc.")
    parser.add_argument("--duration", type=float, default=1.5,
                        help="Segundos que dura el gráfico tras la palabra")
    parser.add_argument("--output", default="config/motions.json",
                        help="JSON de salida")
    parser.add_argument("--render", action="store_true",
                        help="Después de generar JSON, ejecuta add_motion_graphics.py")
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"[!] No existe el video: {args.video}", file=sys.stderr)
        sys.exit(1)

    tmp_fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(tmp_fd)

    try:
        print(f"[+] Extrayendo audio de {args.video} ...")
        extract_audio(args.video, wav_path)

        print(f"[+] Transcribiendo con modelo {args.model} en CUDA (int8) ...")
        words, info = transcribe_words(wav_path, args.model, args.language)
        print(f"[+] Idioma: {info.language} | Palabras totales: {len(words)}")

        print(f"[+] Buscando palabra(s): {args.keyword}")
        effects = build_motions(words, args.keyword, args.effect, args.duration)
        print(f"[+] Coincidencias encontradas: {len(effects)}")

        config = {
            "input": args.video,
            "output": "output/resultado.mp4",
            "fps": 24,
            "effects": effects,
        }

        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"[+] Guardado: {args.output}")

        if args.render:
            print("[+] Lanzando render de hyperframes ...")
            add_script = os.path.join(os.path.dirname(__file__), "add_motion_graphics.py")
            subprocess.run(
                [sys.executable, add_script, "--config", args.output],
                check=True,
            )

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


if __name__ == "__main__":
    main()
