import sys
sys.path.insert(0, "scripts")
from colab_bridge import get_token, list_runtimes, execute_remote

token = get_token()
rt = list_runtimes(token)[0]["name"]

code = r'''
import os, time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

dest = "/content/resultado-16min.mp4"
if not os.path.exists(dest):
    print("El archivo resultado-16min.mp4 no existe aún!")
else:
    size = os.path.getsize(dest)
    print(f"Subiendo {dest} ({size / (1024*1024):.1f} MB) a Google Drive...")

    creds = service_account.Credentials.from_service_account_file(
        '/content/drive_sa.json',
        scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=creds)
    output_folder_id = "1yBF7fEkpy6A_VdHlG9T6qbJxGroSapDJ"

    media = MediaFileUpload(dest, mimetype='video/mp4', resumable=True)
    body = {
        'name': 'resultado-16min.mp4',
        'parents': [output_folder_id]
    }
    req = service.files().create(body=body, media_body=media, fields='id, name')
    
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"Progreso subida a Drive: {int(status.progress() * 100)}%")

    print(f"✅ SUBIDA EXITOSA! ID en Drive: {response.get('id')}")
'''

res = execute_remote(token, rt, code)
print(res.get("stdout", "") + res.get("stderr", ""))
