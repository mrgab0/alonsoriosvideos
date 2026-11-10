"""
Process 16-minute video with Fazt Web style motion graphics:
1. Upload input-2.mp4 (33.8MB) to Colab in 2MB chunks.
2. Whisper transcribes the 16 minutes in Colab.
3. NVIDIA NIM (DeepSeek Flash) acts as Editorial Director: selects key moments for code terminals and tech pills.
4. MoviePy renders Fazt Web style components frame-by-frame on Colab.
5. Downloads output/resultado-16min.mp4 locally.
"""
import subprocess
import json
import urllib.request
import base64
import os
import sys

from colab_bridge import get_token as get_colab_token, ensure_active_runtime

MCP_URL = "https://colaboratory.googleapis.com/mcp"
PROJECT_ID = "vaka-taxi"
RUNTIME = None

def get_nvidia_key():
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("NVIDIA_API_KEY"):
                return line.split("=")[1].strip()
    raise RuntimeError("NVIDIA_API_KEY not found in .env")

def exec_colab(token, code):
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
    with urllib.request.urlopen(req, timeout=500) as resp:
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

def upload_video(token, local_path, remote_path):
    total_bytes = os.path.getsize(local_path)
    print(f"📤 Subiendo {local_path} ({total_bytes / (1024*1024):.1f} MB) a Colab...")
    exec_colab(token, f"open('{remote_path}', 'wb').close()")
    
    chunk_size = 2000000 # 2 MB por chunk (~17 partes)
    with open(local_path, "rb") as f:
        c_idx = 1
        uploaded = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            b64 = base64.b64encode(chunk).decode("ascii")
            uploaded += len(chunk)
            pct = int(uploaded * 100 / total_bytes)
            print(f"   Enviando chunk {c_idx} ({uploaded // 1048576}MB / {total_bytes // 1048576}MB - {pct}%)...")
            code = f"""
import base64
with open('{remote_path}', 'ab') as f:
    f.write(base64.b64decode('{b64}'))
"""
            exec_colab(token, code)
            c_idx += 1
            
    size_check = exec_colab(token, f"import os; print(os.path.getsize('{remote_path}'))").strip()
    print(f"✅ Video en Colab verificado: {size_check} bytes")

