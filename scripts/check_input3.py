import sys
import os
sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)
print(f"Runtime: {rt}")

# Subir credencial de servicio
with open("credentials/drive_sa.json", "r") as f:
    sa_json_str = f.read()
execute_remote(token, rt, f"""
with open('/content/drive_sa.json', 'w') as f:
    f.write({repr(sa_json_str)})
""")

code = r'''
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    '/content/drive_sa.json',
    scopes=['https://www.googleapis.com/auth/drive']
)
service = build('drive', 'v3', credentials=creds)

files = service.files().list(
    q="trashed = false",
    fields="files(id, name, size)"
).execute().get('files', [])

print(f"TOTAL FILES FOUND: {len(files)}")
for f in files:
    print(f"FILE: {f['name']} | ID: {f['id']} | Size: {f.get('size')} bytes")
'''

res = execute_remote(token, rt, code)
print(res.get("stdout", "") + res.get("stderr", ""))
