from pathlib import Path
import inspect, re, json, subprocess, sys

ROOT = Path.cwd()
FILES = [
    "app.py",
    "safe_long_video_polished.py",
    "batch_long_renderer.py",
    "caption_engine.py",
]

print("CWD:", ROOT)
print("PYTHON:", sys.version)

for name in FILES:
    p = ROOT / name
    print("\n===", name, "exists:", p.exists(), "size:", p.stat().st_size if p.exists() else None)
    if not p.exists():
        continue
    txt = p.read_text(encoding="utf-8", errors="ignore")
    for key in [
        "BatchLongRouter",
        "BatchLong",
        "run_integrated_long_pipeline",
        "render_long_batch_memory",
        "add_captions",
        "caption_mode",
        "style_id",
        "words_path",
        "subscribe",
        "subscribe_overlay",
        "scale=",
        "force_original_aspect_ratio=increase",
        "crop=",
        "setdar=16/9",
        "ffmpeg_final_upscale",
        "1080p",
        "final_quality",
    ]:
        print(f"{key:38} ->", txt.find(key))

print("\n--- IMPORT CHECK ---")
try:
    import safe_long_video_polished as sl
    print("safe_long imported:", sl.__file__)
    print("long signature:", inspect.signature(sl.run_integrated_long_pipeline))
except Exception as e:
    print("safe_long import error:", repr(e))

try:
    import batch_long_renderer as br
    print("batch imported:", br.__file__)
    print("batch signature:", inspect.signature(br.render_long_batch_memory))
    print("vf source contains setdar:", "setdar=16/9" in inspect.getsource(br.vf))
    print("render func contains burn_captions:", "burn_captions" in inspect.getsource(br.render_long_batch_memory))
except Exception as e:
    print("batch import error:", repr(e))

print("\n--- LONG ASSET FOLDERS ---")
for sub in [
    "assets/long/voices",
    "assets/long/clips",
    "assets/long/music",
    "assets/long/sfx",
    "assets/long/intro",
    "assets/long/outro",
    "assets/long/subscribe",
    "assets/long/overlays",
]:
    p = ROOT / sub
    files = list(p.glob("*")) if p.exists() else []
    print(sub, "exists:", p.exists(), "count:", len(files), "sample:", [x.name for x in files[:5]])

print("\n--- OUTPUT VIDEO PROBE ---")
outs = sorted((ROOT / "outputs").glob("*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True) if (ROOT / "outputs").exists() else []
if outs:
    latest = outs[0]
    print("latest:", latest)
    try:
        cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=width,height,display_aspect_ratio",
               "-of", "json", str(latest)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(r.stdout)
        print(r.stderr)
    except Exception as e:
        print("ffprobe failed:", e)
else:
    print("No outputs found")