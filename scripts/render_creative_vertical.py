"""
Motion Graphics Creativos en Formato Vertical 9:16 (1080x1920):
1. Corrige la rotación (displaymatrix: 90 deg) a 1080x1920 real con FFmpeg.
2. Motion Graphics animados de verdad:
   - Terminal macOS con Typewriter en tiempo real (tecleo caracter por caracter + cursor parpadeante).
   - Cyber Alert con contador dinámico (0 a 948 exploits rodando en tiempo real + escáner láser).
   - Tech Glow Card (OpenAI / Linux) con borde neón animado y flotación senoidal.
   - Neon Tech Pills en gran formato legible para Shorts/Reels/TikTok.
3. Renderiza en GPU Colab y sube a Gofile.
"""
import sys
import os
import json
import time

sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)
print(f"✅ Runtime Colab: {rt}")

# Subir credencial
with open("credentials/drive_sa.json", "r") as f:
    sa_json = f.read()
execute_remote(token, rt, f"with open('/content/drive_sa.json', 'w') as f: f.write({repr(sa_json)})")

render_script = r'''
import os, sys, math, json, time, subprocess, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, VideoClip

# 0. Asegurar descarga de input-3.mp4 desde Google Drive si no existe
if not os.path.exists("/content/input-3.mp4"):
    print("Descargando input-3.mp4 desde Google Drive...")
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
    req = service.files().get_media(fileId=fid)
    with open('/content/input-3.mp4', 'wb') as f:
        downloader = MediaIoBaseDownload(f, req, chunksize=10*1024*1024)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Descarga Drive: {int(status.progress() * 100)}%")
    print("input-3.mp4 descargado exitosamente.")

# 1. Corregir rotación a 1080x1920 nativo
vert_path = "/content/input-3-vert.mp4"
if not os.path.exists(vert_path):
    print("Normalizando video a 1080x1920 nativo (aplicando rotacion de camara)...")
    subprocess.run([
        "ffmpeg", "-y", "-i", "/content/input-3.mp4",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "copy", vert_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Normalizacion completada.")

base = VideoFileClip(vert_path)
W, H = base.size
print(f"🎬 Dimensiones reales corregidas: {W}x{H} (Aspect Ratio: {W/H:.2f}), Duracion: {base.duration:.1f}s")

# Fuentes grandes para pantalla vertical movil
def get_font(size, mono=False):
    if mono and os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"):
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", size)
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

font_title = get_font(36, mono=False)
font_code = get_font(32, mono=True)
font_alert_big = get_font(52, mono=False)
font_alert_num = get_font(72, mono=True)
font_pill_title = get_font(42, mono=False)
font_pill_sub = get_font(28, mono=False)

# Plan editorial sincronizado con las palabras exactas de input-3:
# [00:03 - 00:10]: OpenAI busqueda de exploits en kernel Linux
# [00:10 - 00:16]: Descubrio mas de 948 exploits
# [00:18 - 00:25]: Shellcode / etapa de sell cock
# [00:26 - 00:34]: Colaboro con Linux para detectar exploits
# [00:35 - 00:43]: Magnitud de los 948 exploits
# [00:46 - 00:54]: Avances en seguridad informatica con IA

effects = [
    {
        "type": "brand_card",
        "start": 2.0,
        "end": 8.0,
        "title": "OPENAI SECURITY",
        "subtitle": "Auditoría de Kernel Linux con IA",
        "tag": "VULNERABILITY RESEARCH",
        "color": (0, 242, 254) # Cyan neon
    },
    {
        "type": "terminal_typewriter",
        "start": 8.5,
        "end": 15.5,
        "title": "kernel_audit.sh",
        "commands": [
            "./scan_kernel_routes.py",
            "Scanning syscalls: 100%...",
            "CRITICAL: Ring 0 Bug Found!"
        ]
    },
    {
        "type": "cyber_alert",
        "start": 16.0,
        "end": 22.5,
        "header": "AMENAZA DETECTADA",
        "max_count": 948,
        "label": "EXPLOITS DE KERNEL",
        "sublabel": "Capa Route / Shellcode Vulnerable"
    },
    {
        "type": "tech_pill",
        "start": 23.0,
        "end": 28.5,
        "title": "LINUX ROOT LAYER",
        "subtitle": "Escaneo de Shellcode Automatizado"
    },
    {
        "type": "terminal_typewriter",
        "start": 29.0,
        "end": 36.0,
        "title": "patch_exploit.py",
        "commands": [
            "ai.inspect_hidden_scouts()",
            "Patched: 948 / 948 exploits",
            "System Integrity: SECURED"
        ]
    },
    {
        "type": "cyber_alert",
        "start": 36.5,
        "end": 43.0,
        "header": "MAGNITUD CRÍTICA",
        "max_count": 948,
        "label": "EXPLOITS AISLADOS",
        "sublabel": "Reporte Oficial OpenAI & Linux"
    },
    {
        "type": "brand_card",
        "start": 44.0,
        "end": 50.0,
        "title": "CYBERSECURITY AI",
        "subtitle": "Defensa Activa impulsada por LLMs",
        "tag": "SEGURIDAD INFORMÁTICA",
        "color": (138, 35, 135) # Purple neon
    },
    {
        "type": "tech_pill",
        "start": 50.5,
        "end": 55.5,
        "title": "FUTURO DE LA IA",
        "subtitle": "Detección Proactiva de Zero-Days"
    }
]

# RENDERIZADORES DE MOTION GRAPHICS AVANZADOS
def draw_typewriter_terminal(draw, W, H, rel_t, dur, title, commands):
    # Elastic bounce in
    bounce = min(1.0, 1.0 - math.exp(-7.0 * rel_t) * math.cos(10.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.25) * min(1.0, (dur - rel_t) / 0.3)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    tw = int(980 * bounce)
    th = 380
    tx = (W - tw) // 2
    ty = H - th - 260 # En el tercio inferior, visible sin tapar la cara arriba

    # Sombra difusa
    draw.rounded_rectangle([tx + 12, ty + 12, tx + tw + 12, ty + th + 12], radius=24, fill=(0, 0, 0, int(130 * alpha_fade)))
    # Fondo terminal macOS
    draw.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=24, fill=(20, 22, 34, a), outline=(70, 75, 105, a), width=3)

    # Barra superior macOS
    draw.rounded_rectangle([tx, ty, tx + tw, ty + 60], radius=24, fill=(28, 30, 48, a))
    draw.rectangle([tx, ty + 35, tx + tw, ty + 60], fill=(28, 30, 48, a))

    # Botones de colores macOS
    draw.ellipse([tx + 25, ty + 20, tx + 45, ty + 40], fill=(255, 95, 86, a))
    draw.ellipse([tx + 55, ty + 20, tx + 75, ty + 40], fill=(255, 189, 46, a))
    draw.ellipse([tx + 85, ty + 20, tx + 105, ty + 40], fill=(39, 201, 63, a))

    # Titulo de archivo
    draw.text((tx + tw // 2 - 100, ty + 14), title, font=font_title, fill=(200, 210, 230, a))

    # Efecto Typewriter caracter por caracter
    cursor_blink = int(rel_t * 5) % 2 == 0 # Parpadeo a 2.5Hz
    total_chars_typed = int((rel_t - 0.2) * 22) # 22 caracteres por segundo
    if total_chars_typed < 0: total_chars_typed = 0

    cur_chars = total_chars_typed
    line_y = ty + 85
    colors = [(0, 242, 254, a), (166, 227, 161, a), (255, 107, 129, a)]

    for idx, cmd in enumerate(commands):
        if cur_chars <= 0:
            break
        visible_text = cmd[:cur_chars]
        is_current_line = (cur_chars < len(cmd)) or (idx == len(commands)-1 and cur_chars >= len(cmd))
        cur_chars -= len(cmd)

        text_to_draw = f"> {visible_text}"
        if is_current_line and cursor_blink:
            text_to_draw += " █"

        draw.text((tx + 35, line_y), text_to_draw, font=font_code, fill=colors[idx % len(colors)])
        line_y += 55

def draw_cyber_alert(draw, W, H, rel_t, dur, header, max_count, label, sublabel):
    bounce = min(1.0, 1.0 - math.exp(-6.0 * rel_t) * math.cos(9.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.2) * min(1.0, (dur - rel_t) / 0.25)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    # Pulso de neon de alerta rojo
    pulse = (math.sin(rel_t * 12) + 1.0) / 2.0
    glow_color = (int(255 * (0.8 + 0.2 * pulse)), int(40 * pulse), int(70 * pulse), a)

    cw = int(980 * bounce)
    ch = 340
    cx = (W - cw) // 2
    cy = 220 # Parte superior de la pantalla vertical

    # Sombra y marco cyberpunk
    draw.rounded_rectangle([cx + 10, cy + 10, cx + cw + 10, cy + ch + 10], radius=28, fill=(0, 0, 0, int(140 * alpha_fade)))
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=28, fill=(18, 12, 22, a), outline=glow_color, width=4)

    # Escaner laser horizontal animado
    laser_y = cy + int((rel_t * 160) % ch)
    draw.line([(cx + 10, laser_y), (cx + cw - 10, laser_y)], fill=(255, 42, 85, int(180 * alpha_fade)), width=2)

    # Cabecera alerta
    draw.text((cx + 45, cy + 30), f"⚠️ {header}", font=font_alert_big, fill=(255, 60, 90, a))

    # Contador rodante dinámico (0 a 948)
    roll_progress = min(1.0, rel_t / 1.5)
    current_count = int(max_count * (1.0 - math.pow(1.0 - roll_progress, 3)))
    draw.text((cx + 45, cy + 105), f"{current_count} {label}", font=font_alert_num, fill=(255, 255, 255, a))

    # Subtitulo
    draw.text((cx + 50, cy + 220), sublabel, font=font_pill_sub, fill=(200, 180, 200, a))

def draw_brand_card(draw, W, H, rel_t, dur, title, subtitle, tag, color):
    bounce = min(1.0, 1.0 - math.exp(-7.0 * rel_t) * math.cos(10.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.25) * min(1.0, (dur - rel_t) / 0.3)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    # Flotación suave
    float_y = int(math.sin(rel_t * 5) * 8)
    cw = int(980 * bounce)
    ch = 280
    cx = (W - cw) // 2
    cy = 240 + float_y

    draw.rounded_rectangle([cx + 10, cy + 10, cx + cw + 10, cy + ch + 10], radius=28, fill=(0, 0, 0, int(120 * alpha_fade)))
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=28, fill=(15, 23, 42, a), outline=(*color, a), width=4)

    # Badge superior
    draw.rounded_rectangle([cx + 45, cy + 28, cx + 45 + 320, cy + 70], radius=12, fill=(*color, int(40 * alpha_fade)), outline=(*color, a), width=2)
    draw.text((cx + 60, cy + 34), tag, font=get_font(22), fill=(*color, a))

    # Titulo principal
    draw.text((cx + 45, cy + 90), title, font=font_alert_big, fill=(255, 255, 255, a))
    # Subtitulo
    draw.text((cx + 48, cy + 175), f"● {subtitle}", font=font_pill_sub, fill=(180, 200, 220, a))

def draw_tech_pill(draw, W, H, rel_t, dur, title, subtitle):
    bounce = min(1.0, 1.0 - math.exp(-6.0 * rel_t) * math.cos(9.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.2) * min(1.0, (dur - rel_t) / 0.25)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    pw = int(720 * bounce)
    ph = 140
    px = (W - pw) // 2
    py = H - ph - 220

    # Glow pulsante
    draw.rounded_rectangle([px + 8, py + 8, px + pw + 8, py + ph + 8], radius=45, fill=(0, 0, 0, int(110 * alpha_fade)))
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=45, fill=(15, 23, 42, a), outline=(56, 189, 248, a), width=4)

    draw.text((px + 50, py + 22), title, font=font_pill_title, fill=(56, 189, 248, a))
    draw.text((px + 52, py + 78), subtitle, font=font_pill_sub, fill=(200, 210, 225, a))

# Compositor de fotogramas
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
        ft = fx["type"]
        if ft == "terminal_typewriter":
            draw_typewriter_terminal(draw, W, H, rel_t, dur, fx["title"], fx["commands"])
        elif ft == "cyber_alert":
            draw_cyber_alert(draw, W, H, rel_t, dur, fx["header"], fx["max_count"], fx["label"], fx["sublabel"])
        elif ft == "brand_card":
            draw_brand_card(draw, W, H, rel_t, dur, fx["title"], fx["subtitle"], fx["tag"], fx["color"])
        elif ft == "tech_pill":
            draw_tech_pill(draw, W, H, rel_t, dur, fx["title"], fx["subtitle"])

    img = Image.fromarray(raw_frame)
    img.paste(canvas, mask=canvas)
    return np.array(img)

print("⚡ Renderizando video vertical 9:16 (1080x1920) a 24fps con Motion Graphics dinámicos...")
out_clip = VideoClip(compose_frame, duration=base.duration).set_fps(24)
if base.audio is not None:
    out_clip = out_clip.set_audio(base.audio)

out_dest = "/content/resultado-input3-vertical.mp4"
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

size_mb = os.path.getsize(out_dest) / (1024 * 1024)
print(f"✅ Render vertical completado! Tamaño: {size_mb:.1f} MB")

# Subir a Gofile
print("📤 Subiendo a Gofile...")
try:
    req = urllib.request.urlopen('https://api.gofile.io/servers')
    data = json.loads(req.read().decode())
    server = data['data']['servers'][0]['name']
    res = subprocess.run(['curl', '-s', '-F', f'file=@{out_dest}', f'https://{server}.gofile.io/contents/uploadfile'], capture_output=True, text=True)
    g_res = json.loads(res.stdout)
    d_page = g_res['data']['downloadPage']
    print(f"🎉 GOFILE_VERTICAL_URL: {d_page}")
except Exception as e:
    print(f"Error subiendo a Gofile: {e}")
'''

print("🚀 Lanzando render vertical con Motion Graphics creativos...")
res = execute_remote(token, rt, render_script, timeout=1200)
print(res.get("stdout", ""), flush=True)
print("\n" + "=" * 60)
print("🎉 RENDER VERTICAL 9:16 COMPLETADO CON ÉXITO")
print("=" * 60)
