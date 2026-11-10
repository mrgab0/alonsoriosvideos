import sys, os, json
sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)

code = r'''
import os, json
p = "/content/transcript_input3.json"
if os.path.exists(p):
    with open(p, "r", encoding="utf-8") as f:
        print("TRANSCRIPT_CONTENT_START")
        print(f.read())
        print("TRANSCRIPT_CONTENT_END")
else:
    print("NO_FILE")
'''
res = execute_remote(token, rt, code)
print(res.get("stdout", ""))
