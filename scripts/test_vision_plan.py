import sys
sys.path.insert(0, "scripts")
import urllib.request, json, base64

def get_nvidia_key():
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("NVIDIA_API_KEY"):
                return line.split("=")[1].strip()
    raise RuntimeError("NVIDIA_API_KEY not found")

# Read 3 keyframes from Colab
from colab_bridge import get_token, list_runtimes, execute_remote
token = get_token()
rt = list_runtimes(token)[0]["name"]

get_frames_code = '''
import base64
for ts in [90, 300, 600, 750]:
    with open(f"/content/keyframes/frame_{ts}.jpg", "rb") as f:
        print(f"__F_{ts}__" + base64.b64encode(f.read()).decode("ascii") + f"__F_{ts}__")
'''
res = execute_remote(token, rt, get_frames_code)
stdout = res.get("stdout", "")

frames_b64 = {}
for ts in [90, 300, 600, 750]:
    tag = f"__F_{ts}__"
    if tag in stdout:
        frames_b64[ts] = stdout.split(tag)[1].split(tag)[0].strip()

print(f"Captured {len(frames_b64)} keyframes for Nemotron Super VL")

content_list = [
    {
        "type": "text",
        "text": """Eres el Director de Motion Graphics para un canal de programación estilo Fazt Web.
Este video de 16 minutos (969 segundos) es una demostración técnica en pantalla.
Observa las capturas de pantalla adjuntas (a los 90s, 300s, 600s, 750s).

Tu tarea es diseñar entre 6 y 8 efectos visuales estilo Fazt Web a lo largo del video:
- 'terminal_code': Ventana macOS oscura (#1E1E2E) con 3 botones de colores y código relevante en syntax highlighting (máximo 4 líneas).
- 'tech_pill': Insignia flotante moderna con nombre de framework / tecnología y subtítulo.

IMPORTANTE: 
1. En 'code_lines', USA SIEMPRE comillas simples ' dentro del texto (NUNCA comillas dobles ").
2. Responde ÚNICAMENTE con el bloque JSON con la siguiente estructura:
```json
{
  "effects": [
    {
      "type": "terminal_code",
      "start": 45.0,
      "end": 50.0,
      "title": "config.js",
      "code_lines": ["const agent = require('pi');", "agent.start();"]
    },
    {
      "type": "tech_pill",
      "start": 120.0,
      "end": 125.0,
      "tech": "PYTHON",
      "subtitle": "Runtime Engine"
    }
  ]
}
```"""
    }
]

for ts, b64 in frames_b64.items():
    content_list.append({"type": "text", "text": f"Captura a los {ts} segundos:"})
    content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

key = get_nvidia_key()
req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    data=json.dumps({
        "model": "nvidia/nemotron-3.5-super-vl-120b-a12b",
        "messages": [
            {"role": "user", "content": content_list}
        ],
        "max_tokens": 4096,
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
    text = msg.get("content") or msg.get("reasoning_content")
    print("RAW TEXT FROM NEMOTRON:\n", text)
    # Extract JSON
    if "```json" in text:
        clean = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        clean = text.split("```")[1].split("```")[0].strip()
    else:
        clean = text[text.find("{"):text.rfind("}")+1]
    
    try:
        plan = json.loads(clean)
    except Exception as e:
        print("Initial JSON parse error:", e)
        # Fix unescaped quotes in code_lines array
        import re
        def fix_quotes(match):
            inner = match.group(1)
            # Replace internal double quotes not preceded by backslash with single quotes
            fixed = re.sub(r'(?<!\\)"', "'", inner)
            return f': ["{fixed}"]'
        fixed_clean = re.sub(r':\s*\[\s*"([^\]]+)"\s*\]', fix_quotes, clean)
        try:
            plan = json.loads(fixed_clean)
        except Exception:
            # Fallback: simple eval with null/true/false or ast
            import ast
            eval_clean = clean.replace("true", "True").replace("false", "False").replace("null", "None")
            plan = ast.literal_eval(eval_clean)
    print("Parsed Plan successfully:", len(plan.get("effects", [])), "effects!")
    for fx in plan.get("effects", []):
        print(f"[{fx['start']}s - {fx['end']}s] {fx['type']}: {fx.get('title') or fx.get('tech')}")
