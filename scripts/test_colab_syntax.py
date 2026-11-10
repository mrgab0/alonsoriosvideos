import sys, os
sys.path.insert(0, "scripts")
from render_cli import load_profile
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)

with open("scripts/render_cli.py", "r", encoding="utf-8") as f:
    text = f.read()

# Extract colab_script
script_body = text.split("colab_script = r'''")[1].split("'''\n\n    colab_script = colab_script.replace")[0]
script_body = script_body.replace("__VIDEO_NAME__", "input-3.mp4")

print("Validando sintaxis de colab_script...")
res = execute_remote(token, rt, f"try:\n    compile({repr(script_body)}, '<string>', 'exec')\n    print('SYNTAX_OK')\nexcept Exception as e:\n    print('SYNTAX_ERROR:', e)")
print(res.get("stdout", ""))
print(res.get("stderr", ""))
