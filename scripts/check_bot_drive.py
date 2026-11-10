import sys
sys.path.insert(0, 'scripts')
from colab_bridge import get_token, list_runtimes, execute_remote

token = get_token()
rts = list_runtimes(token)
if not rts:
    print("No runtimes found")
    sys.exit(1)
rt = rts[0]['name']

code = '''
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    '/content/drive_sa.json',
    scopes=['https://www.googleapis.com/auth/drive']
)
service = build('drive', 'v3', credentials=creds)

files = service.files().list(
    q="trashed = false",
    fields="files(id, name, mimeType, size)"
).execute().get('files', [])

print(f"TOTAL_FILES: {len(files)}")
for f in files:
    print(f"FILE: {f['name']} | ID: {f['id']} | Size: {f.get('size')} bytes")
'''

res = execute_remote(token, rt, code)
print(res.get('stdout', '') + res.get('stderr', ''))
