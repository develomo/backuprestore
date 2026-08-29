import sys
import os
from pathlib import Path

BASE_DIR = Path(r"D:\My Creation Video Generator\backup")
sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)

from batch_long_renderer import render_long_batch_memory

ASSETS = BASE_DIR / "assets" / "long"
OUTPUT = BASE_DIR / "outputs" / "terminal_test_final.mp4"

def get_first(folder, exts):
    p = ASSETS / folder
    if not p.exists(): return None
    for f in p.iterdir():
        if f.suffix.lower() in exts: return str(f)
    return None

voice = get_first("voices", {".mp3", ".wav", ".m4a"})
clips_dir = ASSETS / "clips"
clips = [str(f) for f in clips_dir.glob("*.mp4")] if clips_dir.exists() else []
music = get_first("music", {".mp3", ".wav"})
sfx = [str(f) for f in (ASSETS / "sfx").glob("*")] if (ASSETS / "sfx").exists() else []
intro = get_first("intro", {".mp4", ".mov"})
outro = get_first("outro", {".mp4", ".mov"})
subscribe = get_first("overlays", {".png", ".mov", ".mp4"})

# Hardcode the exact logo path
logo = BASE_DIR / "assets" / "long" / "watermark" / "luxuary lifestyle.png"
logo_path = str(logo) if logo.exists() else None

print("="*60)
print("TERMINAL DIRECT RENDER TEST (Bypassing UI)")
print("="*60)
print(f"Voice: {voice}")
print(f"Clips: {len(clips)} found")
print(f"Logo: {logo_path}")
print(f"Outro: {outro}")
print("="*60)

if not voice or not clips:
    print("ERROR: Voice or Clips missing!")
    sys.exit(1)

final_video = render_long_batch_memory(
    voice_path=voice,
    clips=clips,
    output_path=str(OUTPUT),
    music_path=music,
    sfx_files=sfx,
    intro_path=intro,
    outro_path=outro,
    subscribe_overlay=subscribe,
    quality="480p",
    fps=24,
    batch_size=2,
    final_quality="480p",
    add_captions=True,  # FORCE CAPTIONS
    caption_mode="phrase",
    style_id="phrase_crystal_cyan",
    custom_logo_path=logo_path, # FORCE LOGO
    wm_opacity=0.6,
    cleanup=True
)

print("\n" + "="*60)
print(f"✅ RENDER COMPLETE: {final_video}")
print("="*60)
print("\n👉 To open the video, copy and paste this command in terminal:")
print(f'start "" "{final_video}"')
