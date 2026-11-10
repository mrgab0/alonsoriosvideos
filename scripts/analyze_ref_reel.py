import sys, os
sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)

code = r'''
import subprocess, os, json

print("Instalando yt-dlp...")
subprocess.run(["pip", "install", "-q", "-U", "yt-dlp"])

ref_url = "https://www.facebook.com/reel/1454529902811491/"
out_path = "/content/ref_video.mp4"

# Intentar descargar
print(f"Descargando reel de referencia: {ref_url} ...")
cmd = ["yt-dlp", "-f", "b/best", "--no-warnings", "-o", out_path, ref_url]
res = subprocess.run(cmd, capture_output=True, text=True)

print("STDOUT:", res.stdout[:500])
print("STDERR:", res.stderr[:500])

if os.path.exists(out_path):
    print(f"✅ Video descargado! Tamaño: {os.path.getsize(out_path)/(1024*1024):.1f} MB")
    # Extraer 5 fotogramas clave
    os.makedirs("/content/ref_frames", exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", out_path,
        "-vf", "fps=1", "/content/ref_frames/frame_%03d.png"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    frames = os.listdir("/content/ref_frames")
    print("FRAMES_EXTRACTED:", len(frames), sorted(frames)[:10])
else:
    print("❌ No se pudo descargar el reel directamente.")
'''

res = execute_remote(token, rt, code, timeout=120)
print(res.get("stdout", ""))
