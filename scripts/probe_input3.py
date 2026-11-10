import sys
sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)

# Subir credencial a Colab
with open("credentials/drive_sa.json", "r") as f:
    sa_json = f.read()

execute_remote(token, rt, f"""
with open('/content/drive_sa.json', 'w') as f:
    f.write({repr(sa_json)})
""")

code = r'''
import os, subprocess
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

creds = service_account.Credentials.from_service_account_file(
    '/content/drive_sa.json',
    scopes=['https://www.googleapis.com/auth/drive']
)
service = build('drive', 'v3', credentials=creds)

files = service.files().list(
    q="name = 'input-3.mp4' and trashed = false",
    fields="files(id, name, size)"
).execute().get('files', [])

fid = files[0]['id']
dest = '/content/input-3.mp4'
if not os.path.exists(dest):
    print("Descargando input-3.mp4...")
    req = service.files().get_media(fileId=fid)
    with open(dest, 'wb') as fh:
        dl = MediaIoBaseDownload(fh, req, chunksize=20*1024*1024)
        done = False
        while not done:
            status, done = dl.next_chunk()
    print("Descarga completa.")

# Check video streams and rotation
res = subprocess.run(['ffprobe', '-i', dest], capture_output=True, text=True)
print("FFPROBE_STDERR:")
for line in res.stderr.splitlines():
    if 'Stream #0:' in line or 'displaymatrix' in line or 'rotation' in line or 'rotate' in line or 'Video:' in line:
        print("  ", line)
'''

res = execute_remote(token, rt, code)
print(res.get("stdout", "") + res.get("stderr", ""))
