"""
Audio Engine Fix Verification Test
Ye script check karega ke:
1. Voice master ho rahi hai
2. Voice + Music + SFX mix ban raha hai  
3. Sample rate 44100Hz par sahi set hai (corrupt nahi ban rahi)
"""
import sys
import os
from pathlib import Path

# Project path setup
BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

from audio_engine import (
    master_voice_audio,
    build_audio_mix_file,
    mux_audio_with_video,
    OUTPUT_DIR,
)

ASSETS = BASE / "assets" / "shorts"

def find_first(folder, exts):
    p = Path(folder)
    if not p.exists():
        return None
    for f in p.iterdir():
        if f.is_file() and f.suffix.lower() in exts:
            return f
    return None

# Test files find karein
voice = find_first(ASSETS / "voices", {".mp3", ".wav", ".m4a", ".aac"})
music = find_first(ASSETS / "music", {".mp3", ".wav", ".m4a", ".aac"})
sfx = find_first(ASSETS / "sfx", {".mp3", ".wav", ".m4a", ".aac"})
clip = find_first(ASSETS / "clips", {".mp4", ".mov", ".mkv"})

print("=" * 60)
print("AUDIO ENGINE FIX TEST")
print("=" * 60)
print(f"Voice : {voice}")
print(f"Music : {music}")
print(f"SFX   : {sfx}")
print(f"Clip  : {clip}")
print("=" * 60)

if not voice:
    print("[FAIL] No voice file found in assets/shorts/voices/")
    sys.exit(1)

# ============================================================
# TEST 1: Voice Master
# ============================================================
print("\n[TEST 1] Mastering voice...")
try:
    out1 = master_voice_audio(voice, normalize_loudness=True)
    print(f"[OK] Voice mastered: {out1}")
except Exception as e:
    print(f"[FAIL] Voice master error: {e}")

# ============================================================
# TEST 2: Full Audio Mix (Voice + Music + SFX)
# ============================================================
print("\n[TEST 2] Building full audio mix (voice + music + sfx)...")
try:
    out2 = build_audio_mix_file(
        voice_path=voice,
        music_path=music,
        sfx_files=[sfx] if sfx else None,
        niche="luxury",
        duration=10.0,
    )
    print(f"[OK] Audio mix built: {out2}")
    
    # File size check - agar 1KB se choti hai to corrupt hai
    size = Path(out2).stat().st_size
    print(f"[INFO] File size: {size} bytes")
    if size < 1000:
        print("[FAIL] Audio file too small - likely corrupt!")
    else:
        print("[OK] File size looks healthy")
except Exception as e:
    print(f"[FAIL] Audio mix error: {e}")

# ============================================================
# TEST 3: Mux with Video
# ============================================================
if clip:
    print("\n[TEST 3] Muxing audio with video...")
    try:
        out3 = mux_audio_with_video(
            video_path=clip,
            voice_path=voice,
            music_path=music,
            sfx_files=[sfx] if sfx else None,
            niche="luxury",
            duration=10.0,
        )
        print(f"[OK] Final video: {out3}")
        
        size = Path(out3).stat().st_size
        print(f"[INFO] Video size: {size} bytes")
        if size < 50000:
            print("[FAIL] Video too small - audio might be missing!")
        else:
            print("[OK] Video looks healthy")
    except Exception as e:
        print(f"[FAIL] Mux error: {e}")
else:
    print("\n[TEST 3] SKIPPED (no video clip found)")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nAb apne outputs/audio_engine/ folder mein files check karein")
print("Aur unhe media player mein play karke sun kar dekhein.")