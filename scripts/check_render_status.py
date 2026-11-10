import sys, os, time
sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)

code = r'''
import os, time, subprocess

now = time.time()
print("Archivos en /content:")
for f in os.listdir("/content"):
    p = os.path.join("/content", f)
    if os.path.isfile(p):
        age_sec = now - os.path.getmtime(p)
        print(f"  {f}: {os.path.getsize(p)/(1024*1024):.2f} MB (modificado hace {int(age_sec)}s)")

# Ver si ffmpeg corre
ps = subprocess.check_output(["ps", "aux"]).decode()
ffmpeg_procs = [l for l in ps.splitlines() if "ffmpeg" in l and "<defunct>" not in l]
print(f"FFMPEG_CORRIENDO: {len(ffmpeg_procs)}")
for p in ffmpeg_procs:
    print("  ", p[:100])
'''

res = execute_remote(token, rt, code)
print(res.get("stdout", ""))
