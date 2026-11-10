"""
Script de Renderizado y Entrega de Video de 16 Minutos (input-2.mp4):
- Aplica el plan editorial diseñado por NVIDIA Nemotron 3.5 Super VL (estética Fazt Web).
- Renderiza en la GPU de Google Colab con optimización bypass ultrafast.
- Sube el resultado final directo a Google Drive (hyperframes/output/resultado-16min.mp4).
"""
import sys
import os
import json
import time

sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)
print(f"✅ Runtime Colab listo: {rt}")

# 1. Definir el plan curado por Nemotron Super VL para los 16 minutos
fazt_plan = {
    "effects": [
        {
            "type": "tech_pill",
            "start": 85.0,
            "end": 91.0,
            "tech": "MCP PROTOCOL",
            "subtitle": "Estándar de Contexto IA"
        },
        {
            "type": "terminal_code",
            "start": 150.0,
            "end": 156.0,
            "title": "config.json",
            "code_lines": [
                "  'model': 'pi-agent',",
                "  'runtime': 'ollama',",
                "  'timeout': 3000,",
                "  'status': 'online'"
            ]
        },
        {
            "type": "tech_pill",
            "start": 290.0,
            "end": 296.0,
            "tech": "PI SDK",
            "subtitle": "Documentación y Referencia"
        },
        {
            "type": "terminal_code",
            "start": 410.0,
            "end": 416.0,
            "title": "server.ts",
            "code_lines": [
                "import { McpServer } from '@modelcontextprotocol/sdk';",
                "const server = new McpServer({ name: 'hyperframes' });",
                "await server.connect(transport);"
            ]
        },
        {
            "type": "tech_pill",
            "start": 540.0,
            "end": 546.0,
            "tech": "OLLAMA ENGINE",
            "subtitle": "Inferencia Local en GPU"
        },
        {
            "type": "tech_pill",
            "start": 670.0,
            "end": 676.0,
            "tech": "NVIDIA NEMOTRON",
            "subtitle": "Vision Language Model 120B"
        },
        {
            "type": "terminal_code",
            "start": 770.0,
            "end": 776.0,
            "title": "deploy.sh",
            "code_lines": [
                "$ git init",
                "$ git add .",
                "$ git commit -m 'Fazt Web autonomous pipeline'",
                "$ git push origin main"
            ]
        },
        {
            "type": "tech_pill",
            "start": 870.0,
            "end": 876.0,
            "tech": "GITHUB CLOUD",
            "subtitle": "Control de Versiones y CI/CD"
        }
    ]
}

# 2. Subir plan a Colab
plan_json = json.dumps(fazt_plan)
execute_remote(token, rt, f"import json; json.dump({plan_json}, open('/content/fazt_plan.json', 'w'))")
print(f"📋 Plan de Nemotron Super VL guardado en Colab ({len(fazt_plan['effects'])} efectos).")

# 3. Código de Render en Colab
render_code = r'''
import os, sys, math, json, time
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
print(f"🎬 Dimensiones: {W}x{H}, Duración: {base.duration:.1f}s ({base.duration/60:.1f} min)")

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

print("⚡ Renderizando los 16 minutos a 24fps (libx264, preset ultrafast)...")
t0 = time.time()
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
render_time = time.time() - t0
size_mb = os.path.getsize(out_dest) / (1024 * 1024)
print(f"✅ Render completado en {render_time:.1f}s ({render_time/60:.1f} min)! Tamaño: {size_mb:.1f} MB")

# Subir a Google Drive
print("📤 Subiendo resultado-16min.mp4 a tu carpeta hyperframes/output en Google Drive...")
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

creds = service_account.Credentials.from_service_account_file(
    '/content/drive_sa.json',
    scopes=['https://www.googleapis.com/auth/drive']
)
service = build('drive', 'v3', credentials=creds)

output_folder_id = "1yBF7fEkpy6A_VdHlG9T6qbJxGroSapDJ"

media = MediaFileUpload(out_dest, mimetype='video/mp4', resumable=True)
body = {
    'name': 'resultado-16min.mp4',
    'parents': [output_folder_id]
}
up_res = service.files().create(body=body, media_body=media, fields='id, name').execute()
print(f"🎉 ÉXITO TOTAL: Video guardado en Google Drive! File ID: {up_res.get('id')}")
'''

print("🚀 Lanzando proceso de render y subida en Colab...")
res = execute_remote(token, rt, render_code)
print(res.get("stdout", "") + res.get("stderr", ""))
