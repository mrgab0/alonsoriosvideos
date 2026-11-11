"""
scripts/update_sfx_palette.py
Descarga la paleta expandida de efectos de sonido con alto contraste auditivo.
Todos son micro-fragmentos (< 0.3s) bajo licencia CC0.
"""

import os, urllib.request, wave

SFX_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "sfx")
os.makedirs(SFX_DIR, exist_ok=True)

NEW_SOUNDS = {
    "ding_confirm.wav": "https://raw.githubusercontent.com/Calinou/kenney-interface-sounds/master/addons/kenney_interface_sounds/confirmation_001.wav",
    "sub_drop.wav": "https://raw.githubusercontent.com/Calinou/kenney-interface-sounds/master/addons/kenney_interface_sounds/drop_001.wav",
    "key_tick.wav": "https://raw.githubusercontent.com/Calinou/kenney-interface-sounds/master/addons/kenney_interface_sounds/tick_001.wav",
    "crystal_glass.wav": "https://raw.githubusercontent.com/Calinou/kenney-interface-sounds/master/addons/kenney_interface_sounds/glass_001.wav"
}

for name, url in NEW_SOUNDS.items():
    dest = os.path.join(SFX_DIR, name)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    with open(dest, "wb") as f:
        f.write(data)
    with wave.open(dest, "rb") as w:
        dur = w.getnframes() / w.getframerate()
        print(f"  [✓] {name:18} | {dur:.2f}s | {len(data)/1024:.1f} KB")

print("\nPaleta sonora expandida lista.")
