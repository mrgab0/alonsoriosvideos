import time
import base64
import os
import sys

sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
runtime = ensure_active_runtime(token)

t0 = time.time()
with open("example/input-2.mp4", "rb") as f:
    data = f.read(450000)

b64 = base64.b64encode(data).decode("ascii")
code = f"""
import base64
with open('/content/test_chunk.bin', 'wb') as f:
    f.write(base64.b64decode('{b64}'))
"""
execute_remote(token, runtime, code)
check = execute_remote(token, runtime, "import os; print(os.path.getsize('/content/test_chunk.bin'))")
print(f"✅ Chunk 450KB escrito con éxito: {check.get('stdout', '').strip()} bytes en {time.time()-t0:.2f}s")
