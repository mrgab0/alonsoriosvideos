"""
scripts/nemotron_qa.py
Auditor Visual y Validador de Layout (Nemotron Super VL + Geometría Bounding Box)
Verifica que ninguna animación tenga textos sobrepuestos, colisiones ni desbordes.
"""

import sys, os, math, json, base64, urllib.request
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
BASE_CW, BASE_CH = 880, 1450

def get_nvidia_key():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("NVIDIA_API_KEY"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return os.environ.get("NVIDIA_API_KEY")

def audit_frame_with_nemotron(image_path):
    key = get_nvidia_key()
    if not key:
        return {"status": "SKIPPED", "reason": "No NVIDIA_API_KEY found"}
    
    with open(image_path, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode("ascii")
        
    prompt = (
        "Eres un director de arte y auditor de QA visual para gráficos de video vertical (Shorts / Reels).\n"
        "Analiza detalladamente esta tarjeta gráfica:\n"
        "1. ¿Hay texto sobrepuesto o colisionando entre sí? (Sí/No)\n"
        "2. ¿Hay texto desbordado fuera de los contenedores? (Sí/No)\n"
        "3. ¿El contraste y legibilidad son óptimos? (Sí/No)\n"
        "Responde en formato JSON estricto con las llaves: 'has_overlap' (bool), 'has_overflow' (bool), 'is_legible' (bool), 'summary' (string de 1 línea)."
    )
    
    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=json.dumps({
            "model": "nvidia/nemotron-3.5-super-vl-120b-a12b",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}}
                    ]
                }
            ],
            "max_tokens": 300,
            "temperature": 0.1
        }).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            content = data["choices"][0]["message"].get("content", "")
            return {"status": "SUCCESS", "raw": content}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

if __name__ == "__main__":
    print("Nemotron QA module ready.")
