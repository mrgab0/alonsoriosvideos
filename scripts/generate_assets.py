"""
generate_assets.py
==================
Genera PNGs con canal alfa (transparencia) para usar como overlays en After
Effects, Premiere o cualquier editor de video.

Efectos generados:
  - arrow.png       : flecha simple
  - highlight.png   : círculo resaltador
  - lower_third.png : barra inferior con texto vacío (para editar en AE)

Uso:
    python scripts/generate_assets.py
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

W, H = 1920, 1080


def get_font(size, bold=False):
    candidates = []
    import sys
    if sys.platform.startswith("win"):
        base = "C:/Windows/Fonts/"
        candidates += [
            base + ("arialbd.ttf" if bold else "arial.ttf"),
        ]
    else:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def save_rgba(img, name):
    path = os.path.join(ASSETS_DIR, name)
    img.save(path, "PNG")
    print(f"[+] Guardado: {path}")


# 1. Flecha roja
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
draw.line([200, 540, 900, 540], fill=(255, 0, 0, 255), width=12)
# punta
import math
angle = math.atan2(0, 700)
tip = 40
p1 = (900 - tip * math.cos(angle - math.pi / 6), 540 - tip * math.sin(angle - math.pi / 6))
p2 = (900 - tip * math.cos(angle + math.pi / 6), 540 - tip * math.sin(angle + math.pi / 6))
draw.polygon([(900, 540), p1, p2], fill=(255, 0, 0, 255))
save_rgba(img, "arrow.png")

# 2. Círculo resaltador amarillo
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
draw.ellipse([520, 260, 760, 500], fill=(255, 215, 0, 90), outline=(255, 215, 0, 220), width=6)
save_rgba(img, "highlight.png")

# 3. Lower third vacío (barra negra translúcida)
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
draw.rectangle([0, int(H * 0.82), W, int(H * 0.92)], fill=(0, 0, 0, 150))
save_rgba(img, "lower_third.png")

print("[+] Assets generados en", ASSETS_DIR)
