import sys, os, json
sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)
print("Runtime:", rt)

# Subir credencial
with open("credentials/drive_sa.json", "r") as f:
    sa_json = f.read()
execute_remote(token, rt, f"with open('/content/drive_sa.json', 'w') as f: f.write({repr(sa_json)})")

code = r'''
import os, subprocess, json

# Descargar si falta
if not os.path.exists("/content/input-3.mp4"):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    creds = service_account.Credentials.from_service_account_file('/content/drive_sa.json', scopes=['https://www.googleapis.com/auth/drive'])
    service = build('drive', 'v3', credentials=creds)
    files = service.files().list(q="name = 'input-3.mp4' and trashed = false", fields="files(id, name, size)").execute().get('files', [])
    fid = files[0]['id']
    req = service.files().get_media(fileId=fid)
    with open('/content/input-3.mp4', 'wb') as f:
        dl = MediaIoBaseDownload(f, req, chunksize=10*1024*1024)
        done = False
        while not done:
            status, done = dl.next_chunk()
    print("Descarga input-3.mp4 lista.")

# Whisper
try:
    from faster_whisper import WhisperModel
except ImportError:
    subprocess.run(["pip", "install", "-q", "faster-whisper"])
    from faster_whisper import WhisperModel

# Extraer audio wav
subprocess.run(["ffmpeg", "-y", "-i", "/content/input-3.mp4", "-vn", "-ar", "16000", "-ac", "1", "/content/audio.wav"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

model = WhisperModel("tiny", device="cpu", compute_type="int8")
segments, info = model.transcribe("/content/audio.wav", language="es", vad_filter=True, word_timestamps=True)

print("--- TRANSCRIPCIÓN DETALLADA CON TIMESTAMPS ---")
for s in segments:
    print(f"[{s.start:5.2f}s -> {s.end:5.2f}s] {s.text}")
    for w in s.words[:8]: # Muestra palabras
        print(f"     ({w.start:5.2f}s - {w.end:5.2f}s): {w.word}")
'''

res = execute_remote(token, rt, code, timeout=300)
print(res.get("stdout", ""))
