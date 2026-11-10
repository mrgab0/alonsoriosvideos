import sys
sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)

check_script = r'''
import subprocess, json
res = subprocess.run([
    'ffprobe', '-v', 'error', 
    '-select_streams', 'v:0', 
    '-show_entries', 'stream=width,height,codec_name:stream_tags=rotate:stream_side_data=rotation', 
    '-of', 'json', '/content/input-3.mp4'
], capture_output=True, text=True)
print("FFPROBE_DATA:")
print(res.stdout)
'''

res = execute_remote(token, rt, check_script)
print(res.get("stdout", "") + res.get("stderr", ""))
