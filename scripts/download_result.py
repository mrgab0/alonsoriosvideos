"""
Download resultado-16min.mp4 from Colab in 750KB chunks to local output/
"""
import sys
import os
import json
import base64
import time

sys.path.insert(0, "scripts")
from colab_bridge import get_token, list_runtimes, execute_remote

token = get_token()
rts = list_runtimes(token)
if not rts:
    print("No active runtimes found")
    sys.exit(1)
rt = rts[0]["name"]

remote_path = "/content/resultado-16min.mp4"
local_dir = "output"
os.makedirs(local_dir, exist_ok=True)
local_dest = os.path.join(local_dir, "resultado-16min.mp4")

# Check remote size
res = execute_remote(token, rt, f"import os; print('__SIZE__' + str(os.path.getsize('{remote_path}')) + '__SIZE__')")
stdout = res.get("stdout", "")
total_bytes = int(stdout.split("__SIZE__")[1].split("__SIZE__")[0])
print(f"📦 Archivo remoto verificado: {total_bytes / (1024*1024):.1f} MB ({total_bytes} bytes)")

chunk_size = 750000 # 750 KB por bloque
offset = 0

# Check existing partial download for resume
if os.path.exists(local_dest):
    offset = os.path.getsize(local_dest)
    if offset >= total_bytes:
        print(f"✅ Archivo ya descargado completamente: {local_dest} ({offset} bytes)")
        sys.exit(0)
    print(f"Resumiendo descarga desde byte {offset} ({offset / (1024*1024):.1f} MB)...")

mode = "ab" if offset > 0 else "wb"
t0 = time.time()
with open(local_dest, mode) as f_out:
    block_num = offset // chunk_size + 1
    while offset < total_bytes:
        req_size = min(chunk_size, total_bytes - offset)
        code = f"""
import base64
with open('{remote_path}', 'rb') as f:
    f.seek({offset})
    b = f.read({req_size})
    print('__B64__' + base64.b64encode(b).decode('ascii') + '__B64__')
"""
        res = execute_remote(token, rt, code)
        out = res.get("stdout", "")
        if "__B64__" not in out:
            print(f"[!] Error en bloque {block_num}: No base64 tag found. Reintentando...")
            time.sleep(1)
            continue

        b64_data = out.split("__B64__")[1].split("__B64__")[0].strip()
        binary = base64.b64decode(b64_data)
        f_out.write(binary)
        f_out.flush()
        offset += len(binary)
        
        elapsed = time.time() - t0
        pct = (offset / total_bytes) * 100
        speed_kb = (offset / 1024) / max(0.1, elapsed)
        
        if block_num % 10 == 0 or offset >= total_bytes:
            print(f"   [{pct:5.1f}%] {offset / (1024*1024):.1f} / {total_bytes / (1024*1024):.1f} MB - Bloque {block_num} ({speed_kb:.0f} KB/s)", flush=True)
        block_num += 1

print("\n" + "=" * 60)
print(f"🎉 DESCARGA COMPLETA: {local_dest}")
print(f"⚖️ Tamaño final: {os.path.getsize(local_dest)} bytes ({os.path.getsize(local_dest) / (1024*1024):.1f} MB)")
print("=" * 60)
