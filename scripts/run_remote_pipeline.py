"""
Runs the full HyperFrames pipeline on Google Colab via MCP:
1. Uploads local input video to Colab VM.
2. Installs required dependencies remotely.
3. Transcribes words with Whisper in Colab.
4. Generates motion graphics over the video in Colab.
5. Downloads the rendered MP4 directly to local output/ directory.
Zero local RAM used. Zero browser needed.
"""
import sys
import os
import argparse
from colab_bridge import get_token, get_active_runtime, execute_remote, upload_file, download_file

PIPELINE_CODE = r'''
import os, sys, gc, json, tempfile, wave, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 1. Asegurar dependencias
try:
    import faster_whisper
    from moviepy.editor import VideoFileClip, VideoClip
except ImportError:
    print("[Colab] Instalando dependencias...")
    subprocess.run(["pip", "install", "-q", "faster-whisper", "moviepy==1.0.3", "Pillow", "imageio-ffmpeg"], check=True)
    from moviepy.editor import VideoFileClip, VideoClip
    from faster_whisper import WhisperModel

import imageio_ffmpeg
from faster_whisper import WhisperModel
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

def hex_to_rgba(h, a=1.0):
    h = h.lstrip("#")
    if len(h) == 6:
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (int(255 * a),)
    return (255, 255, 255, int(255 * a))

def get_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def parse_pos(pos, W, H, default_y=None):
    if default_y is None:
        default_y = H // 2
    if not isinstance(pos, (list, tuple)) or len(pos) < 2:
        return (W // 2, default_y)
    x = W // 2 if pos[0] == "center" else (int(pos[0]) if isinstance(pos[0], (int, float)) else W // 2)
    if pos[1] == "center":
        y = H // 2
    elif pos[1] == "bottom":
        y = H - 160
    elif pos[1] == "top":
        y = 160
    elif isinstance(pos[1], (int, float)):
        y = int(pos[1])
    else:
        y = default_y
    return (x, y)

def effect_lower_third(W, H, fx):
    start, end = fx["start"], fx["end"]
    dur = end - start
    color = hex_to_rgba(fx.get("color", "#FFFFFF"))
    bg = hex_to_rgba(fx.get("bg_color", "#000000"), fx.get("bg_opacity", 0.75))
    fontsize = fx.get("fontsize", 42)
    offset_y = fx.get("offset_y", 140)
    pos_y = H - offset_y
    text = fx.get("text", "")
    font = get_font(fontsize, bold=True)
    dummy = Image.new("RGBA", (10, 10))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=1)
    pad = 24
    tw = (bbox[2] - bbox[0]) + 2 * pad
    th = (bbox[3] - bbox[1]) + 2 * pad
    def make_frame(t):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        bx = (W - tw) // 2
        by = pos_y - th // 2
        draw.rectangle([bx, by, bx + tw, by + th], fill=bg)
        draw.text((bx + pad - bbox[0], by + pad - bbox[1]), text, font=font, fill=color, stroke_width=1)
        return np.array(img)
    clip = VideoClip(make_frame, duration=dur)
    return clip.set_start(start)

def effect_highlight(W, H, fx):
    start, end = fx["start"], fx["end"]
    dur = end - start
    center = parse_pos(fx.get("position", ["center", "center"]), W, H, default_y=H // 2)
    radius = fx.get("radius", 110)
    color = hex_to_rgba(fx.get("color", "#FFD700"))
    opacity = fx.get("opacity", 0.45)
    anim = fx.get("animation", "pulse")
    def make_frame(t):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        r = radius
        if anim == "pulse":
            r = radius * (1.0 + 0.18 * math.sin(2 * math.pi * t * 3))
        bbox = [center[0] - r, center[1] - r, center[0] + r, center[1] + r]
        fill = (*color[:3], int(color[3] * opacity))
        draw.ellipse(bbox, fill=fill, outline=(*color[:3], 230), width=4)
        return np.array(img)
    clip = VideoClip(make_frame, duration=dur)
    return clip.set_start(start)

def build_clips(W, H, effects):
    clips = []
    for fx in effects:
        ft = fx.get("type")
        if ft == "lower_third": clips.append(effect_lower_third(W, H, fx))
        elif ft == "highlight": clips.append(effect_highlight(W, H, fx))
    return clips

def ensure_rgba(frame):
    if frame.ndim == 3 and frame.shape[2] == 4:
        return frame
    if frame.ndim == 3 and frame.shape[2] == 3:
        alpha = np.full((frame.shape[0], frame.shape[1], 1), 255, dtype=np.uint8)
        return np.dstack([frame, alpha])
    return frame

def render_video(input_path, output_path, effects, fps=24):
    base = VideoFileClip(input_path)
    W, H = base.size
    overlay_clips = build_clips(W, H, effects)
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
            frame[:, :, :3] = frame[:, :, :3] * (1.0 - alpha) + rgb * alpha
        return (frame[:, :, :3] * 255).astype(np.uint8)
    final_clip = VideoClip(compose_frame, duration=base.duration)
    final_clip = final_clip.set_fps(fps)
    if base.audio is not None:
        final_clip = final_clip.set_audio(base.audio)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    final_clip.write_videofile(output_path, fps=fps, codec="libx264",
                               audio_codec="aac", temp_audiofile="temp-audio.m4a",
                               remove_temp=True, verbose=False, logger=None)
    print(f"✅ Render completado: {output_path}")

def extract_audio(video_path, wav_path):
    cmd = [FFMPEG_EXE, "-y", "-i", video_path,
           "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def load_wav_as_array(wav_path):
    with wave.open(wav_path, "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    dtype = np.int16 if sample_width == 2 else np.int32
    audio = np.frombuffer(raw, dtype=dtype)
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels)[:, 0]
    return audio.astype(np.float32) / 32768.0

def process_pipeline(input_video, output_video, keyword="storm", effect="highlight", duration=1.5):
    print("🎵 [1/4] Extrayendo audio...")
    wav_path = "/tmp/audio.wav"
    extract_audio(input_video, wav_path)
    
    print("🎤 [2/4] Transcribiendo con Whisper tiny en CPU...")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    audio_arr = load_wav_as_array(wav_path)
    segments, info = model.transcribe(audio_arr, word_timestamps=True, vad_filter=True, beam_size=1)
    
    words = []
    print(f"🗣️ Idioma: {info.language}")
    print("📝 Palabras detectadas:")
    for s in segments:
        for w in s.words:
            print(f"   [{w.start:.2f}s - {w.end:.2f}s] {w.word}")
            words.append({"word": w.word, "start": round(float(w.start), 3), "end": round(float(w.end), 3)})
    
    del model
    gc.collect()
    
    print(f"🔍 [3/4] Buscando palabra clave: '{keyword}'...")
    effects = []
    for w in words:
        if keyword.lower() in w["word"].strip().lower():
            effects.append({
                "type": effect,
                "start": w["start"],
                "end": round(w["start"] + duration, 3),
                "text": w["word"],
                "position": ["center", "center"],
                "offset_y": 140,
                "fontsize": 42,
                "color": "#FFFFFF",
                "bg_color": "#000000",
                "bg_opacity": 0.85,
                "animation": "pulse"
            })
    
    # Si no coincide la palabra exacta, usar la primera palabra detectada para demostración
    if not effects and words:
        fallback_word = words[0]
        print(f"⚠️ '{keyword}' no encontrada. Usando primera palabra detectada: '{fallback_word['word']}'")
        effects.append({
            "type": effect,
            "start": fallback_word["start"],
            "end": round(fallback_word["start"] + duration, 3),
            "text": fallback_word["word"],
            "position": ["center", "center"],
            "offset_y": 140,
            "fontsize": 42,
            "color": "#FFFFFF",
            "bg_color": "#000000",
            "bg_opacity": 0.85,
            "animation": "pulse"
        })
        
    print(f"✅ Efectos generados: {len(effects)}")
    print(f"🎬 [4/4] Renderizando video con {effect}...")
    render_video(input_video, output_video, effects, fps=24)
    print("🎉 Pipeline finalizado con éxito.")
'''

