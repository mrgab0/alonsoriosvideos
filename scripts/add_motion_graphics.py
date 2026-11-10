"""
add_motion_graphics.py
======================
Motor de motion graphics para superponer animaciones sobre videos ya grabados.

Soporta:
  - lower_third : texto animado en la parte inferior (acentos / leyendas)
  - highlight   : círculo o rectángulo pulsante sobre una zona
  - arrow       : flecha animada de un punto a otro (flujos)
  - comparison  : split-screen con etiquetas "Antes / DespuÈs"
  - callout     : texto con burbuja y flecha que apunta a un detalle

Uso:
    python scripts/add_motion_graphics.py --config config/motions.json
"""

import argparse
import json
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip, VideoClip


# ---------------------------------------------------------------------------
# Utilidades de color y fuente
# ---------------------------------------------------------------------------

def hex_to_rgba(hex_str, alpha=1.0):
    """Convierte '#RRGGBB' o '#RRGGBBAA' a tupla RGBA (0-255)."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 6:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return (r, g, b, int(255 * alpha))
    elif len(hex_str) == 8:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        a = int(hex_str[6:8], 16)
        return (r, g, b, a)
    return (255, 255, 255, int(255 * alpha))


def get_font(size, bold=False):
    """Intenta cargar una fuente TrueType; si no hay, usa la por defecto de Pillow."""
    candidates = []
    if sys.platform.startswith("win"):
        base = "C:/Windows/Fonts/"
        candidates += [
            base + ("arialbd.ttf" if bold else "arial.ttf"),
            base + ("tahomabd.ttf" if bold else "tahoma.ttf"),
        ]
    elif sys.platform.startswith("darwin"):
        base = "/System/Library/Fonts/Supplemental/"
        candidates += [
            base + ("Arial Bold.ttf" if bold else "Arial.ttf"),
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


def text_to_rgba(text, fontsize, color, bg_color, bold=False, pad=25):
    """Renderiza texto a un array RGBA numpy con fondo opcional."""
    font = get_font(fontsize, bold)
    dummy = Image.new("RGBA", (10, 10))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=1)
    w = (bbox[2] - bbox[0]) + 2 * pad
    h = (bbox[3] - bbox[1]) + 2 * pad
    img = Image.new("RGBA", (max(w, 1), max(h, 1)), bg_color)
    draw = ImageDraw.Draw(img)
    draw.text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=color, stroke_width=1)
    return np.array(img)


def make_text_clip(text, duration, fontsize=40, color=(255, 255, 255, 255),
                   bg_color=(0, 0, 0, 160), bold=False, position=("center", "center")):
    """Crea un ImageClip con texto renderizado por Pillow (sin ImageMagick)."""
    rgba = text_to_rgba(text, fontsize, color, bg_color, bold=bold)
    clip = ImageClip(rgba, ismask=False).set_duration(duration)
    clip = clip.set_position(position)
    return clip


# ---------------------------------------------------------------------------
# Efectos individuales
# ---------------------------------------------------------------------------

def effect_lower_third(W, H, fx):
    start, end = fx["start"], fx["end"]
    dur = end - start
    color = hex_to_rgba(fx.get("color", "#FFFFFF"))
    bg = hex_to_rgba(fx.get("bg_color", "#000000"), fx.get("bg_opacity", 0.75))
    fontsize = fx.get("fontsize", 44)

    offset_y = fx.get("offset_y", 120)
    # Posición cerca del borde inferior usando fracción de alto
    pos_y = 1.0 - (offset_y / H)
    position = (fx.get("position", ["center", "bottom"])[0], pos_y)

    clip = make_text_clip(
        fx["text"],
        dur,
        fontsize=fontsize,
        color=color,
        bg_color=bg,
        position=position,
    )
    return clip.set_start(start)


def effect_highlight(W, H, fx):
    start, end = fx["start"], fx["end"]
    dur = end - start
    center = tuple(fx["position"])
    radius = fx.get("radius", 100)
    color = hex_to_rgba(fx.get("color", "#FFD700"))
    opacity = fx.get("opacity", 0.45)
    anim = fx.get("animation", "pulse")

    def make_frame(t):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        r = radius
        if anim == "pulse":
            r = radius * (1 + 0.18 * np.sin(2 * np.pi * t * 3))
        elif anim == "none":
            r = radius
        bbox = [center[0] - r, center[1] - r, center[0] + r, center[1] + r]
        fill = (*color[:3], int(color[3] * opacity))
        draw.ellipse(bbox, fill=fill, outline=(*color[:3], 220), width=4)
        return np.array(img)

    clip = VideoClip(make_frame, duration=dur)
    return clip.set_start(start)


def effect_arrow(W, H, fx):
    start, end = fx["start"], fx["end"]
    dur = end - start
    p1 = tuple(fx["from"])
    p2 = tuple(fx["to"])
    color = hex_to_rgba(fx.get("color", "#FF0000"))
    width = fx.get("width", 10)
    anim = fx.get("animation", "draw")

    def make_frame(t):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        prog = min(t / dur, 1.0) if anim == "draw" else 1.0
        x2 = p1[0] + (p2[0] - p1[0]) * prog
        y2 = p1[1] + (p2[1] - p1[1]) * prog
        draw.line([p1[0], p1[1], x2, y2], fill=color, width=width)
        # punta de flecha
        if prog > 0.05:
            import math
            angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
            tip_len = width * 3
            p_left = (x2 - tip_len * math.cos(angle - math.pi / 6),
                      y2 - tip_len * math.sin(angle - math.pi / 6))
            p_right = (x2 - tip_len * math.cos(angle + math.pi / 6),
                       y2 - tip_len * math.sin(angle + math.pi / 6))
            draw.polygon([(x2, y2), p_left, p_right], fill=color)
        return np.array(img)

    clip = VideoClip(make_frame, duration=dur)
    return clip.set_start(start)


def effect_comparison(W, H, fx):
    start, end = fx["start"], fx["end"]
    dur = end - start
    split_x = fx.get("split_x", 0.5)
    left_label = fx.get("left_label", "Antes")
    right_label = fx.get("right_label", "Después")
    label_color = hex_to_rgba(fx.get("label_color", "#FFFFFF"))

    def make_frame(t):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        x = int(W * split_x)
        # oscurece la mitad derecha
        draw.rectangle([x, 0, W, H], fill=(0, 0, 0, 110))
        # línea divisoria
        draw.line([x, 0, x, H], fill=(255, 255, 255, 200), width=4)
        # etiquetas
        font = get_font(48, bold=True)
        draw.text((40, 40), left_label, font=font, fill=label_color)
        draw.text((x + 40, 40), right_label, font=font, fill=label_color)
        return np.array(img)

    clip = VideoClip(make_frame, duration=dur)
    return clip.set_start(start)


def effect_callout(W, H, fx):
    start, end = fx["start"], fx["end"]
    dur = end - start
    text = fx["text"]
    pos = tuple(fx["position"])
    arrow_to = tuple(fx["arrow_to"])
    bg_color = hex_to_rgba(fx.get("bg_color", "#0066FF"))
    fontsize = fx.get("fontsize", 36)

    # render texto una sola vez
    rgba = text_to_rgba(text, fontsize, (255, 255, 255, 255), bg_color)
    th, tw = rgba.shape[0], rgba.shape[1]

    def make_frame(t):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # burbuja de texto
        bx, by = pos
        draw.rectangle([bx, by, bx + tw, by + th], fill=bg_color, outline=(255, 255, 255, 200), width=2)
        # flecha de la burbuja hacia el objetivo
        draw.line([bx + tw // 2, by + th, arrow_to[0], arrow_to[1]],
                  fill=(255, 255, 255, 220), width=5)
        # pegar el texto recortado desde el array RGBA
        text_img = Image.fromarray(rgba)
        img.paste(text_img, (bx, by), text_img)
        return np.array(img)

    clip = VideoClip(make_frame, duration=dur)
    clip = clip.set_position((pos[0] / W, pos[1] / H))
    return clip.set_start(start)


# ---------------------------------------------------------------------------
# Orquestador
# ---------------------------------------------------------------------------

def build_clips(W, H, effects):
    clips = []
    for fx in effects:
        ftype = fx["type"]
        if ftype == "lower_third":
            clips.append(effect_lower_third(W, H, fx))
        elif ftype == "highlight":
            clips.append(effect_highlight(W, H, fx))
        elif ftype == "arrow":
            clips.append(effect_arrow(W, H, fx))
        elif ftype == "comparison":
            clips.append(effect_comparison(W, H, fx))
        elif ftype == "callout":
            clips.append(effect_callout(W, H, fx))
        else:
            print(f"[!] Tipo desconocido ignorado: {ftype}", file=sys.stderr)
    return clips


def main():
    parser = argparse.ArgumentParser(description="Agrega motion graphics a un video grabado.")
    parser.add_argument("--config", required=True, help="Ruta al archivo JSON de configuración")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"[!] No se encuentra el config: {args.config}", file=sys.stderr)
        sys.exit(1)

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    input_path = cfg["input"]
    output_path = cfg["output"]
    resolution = cfg.get("resolution", None)
    fps = cfg.get("fps", 30)

    if not os.path.exists(input_path):
        print(f"[!] No se encuentra el video de entrada: {input_path}", file=sys.stderr)
        sys.exit(1)

    base = VideoFileClip(input_path)
    if resolution:
        base = base.resize(resolution)

    W, H = base.size
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    overlay_clips = build_clips(W, H, cfg.get("effects", []))

    def ensure_rgba(frame):
        if frame.ndim == 3 and frame.shape[2] == 4:
            return frame
        if frame.ndim == 3 and frame.shape[2] == 3:
            alpha = np.full((frame.shape[0], frame.shape[1], 1), 255, dtype=np.uint8)
            return np.dstack([frame, alpha])
        return frame

    def compose_frame(t):
        frame = base.get_frame(t)
        frame = ensure_rgba(frame).astype(np.float32) / 255.0

        for clip in overlay_clips:
            if t < clip.start or t > clip.end:
                continue
            rel_t = t - clip.start
            if rel_t < 0 or rel_t > clip.duration:
                continue
            ov = clip.get_frame(rel_t)
            ov = ensure_rgba(ov)
            if ov.shape[:2] != (H, W):
                ov = np.array(Image.fromarray(ov.astype(np.uint8)).resize((W, H), Image.LANCZOS))
                ov = ensure_rgba(ov)
            ov = ov.astype(np.float32) / 255.0
            alpha = ov[:, :, 3:4]
            rgb = ov[:, :, :3]
            frame[:, :, :3] = frame[:, :, :3] * (1 - alpha) + rgb * alpha

        return (frame[:, :, :3] * 255).astype(np.uint8)

    final_clip = VideoClip(compose_frame, duration=base.duration)
    final_clip = final_clip.set_fps(fps)

    if base.audio is not None:
        final_clip = final_clip.set_audio(base.audio)

    print(f"[+] Renderizando a {output_path} ...")
    final_clip.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
    )
    print("[+] Listo.")


if __name__ == "__main__":
    main()
