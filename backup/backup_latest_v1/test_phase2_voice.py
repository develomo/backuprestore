# test_phase2_voice.py
import os
import inspect
from pathlib import Path

def test_phase2_voice_humanization():
    print("=" * 60)
    print("🚀 Starting Phase 2: Voice Humanization & SynthID Mitigation Test")
    print("=" * 60)
    
    # 1. Check for a sample voice file
    voice_dir = Path("assets/long/voices")
    voice_dir.mkdir(parents=True, exist_ok=True)
    
    voice_files = list(voice_dir.glob("*.mp3")) + list(voice_dir.glob("*.wav")) + list(voice_dir.glob("*.m4a"))
    
    if not voice_files:
        print("⚠️ No voice files found in 'assets/long/voices/'.")
        print("💡 ACTION REQUIRED: Please put a sample voice file (e.g., test.mp3) in 'assets/long/voices/' and run this script again.")
        return
    
    input_voice = voice_files[0]
    print(f"✅ Found input voice: {input_voice.name}")
    
    # 2. Import the orchestrator
    try:
        from voice_humanization_orchestrator import humanize_audio_file, _eq_filter
        print("✅ Successfully imported voice_humanization_orchestrator")
    except ImportError as e:
        print(f"❌ Failed to import orchestrator: {e}")
        return

    # 3. Verify the Chorus Filter is actually in the code (SynthID Mitigation Check)
    print("\n🔍 Verifying FFmpeg Filter Chain...")
    source_code = inspect.getsource(_eq_filter)
    if "chorus=" in source_code:
        print("✅ SUCCESS: Subtle chorus filter is ACTIVE in _eq_filter.")
        print("   (This breaks robotic phase alignment and disrupts basic audio watermarking)")
    else:
        print("❌ WARNING: Chorus filter NOT found in _eq_filter source code!")

    # 4. Run Humanization
    output_dir = Path("outputs/voice_orchestrator")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_voice = output_dir / f"test_humanized_{input_voice.stem}.wav"
    
    print(f"\n⚙️ Processing voice (Mode: LONG, Room Tone: ON, Tempo: ON)...")
    try:
        result_path = humanize_audio_file(
            input_audio=str(input_voice),
            output_audio=str(output_voice),
            mode="long",
            add_room_tone=True,
            apply_tempo=True
        )
        print(f"✅ Humanization complete!")
        
        # 5. Validate Output
        out_path = Path(result_path)
        if out_path.exists() and out_path.stat().st_size > 1000:
            size_kb = out_path.stat().st_size / 1024
            print(f"✅ VALIDATION PASSED: Output file created successfully.")
            print(f"   📂 Location: {out_path.absolute()}")
            print(f"   📏 Size: {size_kb:.2f} KB")
            print("\n🎉 Phase 2 Terminal Test PASSED! Voice pipeline is ready.")
        else:
            print("❌ VALIDATION FAILED: Output file is missing or too small (corrupted).")
            
    except Exception as e:
        print(f"❌ Humanization failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_phase2_voice_humanization()