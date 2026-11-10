import sys
sys.path.insert(0, "scripts")
import urllib.request, json, base64

def get_nvidia_key():
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("NVIDIA_API_KEY"):
                return line.split("=")[1].strip()
    raise RuntimeError("NVIDIA_API_KEY not found")

# Get one frame from Colab
from colab_bridge import get_token, list_runtimes, execute_remote
token = get_token()
rt = list_runtimes(token)[0]["name"]

get_b64_code = '''
import base64
with open("/content/keyframes/frame_90.jpg", "rb") as f:
    print("__B64__" + base64.b64encode(f.read()).decode("ascii") + "__B64__")
'''
res = execute_remote(token, rt, get_b64_code)
b64_data = res.get("stdout", "").split("__B64__")[1].split("__B64__")[0].strip()

key = get_nvidia_key()
req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    data=json.dumps({
        "model": "nvidia/nemotron-3.5-super-vl-120b-a12b",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe brevemente qué se ve en esta captura de pantalla de video (código, terminal, aplicación, etc.):"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}}
                ]
            }
        ],
        "max_tokens": 500,
        "temperature": 0.2
    }).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    msg = data["choices"][0]["message"]
    print("Nemotron Vision description:", msg.get("content") or msg.get("reasoning_content"))
