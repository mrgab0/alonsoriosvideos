"""
Motor CLI de Renderizado Hyperframes
Perfil: IAshorts (Vertical 9:16)
- Contenedores rectangulares verticales grandes: 880x1450 (100px laterales).
- Delimitación estricta de márgenes y ajuste de línea (Word Wrap) automático.
- Cero texto desbordado fuera de las cajas.
- Tipografía proporcional escalada con drop-shadow y contraste.
- Fondo Bokeh Blur continuo + viaje espacial cinemático.
- Lead-in de 1 segundo sincronizado con la voz.

Uso:
  python scripts/render_cli.py --input input-3.mp4 --profile IAshorts
  O simplemente:
  render.bat input-3.mp4 IAshorts
"""
import sys
import os
import json
import argparse
import time

sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

def load_profile(profile_name):
    profile_path = os.path.join("profiles", f"{profile_name}.json")
    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Perfil '{profile_name}' no encontrado en {profile_path}")
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_render(video_filename, profile_name="IAshorts"):
    print("=" * 65)
    print(f"🎬 HYPERFRAMES RENDER ENGINE | Perfil: [{profile_name}]")
    print(f"📁 Video objetivo: {video_filename}")
    print("=" * 65)

    profile = load_profile(profile_name)
    token = get_token()
    rt = ensure_active_runtime(token)
    print(f"✅ Runtime Colab: {rt}")

    with open("credentials/drive_sa.json", "r") as f:
        sa_json = f.read()
    execute_remote(token, rt, f"with open('/content/drive_sa.json', 'w') as f: f.write({repr(sa_json)})")

    colab_script = r'''
import os, sys, math, json, time, subprocess, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import VideoFileClip, VideoClip

video_name = "__VIDEO_NAME__"
src_path = f"/content/{video_name}"

# 1. Asegurar descarga desde Google Drive si falta
if not os.path.exists(src_path):
    print(f"Descargando {video_name} desde Google Drive...")
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    creds = service_account.Credentials.from_service_account_file(
        '/content/drive_sa.json',
        scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=creds)
    files = service.files().list(
        q=f"name = '{video_name}' and trashed = false",
        fields="files(id, name, size)"
    ).execute().get('files', [])
    if not files:
        raise RuntimeError(f"{video_name} no encontrado en Drive!")
    fid = files[0]['id']
    req = service.files().get_media(fileId=fid)
    with open(src_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, req, chunksize=10*1024*1024)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    print("Video descargado exitosamente.")

# 2. Corregir rotación a 1080x1920 nativo
vert_path = "/content/input-normalized.mp4"
if not os.path.exists(vert_path):
    print("Normalizando video a 1080x1920 nativo con FFmpeg...")
    subprocess.run([
        "ffmpeg", "-y", "-i", src_path,
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "copy", vert_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

base = VideoFileClip(vert_path)
W, H = base.size
print(f"🎬 Dimensiones: {W}x{H}, Duracion: {base.duration:.1f}s")

# 3. Fuentes TrueType
SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"

def get_font(size, mono=False):
    target = MONO_BOLD if mono else SANS_BOLD
    if os.path.exists(target):
        return ImageFont.truetype(target, size)
    return ImageFont.load_default()

font_title_giant = get_font(68, mono=False)
font_num_giant = get_font(125, mono=True)
font_subtitle = get_font(42, mono=False)
font_body = get_font(34, mono=False)
font_code = get_font(32, mono=True)
font_badge = get_font(28, mono=False)
font_meta = get_font(26, mono=True)

# 4. Helper Word Wrap / Ajuste de Línea
def draw_wrapped_text(draw, text, font, x, y, max_w, line_spacing=10, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0)):
    words = text.split(" ")
    lines = []
    cur_line = []
    for w in words:
        test = " ".join(cur_line + [w])
        bbox = font.getbbox(test)
        if (bbox[2] - bbox[0]) <= max_w:
            cur_line.append(w)
        else:
            if cur_line:
                lines.append(" ".join(cur_line))
            cur_line = [w]
    if cur_line:
        lines.append(" ".join(cur_line))

    cur_y = y
    for line in lines:
        draw.text((x, cur_y), line, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
        bbox = font.getbbox(line)
        cur_y += (bbox[3] - bbox[1]) + line_spacing
    return cur_y

def draw_border_beam(draw, box, t, beam_len=450, color=(0, 242, 254), width=7):
    x0, y0, x1, y1 = box
    bw = x1 - x0
    bh = y1 - y0
    peri = 2 * (bw + bh)
    head = (t * 850) % peri

    def get_pos(dist):
        dist = dist % peri
        if dist < bw: return (x0 + dist, y0)
        dist -= bw
        if dist < bh: return (x1, y0 + dist)
        dist -= bw
        if dist < bw: return (x1 - dist, y1)
        dist -= bw
        return (x0, y1 - dist)

    for i in range(32):
        frac = i / 32
        pos_d = (head - (1.0 - frac) * beam_len) % peri
        px, py = get_pos(pos_d)
        alpha = int(255 * (frac ** 2.2))
        r = int(width * (0.3 + 0.7 * frac))
        draw.ellipse([px - r, py - r, px + r, py + r], fill=(*color, alpha))

def apply_shimmer(img, box, t, speed=850, shimmer_w=240):
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    shim = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shim)
    pos = int((t * speed) % (bw + bh + 400)) - 200
    for i in range(-shimmer_w // 2, shimmer_w // 2, 4):
        dist = abs(i) / (shimmer_w / 2)
        alpha = int(40 * (1.0 - dist))
        cur_x = pos + i
        sdraw.line([(cur_x, 0), (cur_x - bh // 2, bh)], fill=(255, 255, 255, alpha), width=6)
    img.paste(shim, (x0, y0), mask=shim)

# 5. Dimensiones de Perfil IAshorts:
BASE_CW = 880
BASE_CH = 1450

def draw_brand_card_tall(draw, canvas, W, H, rel_t, dur, badge, title1, title2, subtitle, bullets, metrics, color):
    bounce = min(1.0, 1.0 - math.exp(-7.0 * rel_t) * math.cos(9.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.25) * min(1.0, (dur - rel_t) / 0.25)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    zoom = 0.96 + (rel_t / dur) * 0.07
    cw = int(BASE_CW * bounce * zoom)
    ch = int(BASE_CH * zoom)

    drift_x = int(math.sin(rel_t * 1.5) * 16)
    drift_y = int(math.cos(rel_t * 1.2) * 12)
    cx = (W - cw) // 2 + drift_x
    cy = (H - ch) // 2 + drift_y

    max_content_w = cw - 110 # Margen interno seguro

    # Sombra 3D profunda
    draw.rounded_rectangle([cx + 14, cy + 24, cx + cw + 14, cy + ch + 24], radius=38, fill=(0, 0, 0, int(160 * alpha_fade)))
    draw.rounded_rectangle([cx - 12, cy - 12, cx + cw + 12, cy + ch + 12], radius=38, fill=(*color, int(45 * alpha_fade)))
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=34, fill=(14, 22, 38, int(252 * alpha_fade)), outline=(*color, a), width=4)

    draw_border_beam(draw, [cx, cy, cx + cw, cy + ch], rel_t, beam_len=450, color=color, width=7)

    # 1. Badge superior dinámico
    b_bbox = font_badge.getbbox(badge)
    badge_w = (b_bbox[2] - b_bbox[0]) + 90
    draw.rounded_rectangle([cx + 50, cy + 45, cx + 50 + badge_w, cy + 105], radius=16, fill=(*color, int(45 * alpha_fade)), outline=(*color, a), width=2)
    draw.ellipse([cx + 70, cy + 65, cx + 90, cy + 85], fill=(*color, a))
    draw.text((cx + 105, cy + 58), badge, font=font_badge, fill=(*color, a), stroke_width=2, stroke_fill=(0, 0, 0))

    # 2. Título doble gigante
    draw.text((cx + 50, cy + 135), title1, font=font_title_giant, fill=(255, 255, 255, a), stroke_width=3, stroke_fill=(0, 0, 0))
    draw.text((cx + 50, cy + 225), title2, font=font_title_giant, fill=(*color, a), stroke_width=3, stroke_fill=(0, 0, 0))

    draw.line([(cx + 50, cy + 325), (cx + cw - 50, cy + 325)], fill=(40, 60, 95, a), width=3)

    # 3. Subtítulo con Word Wrap
    ly = draw_wrapped_text(draw, subtitle, font_subtitle, cx + 50, cy + 355, max_w=max_content_w, fill=(240, 245, 255, a))
    ly += 25

    # 4. Sección de Bullets con Word Wrap y sangría
    for b in bullets:
        draw.text((cx + 50, ly), "●", font=font_body, fill=(*color, a))
        ly = draw_wrapped_text(draw, b, font_body, cx + 80, ly, max_w=max_content_w - 35, line_spacing=10, fill=(200, 225, 245, a))
        ly += 22

    # 5. Cajas de Métricas Destacadas
    metric_y = max(ly + 20, cy + 810)
    draw.line([(cx + 50, metric_y - 30), (cx + cw - 50, metric_y - 30)], fill=(40, 60, 95, a), width=2)
    
    box_w = (cw - 130) // 2
    # Caja 1
    draw.rounded_rectangle([cx + 50, metric_y, cx + 50 + box_w, metric_y + 210], radius=20, fill=(20, 30, 52, a), outline=(*color, int(150*alpha_fade)), width=2)
    draw.text((cx + 75, metric_y + 20), metrics[0]["value"], font=font_num_giant, fill=(255, 255, 255, a), stroke_width=4, stroke_fill=(0, 0, 0))
    draw.text((cx + 75, metric_y + 155), metrics[0]["label"], font=font_meta, fill=(*color, a))

    # Caja 2
    draw.rounded_rectangle([cx + 70 + box_w, metric_y, cx + cw - 50, metric_y + 210], radius=20, fill=(20, 30, 52, a), outline=(*color, int(150*alpha_fade)), width=2)
    draw.text((cx + 95 + box_w, metric_y + 20), metrics[1]["value"], font=font_num_giant, fill=(50, 255, 120, a), stroke_width=4, stroke_fill=(0, 0, 0))
    draw.text((cx + 95 + box_w, metric_y + 155), metrics[1]["label"], font=font_meta, fill=(50, 255, 120, a))

    # 6. Status Footer Pill Centrado
    status_msg = "ESTADO: COOPERACIÓN ACTIVA EN CURSO"
    s_bbox = font_badge.getbbox(status_msg)
    s_w = s_bbox[2] - s_bbox[0]
    draw.rounded_rectangle([cx + 50, cy + ch - 110, cx + cw - 50, cy + ch - 40], radius=20, fill=(*color, int(35 * alpha_fade)), outline=(*color, a), width=2)
    draw.text((cx + (cw - s_w)//2, cy + ch - 92), status_msg, font=font_badge, fill=(255, 255, 255, a), stroke_width=2, stroke_fill=(0, 0, 0))

    apply_shimmer(canvas, [cx, cy, cx + cw, cy + ch], rel_t)

def draw_terminal_tall(draw, canvas, W, H, rel_t, dur, title, commands):
    bounce = min(1.0, 1.0 - math.exp(-7.0 * rel_t) * math.cos(9.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.25) * min(1.0, (dur - rel_t) / 0.25)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    zoom = 0.96 + (rel_t / dur) * 0.07
    cw = int(BASE_CW * bounce * zoom)
    ch = int(BASE_CH * zoom)

    drift_x = int(math.sin(rel_t * 1.5) * 16)
    drift_y = int(math.cos(rel_t * 1.2) * 12)
    cx = (W - cw) // 2 + drift_x
    cy = (H - ch) // 2 + drift_y

    draw.rounded_rectangle([cx + 14, cy + 24, cx + cw + 14, cy + ch + 24], radius=38, fill=(0, 0, 0, int(160 * alpha_fade)))
    draw.rounded_rectangle([cx - 12, cy - 12, cx + cw + 12, cy + ch + 12], radius=38, fill=(0, 242, 254, int(35 * alpha_fade)))
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=34, fill=(16, 20, 32, int(252 * alpha_fade)), outline=(60, 80, 120, a), width=4)

    # Barra macOS
    bar_h = 85
    draw.rounded_rectangle([cx, cy, cx + cw, cy + bar_h], radius=34, fill=(24, 32, 50, a))
    draw.rectangle([cx, cy + 45, cx + cw, cy + bar_h], fill=(24, 32, 50, a))

    draw.ellipse([cx + 35, cy + 28, cx + 62, cy + 55], fill=(255, 95, 86, a))
    draw.ellipse([cx + 78, cy + 28, cx + 105, cy + 55], fill=(255, 189, 46, a))
    draw.ellipse([cx + 121, cy + 28, cx + 148, cy + 55], fill=(39, 201, 63, a))

    draw.text((cx + cw // 2 - 160, cy + 26), title, font=font_badge, fill=(160, 190, 225, a))

    draw_border_beam(draw, [cx, cy, cx + cw, cy + ch], rel_t, beam_len=450, color=(0, 242, 254), width=7)

    # Typewriter
    total_chars = int((rel_t - 0.2) * 32)
    if total_chars < 0: total_chars = 0

    cur = total_chars
    ly = cy + 120
    colors = [
        [(50, 255, 120), (255, 120, 200), (130, 230, 255)],
        [(255, 200, 80), (240, 245, 255)],
        [(255, 60, 90), (255, 90, 110)],
        [(130, 230, 255), (200, 220, 255)],
        [(255, 200, 80), (255, 120, 200)],
        [(50, 255, 120), (150, 230, 160)],
        [(50, 255, 120), (255, 255, 255)]
    ]

    for idx, (num_str, prefix, text) in enumerate(commands):
        full_line = f"{prefix} {text}"
        if cur <= 0:
            break
        vis_line = full_line[:cur]
        is_active = (cur < len(full_line)) or (idx == len(commands)-1 and cur >= len(full_line))
        cur -= len(full_line)

        lx = cx + 45
        draw.text((lx, ly), num_str, font=font_code, fill=(80, 100, 130, a))
        lx += 50

        draw.text((lx, ly), prefix, font=font_code, fill=(*colors[idx % len(colors)][0], a), stroke_width=2, stroke_fill=(0, 0, 0))
        p_bbox = font_code.getbbox(prefix)
        lx += (p_bbox[2] - p_bbox[0]) + 15

        rem_text = vis_line[len(prefix):].strip()
        # Delimitar ancho de línea de código para que no desborde
        max_code_w = (cx + cw - 50) - lx
        if rem_text:
            while rem_text and (font_code.getbbox(rem_text)[2] - font_code.getbbox(rem_text)[0]) > (max_code_w - 20):
                rem_text = rem_text[:-4] + "..."
            draw.text((lx, ly), rem_text, font=font_code, fill=(*colors[idx % len(colors)][1], a), stroke_width=2, stroke_fill=(0, 0, 0))
            t_bbox = font_code.getbbox(rem_text)
            lx += (t_bbox[2] - t_bbox[0])

        if is_active and (int(rel_t * 4) % 2 == 0):
            draw.text((lx + 6, ly), "█", font=font_code, fill=(0, 242, 254, a), stroke_width=2, stroke_fill=(0, 0, 0))
        ly += 74

    # Output Pane inferior
    draw.line([(cx + 40, cy + ch - 220), (cx + cw - 40, cy + ch - 220)], fill=(40, 55, 80, a), width=2)
    draw.text((cx + 50, cy + ch - 190), "CONSOLA DE SALIDA [KERNEL MONITOR]:", font=font_meta, fill=(120, 150, 190, a))
    draw.rounded_rectangle([cx + 45, cy + ch - 150, cx + cw - 45, cy + ch - 45], radius=16, fill=(10, 14, 24, a), outline=(50, 70, 100, a), width=2)
    draw.text((cx + 70, cy + ch - 115), "[✓] 948 parches de mitigación validados y activos", font=font_body, fill=(50, 255, 120, a))

    apply_shimmer(canvas, [cx, cy, cx + cw, cy + ch], rel_t)

def draw_cyber_alert_tall(draw, canvas, W, H, rel_t, dur, max_count, label, sublabel, detail, breakdown):
    bounce = min(1.0, 1.0 - math.exp(-7.0 * rel_t) * math.cos(9.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.25) * min(1.0, (dur - rel_t) / 0.25)
    if alpha_fade <= 0: return
    a = int(255 * alpha_fade)

    zoom = 0.96 + (rel_t / dur) * 0.07
    cw = int(BASE_CW * bounce * zoom)
    ch = int(BASE_CH * zoom)

    drift_x = int(math.sin(rel_t * 1.6) * 16)
    drift_y = int(math.cos(rel_t * 1.3) * 12)
    cx = (W - cw) // 2 + drift_x
    cy = (H - ch) // 2 + drift_y

    max_content_w = cw - 110

    draw.rounded_rectangle([cx + 14, cy + 24, cx + cw + 14, cy + ch + 24], radius=38, fill=(0, 0, 0, int(160 * alpha_fade)))

    pulse = (math.sin(rel_t * 8) + 1.0) / 2.0
    glow_alpha = int((45 + 35 * pulse) * alpha_fade)
    draw.rounded_rectangle([cx - 12, cy - 12, cx + cw + 12, cy + ch + 12], radius=38, fill=(255, 42, 85, glow_alpha))
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=34, fill=(22, 12, 26, int(252 * alpha_fade)), outline=(255, 50, 90, a), width=4)

    draw_border_beam(draw, [cx, cy, cx + cw, cy + ch], rel_t, beam_len=450, color=(255, 60, 90), width=7)

    # Radar
    rx = cx + cw - 120
    ry = cy + 100
    for r_idx in range(3):
        cur_r = int(((rel_t * 70) + r_idx * 30) % 70) + 8
        r_alpha = int(220 * (1.0 - (cur_r / 80.0)) * alpha_fade)
        draw.ellipse([rx - cur_r, ry - cur_r, rx + cur_r, ry + cur_r], outline=(255, 60, 90, r_alpha), width=3)
    draw.ellipse([rx - 6, ry - 6, rx + 6, ry + 6], fill=(255, 255, 255, a))

    # Scanner bar
    laser_y = cy + int((rel_t * 220) % ch)
    draw.line([(cx + 15, laser_y), (cx + cw - 15, laser_y)], fill=(255, 60, 90, int(140 * alpha_fade)), width=2)

    # Badge delimitado
    draw.rounded_rectangle([cx + 45, cy + 45, cx + 460, cy + 105], radius=16, fill=(255, 42, 85, int(60 * alpha_fade)), outline=(255, 60, 90, a), width=2)
    draw.polygon([(cx + 65, cy + 88), (cx + 82, cy + 60), (cx + 99, cy + 88)], fill=(255, 200, 50, a))
    draw.text((cx + 80, cy + 63), "!", font=get_font(22, mono=True), fill=(0, 0, 0, a))
    draw.text((cx + 115, cy + 58), "AMENAZA ZERO-DAY", font=font_badge, fill=(255, 220, 230, a), stroke_width=2, stroke_fill=(0, 0, 0))

    # Contador gigante 125px
    roll_progress = min(1.0, rel_t / 1.5)
    current_count = int(max_count * (1.0 - math.pow(1.0 - roll_progress, 3)))
    num_str = f"{current_count}"
    draw.text((cx + 45, cy + 130), num_str, font=font_num_giant, fill=(255, 255, 255, a), stroke_width=5, stroke_fill=(0, 0, 0))
    c_bbox = font_num_giant.getbbox(num_str)
    cur_y = cy + 130 + (c_bbox[3] - c_bbox[1]) + 20
    
    # Label con Word Wrap dinámico
    cur_y = draw_wrapped_text(draw, label, font_title_giant, cx + 45, cur_y, max_w=max_content_w, fill=(255, 75, 105, a))
    cur_y += 12

    # Sublabel con Word Wrap dinámico
    cur_y = draw_wrapped_text(draw, sublabel, font_subtitle, cx + 45, cur_y, max_w=max_content_w, fill=(255, 200, 215, a))
    cur_y += 18

    draw.line([(cx + 45, cur_y), (cx + cw - 45, cur_y)], fill=(70, 35, 55, a), width=3)
    cur_y += 24

    # Desglose de vulnerabilidades
    draw.text((cx + 45, cur_y), "DISTRIBUCIÓN DE EXPLOITS POR CAPA:", font=font_meta, fill=(220, 150, 170, a))
    ly = cur_y + 45
    for name, qty in breakdown:
        draw.rounded_rectangle([cx + 45, ly, cx + cw - 45, ly + 75], radius=14, fill=(35, 18, 38, a), outline=(90, 40, 70, a), width=2)
        draw.text((cx + 70, ly + 20), name, font=font_body, fill=(240, 230, 245, a))
        num_str = str(qty)
        n_w = font_subtitle.getbbox(num_str)[2] - font_subtitle.getbbox(num_str)[0]
        draw.text((cx + cw - 80 - n_w, ly + 15), num_str, font=font_subtitle, fill=(255, 80, 110, a), stroke_width=2, stroke_fill=(0, 0, 0))
        ly += 95

    # Barra de mitigación inferior con Word Wrap
    draw.line([(cx + 45, cy + ch - 220), (cx + cw - 45, cy + ch - 220)], fill=(70, 35, 55, a), width=2)
    draw_wrapped_text(draw, detail[0], font_subtitle, cx + 45, cy + ch - 200, max_w=max_content_w, fill=(255, 255, 255, a))
    draw_wrapped_text(draw, detail[1], font_body, cx + 45, cy + ch - 145, max_w=max_content_w, fill=(210, 200, 220, a))

    pw = cw - 90
    prog_pct = min(1.0, 0.2 + (rel_t / dur) * 0.8)
    draw.rounded_rectangle([cx + 45, cy + ch - 80, cx + 45 + pw, cy + ch - 35], radius=18, fill=(35, 20, 38, a), outline=(90, 40, 70, a), width=2)
    draw.rounded_rectangle([cx + 45, cy + ch - 80, cx + 45 + int(pw * prog_pct), cy + ch - 35], radius=18, fill=(255, 42, 85, a))
    draw.text((cx + 45 + pw - 260, cy + ch - 76), f"{int(prog_pct*100)}% MITIGADO", font=font_badge, fill=(255, 255, 255, a), stroke_width=2, stroke_fill=(0, 0, 0))

    apply_shimmer(canvas, [cx, cy, cx + cw, cy + ch], rel_t)

# 6. Timeline Editorial Sincronizado (Perfil IAshorts)
timeline = [
    {
        "type": "brand_card",
        "start": 7.0,
        "end": 15.5,
        "badge": "INVESTIGACIÓN OFICIAL",
        "title1": "OPENAI",
        "title2": "SECURITY",
        "subtitle": "Auditoría Autónoma de Kernel Linux con IA",
        "bullets": [
            "Detección de Zero-Days mediante LLMs avanzados",
            "Reporte oficial coordinado con Linux Foundation",
            "Parcheo directo en módulos críticos de memoria"
        ],
        "metrics": [
            {"value": "948", "label": "VULNERABILIDADES"},
            {"value": "100%", "label": "CONFIRMADO"}
        ],
        "color": (0, 242, 254)
    },
    {
        "type": "cyber_alert",
        "start": 15.5,
        "end": 24.5,
        "max_count": 948,
        "label": "EXPLOITS DETECTADOS",
        "sublabel": "Capa Syscall y Memoria del Kernel",
        "detail": [
            "Aislamiento Preventivo Inmediato",
            "Reporte conjunto OpenAI + Linux Foundation"
        ],
        "breakdown": [
            ("Llamadas de Sistema (Syscalls)", 412),
            ("Inyección de Shellcode / Ring 0", 320),
            ("Corrupción de Memoria Zero-Day", 216)
        ]
    },
    {
        "type": "terminal",
        "start": 24.5,
        "end": 34.0,
        "title": "kernel_audit.py — root@openai",
        "commands": [
            ("1", "$", "python3 audit_kernel.py --deep"),
            ("2", "[*]", "Escaneando llamadas del sistema Ring 0..."),
            ("3", "[*]", "Inspeccionando drivers/net/tun.c..."),
            ("4", "[!]", "ALERTA: 948 exploits de Shellcode detectados!"),
            ("5", "[+]", "Generando parche criptográfico de protección..."),
            ("6", "[+]", "Recompilando módulos del kernel Linux..."),
            ("7", "[✓]", "Kernel Linux asegurado exitosamente.")
        ]
    },
    {
        "type": "brand_card",
        "start": 34.0,
        "end": 43.0,
        "badge": "ALIANZA ESTRATÉGICA",
        "title1": "COOPERACIÓN",
        "title2": "LINUX TEAM",
        "subtitle": "Mitigación Masiva de Vulnerabilidades",
        "bullets": [
            "Parcheo directo de fallas de memoria",
            "Protección de servidores a nivel mundial",
            "Nuevo estándar de cooperación abierta"
        ],
        "metrics": [
            {"value": "948", "label": "PARCHEADOS"},
            {"value": "0-DAY", "label": "NEUTRALIZADOS"}
        ],
        "color": (50, 255, 120)
    },
    {
        "type": "brand_card",
        "start": 43.0,
        "end": 51.5,
        "badge": "DEFENSA ACTIVA CON IA",
        "title1": "CIBERSEGURIDAD",
        "title2": "FUTURO 2026",
        "subtitle": "Detección Proactiva de Zero-Days",
        "bullets": [
            "Agentes autónomos protegiendo el software global",
            "Detección antes de que hackers puedan explotarlo",
            "La inteligencia artificial como escudo digital"
        ],
        "metrics": [
            {"value": "IA", "label": "DEFENSA ACTIVA"},
            {"value": "24/7", "label": "MONITOREO"}
        ],
        "color": (255, 120, 50)
    }
]

# 7. Compositor Principal
def compose_frame(t):
    raw_frame = base.get_frame(t)
    
    blur_weight = 0.0
    if 6.5 <= t <= 52.0:
        fade_in = min(1.0, (t - 6.5) / 0.5)
        fade_out = min(1.0, (52.0 - t) / 0.5)
        blur_weight = fade_in * fade_out

    active_fx = [fx for fx in timeline if fx["start"] <= t <= fx["end"]]

    raw_img = Image.fromarray(raw_frame).convert("RGBA")

    if blur_weight > 0.01:
        small = raw_img.resize((W // 4, H // 4), Image.BILINEAR)
        bokeh_img = small.resize((W, H), Image.BICUBIC)
        tint = Image.new("RGBA", (W, H), (10, 14, 26, int(135 * blur_weight)))
        bokeh_img.paste(tint, mask=tint)
        frame_canvas = Image.blend(raw_img, bokeh_img, blur_weight)
    else:
        frame_canvas = raw_img

    if not active_fx:
        return np.array(frame_canvas.convert("RGB"))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for fx in active_fx:
        rel_t = t - fx["start"]
        dur = fx["end"] - fx["start"]
        ft = fx["type"]
        if ft == "brand_card":
            draw_brand_card_tall(draw, overlay, W, H, rel_t, dur, fx["badge"], fx["title1"], fx["title2"], fx["subtitle"], fx["bullets"], fx["metrics"], fx["color"])
        elif ft == "cyber_alert":
            draw_cyber_alert_tall(draw, overlay, W, H, rel_t, dur, fx["max_count"], fx["label"], fx["sublabel"], fx["detail"], fx["breakdown"])
        elif ft == "terminal":
            draw_terminal_tall(draw, overlay, W, H, rel_t, dur, fx["title"], fx["commands"])

    frame_canvas.paste(overlay, mask=overlay)
    return np.array(frame_canvas.convert("RGB"))

print("⚡ Renderizando con Perfil IAshorts (880x1450 rectangular vertical con Word-Wrap estricto)...")
out_clip = VideoClip(compose_frame, duration=base.duration).set_fps(24)
if base.audio is not None:
    out_clip = out_clip.set_audio(base.audio)

clean_name = video_name.replace('.mp4','')
out_dest = f"/content/resultado-{clean_name}-IAshorts.mp4"
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
print(f"✅ Render perfil IAshorts completado! Tamaño: {size_mb:.1f} MB")

# Subir a Gofile
print("📤 Subiendo a Gofile...")
try:
    req = urllib.request.urlopen('https://api.gofile.io/servers')
    data = json.loads(req.read().decode())
    server = data['data']['servers'][0]['name']
    res = subprocess.run(['curl', '-s', '-F', f'file=@{out_dest}', f'https://{server}.gofile.io/contents/uploadfile'], capture_output=True, text=True)
    g_res = json.loads(res.stdout)
    d_page = g_res['data']['downloadPage']
    print(f"🎉 GOFILE_IASHORTS_FINAL_URL: {d_page}")
except Exception as e:
    print(f"Error subiendo a Gofile: {e}")
'''

    colab_script = colab_script.replace("__VIDEO_NAME__", video_filename)
    print("🚀 Enviando pipeline de renderizado a Colab...")
    res = execute_remote(token, rt, colab_script, timeout=1200)
    print(res.get("stdout", ""), flush=True)
    print(res.get("stderr", ""), flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hyperframes Render Engine")
    parser.add_argument("--input", default="input-3.mp4", help="Nombre del archivo de video en Google Drive")
    parser.add_argument("--profile", default="IAshorts", help="Nombre del perfil (IAshorts, IAyoutube)")
    args = parser.parse_args()

    run_render(args.input, args.profile)
