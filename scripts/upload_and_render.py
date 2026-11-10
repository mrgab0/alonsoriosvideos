"""
One-shot script to upload, run, and download video from Colab GPU.
"""
import subprocess
import json
import urllib.request
import base64
import os
import sys

MCP_URL = "https://colaboratory.googleapis.com/mcp"
PROJECT_ID = "vaka-taxi"
RUNTIME = "runtimes/r-bf1e379d-802f-4c7d-afd2-ce7e0db6ba85"

def get_token():
    cmd = ["gcloud.cmd", "auth", "application-default", "print-access-token"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        return res.stdout.strip()
    except Exception:
        cmd = ["gcloud", "auth", "application-default", "print-access-token"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        return res.stdout.strip()

def exec_code(token, code):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {token}",
        "X-Goog-User-Project": PROJECT_ID,
        "MCP-Protocol-Version": "2026-07-28",
        "Mcp-Method": "tools/call"
    }
    body = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 1,
        "params": {
            "name": "execute_code",
            "arguments": {
                "runtime": RUNTIME,
                "code": code
            }
        }
    }
    req = urllib.request.Request(MCP_URL, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = resp.read().decode("utf-8")
            lines = [line for line in data.splitlines() if line.startswith("data: ")]
            if lines:
                last = json.loads(lines[-1][len("data: "):])
                struct = last.get("result", {}).get("structuredContent", {})
                err = struct.get("error") or struct.get("stderr")
                if err:
                    print(f"   [Colab Error/Stderr] {err}", file=sys.stderr)
                return struct.get("stdout", "")
            return ""
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="replace")
        print(f"[!] HTTP Error {e.code}: {err_msg}", file=sys.stderr)
        raise

def main():
    print("🔑 Obteniendo token...")
    token = get_token()
    
    # 1. Subir input.mp4 en chunks de 500KB
    input_path = "example/input.mp4"
    print(f"📤 Subiendo {input_path} a la GPU T4 de Colab...")
    exec_code(token, "open('/content/input.mp4', 'wb').close()")
    
    chunk_size = 500000  # 500 KB por chunk
    total_bytes = os.path.getsize(input_path)
    with open(input_path, "rb") as f:
        c_idx = 1
        uploaded = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            b64 = base64.b64encode(chunk).decode("ascii")
            uploaded += len(chunk)
            print(f"   Enviando parte {c_idx} ({uploaded}/{total_bytes} bytes - {int(uploaded*100/total_bytes)}%)...")
            upload_code = f"""
import base64
with open('/content/input.mp4', 'ab') as f:
    f.write(base64.b64decode('{b64}'))
"""
            exec_code(token, upload_code)
            c_idx += 1
            
    res_size = exec_code(token, "import os; print(os.path.getsize('/content/input.mp4'))")
    print(f"✅ Video en Colab listo: {res_size.strip()} bytes")

    # 2. Instalar dependencias primero
    print("📦 [Paso 1/2] Verificando e instalando dependencias en Colab...")
    setup_code = """
import subprocess
try:
    import faster_whisper
    import moviepy.editor
    print("DEPENDENCIES_OK")
except ImportError:
    subprocess.run(["pip", "install", "-q", "faster-whisper", "moviepy==1.0.3", "Pillow", "imageio-ffmpeg"], check=True)
    print("DEPENDENCIES_INSTALLED")
"""
    dep_res = exec_code(token, setup_code)
    print(f"   {dep_res.strip()}")

    # 3. Correr pipeline completo en GPU T4
    print("🚀 [Paso 2/2] Ejecutando Whisper y MoviePy en la GPU T4...")
    pipeline = r'''
import subprocess, os, sys, gc, wave, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Instalar si no estan
try:
    from faster_whisper import WhisperModel
    from moviepy.editor import VideoFileClip, VideoClip
except ImportError:
    subprocess.run(["pip", "install", "-q", "faster-whisper", "moviepy==1.0.3", "Pillow", "imageio-ffmpeg"], check=True)
    from faster_whisper import WhisperModel
    from moviepy.editor import VideoFileClip, VideoClip

import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# Extraer audio
subprocess.run([FFMPEG, "-y", "-i", "/content/input.mp4", "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "/tmp/audio.wav"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

with wave.open("/tmp/audio.wav", "rb") as wf:
    raw = wf.readframes(wf.getnframes())
audio_arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

# Whisper en GPU T4 con fallback automatico a CPU
try:
    print("Transcribiendo en GPU T4...")
    model = WhisperModel("tiny", device="cuda", compute_type="float16")
    segments, info = model.transcribe(audio_arr, word_timestamps=True, vad_filter=True)
    words = []
    for s in segments:
        for w in s.words:
            print(f"Palabra: [{w.start:.2f}s - {w.end:.2f}s] {w.word}")
            words.append({"word": w.word, "start": w.start, "end": w.end})
except Exception as ex:
    print(f"Nota GPU: {ex}. Cambiando a CPU rapido...")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_arr, word_timestamps=True, vad_filter=True)
    words = []
    for s in segments:
        for w in s.words:
            print(f"Palabra: [{w.start:.2f}s - {w.end:.2f}s] {w.word}")
            words.append({"word": w.word, "start": w.start, "end": w.end})

del model
gc.collect()

# Efectos highlight estilo Swiss Motion
effects = []
for w in words:
    effects.append({
        "start": w["start"],
        "end": w["start"] + 1.5,
        "text": w["word"]
    })

base = VideoFileClip("/content/input.mp4")
W, H = base.size

def compose_frame(t):
    frame = base.get_frame(t).astype(np.float32) / 255.0
    for fx in effects:
        if fx["start"] <= t <= fx["end"]:
            rel_t = t - fx["start"]
            img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Anillo de pulso minimalista dorado
            r = 100 * (1.0 + 0.15 * math.sin(2 * math.pi * rel_t * 3))
            cx, cy = W // 2, H // 2
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 215, 0, 230), width=5)
            ov = np.array(img).astype(np.float32) / 255.0
            alpha = ov[:, :, 3:4]
            frame = frame * (1.0 - alpha) + ov[:, :, :3] * alpha
    return (frame * 255).astype(np.uint8)

out_clip = VideoClip(compose_frame, duration=base.duration).set_fps(24)
if base.audio is not None:
    out_clip = out_clip.set_audio(base.audio)

out_clip.write_videofile("/content/resultado.mp4", fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
print("FIN_RENDER")
'''
    res = exec_code(token, pipeline)
    print(res)

    # 3. Descargar a output/resultado.mp4
    print("📥 Descargando resultado.mp4 a tu carpeta local output/...")
    os.makedirs("output", exist_ok=True)
    
    # Obtener en 2 bloques base64
    size_str = exec_code(token, "import os; print(os.path.getsize('/content/resultado.mp4'))").strip()
    total_size = int(size_str)
    print(f"Tamaño del video renderizado: {total_size} bytes")

    get_code = """
import base64
with open('/content/resultado.mp4', 'rb') as f:
    print('__B64__' + base64.b64encode(f.read()).decode('ascii') + '__B64__')
"""
    b64_res = exec_code(token, get_code)
    b64_content = b64_res.split("__B64__")[1].split("__B64__")[0].strip()
    
    dest_path = os.path.abspath("output/resultado.mp4")
    with open(dest_path, "wb") as f:
        f.write(base64.b64decode(b64_content))
        
    print(f"🎉 ¡VIDEO DESCARGADO EXITOSAMENTE!")
    print(f"📁 Ubicación local: {dest_path}")
    print(f"⚖️ Tamaño final: {os.path.getsize(dest_path)} bytes")

if __name__ == "__main__":
    main()
