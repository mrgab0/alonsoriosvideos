import sys, os, json
sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)

res = execute_remote(token, rt, "import json; print('===DATA==='); print(open('/content/words_input3.json').read() if os.path.exists('/content/words_input3.json') else 'NONE')")
raw = res.get("stdout", "")
if "===DATA===" in raw:
    content = raw.split("===DATA===")[1].strip()
    with open("output/words_input3.json", "w", encoding="utf-8") as f:
        f.write(content)
    print("Saved to output/words_input3.json. Size:", len(content))
