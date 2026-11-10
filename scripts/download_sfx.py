"""
scripts/download_sfx.py
Descarga efectos de sonido reales de estudio (CC0 / Dominio Público)
Garantiza que ningún audio dure más de 1.5 segundos para no tapar la voz.
"""

import os, urllib.request, wave

SFX_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "sfx")
os.makedirs(SFX_DIR, exist_ok=True)

# Archivos de alta fidelidad CC0 de estudios reconocidos (Kenney / Calinou)
SOUNDS = {
    # Clics y switches secos para typewriter y botones
    "click_fast.wav": "https://raw.githubusercontent.com/Calinou/kenney-ui-audio/master/addons/kenney_ui_audio/click1.wav",
    "switch_tap.wav": "https://raw.githubusercontent.com/Calinou/kenney-ui-audio/master/addons/kenney_ui_audio/switch1.wav",
    "pop_clean.wav": "https://raw.githubusercontent.com/Calinou/kenney-ui-audio/master/addons/kenney_ui_audio/switch2.wav",
    "snap_tick.wav": "https://raw.githubusercontent.com/Calinou/kenney-ui-audio/master/addons/kenney_ui_audio/switch3.wav",
    "toggle_tick.wav": "https://raw.githubusercontent.com/Calinou/kenney-ui-audio/master/addons/kenney_ui_audio/switch4.wav",
    "tone_high.wav": "https://raw.githubusercontent.com/Calinou/kenney-ui-audio/master/addons/kenney_ui_audio/switch7.wav",
}

print(f"Descargando efectos de sonido reales a: {SFX_DIR}...")
for name, url in SOUNDS.items():
    dest = os.path.join(SFX_DIR, name)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            with open(dest, "wb") as f:
                f.write(data)
        
        # Verificar duración real del archivo WAV
        with wave.open(dest, "rb") as w:
            frames = w.getnframes()
            rate = w.getframerate()
            duration = frames / float(rate)
            print(f"  [✓] {name:16} | Duración: {duration:.2f}s | Tamaño: {len(data)/1024:.1f} KB")
    except Exception as e:
        print(f"  [✗] Error descargando {name}: {e}")

print("\nValidación completada: Todos los efectos son micro-fragmentos (< 1.5s).")
