import sys
sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)

code = r'''
import subprocess, json
cmd = ["ffprobe", "-v", "error", "-show_streams", "-select_streams", "v:0", "-of", "json", "/content/input-3.mp4"]
res = subprocess.run(cmd, capture_output=True, text=True)
print("FFPROBE_OUTPUT:")
print(res.stdout)
'''
res = execute_remote(token, rt, code)
print(res.get("stdout", "") + res.get("stderr", ""))
