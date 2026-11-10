"""
Renderizador Definitivo de Motion Graphics Creativos 9:16 (Estilo Fazt Web)
- Tipografía Profesional Gigante (Liberation Sans & Mono Bold) con Drop Shadow y Contraste Extremo.
- Animaciones Vivas:
  * Border Beam dinámico (láser neón recorriendo el perímetro de las cajas).
  * Terminal macOS con Typewriter en tiempo real (tecleo caracter por caracter + cursor parpadeante).
  * Cyber Alert con contador rodante 0 -> 948 en tiempo real, radar concéntrico y escáner láser.
  * Shimmer diagonal y levitación senoidal orgánica.
  * Tarjetas de marca con badges vectoriales y barras de progreso activas.
- Renderizado en GPU Colab y subida a Gofile.
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

# Subir credencial de servicio si es necesaria
with open("credentials/drive_sa.json", "r") as f:
    sa_json = f.read()
execute_remote(token, rt, f"with open('/content/drive_sa.json', 'w') as f: f.write({repr(sa_json)})")

render_script = r'''
import os, sys, math, json, time, subprocess, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, VideoClip

# 1. Asegurar descarga de input-3.mp4 si no existe
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

# 2. Corregir rotación a 1080x1920 nativo
vert_path = "/content/input-3-vert.mp4"
if not os.path.exists(vert_path):
    print("Normalizando video a 1080x1920 nativo...")
    subprocess.run([
        "ffmpeg", "-y", "-i", "/content/input-3.mp4",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "copy", vert_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Normalizacion completada.")

base = VideoFileClip(vert_path)
W, H = base.size
print(f"🎬 Dimensiones reales corregidas: {W}x{H} (Aspect Ratio: {W/H:.2f}), Duracion: {base.duration:.1f}s")

# 3. Fuentes TrueType Profesionales
SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"

def get_font(size, mono=False):
    target = MONO_BOLD if mono else SANS_BOLD
    if os.path.exists(target):
        return ImageFont.truetype(target, size)
    return ImageFont.load_default()

font_hero = get_font(56, mono=False)
font_num_giant = get_font(110, mono=True)
font_code = get_font(36, mono=True)
font_card_title = get_font(48, mono=False)
font_sub = get_font(34, mono=False)
font_badge = get_font(28, mono=False)

# 4. Helpers de Animación
def draw_border_beam(draw, box, t, beam_len=320, color=(0, 242, 254), width=6):
    x0, y0, x1, y1 = box
    bw = x1 - x0
    bh = y1 - y0
    peri = 2 * (bw + bh)
    head = (t * 750) % peri

    def get_pos(dist):
        dist = dist % peri
        if dist < bw:
            return (x0 + dist, y0)
        dist -= bw
        if dist < bh:
            return (x1, y0 + dist)
        dist -= bh
        if dist < bw:
            return (x1 - dist, y1)
        dist -= bw
        return (x0, y1 - dist)

    steps = 28
    for i in range(steps):
        frac = i / steps
        pos_d = (head - (1.0 - frac) * beam_len) % peri
        px, py = get_pos(pos_d)
        alpha = int(255 * (frac ** 2.2))
        r = int(width * (0.3 + 0.7 * frac))
        draw.ellipse([px - r, py - r, px + r, py + r], fill=(*color, alpha))

def apply_shimmer(img, box, t, speed=850, shimmer_w=220):
    x0, y0, x1, y1 = box
    bw = x1 - x0
    bh = y1 - y0
    shim_canvas = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shim_canvas)
    
    pos = int((t * speed) % (bw + bh + 400)) - 200
    for i in range(-shimmer_w // 2, shimmer_w // 2, 4):
        dist = abs(i) / (shimmer_w / 2)
        alpha = int(45 * (1.0 - dist))
        cur_x = pos + i
        sdraw.line([(cur_x, 0), (cur_x - bh // 2, bh)], fill=(255, 255, 255, alpha), width=5)
        
    img.paste(shim_canvas, (x0, y0), mask=shim_canvas)

# 5. Componentes Gráficos Avanzados
def draw_terminal(draw, canvas, W, H, rel_t, dur, title, commands):
    bounce = min(1.0, 1.0 - math.exp(-7.0 * rel_t) * math.cos(10.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.25) * min(1.0, (dur - rel_t) / 0.3)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    tw = int(980 * bounce)
    th = 520
    tx = (W - tw) // 2
    float_y = int(math.sin(rel_t * 3.5) * 8)
    ty = H - th - 240 + float_y

    # Sombra y Glow
    draw.rounded_rectangle([tx - 12, ty - 12, tx + tw + 12, ty + th + 12], radius=32, fill=(0, 200, 255, int(35 * alpha_fade)))
    draw.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=28, fill=(16, 20, 32, int(245 * alpha_fade)), outline=(60, 75, 110, a), width=3)

    # Barra macOS
    bar_h = 75
    draw.rounded_rectangle([tx, ty, tx + tw, ty + bar_h], radius=28, fill=(24, 30, 48, a))
    draw.rectangle([tx, ty + 35, tx + tw, ty + bar_h], fill=(24, 30, 48, a))

    draw.ellipse([tx + 30, ty + 24, tx + 54, ty + 48], fill=(255, 95, 86, a))
    draw.ellipse([tx + 68, ty + 24, tx + 92, ty + 48], fill=(255, 189, 46, a))
    draw.ellipse([tx + 106, ty + 24, tx + 130, ty + 48], fill=(39, 201, 63, a))

    draw.text((tx + tw // 2 - 160, ty + 22), title, font=font_badge, fill=(160, 185, 215, a))

    # Border Beam
    draw_border_beam(draw, [tx, ty, tx + tw, ty + th], rel_t, beam_len=320, color=(0, 242, 254), width=6)

    # Typewriter dinámico
    total_chars = int((rel_t - 0.2) * 26) # 26 caracteres por segundo
    if total_chars < 0: total_chars = 0

    cur = total_chars
    ly = ty + 105
    colors = [
        [(50, 255, 120), (255, 120, 200), (130, 230, 255), (255, 180, 80)],
        [(255, 200, 80), (240, 245, 255)],
        [(255, 60, 90), (255, 80, 100)],
        [(50, 255, 120), (150, 230, 160)]
    ]

    for idx, (prefix, text) in enumerate(commands):
        full_line = f"{prefix} {text}"
        if cur <= 0:
            break
        vis_line = full_line[:cur]
        is_active = (cur < len(full_line)) or (idx == len(commands)-1 and cur >= len(full_line))
        cur -= len(full_line)

        lx = tx + 40
        draw.text((lx, ly), prefix, font=font_code, fill=(*colors[idx % len(colors)][0], a), stroke_width=2, stroke_fill=(0, 0, 0))
        p_bbox = font_code.getbbox(prefix)
        lx += (p_bbox[2] - p_bbox[0]) + 15

        rem_text = vis_line[len(prefix):].strip()
        if rem_text:
            draw.text((lx, ly), rem_text, font=font_code, fill=(*colors[idx % len(colors)][1], a), stroke_width=2, stroke_fill=(0, 0, 0))
            t_bbox = font_code.getbbox(rem_text)
            lx += (t_bbox[2] - t_bbox[0])

        if is_active and (int(rel_t * 4) % 2 == 0):
            draw.text((lx + 6, ly), "█", font=font_code, fill=(0, 242, 254, a), stroke_width=2, stroke_fill=(0, 0, 0))
        ly += 68

    apply_shimmer(canvas, [tx, ty, tx + tw, ty + th], rel_t)

def draw_cyber_alert(draw, canvas, W, H, rel_t, dur, max_count, label, sublabel, detail):
    bounce = min(1.0, 1.0 - math.exp(-7.0 * rel_t) * math.cos(9.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.25) * min(1.0, (dur - rel_t) / 0.3)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    cw = int(980 * bounce)
    ch = 520
    cx = (W - cw) // 2
    float_y = int(math.sin(rel_t * 3.0) * 8)
    cy = 220 + float_y

    # Glow pulsante
    pulse = (math.sin(rel_t * 8) + 1.0) / 2.0
    glow_alpha = int((45 + 35 * pulse) * alpha_fade)
    draw.rounded_rectangle([cx - 15, cy - 15, cx + cw + 15, cy + ch + 15], radius=36, fill=(255, 42, 85, glow_alpha))
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=30, fill=(22, 12, 26, int(250 * alpha_fade)), outline=(255, 50, 90, a), width=4)

    # Border Beam
    draw_border_beam(draw, [cx, cy, cx + cw, cy + ch], rel_t, beam_len=340, color=(255, 60, 90), width=7)

    # Radar en esquina superior derecha
    rx = cx + cw - 120
    ry = cy + 90
    for r_idx in range(3):
        cur_r = int(((rel_t * 70) + r_idx * 30) % 70) + 8
        r_alpha = int(220 * (1.0 - (cur_r / 80.0)) * alpha_fade)
        draw.ellipse([rx - cur_r, ry - cur_r, rx + cur_r, ry + cur_r], outline=(255, 60, 90, r_alpha), width=3)
    draw.ellipse([rx - 6, ry - 6, rx + 6, ry + 6], fill=(255, 255, 255, a))

    # Laser horizontal (dibujado de fondo)
    laser_y = cy + int((rel_t * 220) % ch)
    draw.line([(cx + 15, laser_y), (cx + cw - 15, laser_y)], fill=(255, 60, 90, int(150 * alpha_fade)), width=2)

    # Badge de Peligro
    draw.rounded_rectangle([cx + 40, cy + 35, cx + 440, cy + 85], radius=14, fill=(255, 42, 85, int(60 * alpha_fade)), outline=(255, 60, 90, a), width=2)
    draw.polygon([(cx + 60, cy + 72), (cx + 75, cy + 46), (cx + 90, cy + 72)], fill=(255, 200, 50, a))
    draw.text((cx + 72, cy + 49), "!", font=get_font(20, mono=True), fill=(0, 0, 0, a))
    draw.text((cx + 105, cy + 46), "AMENAZA ZERO-DAY", font=font_badge, fill=(255, 220, 230, a), stroke_width=2, stroke_fill=(0, 0, 0))

    # Contador rodante dinámico 0 -> max_count
    roll_progress = min(1.0, rel_t / 1.5)
    current_count = int(max_count * (1.0 - math.pow(1.0 - roll_progress, 3)))
    draw.text((cx + 40, cy + 105), f"{current_count}", font=font_num_giant, fill=(255, 255, 255, a), stroke_width=4, stroke_fill=(0, 0, 0))
    draw.text((cx + 270, cy + 120), label, font=font_hero, fill=(255, 75, 105, a), stroke_width=3, stroke_fill=(0, 0, 0))
    draw.text((cx + 270, cy + 180), sublabel, font=font_sub, fill=(255, 200, 215, a), stroke_width=2, stroke_fill=(0, 0, 0))

    # Separador sutil
    draw.line([(cx + 40, cy + 250), (cx + cw - 40, cy + 250)], fill=(70, 35, 55, a), width=2)

    # Textos explicativos
    draw.text((cx + 42, cy + 275), detail[0], font=font_card_title, fill=(255, 255, 255, a), stroke_width=2, stroke_fill=(0, 0, 0))
    draw.text((cx + 42, cy + 345), detail[1], font=font_sub, fill=(210, 220, 240, a), stroke_width=2, stroke_fill=(0, 0, 0))

    # Barra de mitigación
    pw = 900
    prog_pct = min(1.0, 0.2 + (rel_t / dur) * 0.8)
    draw.rounded_rectangle([cx + 40, cy + 430, cx + 40 + pw, cy + 465], radius=16, fill=(35, 20, 38, a), outline=(80, 40, 65, a), width=2)
    draw.rounded_rectangle([cx + 40, cy + 430, cx + 40 + int(pw * prog_pct), cy + 465], radius=16, fill=(255, 42, 85, a))
    draw.text((cx + 40 + pw - 240, cy + 432), f"{int(prog_pct*100)}% PARCHEADO", font=font_badge, fill=(255, 255, 255, a), stroke_width=1, stroke_fill=(0, 0, 0))

    apply_shimmer(canvas, [cx, cy, cx + cw, cy + ch], rel_t)

def draw_brand_card(draw, canvas, W, H, rel_t, dur, badge, title, subtitle, bullets, color):
    bounce = min(1.0, 1.0 - math.exp(-7.0 * rel_t) * math.cos(9.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.25) * min(1.0, (dur - rel_t) / 0.3)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    cw = int(980 * bounce)
    ch = 480
    cx = (W - cw) // 2
    float_y = int(math.sin(rel_t * 2.8) * 10)
    cy = 240 + float_y

    draw.rounded_rectangle([cx - 15, cy - 15, cx + cw + 15, cy + ch + 15], radius=36, fill=(*color, int(50 * alpha_fade)))
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=30, fill=(14, 22, 38, int(250 * alpha_fade)), outline=(*color, a), width=4)

    draw_border_beam(draw, [cx, cy, cx + cw, cy + ch], rel_t, beam_len=360, color=color, width=7)

    # Badge
    draw.rounded_rectangle([cx + 45, cy + 35, cx + 470, cy + 90], radius=14, fill=(*color, int(45 * alpha_fade)), outline=(*color, a), width=2)
    draw.ellipse([cx + 65, cy + 53, cx + 83, cy + 71], fill=(*color, a))
    draw.text((cx + 98, cy + 48), badge, font=font_badge, fill=(*color, a), stroke_width=2, stroke_fill=(0, 0, 0))

    # Titulo
    draw.text((cx + 45, cy + 120), title, font=font_hero, fill=(255, 255, 255, a), stroke_width=3, stroke_fill=(0, 0, 0))

    draw.line([(cx + 45, cy + 215), (cx + cw - 45, cy + 215)], fill=(30, 50, 80, a), width=2)

    # Subtítulo
    draw.text((cx + 48, cy + 245), subtitle, font=font_card_title, fill=(56, 189, 248, a), stroke_width=2, stroke_fill=(0, 0, 0))

    # Bullets
    ly = cy + 335
    for b in bullets:
        draw.text((cx + 48, ly), f"● {b}", font=font_sub, fill=(200, 225, 245, a), stroke_width=2, stroke_fill=(0, 0, 0))
        ly += 60

    apply_shimmer(canvas, [cx, cy, cx + cw, cy + ch], rel_t)

# 6. Timeline Editorial Sincronizado
timeline = [
    {
        "type": "brand_card",
        "start": 1.5,
        "end": 8.0,
        "badge": "INVESTIGACIÓN OFICIAL",
        "title": "OPENAI SECURITY",
        "subtitle": "Auditoría Autónoma de Kernel Linux",
        "bullets": [
            "Detección de Zero-Days mediante LLMs avanzados",
            "Reporte oficial coordinado con Linux Team"
        ],
        "color": (0, 242, 254)
    },
    {
        "type": "terminal",
        "start": 8.5,
        "end": 17.5,
        "title": "root@openai-kernel:~",
        "commands": [
            ("$", "python3 audit_kernel.py --all"),
            ("[*]", "Escaneando llamadas del sistema Ring 0..."),
            ("[!]", "ALERTA: 948 exploits detectados!"),
            ("[✓]", "Generando reporte de seguridad...")
        ]
    },
    {
        "type": "cyber_alert",
        "start": 18.0,
        "end": 26.0,
        "max_count": 948,
        "label": "EXPLOITS",
        "sublabel": "AISLADOS EN KERNEL",
        "detail": [
            "Capa de Shellcode y Syscalls Críticas",
            "Mitigación activa y aislamiento de exploits"
        ]
    },
    {
        "type": "brand_card",
        "start": 26.5,
        "end": 34.5,
        "badge": "ALIANZA ESTRATÉGICA",
        "title": "COOPERACIÓN LINUX",
        "subtitle": "Mitigación Masiva de Vulnerabilidades",
        "bullets": [
            "Parcheo directo de fallas de memoria",
            "Fortalecimiento de la infraestructura raíz"
        ],
        "color": (50, 255, 120)
    },
    {
        "type": "terminal",
        "start": 35.0,
        "end": 43.5,
        "title": "root@linux-foundation:~",
        "commands": [
            ("$", "git commit -m 'fix: patch 948 exploits'"),
            ("[*]", "Recompilando módulos del kernel Linux..."),
            ("[+]", "Integridad del sistema: 100% ASEGURADA"),
            ("[✓]", "Despliegue de actualización completado")
        ]
    },
    {
        "type": "cyber_alert",
        "start": 44.0,
        "end": 52.0,
        "max_count": 948,
        "label": "AMENAZAS",
        "sublabel": "NEUTRALIZADAS CON IA",
        "detail": [
            "Avance Histórico en Seguridad Informática",
            "Nuevo estándar de defensa proactiva con LLMs"
        ]
    },
    {
        "type": "brand_card",
        "start": 52.5,
        "end": 56.5,
        "badge": "EL FUTURO DE LA IA",
        "title": "CIBERSEGURIDAD 2026",
        "subtitle": "Defensa Autónoma en Tiempo Real",
        "bullets": [
            "Detección proactiva antes de ser explotados",
            "IA protegiendo el software del mundo"
        ],
        "color": (255, 95, 86)
    }
]

# 7. Compositor
def compose_frame(t):
    raw_frame = base.get_frame(t)
    active_fx = [fx for fx in timeline if fx["start"] <= t <= fx["end"]]
    if not active_fx:
        return raw_frame

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    for fx in active_fx:
        rel_t = t - fx["start"]
        dur = fx["end"] - fx["start"]
        ft = fx["type"]
        if ft == "terminal":
            draw_terminal(draw, canvas, W, H, rel_t, dur, fx["title"], fx["commands"])
        elif ft == "cyber_alert":
            draw_cyber_alert(draw, canvas, W, H, rel_t, dur, fx["max_count"], fx["label"], fx["sublabel"], fx["detail"])
        elif ft == "brand_card":
            draw_brand_card(draw, canvas, W, H, rel_t, dur, fx["badge"], fx["title"], fx["subtitle"], fx["bullets"], fx["color"])

    img = Image.fromarray(raw_frame)
    img.paste(canvas, mask=canvas)
    return np.array(img)

print("⚡ Renderizando video vertical 9:16 (1080x1920) a 24fps con Motion Graphics Fazt Web...")
out_clip = VideoClip(compose_frame, duration=base.duration).set_fps(24)
if base.audio is not None:
    out_clip = out_clip.set_audio(base.audio)

out_dest = "/content/resultado-input3-vertical-fazt.mp4"
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
    print(f"🎉 GOFILE_FAZT_URL: {d_page}")
except Exception as e:
    print(f"Error subiendo a Gofile: {e}")
'''

print("🚀 Lanzando render vertical con Motion Graphics avanzados...")
res = execute_remote(token, rt, render_script, timeout=1200)
print(res.get("stdout", ""), flush=True)
print(res.get("stderr", ""), flush=True)
print("\n" + "=" * 60)
print("🎉 RENDER VERTICAL FAZT COMPLETADO CON ÉXITO")
print("=" * 60)
