import sys
sys.path.insert(0, "scripts")
from colab_bridge import get_token, list_runtimes, execute_remote

token = get_token()
rt = list_runtimes(token)[0]["name"]

remote_code = r'''
import os, subprocess
from PIL import Image

os.makedirs('/content/keyframes', exist_ok=True)
# Extract frames at 30s, 90s, 180s, 300s, 450s, 600s, 750s, 900s
timestamps = [30, 90, 180, 300, 450, 600, 750, 900]
for ts in timestamps:
    out = f'/content/keyframes/frame_{ts}.jpg'
    subprocess.run(['ffmpeg', '-y', '-ss', str(ts), '-i', '/content/input-2.mp4', '-vframes', '1', '-q:v', '2', out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(out):
        print(f"Extracted frame at {ts}s: {os.path.getsize(out)} bytes")

# Print OCR / text or list of frames
print("Frames in /content/keyframes:", os.listdir('/content/keyframes'))
'''

res = execute_remote(token, rt, remote_code)
print(res.get("stdout", "") + res.get("stderr", ""))
