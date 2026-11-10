import sys, os
sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)

code = r'''
import os, subprocess, json, urllib.request

video_path = "/content/resultado-input-3-IAshorts.mp4"
if not os.path.exists(video_path):
    print("ERROR: Archivo no existe!")
else:
    size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"Subiendo {video_path} ({size_mb:.1f} MB) a Gofile...")
    
    req = urllib.request.urlopen('https://api.gofile.io/servers')
    data = json.loads(req.read().decode())
    server = data['data']['servers'][0]['name']
    
    cmd = ['curl', '-s', '-F', f'file=@{video_path}', f'https://{server}.gofile.io/contents/uploadfile']
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    try:
        g_res = json.loads(res.stdout)
        url = g_res['data']['downloadPage']
        print(f"🎉 GOFILE_IASHORTS_FINAL_URL: {url}")
    except Exception as e:
        print("Error parseando respuesta gofile:", res.stdout, e)
'''

res = execute_remote(token, rt, code, timeout=180)
print(res.get("stdout", ""))
print(res.get("stderr", ""))
