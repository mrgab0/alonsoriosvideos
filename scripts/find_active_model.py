import urllib.request
import json

with open(".env", "r") as f:
    key = [l.split("=")[1].strip() for l in f if l.startswith("NVIDIA_API_KEY")][0]

req = urllib.request.Request("https://integrate.api.nvidia.com/v1/models", headers={"Authorization": f"Bearer {key}"})
models = [m["id"] for m in json.loads(urllib.request.urlopen(req).read())["data"]]

found = 0
for m in models:
    data = json.dumps({"model": m, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}).encode("utf-8")
    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=data,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"🎯 MODELO ACTIVO: {m}")
            found += 1
            if found >= 3:
                break
    except urllib.error.HTTPError:
        pass
print("Búsqueda completada.")
