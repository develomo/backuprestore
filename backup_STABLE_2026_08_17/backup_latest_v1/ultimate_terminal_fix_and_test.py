# ultimate_terminal_fix_and_test.py
# 100% TERMINAL DIRECT FIX - Bypasses Streamlit UI completely
import shutil
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "batch_long_renderer.py"

def fix_outro_looping_bug():
    """Fixes the bug where Outro was being looped along with the main body."""
    if not TARGET.exists():
        print("[ERROR] batch_long_renderer.py not found!")
        return False
    
    # Backup first
    backup = TARGET.with_suffix(".py.terminal_fix_backup")
    if not backup.exists():
        shutil.copy2(TARGET, backup)
        print(f"[OK] Backup created: {backup.name}")
        
    content = TARGET.read_text(encoding="utf-8")
    
    # Find the exact buggy block
    start_idx = content.find('outputs.append(outro_out)')
    end_idx = content.find('elif visual_duration > total_duration + .5:', start_idx)
    
    if start_idx != -1 and end_idx != -1:
        old_block = content[start_idx:end_idx]
        indent = len(old_block) - len(old_block.lstrip())
        ind = ' ' * indent
        
        new_block = f"""{ind}# FIX: Separate body from outro before looping
{ind}body_outputs = [p for p in outputs if p != outro_out]
{ind}if not body_outputs:
{ind}    raise RuntimeError("No visual outputs rendered for body")
{ind}video_raw = temp / "video_raw.mp4"
{ind}concat_files(body_outputs, video_raw, niche=preset.get("niche", "default"), use_transitions=True,
{ind}             global_indices=list(range(len(body_outputs))), chapter_flags=[False] * len(body_outputs))
{ind}safe_gc()
{ind}visual_duration = probe_duration(video_raw)
{ind}target_body_duration = total_duration - outro_sec
{ind}if visual_duration < target_body_duration - 0.5:
{ind}    extended = temp / "video_duration_fixed.mp4"
{ind}    log(f"[StableLong] visual shorter ({{visual_duration:.2f}} < {{target_body_duration:.2f}}); LOOPING body to match voice duration")
{ind}    run_cmd([
{ind}        FFMPEG, "-y", "-stream_loop", "-1", "-i", str(video_raw), "-t", f"{{target_body_duration:.3f}}",
{ind}        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", "-pix_fmt", "yuv420p",
{ind}        "-threads", "0", str(extended),
{ind}    ], timeout=600)
{ind}    video_raw = extended
{ind}
{ind}# NOW append outro at the very end
{ind}if outro_out and outro_out.exists():
{ind}    final_visual = temp / "final_visual_with_outro.mp4"
{ind}    log(f"[StableLong] Appending {{outro_sec}}s outro at the EXACT end")
{ind}    concat_files([video_raw, outro_out], final_visual, use_transitions=False)
{ind}    video_raw = final_visual
{ind}"""
        content = content[:start_idx] + new_block + content[end_idx:]
        TARGET.write_text(content, encoding="utf-8")
        print("[OK] Outro Looping Bug FIXED! (Outro will now only appear at the exact last 2 seconds)")
        return True
    else:
        print("[INFO] Outro block already fixed or not found.")
        return True

def create_terminal_test_script():
    """Creates a script to test rendering directly from terminal."""
    test_script = BASE_DIR / "terminal_test_long.py"
    
    code = """import sys
import os
from pathlib import Path

BASE_DIR = Path(r"D:\\My Creation Video Generator\\backup")
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

print("\\n" + "="*60)
print(f"✅ RENDER COMPLETE: {final_video}")
print("="*60)
print("\\n👉 To open the video, copy and paste this command in terminal:")
print(f'start "" "{final_video}"')
"""
    test_script.write_text(code, encoding="utf-8")
    print(f"[OK] Created terminal test script: {test_script.name}")

if __name__ == "__main__":
    print("🚀 Starting Ultimate Terminal Fix...")
    fix_outro_looping_bug()
    create_terminal_test_script()
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print("\n📋 NEXT STEPS (Run these commands one by one):")
    print("1. python terminal_test_long.py")
    print("2. Wait for render to finish.")
    print("3. Copy the 'start' command it gives you at the end to open the video!")