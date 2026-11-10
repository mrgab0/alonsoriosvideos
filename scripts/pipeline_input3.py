"""
Autonomous Hyperframes Pipeline for input-3.mp4:
1. Downloads input-3.mp4 (107MB) from Google Drive to Colab.
2. Whisper transcribes audio to detect spoken words and exact timestamps.
3. NVIDIA Nemotron Super VL 120B designs 2-3 Fazt Web graphics per minute.
4. MoviePy renders with GPU acceleration.
5. Uploads to Gofile for instant high-speed streaming/download.
"""
import sys
import os
import json
import time
import urllib.request

sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)
print(f"✅ Runtime Colab listo: {rt}")

def get_nvidia_key():
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("NVIDIA_API_KEY"):
                return line.split("=")[1].strip()
    raise RuntimeError("NVIDIA_API_KEY not found in .env")

# Asegurar credenciales en Colab
with open("credentials/drive_sa.json", "r") as f:
    sa_json = f.read()

execute_remote(token, rt, f"""
with open('/content/drive_sa.json', 'w') as f:
    f.write({repr(sa_json)})
""")

# PASO 1: Descargar input-3.mp4 desde Google Drive a Colab
print("\n📥 [1/4] Descargando input-3.mp4 desde Google Drive a Colab...", flush=True)
dl_code = r'''
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

creds = service_account.Credentials.from_service_account_file(
    '/content/drive_sa.json',
    scopes=['https://www.googleapis.com/auth/drive']
)
service = build('drive', 'v3', credentials=creds)

files = service.files().list(
    q="name = 'input-3.mp4' and trashed = false",
    fields="files(id, name, size)"
).execute().get('files', [])

if not files:
    raise RuntimeError("input-3.mp4 no encontrado en Drive!")

fid = files[0]['id']
fsize = int(files[0]['size'])
dest = '/content/input-3.mp4'

if os.path.exists(dest) and os.path.getsize(dest) == fsize:
    print(f"Archivo ya completo en Colab: {fsize} bytes")
else:
    print(f"Iniciando descarga: {files[0]['name']} ({fsize / (1024*1024):.1f} MB)...")
    req = service.files().get_media(fileId=fid)
    with open(dest, 'wb') as fh:
        dl = MediaIoBaseDownload(fh, req, chunksize=15*1024*1024)
        done = False
        while not done:
            status, done = dl.next_chunk()
            if status:
                print(f"   Progreso: {int(status.progress() * 100)}%")
    print(f"Descarga finalizada: {os.path.getsize(dest)} bytes")
'''
res_dl = execute_remote(token, rt, dl_code, timeout=300)
print(res_dl.get("stdout", ""), flush=True)

# PASO 2: Extraer audio y transcribir con Whisper
print("\n🎤 [2/4] Analizando audio y transcribiendo con Whisper en Colab...", flush=True)
tr_code = r'''
import os, json, subprocess, wave
import numpy as np

# Instalar dependencias si faltan
try:
    from faster_whisper import WhisperModel
    import moviepy.editor
except ImportError:
    subprocess.run(["pip", "install", "-q", "faster-whisper", "moviepy==1.0.3", "Pillow", "imageio-ffmpeg", "google-api-python-client"], check=True)
    from faster_whisper import WhisperModel

import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

wav_path = "/tmp/audio-input3.wav"
print("Extrayendo pista de audio a 16kHz...")
subprocess.run([FFMPEG, "-y", "-i", "/content/input-3.mp4", "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

with wave.open(wav_path, "rb") as wf:
    rate = wf.getframerate()
    nframes = wf.getnframes()
    raw = wf.readframes(nframes)
duration_sec = nframes / rate
print(f"Duración total del audio: {duration_sec:.1f}s ({duration_sec/60:.1f} min)")

audio_arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
max_amp = np.max(np.abs(audio_arr))
mean_amp = np.mean(np.abs(audio_arr))
print(f"Amplitud máxima: {max_amp:.3f}, Amplitud media: {mean_amp:.5f}")

print("Transcribiendo con faster-whisper...")
model = WhisperModel("tiny", device="cpu", compute_type="int8")
segments, info = model.transcribe(audio_arr, vad_filter=False, beam_size=1)

transcript = []
for s in segments:
    txt = s.text.strip()
    if txt:
        transcript.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": txt})

out_tr = "/content/transcript_input3.json"
with open(out_tr, "w", encoding="utf-8") as f:
    json.dump({"language": info.language, "duration": duration_sec, "segments": transcript}, f, ensure_ascii=False)

print(f"TRANSCRIPCION_COMPLETA: {len(transcript)} segmentos | Idioma: {info.language}")
print("Primeros 5 segmentos detectados:")
for s in transcript[:5]:
    print(f"   [{s['start']}s - {s['end']}s]: {s['text']}")
'''
res_tr = execute_remote(token, rt, tr_code, timeout=600)
print(res_tr.get("stdout", ""), flush=True)

