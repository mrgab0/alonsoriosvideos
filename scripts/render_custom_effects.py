"""
Renders custom paper-animated and hand-drawn effects on Google Colab GPU:
1. 'storm': Stop-motion paper cutout clouds, zigzag origami lightning, paper rain.
2. 'refuge here': Spring-bouncing paper tent (bottom-left) and paper cave (bottom-right).
3. 'Just sit back and relax': Progressive write-on 'CHILL!!' with marker tip and vibrating doodle sparkles.
"""
import subprocess
import json
import urllib.request
import base64
import os
import sys

MCP_URL = "https://colaboratory.googleapis.com/mcp"
PROJECT_ID = "vaka-taxi"
RUNTIME = "runtimes/r-bf1e379d-802f-4c7d-afd2-ce7e0db6ba85"

def get_token():
    cmd = ["gcloud.cmd", "auth", "application-default", "print-access-token"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        return res.stdout.strip()
    except Exception:
        cmd = ["gcloud", "auth", "application-default", "print-access-token"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        return res.stdout.strip()

def exec_code(token, code):
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
    try:
        with urllib.request.urlopen(req, timeout=400) as resp:
            data = resp.read().decode("utf-8")
            lines = [line for line in data.splitlines() if line.startswith("data: ")]
            if lines:
                last = json.loads(lines[-1][len("data: "):])
                struct = last.get("result", {}).get("structuredContent", {})
                err = struct.get("error") or struct.get("stderr")
                if err:
                    print(f"   [Colab Stderr/Error] {err}", file=sys.stderr)
                return struct.get("stdout", "")
            return ""
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="replace")
        print(f"[!] HTTP Error {e.code}: {err_msg}", file=sys.stderr)
        raise

REMOTE_SCRIPT = r'''
import os, sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, VideoClip

print("🎬 Iniciando compositor de efectos de autor...")

# -------------------------------------------------------------
# Fuentes del sistema en Linux / Colab
# -------------------------------------------------------------
def get_font(size, bold=True):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

# -------------------------------------------------------------
# EFECTO 1: Paper Cutout Storm (0.34s - 2.20s)
# -------------------------------------------------------------
def draw_storm(draw, W, H, rel_t, dur):
    # Cuantizar a 10 fps para stop-motion autentico
    fps_stop = 10.0
    t_step = math.floor(rel_t * fps_stop) / fps_stop
    
    # Entrada/Salida suave
    alpha_fade = min(1.0, rel_t / 0.25) * min(1.0, (dur - rel_t) / 0.3)
    if alpha_fade <= 0:
        return
        
    alpha_byte = int(255 * alpha_fade)
    
    # 1. Nubes de cartulina en la parte superior (W // 2, 220)
    cx, cy = W // 2, 230
    wobble_x = int(math.sin(t_step * 14.0) * 4)
    wobble_y = int(math.cos(t_step * 12.0) * 3)
    cx += wobble_x
    cy += wobble_y

    # Sombra de papel (drop shadow desplazada)
    shadow_col = (10, 15, 25, int(110 * alpha_fade))
    for ox, oy, r in [(cx-140+8, cy+10, 95), (cx+130+8, cy+15, 90), (cx-60+8, cy-35, 120), (cx+50+8, cy-30, 115)]:
        draw.ellipse([ox - r, oy - r, ox + r, oy + r], fill=shadow_col)
        
    # Capa de nube trasera (Gris azulado oscuro #2C3E50)
    back_cloud = (44, 62, 80, alpha_byte)
    for ox, oy, r in [(cx-140, cy+10, 95), (cx+130, cy+15, 90), (cx-60, cy-35, 120), (cx+50, cy-30, 115)]:
        draw.ellipse([ox - r, oy - r, ox + r, oy + r], fill=back_cloud, outline=(240, 245, 250, int(180*alpha_fade)), width=4)

    # Capa de nube frontal (Gris tormenta medio #4A6572)
    front_cloud = (74, 101, 114, alpha_byte)
    for ox, oy, r in [(cx-100, cy+30, 80), (cx+90, cy+35, 75), (cx, cy+10, 100)]:
        draw.ellipse([ox - r, oy - r, ox + r, oy + r], fill=front_cloud, outline=(255, 255, 255, alpha_byte), width=4)

    # 2. Rayo de origami (destellos discontinuos estilo stop-motion)
    flash_active = (0.5 <= rel_t <= 0.85) or (1.2 <= rel_t <= 1.45)
    if flash_active and (int(t_step * 10) % 3 != 0):
        # Rayo zigzag amarillo #F4D03F
        pts = [
            (cx - 20, cy + 90),
            (cx + 40, cy + 220),
            (cx + 5,  cy + 220),
            (cx + 60, cy + 390),
            (cx - 10, cy + 260),
            (cx + 25, cy + 260),
        ]
        # Sombra de rayo
        pts_shadow = [(p[0]+6, p[1]+6) for p in pts]
        draw.polygon(pts_shadow, fill=(20, 20, 20, int(120*alpha_fade)))
        draw.polygon(pts, fill=(244, 208, 63, alpha_byte), outline=(255, 255, 255, alpha_byte))

    # 3. Gotas de lluvia de papel (trazos inclinados que caen)
    rain_col = (160, 230, 245, int(210 * alpha_fade))
    for i in range(16):
        rand_x = (i * 45 + int(t_step * 100) * 17) % (W - 100) + 50
        rand_y = (int(t_step * 600) + i * 50) % 400 + cy + 90
        length = 26
        dx = -8
        draw.line([rand_x, rand_y, rand_x + dx, rand_y + length], fill=rain_col, width=5)

# -------------------------------------------------------------
# EFECTO 2: Paper Refuge - Carpa y Cueva (2.30s - 4.80s)
# -------------------------------------------------------------
def draw_refuge(draw, W, H, rel_t, dur):
    # Spring bounce physics al entrar
    bounce = min(1.0, 1.0 - math.exp(-7.0 * rel_t) * math.cos(13.0 * rel_t))
    alpha_fade = min(1.0, rel_t / 0.2) * min(1.0, (dur - rel_t) / 0.3)
    if alpha_fade <= 0:
        return
        
    alpha_byte = int(255 * alpha_fade)

    # 1. ESQUINA INFERIOR IZQUIERDA: Carpa de papel scout
    tent_x = int(140 * bounce)
    tent_y = H - 180
    
    # Sombra en el suelo
    draw.ellipse([tent_x - 120, tent_y + 90, tent_x + 120, tent_y + 130], fill=(0, 0, 0, int(100 * alpha_fade)))
    
    # Palos de madera que cruzan la punta
    wood_col = (180, 110, 60, alpha_byte)
    draw.line([tent_x - 100, tent_y + 100, tent_x + 35, tent_y - 120], fill=wood_col, width=8)
    draw.line([tent_x + 100, tent_y + 100, tent_x - 35, tent_y - 120], fill=wood_col, width=8)
    
    # Cara izquierda de la carpa (Terracota cálido #E76F51)
    tent_left = [(tent_x, tent_y - 100), (tent_x - 90, tent_y + 90), (tent_x, tent_y + 90)]
    draw.polygon(tent_left, fill=(231, 111, 81, alpha_byte), outline=(255, 255, 255, alpha_byte))
    
    # Cara derecha (Naranja tostado más sombreado #D65A31)
    tent_right = [(tent_x, tent_y - 100), (tent_x, tent_y + 90), (tent_x + 90, tent_y + 90)]
    draw.polygon(tent_right, fill=(214, 90, 49, alpha_byte), outline=(255, 255, 255, alpha_byte))
    
    # Puerta interior oscura y solapa abierta
    door = [(tent_x - 20, tent_y + 90), (tent_x, tent_y - 10), (tent_x + 20, tent_y + 90)]
    draw.polygon(door, fill=(30, 25, 45, alpha_byte))
    # Luz dorada acogedora dentro de la carpa
    draw.ellipse([tent_x - 12, tent_y + 50, tent_x + 12, tent_y + 85], fill=(255, 215, 0, int(220 * alpha_fade)))

    # Etiqueta de papel cosida
    font_small = get_font(24, bold=True)
    draw.rectangle([tent_x - 55, tent_y + 105, tent_x + 55, tent_y + 135], fill=(250, 245, 230, alpha_byte), outline=(40,40,40,alpha_byte), width=2)
    draw.text((tent_x - 42, tent_y + 108), "REFUGE", font=font_small, fill=(40, 40, 40, alpha_byte))

    # 2. ESQUINA INFERIOR DERECHA: Cueva de rocas de papel
    cave_x = W - int(140 * bounce)
    cave_y = H - 180
    
    # Sombra de la montaña de rocas
    draw.ellipse([cave_x - 120, cave_y + 90, cave_x + 120, cave_y + 130], fill=(0, 0, 0, int(100 * alpha_fade)))
    
    # Capas de rocas redondeadas superpuestas
    rock_dark = (75, 85, 99, alpha_byte)
    draw.ellipse([cave_x - 110, cave_y - 90, cave_x + 110, cave_y + 100], fill=rock_dark, outline=(255, 255, 255, alpha_byte), width=4)
    rock_mid = (107, 114, 128, alpha_byte)
    draw.ellipse([cave_x - 85, cave_y - 60, cave_x + 85, cave_y + 100], fill=rock_mid, outline=(240, 240, 240, alpha_byte), width=3)
    
    # Entrada de la cueva en arco negro
    cave_mouth = [(cave_x - 45, cave_y + 95), (cave_x - 45, cave_y + 10), (cave_x, cave_y - 25), (cave_x + 45, cave_y + 10), (cave_x + 45, cave_y + 95)]
    draw.polygon(cave_mouth, fill=(15, 18, 25, alpha_byte))
    # Brillo cálido de fogata en la cueva
    draw.ellipse([cave_x - 18, cave_y + 55, cave_x + 18, cave_y + 90], fill=(255, 140, 0, int(200 * alpha_fade)))

# -------------------------------------------------------------
# EFECTO 3: Hand-Drawn Write-On 'CHILL!!' (5.20s - 7.50s)
# -------------------------------------------------------------
def draw_chill(draw, W, H, rel_t, dur):
    write_dur = 1.3
    prog = min(1.0, rel_t / write_dur)
    
    alpha_fade = min(1.0, rel_t / 0.15) * min(1.0, (dur - rel_t) / 0.25)
    if alpha_fade <= 0:
        return
        
    alpha_byte = int(255 * alpha_fade)
    
    # Line boil sutil de animacion tradicional
    wobble = math.sin(rel_t * 28.0) * 2.0
    
    cx = W // 2
    cy = H // 2 + 80
    
    font_large = get_font(84, bold=True)
    full_text = "CHILL!!"
    
    # Cuantas letras revelar segun el tiempo
    num_letters = max(1, int(len(full_text) * prog))
    visible_text = full_text[:num_letters]
    
    # Bbox de referencia
    dummy = Image.new("RGBA", (10, 10))
    d_dummy = ImageDraw.Draw(dummy)
    bbox_full = d_dummy.textbbox((0, 0), full_text, font=font_large)
    tw_full = bbox_full[2] - bbox_full[0]
    th_full = bbox_full[3] - bbox_full[1]
    
    start_x = cx - tw_full // 2
    start_y = cy - th_full // 2
    
    # 1. Placa/Bocadillo de fondo dibujandose
    if prog > 0.1:
        pad = 28
        rect_w = int((tw_full + pad * 2) * prog)
        bx1 = start_x - pad
        by1 = start_y - pad
        bx2 = bx1 + rect_w
        by2 = start_y + th_full + pad
        
        # Sombra pop-art
        draw.rectangle([bx1 + 8, by1 + 8, bx2 + 8, by2 + 8], fill=(0, 0, 0, int(90 * alpha_fade)))
        # Fondo amarillo pastel vibrante #FFE66D
        draw.rectangle([bx1, by1, bx2, by2], fill=(255, 230, 109, alpha_byte), outline=(30, 30, 30, alpha_byte), width=5)

    # 2. Letras renderizadas con sombra pop
    # Sombra negra solida
    draw.text((start_x + 5, start_y + 5 + wobble), visible_text, font=font_large, fill=(30, 30, 30, alpha_byte))
    # Texto frontal turquesa energetico #4ECDC4
    draw.text((start_x, start_y + wobble), visible_text, font=font_large, fill=(78, 205, 196, alpha_byte))
    
    # 3. Lapiz/Marcador dibujando en la punta actual
    if prog < 1.0:
        bbox_curr = d_dummy.textbbox((0, 0), visible_text, font=font_large)
        pen_x = start_x + (bbox_curr[2] - bbox_curr[0]) + 10
        pen_y = start_y + th_full // 2
        # Trazador circular
        draw.ellipse([pen_x - 8, pen_y - 8, pen_x + 8, pen_y + 8], fill=(255, 107, 107, alpha_byte), outline=(30, 30, 30, alpha_byte), width=3)
        draw.line([pen_x, pen_y, pen_x + 20, pen_y - 25], fill=(30, 30, 30, alpha_byte), width=4)

    # 4. Estrellitas y destellos doodle al terminar la palabra
    if prog >= 0.85:
        sparkle_t = (rel_t - 1.1)
        pop = min(1.0, sparkle_t * 4.0)
        sparkle_col = (255, 107, 107, int(230 * alpha_fade))
        
        # Estrella izquierda
        s1x, s1y = start_x - 55, start_y - 15
        sz = int(20 * pop)
        draw.line([s1x - sz, s1y, s1x + sz, s1y], fill=sparkle_col, width=4)
        draw.line([s1x, s1y - sz, s1x, s1y + sz], fill=sparkle_col, width=4)
        
        # Estrella derecha
        s2x, s2y = start_x + tw_full + 50, start_y - 25
        draw.line([s2x - sz, s2y, s2x + sz, s2y], fill=sparkle_col, width=4)
        draw.line([s2x, s2y - sz, s2x, s2y + sz], fill=sparkle_col, width=4)

# -------------------------------------------------------------
# Motor de Composicion MoviePy
# -------------------------------------------------------------
base_clip = VideoFileClip("/content/input.mp4")
W, H = base_clip.size
print(f"Resolución de video base: {W}x{H}, Duración: {base_clip.duration:.2f}s")

# Definir tiempos exactos segun Whisper
t_storm_start, t_storm_end = 0.34, 2.20
t_refuge_start, t_refuge_end = 2.30, 4.80
t_chill_start,  t_chill_end  = 5.20, 7.50

def make_frame(t):
    base_frame = base_clip.get_frame(t).astype(np.float32) / 255.0
    
    # Crear lienzo transparente
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    
    # Efecto 1
    if t_storm_start <= t <= t_storm_end:
        draw_storm(draw, W, H, t - t_storm_start, t_storm_end - t_storm_start)
        
    # Efecto 2
    if t_refuge_start <= t <= t_refuge_end:
        draw_refuge(draw, W, H, t - t_refuge_start, t_refuge_end - t_refuge_start)
        
    # Efecto 3
    if t_chill_start <= t <= t_chill_end:
        draw_chill(draw, W, H, t - t_chill_start, t_chill_end - t_chill_start)
        
    # Mezcla alfa exacta
    overlay = np.array(canvas).astype(np.float32) / 255.0
    alpha = overlay[:, :, 3:4]
    rgb = overlay[:, :, :3]
    
    final_frame = base_frame * (1.0 - alpha) + rgb * alpha
    return (final_frame * 255).astype(np.uint8)

print("🎨 Renderizando composición con los 3 efectos de autor...")
final_video = VideoClip(make_frame, duration=base_clip.duration).set_fps(24)
if base_clip.audio is not None:
    final_video = final_video.set_audio(base_clip.audio)

output_path = "/content/resultado_custom.mp4"
final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
print("FIN_RENDER_CUSTOM")
'''

def main():
    print("🔑 Obteniendo token ADC...")
    token = get_token()
    
    print("🚀 Enviando compositor de autor a Colab...")
    res = exec_code(token, REMOTE_SCRIPT)
    print(res)
    
    print("📥 Descargando resultado_custom.mp4 a output/resultado.mp4...")
    get_code = """
import base64
with open('/content/resultado_custom.mp4', 'rb') as f:
    print('__B64__' + base64.b64encode(f.read()).decode('ascii') + '__B64__')
"""
    b64_res = exec_code(token, get_code)
    b64_content = b64_res.split("__B64__")[1].split("__B64__")[0].strip()
    
    dest_path = os.path.abspath("output/resultado.mp4")
    with open(dest_path, "wb") as f:
        f.write(base64.b64decode(b64_content))
        
    print(f"\n🎉 ¡OBRA MAESTRA FINALIZADA Y DESCARGADA!")
    print(f"📁 Video listo en: {dest_path}")
    print(f"⚖️ Tamaño final: {os.path.getsize(dest_path)} bytes")

if __name__ == "__main__":
    main()
