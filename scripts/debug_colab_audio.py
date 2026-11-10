import sys
sys.path.insert(0, "scripts")
from colab_bridge import get_token, list_runtimes, execute_remote

token = get_token()
rt = list_runtimes(token)[0]["name"]

remote_code = r'''
import os, wave
import numpy as np

wav_path = "/tmp/audio-16min.wav"
if not os.path.exists(wav_path):
    print("WAV does not exist")
else:
    with wave.open(wav_path, "rb") as wf:
        nframes = wf.getnframes()
        rate = wf.getframerate()
        channels = wf.getnchannels()
        raw = wf.readframes(nframes)
    arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    print(f"Channels: {channels}, Rate: {rate}, Frames: {nframes}, Duration: {nframes/rate:.1f}s")
    print(f"Max amp: {np.max(np.abs(arr)):.4f}, Mean amp: {np.mean(np.abs(arr)):.6f}")

    from faster_whisper import WhisperModel
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    
    # Try transcribing first 60 seconds
    first_60s = arr[:rate * 60]
    print(f"Transcribing first 60s (max amp: {np.max(np.abs(first_60s)):.4f})...")
    segments, info = model.transcribe(first_60s, vad_filter=False, beam_size=1)
    segs = list(segments)
    print(f"Detected Lang: {info.language} (prob {info.language_probability:.2f}), Segments: {len(segs)}")
    for s in segs[:5]:
        print(f"[{s.start:.1f} - {s.end:.1f}]: {s.text}")
'''

res = execute_remote(token, rt, remote_code)
print(res.get("stdout", "") + res.get("stderr", ""))
