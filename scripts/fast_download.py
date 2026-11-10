"""
Descarga directa de resultado-16min.mp4 desde Colab en bloques de 1.5 MB
"""
import sys
import os
import base64
import time

sys.path.insert(0, "scripts")
from colab_bridge import get_token, list_runtimes, execute_remote

token = get_token()
rt = list_runtimes(token)[0]["name"]

remote_path = "/content/resultado-16min.mp4"
local_dest = os.path.abspath("output/resultado-16min.mp4")
os.makedirs("output", exist_ok=True)

# Obtener tamaño remoto
res = execute_remote(token, rt, f"import os; print('__SZ__' + str(os.path.getsize('{remote_path}')) + '__SZ__')")
total_bytes = int(res.get("stdout", "").split("__SZ__")[1].split("__SZ__")[0])
print(f"📦 Tamaño total a transferir: {total_bytes / (1024*1024):.1f} MB ({total_bytes} bytes)")

chunk_size = 1500000 # 1.5 MB por bloque (~83 bloques)
offset = 0
mode = "wb"

# Si ya existe parcialmente, verificar si podemos resumir
if os.path.exists(local_dest):
    cur = os.path.getsize(local_dest)
    if cur == total_bytes:
        print(f"✅ Archivo ya completo localmente: {local_dest}")
        sys.exit(0)

t0 = time.time()
with open(local_dest, "wb") as f_out:
    block = 1
    total_blocks = (total_bytes + chunk_size - 1) // chunk_size
    while offset < total_bytes:
        req_sz = min(chunk_size, total_bytes - offset)
        code = f"""
import base64
with open('{remote_path}', 'rb') as f:
    f.seek({offset})
    data = f.read({req_sz})
    print('__B64__' + base64.b64encode(data).decode('ascii') + '__B64__')
"""
        res = execute_remote(token, rt, code, timeout=60)
        out = res.get("stdout", "")
        if "__B64__" not in out:
            print(f"[!] Error leyendo bloque {block}, reintentando...")
            time.sleep(1)
            continue
        
        b64 = out.split("__B64__")[1].split("__B64__")[0].strip()
        binary = base64.b64decode(b64)
        f_out.write(binary)
        f_out.flush()
        offset += len(binary)
        
        pct = int(offset * 100 / total_bytes)
        print(f"📥 [{pct:3d}%] Bloque {block}/{total_blocks} ({offset // 1048576}MB / {total_bytes // 1048576}MB)", flush=True)
        block += 1

elapsed = time.time() - t0
print("\n" + "=" * 60)
print(f"🎉 ARCHIVO LISTO EN LOCAL: {local_dest}")
print(f"⏱️ Tiempo de transferencia: {elapsed:.1f}s ({offset / (1024*1024):.1f} MB)")
print("=" * 60)
