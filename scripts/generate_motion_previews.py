"""
Generador y Verificador de Motion Graphics Dinámicos (Estilo Fazt Web)
Utilizando las fuentes Liberation reales de Colab:
- /usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf
- /usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf
Descarga los PNGs localmente para inspección visual directa.
"""
import sys
import os
import json
import base64

sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)
print(f"✅ Runtime Colab: {rt}")

preview_script = r'''
import os, sys, math, json, io, base64
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920

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

# Helper: Draw Border Beam (Láser dinámico que orbita los bordes)
def draw_border_beam(draw, box, t, beam_len=300, color=(0, 242, 254), width=6):
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

    steps = 30
    for i in range(steps):
        frac = i / steps
        pos_d = (head - (1.0 - frac) * beam_len) % peri
        px, py = get_pos(pos_d)
        alpha = int(255 * (frac ** 2.2))
        r = int(width * (0.3 + 0.7 * frac))
        draw.ellipse([px - r, py - r, px + r, py + r], fill=(*color, alpha))

# Helper: Shimmer diagonal
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

# 1. RENDERIZADOR TERMINAL FAZT WEB
def render_terminal_frame(t):
    base = Image.new("RGBA", (W, H), (15, 18, 28, 255))
    draw = ImageDraw.Draw(base)

    tw, th = 980, 520
    tx = (W - tw) // 2
    float_y = int(math.sin(t * 3.5) * 10)
    ty = H - th - 240 + float_y

    # Outer Glow difuso
    glow_box = [tx - 12, ty - 12, tx + tw + 12, ty + th + 12]
    draw.rounded_rectangle(glow_box, radius=32, fill=(0, 200, 255, 35))

    # Caja fondo terminal oscuro
    draw.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=28, fill=(16, 20, 32, 245), outline=(60, 75, 110, 255), width=3)

    # Barra superior ventana macOS
    bar_h = 75
    draw.rounded_rectangle([tx, ty, tx + tw, ty + bar_h], radius=28, fill=(24, 30, 48, 255))
    draw.rectangle([tx, ty + 35, tx + tw, ty + bar_h], fill=(24, 30, 48, 255))

    # Botones macOS
    draw.ellipse([tx + 30, ty + 24, tx + 54, ty + 48], fill=(255, 95, 86, 255))
    draw.ellipse([tx + 68, ty + 24, tx + 92, ty + 48], fill=(255, 189, 46, 255))
    draw.ellipse([tx + 106, ty + 24, tx + 130, ty + 48], fill=(39, 201, 63, 255))

    # Titulo de pestaña
    draw.text((tx + tw // 2 - 160, ty + 22), "root@openai-kernel:~", font=font_badge, fill=(160, 185, 215, 255))

    # Border beam orbitando la terminal
    draw_border_beam(draw, [tx, ty, tx + tw, ty + th], t, beam_len=320, color=(0, 242, 254), width=6)

    # Shimmer diagonal sutil
    apply_shimmer(base, [tx, ty, tx + tw, ty + th], t)

    # Contenido con Syntax Highlighting
    lines = [
        [("$ ", (50, 255, 120)), ("python3 ", (255, 120, 200)), ("audit_kernel.py ", (130, 230, 255)), ("--all", (255, 180, 80))],
        [("[*] ", (255, 200, 80)), ("Escaneando llamadas Ring 0...", (240, 245, 255))],
        [("[!] ", (255, 60, 90)), ("ALERTA: 948 exploits detectados!", (255, 80, 100))],
        [("[✓] ", (50, 255, 120)), ("Generando reporte de seguridad...", (150, 230, 160))]
    ]

    ly = ty + 105
    for l_idx, segments in enumerate(lines):
        lx = tx + 40
        for text, color in segments:
            draw.text((lx, ly), text, font=font_code, fill=(*color, 255), stroke_width=2, stroke_fill=(0, 0, 0))
            bbox = font_code.getbbox(text)
            lx += (bbox[2] - bbox[0])
        ly += 68

    # Cursor parpadeante
    if int(t * 4) % 2 == 0:
        draw.text((lx + 6, ly - 68), "█", font=font_code, fill=(0, 242, 254, 255), stroke_width=2, stroke_fill=(0, 0, 0))

    return base

# 2. RENDERIZADOR CYBER RADAR ALERT
def render_radar_alert_frame(t):
    base = Image.new("RGBA", (W, H), (15, 18, 28, 255))
    draw = ImageDraw.Draw(base)

    cw, ch = 980, 520
    cx = (W - cw) // 2
    float_y = int(math.sin(t * 3.0) * 8)
    cy = 220 + float_y

    # Glow rojo exterior pulsante
    pulse = (math.sin(t * 8) + 1.0) / 2.0
    glow_alpha = int(45 + 35 * pulse)
    draw.rounded_rectangle([cx - 15, cy - 15, cx + cw + 15, cy + ch + 15], radius=36, fill=(255, 42, 85, glow_alpha))

    # Fondo oscuro Cyberpunk
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=30, fill=(22, 12, 26, 250), outline=(255, 50, 90, 240), width=4)

    # Border beam carmesí
    draw_border_beam(draw, [cx, cy, cx + cw, cy + ch], t, beam_len=340, color=(255, 60, 90), width=7)

    # Radar animado a la derecha
    rx = cx + cw - 140
    ry = cy + 130
    for r_idx in range(3):
        cur_r = int(((t * 85) + r_idx * 40) % 100) + 10
        r_alpha = int(220 * (1.0 - (cur_r / 110.0)))
        draw.ellipse([rx - cur_r, ry - cur_r, rx + cur_r, ry + cur_r], outline=(255, 60, 90, r_alpha), width=3)
    draw.ellipse([rx - 8, ry - 8, rx + 8, ry + 8], fill=(255, 255, 255, 255))

    # Laser scanner bar horizontal
    laser_y = cy + int((t * 220) % ch)
    draw.line([(cx + 15, laser_y), (cx + cw - 15, laser_y)], fill=(255, 60, 90, 190), width=3)

    # Badge de Peligro Vectorial
    draw.rounded_rectangle([cx + 40, cy + 35, cx + 440, cy + 85], radius=14, fill=(255, 42, 85, 60), outline=(255, 60, 90, 255), width=2)
    draw.polygon([(cx + 60, cy + 72), (cx + 75, cy + 46), (cx + 90, cy + 72)], fill=(255, 200, 50, 255))
    draw.text((cx + 72, cy + 49), "!", font=get_font(20, mono=True), fill=(0, 0, 0, 255))
    draw.text((cx + 105, cy + 46), "AMENAZA ZERO-DAY", font=font_badge, fill=(255, 220, 230, 255), stroke_width=2, stroke_fill=(0, 0, 0))

    # Contador gigante 948 y etiqueta
    draw.text((cx + 40, cy + 105), "948", font=font_num_giant, fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
    draw.text((cx + 285, cy + 140), "EXPLOITS DETECTADOS", font=font_hero, fill=(255, 75, 105, 255), stroke_width=3, stroke_fill=(0, 0, 0))

    # Separador sutil
    draw.line([(cx + 40, cy + 245), (cx + cw - 40, cy + 245)], fill=(70, 35, 55, 255), width=2)

    # Subtítulo explicativo en tamaño gigante legible
    draw.text((cx + 42, cy + 270), "Kernel Linux & Capa Syscall Vulnerable", font=font_card_title, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    draw.text((cx + 42, cy + 345), "Reporte de Seguridad Conjunto OpenAI + Linux", font=font_sub, fill=(210, 220, 240, 255), stroke_width=2, stroke_fill=(0, 0, 0))

    # Barra de mitigación
    pw = 900
    prog_pct = min(1.0, 0.2 + ((t * 0.3) % 0.8))
    draw.rounded_rectangle([cx + 40, cy + 430, cx + 40 + pw, cy + 465], radius=16, fill=(35, 20, 38, 255), outline=(80, 40, 65, 255), width=2)
    draw.rounded_rectangle([cx + 40, cy + 430, cx + 40 + int(pw * prog_pct), cy + 465], radius=16, fill=(255, 42, 85, 255))
    draw.text((cx + 40 + pw - 240, cy + 432), f"{int(prog_pct*100)}% PARCHEADO", font=font_badge, fill=(255, 255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0))

    apply_shimmer(base, [cx, cy, cx + cw, cy + ch], t)
    return base

# 3. RENDERIZADOR BRAND CARD FUTURISTA (OPENAI)
def render_brand_card_frame(t):
    base = Image.new("RGBA", (W, H), (15, 18, 28, 255))
    draw = ImageDraw.Draw(base)

    cw, ch = 980, 480
    cx = (W - cw) // 2
    float_y = int(math.sin(t * 2.8) * 12)
    cy = 240 + float_y

    # Glow cian exterior
    draw.rounded_rectangle([cx - 15, cy - 15, cx + cw + 15, cy + ch + 15], radius=36, fill=(0, 242, 254, 50))

    # Fondo tarjeta
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=30, fill=(14, 22, 38, 250), outline=(0, 242, 254, 230), width=4)

    # Border beam cian eléctrico
    draw_border_beam(draw, [cx, cy, cx + cw, cy + ch], t, beam_len=360, color=(0, 242, 254), width=7)

    # Badge con tag
    draw.rounded_rectangle([cx + 45, cy + 35, cx + 460, cy + 90], radius=14, fill=(0, 242, 254, 45), outline=(0, 242, 254, 255), width=2)
    draw.ellipse([cx + 65, cy + 53, cx + 83, cy + 71], fill=(0, 242, 254, 255))
    draw.text((cx + 98, cy + 48), "INVESTIGACIÓN OFICIAL", font=font_badge, fill=(0, 242, 254, 255), stroke_width=2, stroke_fill=(0, 0, 0))

    # Titulo principal en 56px bold
    draw.text((cx + 45, cy + 120), "OPENAI SECURITY", font=font_hero, fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))

    # Separador sutil
    draw.line([(cx + 45, cy + 215), (cx + cw - 45, cy + 215)], fill=(30, 50, 80, 255), width=2)

    # Subtítulo explicativo gigante
    draw.text((cx + 48, cy + 245), "Auditoría Autónoma de Kernel Linux", font=font_card_title, fill=(56, 189, 248, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    draw.text((cx + 48, cy + 335), "● Detección de Zero-Days mediante LLMs avanzados", font=font_sub, fill=(200, 225, 245, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    draw.text((cx + 48, cy + 395), "● Cooperación proactiva con la comunidad de Linux", font=font_sub, fill=(160, 190, 220, 255), stroke_width=2, stroke_fill=(0, 0, 0))

    apply_shimmer(base, [cx, cy, cx + cw, cy + ch], t)
    return base

# Generar fotogramas
f_term = render_terminal_frame(2.5)
f_radar = render_radar_alert_frame(3.2)
f_card = render_brand_card_frame(1.8)

os.makedirs("/content/previews", exist_ok=True)
f_term.save("/content/previews/preview_terminal.png")
f_radar.save("/content/previews/preview_radar.png")
f_card.save("/content/previews/preview_brand.png")

# Empaquetar en base64
res = {}
for name in ["preview_terminal", "preview_radar", "preview_brand"]:
    with open(f"/content/previews/{name}.png", "rb") as f:
        res[name] = base64.b64encode(f.read()).decode("utf-8")

print("PREVIEWS_JSON_START")
print(json.dumps(res))
print("PREVIEWS_JSON_END")
'''

print("🎨 Generando fotogramas con fuentes Liberation reales y renderizado avanzado...")
out = execute_remote(token, rt, preview_script, timeout=60)
raw = out.get("stdout", "")

if "PREVIEWS_JSON_START" in raw and "PREVIEWS_JSON_END" in raw:
    json_str = raw.split("PREVIEWS_JSON_START")[1].split("PREVIEWS_JSON_END")[0].strip()
    data = json.loads(json_str)
    
    os.makedirs("output/previews", exist_ok=True)
    for name, b64 in data.items():
        file_path = f"output/previews/{name}.png"
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(b64))
        print(f"📸 Guardado localmente: {file_path} ({os.path.getsize(file_path)/1024:.1f} KB)")
else:
    print("Error generando previews:", raw)
