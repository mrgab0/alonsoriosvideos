import sys, os, json
sys.path.insert(0, "scripts")
from colab_bridge import get_token, ensure_active_runtime, execute_remote

token = get_token()
rt = ensure_active_runtime(token)

code = r'''
import os, json, subprocess
from faster_whisper import WhisperModel

if not os.path.exists("/content/audio.wav"):
    subprocess.run(["ffmpeg", "-y", "-i", "/content/input-3.mp4", "-vn", "-ar", "16000", "-ac", "1", "/content/audio.wav"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

model = WhisperModel("tiny", device="cpu", compute_type="int8")
segments, info = model.transcribe("/content/audio.wav", language="es", vad_filter=True, word_timestamps=True)

res = []
for s in segments:
    words = [{"word": w.word, "start": round(w.start, 2), "end": round(w.end, 2)} for w in s.words]
    res.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text, "words": words})

with open("/content/words_input3.json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False)

print("SAVED_WORDS_COUNT:", len(res))
for r in res:
    print(f"[{r['start']}s -> {r['end']}s]: {r['text']}")
'''

res = execute_remote(token, rt, code, timeout=120)
print(res.get("stdout", ""))
