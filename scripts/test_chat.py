import urllib.request
import json

with open(".env", "r") as f:
    key = [l.split("=")[1].strip() for l in f if l.startswith("NVIDIA_API_KEY")][0]

test_models = [
    "meta/llama-3.1-8b-instruct",
    "meta/llama-3.3-70b-instruct",
    "mistralai/mistral-7b-instruct-v0.3",
    "microsoft/phi-3-mini-4k-instruct",
    "nvidia/llama-3.1-nemotron-70b-instruct"
]

for m in test_models:
    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=json.dumps({"model": m, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"✅ {m}: FUNCIONA! ({data['choices'][0]['message']['content'].strip()})")
            break
    except urllib.error.HTTPError as e:
        print(f"❌ {m}: {e.code}")