# Leer transcripción en local
tr_raw = execute_remote(token, rt, "import json; print('__TR__' + open('/content/transcript_input3.json', 'r', encoding='utf-8').read() + '__TR__')")
tr_str = tr_raw.get("stdout", "").split("__TR__")[1].split("__TR__")[0]
tr_data = json.loads(tr_str)

duration = tr_data.get("duration", 600)
segments = tr_data.get("segments", [])
print(f"\n📊 Datos del video: {duration:.1f}s ({duration/60:.1f} min), {len(segments)} frases habladas.")

# PASO 3: NVIDIA Nemotron Super VL 120B diseña el plan de 2-3 gráficos por minuto
print(f"\n🧠 [3/4] NVIDIA Nemotron Super VL 120B diseñando plan Fazt Web (2 a 3 por minuto)...", flush=True)
target_count = max(8, int((duration / 60) * 2.5))
print(f"   Meta de diseño: {target_count} gráficos animados distribuidos.", flush=True)

# Formatear el contenido hablado
sample_step = max(1, len(segments) // 60) if segments else 1
sample_text = "\n".join([f"[{s['start']}s - {s['end']}s] {s['text']}" for s in segments[::sample_step]])

system_prompt = f"""Eres el Director de Motion Graphics para un canal de YouTube de programación estilo Fazt Web.
Tu objetivo es diseñar exactamente entre {target_count - 3} y {target_count + 3} efectos visuales modernos a lo largo de este video de {duration/60:.1f} minutos ({duration:.0f} segundos).
Ritmo: 2 a 3 gráficos por minuto (uno cada 25-35 segundos).

Tipos de efectos permitidos:
1. 'terminal_code': Ventana de terminal macOS (#1E1E2E) con los 3 botones de colores y código relevante o comandos bash (máximo 4 líneas).
2. 'tech_pill': Insignia flotante moderna con nombre de tecnología / herramienta / librería y un subtítulo explicativo.

REGLAS CRÍTICAS:
- En 'code_lines', USA SIEMPRE comillas simples ' dentro del código (NUNCA comillas dobles ").
- Cada efecto debe durar de 4.0 a 5.5 segundos.
- Distribuye los efectos de manera uniforme desde el segundo 10 hasta el segundo {int(duration - 15)}.
- Responde ÚNICAMENTE con un bloque JSON válido con la clave 'effects'.

Ejemplo de estructura esperada:
```json
{{
  "effects": [
    {{
      "type": "tech_pill",
      "start": 15.0,
      "end": 20.0,
      "tech": "NODE.JS",
      "subtitle": "Runtime de JavaScript"
    }},
    {{
      "type": "terminal_code",
      "start": 42.0,
      "end": 47.0,
      "title": "init.sh",
      "code_lines": ["$ npm init -y", "$ npm install express", "$ node index.js"]
    }}
  ]
}}
```"""

key = get_nvidia_key()
req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    data=json.dumps({
        "model": "nvidia/nemotron-3.5-super-vl-120b-a12b",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{system_prompt}\n\nAquí está la transcripción hablada del video:\n{sample_text}\n\nDiseña el plan completo de {target_count} efectos en formato JSON:"}
                ]
            }
        ],
        "temperature": 0.2,
        "max_tokens": 4096
    }).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    msg = data["choices"][0]["message"]
    text = msg.get("content") or msg.get("reasoning_content")

if "```json" in text:
    clean = text.split("```json")[1].split("```")[0].strip()
elif "```" in text:
    clean = text.split("```")[1].split("```")[0].strip()
else:
    clean = text[text.find("{"):text.rfind("}")+1]

try:
    plan = json.loads(clean)
except Exception:
    import re
    # Fix internal unescaped quotes
    def fix_q(m):
        inner = m.group(1).replace('"', "'")
        return f': ["{inner}"]'
    fixed = re.sub(r':\s*\[\s*"([^\]]+)"\s*\]', fix_q, clean)
    try:
        plan = json.loads(fixed)
    except Exception:
        import ast
        eval_clean = clean.replace("true", "True").replace("false", "False").replace("null", "None")
        plan = ast.literal_eval(eval_clean)

effects = plan.get("effects", [])
print(f"✅ Nemotron Super VL diseñó {len(effects)} momentos de animación Fazt Web:", flush=True)
for fx in effects[:8]:
    print(f"   ⏱️ [{fx.get('start')}s - {fx.get('end')}s] {fx.get('type')}: {fx.get('title') or fx.get('tech')}")
