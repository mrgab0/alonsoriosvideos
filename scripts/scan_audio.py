import sys
sys.path.insert(0, "scripts")
from colab_bridge import get_token, list_runtimes, execute_remote

token = get_token()
rt = list_runtimes(token)[0]["name"]

remote_code = r'''
import wave
import numpy as np

wav_path = "/tmp/audio-16min.wav"
with wave.open(wav_path, "rb") as wf:
    rate = wf.getframerate()
    nframes = wf.getnframes()
    raw = wf.readframes(nframes)

arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

# 1-second chunks
chunk_size = rate
n_chunks = len(arr) // chunk_size
active_seconds = []
for sec in range(n_chunks):
    chunk = arr[sec*chunk_size : (sec+1)*chunk_size]
    max_amp = np.max(np.abs(chunk))
    if max_amp > 0.05:
        active_seconds.append((sec, max_amp))

print(f"Total seconds: {n_chunks}")
print(f"Active seconds with sound: {len(active_seconds)}")
if active_seconds:
    print(f"First 10 active moments (second, peak): {active_seconds[:10]}")
    print(f"Last 5 active moments: {active_seconds[-5:]}")
else:
    print("NO AUDIO DETECTED ANYWHERE IN THE FILE!")
'''

res = execute_remote(token, rt, remote_code)
print(res.get("stdout", "") + res.get("stderr", ""))