def main():
    global RUNTIME
    print("🔑 [1/5] Inicializando credenciales y verificando máquina en Colab...", flush=True)
    token = get_colab_token()
    nvidia_key = get_nvidia_key()
    RUNTIME = ensure_active_runtime(token)
    print(f"💻 Máquina de render asignada: {RUNTIME}", flush=True)
    
    local_input = "example/input-2.mp4"
    remote_input = "/content/input-2.mp4"
    remote_output = "/content/resultado-16min.mp4"
    
    # 1. Subida del video
    upload_video(token, local_input, remote_input)

    # 2. Transcripción con Whisper en Colab
    print("🎤 [2/5] Transcribiendo los 16 minutos con Whisper en Colab...", flush=True)
    transcribe_script = f"""
import subprocess, wave, gc, json
import numpy as np

# Instalar si falta
try:
    from faster_whisper import WhisperModel
    import moviepy.editor
except ImportError:
    subprocess.run(["pip", "install", "-q", "faster-whisper", "moviepy==1.0.3", "Pillow", "imageio-ffmpeg"], check=True)
    from faster_whisper import WhisperModel

import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# Extraer audio 16kHz
wav_path = "/tmp/audio-16min.wav"
subprocess.run([FFMPEG, "-y", "-i", "{remote_input}", "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

with wave.open(wav_path, "rb") as wf:
    raw = wf.readframes(wf.getnframes())
audio_arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

print("Procesando audio en Whisper...")
model = WhisperModel("tiny", device="cpu", compute_type="int8")
segments, info = model.transcribe(audio_arr, word_timestamps=False, vad_filter=True, beam_size=1)

transcript = []
for s in segments:
    transcript.append({{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}})

with open("/content/transcript.json", "w", encoding="utf-8") as f:
    json.dump({{"language": info.language, "segments": transcript}}, f, ensure_ascii=False)

print("TRANSCRIPT_DONE: " + str(len(transcript)) + " segmentos")
"""
    t_res = exec_colab(token, transcribe_script)
    print(f"   {t_res.strip()}", flush=True)

    # 3. Leer transcripción y llamar a NVIDIA Nemotron Super VL 120B Director
    print("🧠 [3/5] Consultando a NVIDIA Nemotron Super VL 120B para plan editorial estilo Fazt Web...", flush=True)
    get_tr_code = "import json; print('__TR__' + open('/content/transcript.json', 'r', encoding='utf-8').read() + '__TR__')"
    tr_raw = exec_colab(token, get_tr_code)
    tr_json_str = tr_raw.split("__TR__")[1].split("__TR__")[0]
    transcript_data = json.loads(tr_json_str)
    
    segments = transcript_data.get("segments", [])
    print(f"   Total de segmentos de audio analizados: {len(segments)}", flush=True)
    
    # Tomar muestra representativa de los 16 minutos para el prompt del LLM
    text_summary = "\n".join([f"[{s['start']}s - {s['end']}s] {s['text']}" for s in segments[::max(1, len(segments)//30)]])
    
    system_prompt = """Eres el Director de Animación y Efectos Visuales para un canal de YouTube de programación estilo Fazt Web.
Tu objetivo es seleccionar de 6 a 10 momentos estratégicos en el video para superponer gráficos limpios y modernos:
Tipos de efectos permitidos:
1. 'terminal_code': Ventana de terminal estilo macOS (#1E1E2E, 3 botones de color, código relevante con colores).
2. 'tech_pill': Insignia flotante moderna con nombre de tecnología / herramienta clave.

Responde con un bloque JSON con la clave 'effects' con la siguiente estructura:
```json
{
  "effects": [
    {
      "type": "terminal_code",
      "start": 12.0,
      "end": 17.0,
      "title": "server.py",
      "code_lines": ["import fastapi", "app = fastapi.FastAPI()"]
    },
    {
      "type": "tech_pill",
      "start": 45.0,
      "end": 49.0,
      "tech": "DOCKER",
      "subtitle": "Containerization"
    }
  ]
}
```"""

    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=json.dumps({
            "model": "nvidia/nemotron-3.5-super-vl-120b-a12b",
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": f"{system_prompt}\n\nAquí están los momentos clave del video de 16 minutos:\n{text_summary}\n\nGenera el plan de efectos estilo Fazt Web en JSON:"}]}
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
        full_text = content if "```json" in content or "effects" in content else (reasoning + "\n" + content)
        
        # Extraer bloque JSON
        if "```json" in full_text:
            json_str = full_text.split("```json")[1].split("```")[0].strip()
        elif "```" in full_text:
            json_str = full_text.split("```")[1].split("```")[0].strip()
        elif "{" in full_text and "}" in full_text:
            json_str = full_text[full_text.find("{"):full_text.rfind("}")+1]
        else:
            json_str = full_text.strip()
            
        effects_plan = json.loads(json_str)
        
    print(f"✅ Plan de efectos de NVIDIA Nemotron listo: {len(effects_plan.get('effects', []))} gráficos diseñados.", flush=True)
    for fx in effects_plan.get("effects", []):
        print(f"   ⏱️ [{fx.get('start')}s - {fx.get('end')}s] {fx.get('type')}: {fx.get('title') or fx.get('tech')}", flush=True)

    # Guardar plan en Colab
    plan_json_str = json.dumps(effects_plan)
    exec_colab(token, f"import json; json.dump({plan_json_str}, open('/content/fazt_plan.json', 'w'))")

    # 4. Renderizado Fazt Web en Colab
    print("🎨 [4/5] Renderizando video con estética Fazt Web en Colab...")
    render_script = r'''
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
print(f"Base: {W}x{H}, Dur: {base.duration:.1f}s, Efectos: {len(effects)}")

font_title = get_font(26, bold=True)
font_code = get_font(24, bold=False)
font_pill = get_font(32, bold=True)
font_sub = get_font(20, bold=False)

def draw_terminal(draw, W, H, rel_t, dur, title, code_lines):
    # Spring bounce in
    bounce = min(1.0, 1.0 - math.exp(-7.0 * rel_t) * math.cos(12.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.25) * min(1.0, (dur - rel_t) / 0.3)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    tw, th = int(480 * bounce), 260
    tx, ty = W - tw - 40, 60

    # Sombra
    draw.rounded_rectangle([tx + 8, ty + 8, tx + tw + 8, ty + th + 8], radius=16, fill=(0, 0, 0, int(120 * alpha_fade)))
    # Fondo ventana terminal oscura
    draw.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=16, fill=(30, 30, 46, a), outline=(60, 60, 85, a), width=2)

    # Barra superior de macOS
    draw.rounded_rectangle([tx, ty, tx + tw, ty + 45], radius=16, fill=(24, 24, 37, a))
    draw.rectangle([tx, ty + 30, tx + tw, ty + 45], fill=(24, 24, 37, a)) # esquina inferior plana

    # Botones macOS
    draw.ellipse([tx + 18, ty + 16, tx + 30, ty + 28], fill=(255, 95, 86, a))   # Rojo
    draw.ellipse([tx + 38, ty + 16, tx + 50, ty + 28], fill=(255, 189, 46, a))  # Amarillo
    draw.ellipse([tx + 58, ty + 16, tx + 70, ty + 28], fill=(39, 201, 63, a))   # Verde

    # Titulo de archivo
    draw.text((tx + tw // 2 - 40, ty + 12), title or "terminal.sh", font=font_title, fill=(180, 190, 205, a))

    # Lineas de codigo con syntax highlight
    colors = [(203, 166, 247, a), (166, 227, 161, a), (137, 180, 250, a), (249, 226, 175, a)]
    line_y = ty + 65
    for i, line in enumerate(code_lines[:5]):
        col = colors[i % len(colors)]
        draw.text((tx + 25, line_y), f"> {line}", font=font_code, fill=col)
        line_y += 35

def draw_pill(draw, W, H, rel_t, dur, tech, subtitle):
    bounce = min(1.0, 1.0 - math.exp(-6.0 * rel_t) * math.cos(10.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.2) * min(1.0, (dur - rel_t) / 0.25)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    pw, ph = int(320 * bounce), 85
    px, py = 40, H - ph - 60

    # Sombra
    draw.rounded_rectangle([px + 6, py + 6, px + pw + 6, py + ph + 6], radius=25, fill=(0, 0, 0, int(100 * alpha_fade)))
    # Fondo pill neon
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=25, fill=(17, 24, 39, a), outline=(56, 189, 248, a), width=3)

    # Texto
    draw.text((px + 30, py + 14), tech or "TECH", font=font_pill, fill=(56, 189, 248, a))
    draw.text((px + 32, py + 50), subtitle or "Framework", font=font_sub, fill=(156, 163, 175, a))

def compose_frame(t):
    frame = base.get_frame(t).astype(np.float32) / 255.0
    canvas = None
    draw = None
    
    for fx in effects:
        start, end = fx["start"], fx["end"]
        if start <= t <= end:
            if canvas is None:
                canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                draw = ImageDraw.Draw(canvas)
            rel_t = t - start
            dur = end - start
            ft = fx["type"]
            if ft == "terminal_code":
                draw_terminal(draw, W, H, rel_t, dur, fx.get("title"), fx.get("code_lines", []))
            elif ft == "tech_pill":
                draw_pill(draw, W, H, rel_t, dur, fx.get("tech"), fx.get("subtitle"))
                
    if canvas is not None:
        ov = np.array(canvas).astype(np.float32) / 255.0
        alpha = ov[:, :, 3:4]
        frame = frame * (1.0 - alpha) + ov[:, :, :3] * alpha
        
    return (frame * 255).astype(np.uint8)

print("Renderizando video completo...")
out_clip = VideoClip(compose_frame, duration=base.duration).set_fps(24)
if base.audio is not None:
    out_clip = out_clip.set_audio(base.audio)

out_clip.write_videofile("/content/resultado-16min.mp4", fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
print("FIN_RENDER_16MIN")
'''
    exec_colab(token, render_script)

    # 5. Descarga
    print("📥 [5/5] Descargando resultado-16min.mp4 a tu carpeta output/...")
    os.makedirs("output", exist_ok=True)
    dest_path = os.path.abspath("output/resultado-16min.mp4")
    
    # Descargar en bloques base64
    get_size_code = "import os; print(os.path.getsize('/content/resultado-16min.mp4'))"
    res_size = exec_colab(token, get_size_code).strip()
    total_dl = int(res_size)
    print(f"   Tamaño final a descargar: {total_dl / (1024*1024):.1f} MB")
    
    dl_chunk = 4000000 # 4MB por bloque de descarga
    with open(dest_path, "wb") as f_out:
        offset = 0
        b_idx = 1
        while offset < total_dl:
            chunk_code = f"""
import base64
with open('/content/resultado-16min.mp4', 'rb') as f:
    f.seek({offset})
    data = f.read({dl_chunk})
    print('__B64__' + base64.b64encode(data).decode('ascii') + '__B64__')
"""
            raw_dl = exec_colab(token, chunk_code)
            b64_str = raw_dl.split("__B64__")[1].split("__B64__")[0].strip()
            binary_data = base64.b64decode(b64_str)
            f_out.write(binary_data)
            offset += len(binary_data)
            pct = int(offset * 100 / total_dl)
            print(f"   Descargado bloque {b_idx} ({offset // 1048576}MB / {total_dl // 1048576}MB - {pct}%)...")
            b_idx += 1

    print(f"\n🎉 ¡VIDEO DE 16 MINUTOS COMPLETADO CON ESTILO FAZT WEB!")
    print(f"📁 Ubicación local: {dest_path}")
    print(f"⚖️ Tamaño: {os.path.getsize(dest_path)} bytes")

if __name__ == "__main__":
    main()