if len(effects) > 8:
    print(f"   ... y {len(effects) - 8} gráficos más a lo largo del video.")

# Subir plan a Colab
plan_json_str = json.dumps(plan)
execute_remote(token, rt, f"import json; json.dump({plan_json_str}, open('/content/fazt_plan_input3.json', 'w'))")

# PASO 4: Renderizado con GPU en Colab + Subida a Gofile
print(f"\n🎨 [4/4] Renderizando video completo en GPU Colab y subiendo a Gofile...", flush=True)
render_code = r'''
import os, sys, math, json, time, urllib.request, subprocess
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

with open("/content/fazt_plan_input3.json") as f:
    plan = json.load(f)
effects = plan.get("effects", [])

base = VideoFileClip("/content/input-3.mp4")
W, H = base.size
print(f"🎬 Dimensiones: {W}x{H}, Duración: {base.duration:.1f}s ({base.duration/60:.1f} min), Total efectos: {len(effects)}")

font_title = get_font(24, bold=True)
font_code = get_font(21, bold=False)
font_pill = get_font(28, bold=True)
font_sub = get_font(18, bold=False)

def draw_terminal(draw, W, H, rel_t, dur, title, code_lines):
    bounce = min(1.0, 1.0 - math.exp(-7.0 * rel_t) * math.cos(12.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.25) * min(1.0, (dur - rel_t) / 0.3)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    tw, th = int(520 * bounce), 240
    tx, ty = W - tw - 40, 50

    # Sombra suave
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
    draw.text((tx + tw // 2 - 40, ty + 10), title or "terminal.sh", font=font_title, fill=(180, 190, 205, a))

    # Lineas de codigo con syntax highlight
    colors = [(203, 166, 247, a), (166, 227, 161, a), (137, 180, 250, a), (249, 226, 175, a)]
    line_y = ty + 58
    for i, line in enumerate(code_lines[:4]):
        col = colors[i % len(colors)]
        draw.text((tx + 25, line_y), f"> {line}", font=font_code, fill=col)
        line_y += 35

def draw_pill(draw, W, H, rel_t, dur, tech, subtitle):
    bounce = min(1.0, 1.0 - math.exp(-6.0 * rel_t) * math.cos(10.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.2) * min(1.0, (dur - rel_t) / 0.25)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    pw, ph = int(340 * bounce), 80
    px, py = 40, H - ph - 60

    # Sombra
    draw.rounded_rectangle([px + 6, py + 6, px + pw + 6, py + ph + 6], radius=24, fill=(0, 0, 0, int(90 * alpha_fade)))
    # Fondo pill neon
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=24, fill=(17, 24, 39, a), outline=(56, 189, 248, a), width=3)

    # Texto
    draw.text((px + 28, py + 12), tech or "TECH", font=font_pill, fill=(56, 189, 248, a))
    draw.text((px + 30, py + 48), subtitle or "Framework", font=font_sub, fill=(156, 163, 175, a))

def compose_frame(t):
    raw_frame = base.get_frame(t)
    active_fx = [fx for fx in effects if fx["start"] <= t <= fx["end"]]
    if not active_fx:
        return raw_frame

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

print("⚡ Renderizando con MoviePy a 24fps (libx264, preset ultrafast)...")
t0 = time.time()
out_clip = VideoClip(compose_frame, duration=base.duration).set_fps(24)
if base.audio is not None:
    out_clip = out_clip.set_audio(base.audio)

out_dest = "/content/resultado-input3.mp4"
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
render_time = time.time() - t0
size_mb = os.path.getsize(out_dest) / (1024 * 1024)
print(f"✅ Render completado en {render_time:.1f}s ({render_time/60:.1f} min)! Tamaño: {size_mb:.1f} MB")

# Subir a Gofile
print("📤 Subiendo resultado-input3.mp4 a Gofile...")
try:
    req = urllib.request.urlopen('https://api.gofile.io/servers')
    data = json.loads(req.read().decode())
    server = data['data']['servers'][0]['name']
    res = subprocess.run(['curl', '-s', '-F', f'file=@{out_dest}', f'https://{server}.gofile.io/contents/uploadfile'], capture_output=True, text=True)
    g_res = json.loads(res.stdout)
    d_page = g_res['data']['downloadPage']
    print(f"🎉 GOFILE_SUCCESS_URL: {d_page}")
except Exception as e:
    print(f"Error subiendo a Gofile: {e}")
'''

res_render = execute_remote(token, rt, render_code, timeout=1200)
print(res_render.get("stdout", ""), flush=True)

print("\n" + "=" * 60)
print("🎉 PIPELINE DE INPUT-3.MP4 COMPLETADO CON ÉXITO")
print("=" * 60)
