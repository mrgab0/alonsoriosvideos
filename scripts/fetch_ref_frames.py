import sys, os, json, base64
sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)

code = r'''
import os, json, base64

targets = ["frame_002.png", "frame_005.png", "frame_010.png", "frame_018.png"]
data = {}
for t in targets:
    p = os.path.join("/content/ref_frames", t)
    if os.path.exists(p):
        with open(p, "rb") as f:
            data[t] = base64.b64encode(f.read()).decode("utf-8")

print("REF_FRAMES_START")
print(json.dumps(data))
print("REF_FRAMES_END")
'''

res = execute_remote(token, rt, code)
raw = res.get("stdout", "")
if "REF_FRAMES_START" in raw and "REF_FRAMES_END" in raw:
    data = json.loads(raw.split("REF_FRAMES_START")[1].split("REF_FRAMES_END")[0].strip())
    os.makedirs("output/ref_frames", exist_ok=True)
    for k, b64 in data.items():
        fp = f"output/ref_frames/{k}"
        with open(fp, "wb") as f:
            f.write(base64.b64decode(b64))
        print(f"Downloaded: {fp} ({os.path.getsize(fp)/1024:.1f} KB)")
