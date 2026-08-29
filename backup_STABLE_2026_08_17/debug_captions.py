import sys
import traceback
from pathlib import Path

# Project ke modules import karein
from batch_long_renderer import load_caption_words, group_caption_words, burn_captions

def main():
    print("="*60)
    print("🔍 CAPTIONS DEEP DEBUG SCRIPT")
    print("="*60)

    # 1. Auto-detect pehli voice file
    voice_dir = Path("assets/long/voices")
    voice_files = list(voice_dir.glob("*.mp3")) + list(voice_dir.glob("*.wav")) + list(voice_dir.glob("*.m4a"))
    
    if not voice_files:
        print("❌ Voice file nahi mili! assets/long/voices mein kuch daalein.")
        return
    
    voice_path = voice_files[0]
    print(f"🎤 Voice file: {voice_path}")

    # 2. Pehli clip file (burn captions ke liye ek video chahiye)
    clips_dir = Path("assets/long/clips")
    clip_files = list(clips_dir.glob("*.mp4")) + list(clips_dir.glob("*.mov"))
    
    if not clip_files:
        print("❌ Clip file nahi mili! assets/long/clips mein kuch daalein.")
        return
    
    clip_path = clip_files[0]
    print(f"🎬 Clip file: {clip_path}")

    # 3. STEP 1: Check if load_caption_words returns anything
    print("\n📝 STEP 1: load_caption_words test...")
    try:
        words = load_caption_words(
            voice_path=str(voice_path),
            words=None,
            words_path=None,
            transcript_text=None,
            total_duration=30.0  # test duration
        )
        print(f"   ✅ load_caption_words returned {len(words)} words.")
        if len(words) > 0:
            print(f"   Sample: {words[:2]}")
        else:
            print("   ⚠️ WARNING: 0 words returned! Whisper may have failed.")
    except Exception as e:
        print(f"   ❌ EXCEPTION in load_caption_words: {e}")
        traceback.print_exc()
        return

    # 4. STEP 2: Check if group_caption_words works
    print("\n📝 STEP 2: group_caption_words test...")
    try:
        segments = group_caption_words(words, mode="phrase", style_id="phrase_premium_white", niche="default")
        print(f"   ✅ group_caption_words returned {len(segments)} segments.")
        if len(segments) > 0:
            print(f"   Sample: {segments[:2]}")
        else:
            print("   ⚠️ WARNING: 0 segments! Captions will not render.")
    except Exception as e:
        print(f"   ❌ EXCEPTION in group_caption_words: {e}")
        traceback.print_exc()
        return

    # 5. STEP 3: Actually run burn_captions on a real video
    print("\n📝 STEP 3: Running ACTUAL burn_captions test...")
    output_video = Path("outputs") / "debug_captions_test.mp4"
    output_video.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = burn_captions(
            video=str(clip_path),
            out=str(output_video),
            voice_path=str(voice_path),
            words=words,
            caption_mode="phrase",
            style_id="phrase_premium_white",
            size=(854, 480),
            niche='default'
        )
        print(f"   ✅ burn_captions completed successfully!")
        print(f"   📹 Output video saved at: {result}")
        
        # Check if output file exists and has size
        if Path(result).exists():
            size_mb = Path(result).stat().st_size / (1024 * 1024)
            print(f"   📊 File size: {size_mb:.2f} MB")
        else:
            print("   ❌ Output file not found!")

    except Exception as e:
        print(f"   ❌ EXCEPTION in burn_captions: {e}")
        traceback.print_exc()
        return

    print("\n" + "="*60)
    print("✅ Debug complete. Output video path dekhein aur captions check karein.")
    print("="*60)

if __name__ == "__main__":
    main()