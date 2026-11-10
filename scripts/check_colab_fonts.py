import sys, os
sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)

code = r'''
import os, subprocess, urllib.request

# Ver qué fuentes TTF ya existen
found = []
for root, dirs, files in os.walk("/usr/share/fonts"):
    for f in files:
        if f.endswith(".ttf"):
            found.append(os.path.join(root, f))
print("FONTS_FOUND:", found[:15])

# Instalar fonts dejavu si no están
if not found:
    subprocess.run(["apt-get", "update", "-qq"], stdout=subprocess.DEVNULL)
    subprocess.run(["apt-get", "install", "-y", "-qq", "fonts-dejavu", "fonts-liberation"], stdout=subprocess.DEVNULL)
    for root, dirs, files in os.walk("/usr/share/fonts"):
        for f in files:
            if f.endswith(".ttf"):
                found.append(os.path.join(root, f))
    print("AFTER_INSTALL:", found[:15])
'''
res = execute_remote(token, rt, code)
print(res.get("stdout", ""))
print(res.get("stderr", ""))
