import urllib.request
import json
import os

with open(".env", "r") as f:
    lines = f.readlines()
    key = [l.split("=")[1].strip() for l in lines if l.startswith("NVIDIA_API_KEY")][0]

req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/models",
    headers={"Authorization": f"Bearer {key}"}
)

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        models = [m["id"] for m in data.get("data", [])]
        print(f"✅ NVIDIA NIM Conectado! Total de modelos disponibles: {len(models)}")
        # Filtrar modelos clave
        nemotrons = [m for m in models if "nemotron" in m.lower()]
        print("Modelos Nemotron disponibles:")
        for nm in nemotrons[:5]:
            print(f"  - {nm}")
except Exception as ex:
    print(f"❌ Error al conectar con NVIDIA: {ex}")
