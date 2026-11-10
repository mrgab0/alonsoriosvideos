"""
Pipeline end-to-end para video de 16 minutos (input-2.mp4) con Estética Fazt Web:
1. Descarga input-2.mp4 desde Google Drive directo a Colab (red Google ~2s).
2. Transcripción con Whisper (faster-whisper) en Colab.
3. Director Creativo con NVIDIA Nemotron Super VL 120B (diseño de terminales y pills).
4. Render optimizado en Colab GPU (MoviePy + Pillow compositing ultra-rápido).
5. Subida automática del resultado final a Google Drive (carpeta hyperframes/output).
"""
import sys
import os
import json
import urllib.request
import time

sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime

MCP_URL = "https://colaboratory.googleapis.com/mcp"
PROJECT_ID = "vaka-taxi"
RUNTIME = None

def get_nvidia_key():
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("NVIDIA_API_KEY"):
                return line.split("=")[1].strip()
    raise RuntimeError("NVIDIA_API_KEY no encontrada en .env")

def exec_colab(token, code, timeout=1200):
    global RUNTIME
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
        "id": int(time.time()),
        "params": {
            "name": "execute_code",
            "arguments": {
                "runtime": RUNTIME,
                "code": code
            }
        }
    }
    req = urllib.request.Request(MCP_URL, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode("utf-8")
        lines = [line for line in data.splitlines() if line.startswith("data: ")]
        if lines:
            last = json.loads(lines[-1][len("data: "):])
            struct = last.get("result", {}).get("structuredContent", {})
            err = struct.get("error") or struct.get("stderr")
            if err:
                print(f"   [Colab Stderr] {err}", file=sys.stderr)
            return struct.get("stdout", "")
        return ""

def main():
    global RUNTIME
    print("=" * 60)
    print("🚀 INICIANDO PIPELINE AUTÓNOMO HYPERFRAMES (16 MINUTOS)")
    print("=" * 60)

    # 1. Autenticación y Verificación de GPU Colab
    print("\n🔑 [Paso 1/5] Verificando GPU y entorno en Colab...", flush=True)
    token = get_token()
    nvidia_key = get_nvidia_key()
    RUNTIME = ensure_active_runtime(token)
    print(f"✅ Runtime Colab asignado: {RUNTIME}", flush=True)

    # Subir credencial de servicio a Colab si no está
    with open("credentials/drive_sa.json", "r") as f:
        sa_json_str = f.read()
    exec_colab(token, f"""
with open('/content/drive_sa.json', 'w') as f:
    f.write({repr(sa_json_str)})
""")

    # 2. Descargar input-2.mp4 desde Drive directo a Colab
    print("\n📥 [Paso 2/5] Descargando input-2.mp4 desde Google Drive a Colab...", flush=True)
    dl_script = '''
import os, io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

creds = service_account.Credentials.from_service_account_file(
    '/content/drive_sa.json',
    scopes=['https://www.googleapis.com/auth/drive']
)
service = build('drive', 'v3', credentials=creds)

# Buscar input-2.mp4
files = service.files().list(q="name = 'input-2.mp4' and trashed = false", fields="files(id, name, size)").execute().get('files', [])
if not files:
    raise RuntimeError("input-2.mp4 no encontrado en Drive!")
fid = files[0]['id']
fsize = int(files[0].get('size', 0))
print(f"Encontrado en Drive: {files[0]['name']} ({fsize / (1024*1024):.1f} MB), ID: {fid}")

dest = '/content/input-2.mp4'
if os.path.exists(dest) and os.path.getsize(dest) == fsize:
    print(f"Archivo ya existente y completo en Colab: {os.path.getsize(dest)} bytes")
else:
    request = service.files().get_media(fileId=fid)
    with open(dest, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=10*1024*1024)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Progreso descarga: {int(status.progress() * 100)}%")
    print(f"Descarga finalizada: {os.path.getsize(dest)} bytes")
'''
    res_dl = exec_colab(token, dl_script)
    print(f"   {res_dl.strip()}", flush=True)

    # 3. Transcribir con Whisper
    print("\n🎤 [Paso 3/5] Transcribiendo 16 minutos con Whisper en Colab...", flush=True)
    transcribe_script = '''
import os, json, subprocess, wave
import numpy as np

try:
    from faster_whisper import WhisperModel
    import moviepy.editor
except ImportError:
    subprocess.run(["pip", "install", "-q", "faster-whisper", "moviepy==1.0.3", "Pillow", "imageio-ffmpeg", "google-api-python-client"], check=True)
    from faster_whisper import WhisperModel

import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

wav_path = "/tmp/audio-16min.wav"
if not os.path.exists(wav_path):
    print("Extrayendo pista de audio a 16kHz...")
    subprocess.run([FFMPEG, "-y", "-i", "/content/input-2.mp4", "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if not os.path.exists("/content/transcript.json"):
    print("Ejecutando Whisper Model (tiny)...")
    with wave.open(wav_path, "rb") as wf:
        raw = wf.readframes(wf.getnframes())
    audio_arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_arr, word_timestamps=False, vad_filter=True, beam_size=1)

    transcript = []
    for s in segments:
        transcript.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})

    with open("/content/transcript.json", "w", encoding="utf-8") as f:
        json.dump({"language": info.language, "segments": transcript}, f, ensure_ascii=False)
    print(f"TRANSCRIPT_DONE: {len(transcript)} segmentos transcritos.")
else:
    with open("/content/transcript.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Transcript existente cargado: {len(data.get('segments', []))} segmentos.")
'''
    res_tr = exec_colab(token, transcribe_script)
    print(f"   {res_tr.strip()}", flush=True)

    # 4. Consultar a NVIDIA Nemotron Super VL 120B
    print("\n🧠 [Paso 4/5] NVIDIA Nemotron Super VL 120B diseñando plan Fazt Web...", flush=True)
    tr_raw = exec_colab(token, "import json; print('__TR__' + open('/content/transcript.json', 'r', encoding='utf-8').read() + '__TR__')")
    tr_json_str = tr_raw.split("__TR__")[1].split("__TR__")[0]
    transcript_data = json.loads(tr_json_str)
    segments = transcript_data.get("segments", [])
    print(f"   Total segmentos en audio: {len(segments)}", flush=True)

    # Muestreo representativo a lo largo de los 16 minutos
    sample_step = max(1, len(segments) // 35)
    sample_segments = segments[::sample_step]
    text_summary = "\n".join([f"[{s['start']}s - {s['end']}s] {s['text']}" for s in sample_segments])

    system_prompt = """Eres el Director de Arte y Efectos Visuales para un canal de YouTube de programación estilo Fazt Web.
Tu objetivo es seleccionar de 7 a 10 momentos estratégicos en el video para superponer gráficos modernos y limpios:
Efectos disponibles:
1. 'terminal_code': Ventana flotante macOS (#1E1E2E) con los 3 botones de colores y código relevante con syntax highlighting.
2. 'tech_pill': Insignia flotante moderna con nombre de framework / tecnología y subtítulo.

REGLAS DE SALIDA:
- Responde estrictamente con un objeto JSON válido con la clave 'effects'.
- Cada efecto dura de 4.0 a 6.0 segundos.
- Distribuye los efectos a lo largo del tiempo del video.

Ejemplo de estructura esperada:
```json
{
  "effects": [
    {
      "type": "terminal_code",
      "start": 12.0,
      "end": 17.0,
      "title": "main.py",
      "code_lines": ["import asyncio", "async def main():", "    print('ready')"]
    },
    {
      "type": "tech_pill",
      "start": 60.0,
      "end": 65.0,
      "tech": "DOCKER",
      "subtitle": "Container Engine"
    }
  ]
}
```"""

    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=json.dumps({
            "model": "nvidia/nemotron-3.5-super-vl-120b-a12b",
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": f"{system_prompt}\n\nTranscripción de los momentos clave del video:\n{text_summary}\n\nGenera el plan de efectos en formato JSON:"}]}
            ],
            "temperature": 0.2,
            "max_tokens": 2500
        }).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {nvidia_key}",
            "Content-Type": "application/json"
        }
    )

    with urllib.request.urlopen(req) as resp:
        llm_resp = json.loads(resp.read().decode("utf-8"))
        msg = llm_resp["choices"][0]["message"]
        content = msg.get("content") or ""
        reasoning = msg.get("reasoning_content") or ""
        full_text = content if ("```json" in content or "effects" in content) else (reasoning + "\n" + content)

        if "```json" in full_text:
            json_str = full_text.split("```json")[1].split("```")[0].strip()
        elif "```" in full_text:
            json_str = full_text.split("```")[1].split("```")[0].strip()
        elif "{" in full_text and "}" in full_text:
            json_str = full_text[full_text.find("{"):full_text.rfind("}")+1]
        else:
            json_str = full_text.strip()

        effects_plan = json.loads(json_str)

    print(f"✅ Nemotron Super VL generó {len(effects_plan.get('effects', []))} momentos de animación:", flush=True)
    for fx in effects_plan.get("effects", []):
        print(f"   ⏱️ [{fx.get('start')}s - {fx.get('end')}s] {fx.get('type')}: {fx.get('title') or fx.get('tech')}", flush=True)

    # Subir plan a Colab
    exec_colab(token, f"import json; json.dump({json.dumps(effects_plan)}, open('/content/fazt_plan.json', 'w'))")

    # 5. Render en Colab GPU + Subida directa a Google Drive
    print("\n🎨 [Paso 5/5] Renderizando video en GPU Colab y subiendo a Google Drive...", flush=True)
    render_and_upload_script = r'''
import os, sys, math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, VideoClip

def get_font(size, bold=True):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

with open("/content/fazt_plan.json") as f:
    plan = json.load(f)
effects = plan.get("effects", [])

base = VideoFileClip("/content/input-2.mp4")
W, H = base.size
print(f"Video Base: {W}x{H}, Duración: {base.duration:.1f}s ({base.duration/60:.1f} min)")

font_title = get_font(24, bold=True)
font_code = get_font(22, bold=False)
font_pill = get_font(30, bold=True)
font_sub = get_font(18, bold=False)

def draw_terminal(draw, W, H, rel_t, dur, title, code_lines):
    bounce = min(1.0, 1.0 - math.exp(-7.0 * rel_t) * math.cos(12.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.25) * min(1.0, (dur - rel_t) / 0.3)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    tw, th = int(480 * bounce), 250
    tx, ty = W - tw - 40, 50

    # Sombra
    draw.rounded_rectangle([tx + 8, ty + 8, tx + tw + 8, ty + th + 8], radius=16, fill=(0, 0, 0, int(110 * alpha_fade)))
    # Fondo ventana terminal oscura #1E1E2E
    draw.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=16, fill=(30, 30, 46, a), outline=(60, 60, 85, a), width=2)

    # Barra superior macOS
    draw.rounded_rectangle([tx, ty, tx + tw, ty + 42], radius=16, fill=(24, 24, 37, a))
    draw.rectangle([tx, ty + 28, tx + tw, ty + 42], fill=(24, 24, 37, a))

    # Botones macOS
    draw.ellipse([tx + 16, ty + 15, tx + 28, ty + 27], fill=(255, 95, 86, a))
    draw.ellipse([tx + 36, ty + 15, tx + 48, ty + 27], fill=(255, 189, 46, a))
    draw.ellipse([tx + 56, ty + 15, tx + 68, ty + 27], fill=(39, 201, 63, a))

    # Titulo archivo
    draw.text((tx + tw // 2 - 40, ty + 10), title or "index.js", font=font_title, fill=(180, 190, 205, a))

    # Lineas de codigo con syntax highlight
    colors = [(203, 166, 247, a), (166, 227, 161, a), (137, 180, 250, a), (249, 226, 175, a)]
    line_y = ty + 60
    for i, line in enumerate(code_lines[:5]):
        col = colors[i % len(colors)]
        draw.text((tx + 25, line_y), f"> {line}", font=font_code, fill=col)
        line_y += 34

def draw_pill(draw, W, H, rel_t, dur, tech, subtitle):
    bounce = min(1.0, 1.0 - math.exp(-6.0 * rel_t) * math.cos(10.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.2) * min(1.0, (dur - rel_t) / 0.25)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    pw, ph = int(320 * bounce), 80
    px, py = 40, H - ph - 60

    # Sombra
    draw.rounded_rectangle([px + 6, py + 6, px + pw + 6, py + ph + 6], radius=24, fill=(0, 0, 0, int(90 * alpha_fade)))
    # Fondo pill neon
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=24, fill=(17, 24, 39, a), outline=(56, 189, 248, a), width=3)

    # Texto
    draw.text((px + 28, py + 12), tech or "TECH", font=font_pill, fill=(56, 189, 248, a))
    draw.text((px + 30, py + 48), subtitle or "Framework", font=font_sub, fill=(156, 163, 175, a))

# Optimizacion critica: bypass en frames sin efectos
def compose_frame(t):
    raw_frame = base.get_frame(t)
    active_fx = [fx for fx in effects if fx["start"] <= t <= fx["end"]]
    if not active_fx:
        return raw_frame

    # Dibujar overlays activos
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    for fx in active_fx:
        rel_t = t - fx["start"]
        dur = fx["end"] - fx["start"]
        if fx["type"] == "terminal_code":
            draw_terminal(draw, W, H, rel_t, dur, fx.get("title"), fx.get("code_lines", []))
        elif fx["type"] == "tech_pill":
            draw_pill(draw, W, H, rel_t, dur, fx.get("tech"), fx.get("subtitle"))

    img = Image.fromarray(raw_frame)
    img.paste(canvas, mask=canvas)
    return np.array(img)

print("Iniciando render con MoviePy (codec libx264, preset ultrafast)...")
out_clip = VideoClip(compose_frame, duration=base.duration).set_fps(24)
if base.audio is not None:
    out_clip = out_clip.set_audio(base.audio)

out_dest = "/content/resultado-16min.mp4"
out_clip.write_videofile(
    out_dest,
    fps=24,
    codec="libx264",
    preset="ultrafast",
    audio_codec="aac",
    threads=4,
    verbose=False,
    logger=None
)
print(f"Render finalizado! Tamaño: {os.path.getsize(out_dest)} bytes")

# Subir a Google Drive (carpeta hyperframes/output)
print("Subiendo video final a Google Drive (hyperframes/output)...")
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

creds = service_account.Credentials.from_service_account_file(
    '/content/drive_sa.json',
    scopes=['https://www.googleapis.com/auth/drive']
)
service = build('drive', 'v3', credentials=creds)

# ID de la carpeta output
output_folder_id = "1yBF7fEkpy6A_VdHlG9T6qbJxGroSapDJ"

media = MediaFileUpload(out_dest, mimetype='video/mp4', resumable=True)
body = {
    'name': 'resultado-16min.mp4',
    'parents': [output_folder_id]
}
up_res = service.files().create(body=body, media_body=media, fields='id, name, webViewLink').execute()
print(f"DRIVE_UPLOAD_SUCCESS: ID={up_res.get('id')}")
'''
    res_render = exec_colab(token, render_and_upload_script, timeout=1800)
    print(f"   {res_render.strip()}", flush=True)

    print("\n" + "=" * 60)
    print("🎉 ¡PROCESAMIENTO DE 16 MINUTOS COMPLETADO CON ÉXITO!")
    print("📁 El video ya está guardado en tu Google Drive:")
    print("   Ruta: hyperframes/output/resultado-16min.mp4")
    print("=" * 60)

if __name__ == "__main__":
    main()