def main():
    parser = argparse.ArgumentParser(description="Ejecutar Hyperframes en Colab MCP")
    parser.add_argument("--input", default="example/input.mp4", help="Video de entrada")
    parser.add_argument("--output", default="output/resultado.mp4", help="Destino del video renderizado")
    parser.add_argument("--keyword", default="storm", help="Palabra clave a detectar")
    parser.add_argument("--effect", default="highlight", help="Efecto: highlight o lower_third")
    args = parser.parse_args()

    input_file = os.path.abspath(args.input)
    output_file = os.path.abspath(args.output)

    if not os.path.exists(input_file):
        # Fallback to sample/input.mp4
        if os.path.exists("sample/input.mp4"):
            input_file = os.path.abspath("sample/input.mp4")
        else:
            print(f"[!] Archivo de entrada no encontrado: {args.input}", file=sys.stderr)
            sys.exit(1)

    print("🔑 Obteniendo token de autenticación...")
    token = get_token()
    print("🛰️ Conectando con máquina activa en Colab...")
    runtime = get_active_runtime(token)
    if not runtime:
        print("[!] No hay runtimes activos. Crea uno primero.", file=sys.stderr)
        sys.exit(1)
    print(f"💻 Runtime remoto: {runtime}")

    # 1. Subir video
    remote_input = "/content/input.mp4"
    remote_output = "/content/resultado.mp4"
    upload_file(token, runtime, input_file, remote_input)

    # 2. Ejecutar pipeline
    remote_runner = f"""
{PIPELINE_CODE}
process_pipeline('{remote_input}', '{remote_output}', keyword='{args.keyword}', effect='{args.effect}')
"""
    print("⚡ Ejecutando pipeline en la nube de Google Colab...")
    execute_remote(token, runtime, remote_runner)

    # 3. Descargar resultado
    download_file(token, runtime, remote_output, output_file)
    print(f"\n🎉 ¡LISTO! Tu video fue renderizado en la nube y guardado localmente en:")
    print(f"👉 {output_file}")

if __name__ == "__main__":
    main()
