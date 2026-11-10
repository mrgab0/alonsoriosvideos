"""
Generador y Verificador Visual de Snippets Verticales 880x1450 (Perfil IAshorts)
Con ajuste de línea (Word Wrap) automático y delimitación estricta de márgenes.
"""
import sys, os, json, base64
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

font_title_giant = get_font(68, mono=False)
font_num_giant = get_font(125, mono=True)
font_subtitle = get_font(44, mono=False)
font_body = get_font(34, mono=False)
font_code = get_font(34, mono=True)
font_badge = get_font(28, mono=False)
font_meta = get_font(26, mono=True)

# Helper: Word Wrap
def draw_wrapped_text(draw, text, font, x, y, max_w, line_spacing=12, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0)):
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

BASE_CW = 880
BASE_CH = 1450

# 1. PREVIEW BRAND CARD
def render_brand_preview(t):
    base = Image.new("RGBA", (W, H), (14, 18, 30, 255))
    draw = ImageDraw.Draw(base)

    cw, ch = BASE_CW, BASE_CH
    cx = (W - cw) // 2
    cy = (H - ch) // 2
    color = (0, 242, 254)

    # Sombra 3D profunda
    draw.rounded_rectangle([cx + 14, cy + 24, cx + cw + 14, cy + ch + 24], radius=38, fill=(0, 0, 0, 160))
    draw.rounded_rectangle([cx - 12, cy - 12, cx + cw + 12, cy + ch + 12], radius=38, fill=(*color, 45))
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=34, fill=(14, 22, 38, 252), outline=(*color, 255), width=4)

    draw_border_beam(draw, [cx, cy, cx + cw, cy + ch], t, beam_len=450, color=color, width=7)

    # Badge dinámico con ancho medido
    badge = "INVESTIGACIÓN OFICIAL"
    b_bbox = font_badge.getbbox(badge)
    badge_w = (b_bbox[2] - b_bbox[0]) + 90
    draw.rounded_rectangle([cx + 50, cy + 45, cx + 50 + badge_w, cy + 105], radius=16, fill=(*color, 45), outline=(*color, 255), width=2)
    draw.ellipse([cx + 70, cy + 65, cx + 90, cy + 85], fill=(*color, 255))
    draw.text((cx + 105, cy + 58), badge, font=font_badge, fill=(*color, 255), stroke_width=2, stroke_fill=(0, 0, 0))

    # Título doble gigante
    draw.text((cx + 50, cy + 135), "OPENAI", font=font_title_giant, fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    draw.text((cx + 50, cy + 225), "SECURITY", font=font_title_giant, fill=(*color, 255), stroke_width=3, stroke_fill=(0, 0, 0))

    draw.line([(cx + 50, cy + 325), (cx + cw - 50, cy + 325)], fill=(40, 60, 95, 255), width=3)

    # Subtítulo delimitado con Word Wrap
    max_text_w = cw - 110 # 770px de ancho disponible
    draw_wrapped_text(draw, "Auditoría Autónoma del Kernel Linux con IA", font_subtitle, cx + 50, cy + 355, max_w=max_text_w, fill=(240, 245, 255, 255))

    # Bullets delimitados con Word Wrap
    bullets = [
        "Detección de Zero-Days mediante LLMs avanzados",
        "Reporte oficial coordinado con Linux Foundation",
        "Parcheo directo en módulos críticos de memoria"
    ]
    ly = cy + 450
    for b in bullets:
        draw.text((cx + 50, ly), "●", font=font_body, fill=(*color, 255))
        ly = draw_wrapped_text(draw, b, font=font_body, cx + 80, ly, max_w=max_text_w - 35, line_spacing=10, fill=(200, 225, 245, 255))
        ly += 22

    # Cajas de métricas dobles
    draw.line([(cx + 50, cy + 780), (cx + cw - 50, cy + 780)], fill=(40, 60, 95, 255), width=2)
    box_w = (cw - 130) // 2

    draw.rounded_rectangle([cx + 50, cy + 810, cx + 50 + box_w, cy + 1020], radius=20, fill=(20, 30, 52, 255), outline=(*color, 150), width=2)
    draw.text((cx + 75, cy + 830), "948", font=font_num_giant, fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
    draw.text((cx + 75, cy + 965), "VULNERABILIDADES", font=font_meta, fill=(*color, 255))

    draw.rounded_rectangle([cx + 70 + box_w, cy + 810, cx + cw - 50, cy + 1020], radius=20, fill=(20, 30, 52, 255), outline=(*color, 150), width=2)
    draw.text((cx + 95 + box_w, cy + 830), "100%", font=font_num_giant, fill=(50, 255, 120, 255), stroke_width=4, stroke_fill=(0, 0, 0))
    draw.text((cx + 95 + box_w, cy + 965), "CONFIRMADO", font=font_meta, fill=(50, 255, 120, 255))

    # Status Footer Pill
    draw.rounded_rectangle([cx + 50, cy + ch - 110, cx + cw - 50, cy + ch - 40], radius=20, fill=(*color, 35), outline=(*color, 255), width=2)
    draw.text((cx + 75, cy + ch - 92), "ESTADO: COOPERACIÓN ACTIVA EN CURSO", font=font_badge, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))

    apply_shimmer(base, [cx, cy, cx + cw, cy + ch], t)
    return base

f = render_brand_preview(2.0)
os.makedirs("/content/previews", exist_ok=True)
f.save("/content/previews/preview_wrapped_brand.png")

with open("/content/previews/preview_wrapped_brand.png", "rb") as fh:
    b64 = base64.b64encode(fh.read()).decode("utf-8")

print("PREVIEW_WRAPPED_START")
print(b64)
print("PREVIEW_WRAPPED_END")
'''

res = execute_remote(token, rt, preview_script, timeout=60)
raw = res.get("stdout", "")
if "PREVIEW_WRAPPED_START" in raw and "PREVIEW_WRAPPED_END" in raw:
    b64 = raw.split("PREVIEW_WRAPPED_START")[1].split("PREVIEW_WRAPPED_END")[0].strip()
    os.makedirs("output/previews", exist_ok=True)
    out_file = "output/previews/preview_wrapped_brand.png"
    with open(out_file, "wb") as f:
        f.write(base64.b64decode(b64))
    print(f"✅ Guardado localmente: {out_file} ({os.path.getsize(out_file)/1024:.1f} KB)")
else:
    print("Error:", raw)
