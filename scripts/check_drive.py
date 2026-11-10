import sys
import os

sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)

code = """
import os
try:
    from google.colab import drive
    if not os.path.exists('/content/drive/MyDrive'):
        drive.mount('/content/drive', force_remount=False)
    p = '/content/drive/MyDrive/hyperframes/input'
    print('Drive montado!')
    if os.path.exists(p):
        print('Archivos en hyperframes/input:', os.listdir(p))
    else:
        print('Contenido en MyDrive:', [x for x in os.listdir('/content/drive/MyDrive') if not x.startswith('.')][:10])
except Exception as e:
    print('Excepcion en Colab Drive:', e)
"""

res = execute_remote(token, rt, code)
print(res.get("stdout", "") + res.get("stderr", ""))
