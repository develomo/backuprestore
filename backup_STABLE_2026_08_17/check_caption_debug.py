import os, sys, inspect
from pathlib import Path

print("PYTHON:", sys.version)
print("CWD:", os.getcwd())

print("\n--- Whisper check ---")
try:
    import whisper
    print("whisper installed:", whisper.__file__)
except Exception as e:
    print("whisper error:", repr(e))

print("\n--- Pipeline functions ---")
import master_pipeline
for name in [
    "run_integrated_short_pipeline",
    "apply_integrated_visual_layers",
    "apply_visual_layers",
    "_auto_caption_words_if_missing",
    "add_captions_to_video",
]:
    obj = getattr(master_pipeline, name, None)
    print(name, "=", bool(obj))
    if obj:
        try:
            print("signature:", inspect.signature(obj))
        except Exception as e:
            print("signature error:", e)

print("\n--- Voice files ---")
voice_dir = Path("assets/shorts/voices")
print("voice_dir exists:", voice_dir.exists())
for p in sorted(voice_dir.glob("*")):
    print(p.name, p.suffix, p.stat().st_size)

print("\n--- Transcript json files near voice ---")
for p in sorted(voice_dir.glob("*.json")):
    print("json:", p.name, p.stat().st_size)

print("\n--- Caption words search indicators ---")
text = Path("master_pipeline.py").read_text(encoding="utf-8", errors="ignore")
for term in ["warning impact now alert", "warning", "_auto_caption_words_if_missing", "apply_integrated_visual_layers", "transcript", "whisper"]:
    print(term, "=>", text.find(term))