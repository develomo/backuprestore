from pathlib import Path
from batch_long_renderer import render_long_batch_memory

def main():
    # Auto-detect assets from your folders
    voice_dir = Path("assets/long/voices")
    clips_dir = Path("assets/long/clips")

    # Pehli available voice file dhundho (.mp3, .wav, .m4a)
    voice_files = list(voice_dir.glob("*.mp3")) + list(voice_dir.glob("*.wav")) + list(voice_dir.glob("*.m4a"))
    # Pehli available clip files dhundho (.mp4, .mov, .mkv)
    clip_files = list(clips_dir.glob("*.mp4")) + list(clips_dir.glob("*.mov")) + list(clips_dir.glob("*.mkv"))

    if not voice_files:
        print("❌ Error: assets/long/voices mein koi audio file nahi mili.")
        return
    if not clip_files:
        print("❌ Error: assets/long/clips mein koi video file nahi mili.")
        return

    voice_path = str(voice_files[0])
    # Sirf pehli 5 clips use karein (test ke liye)
    clips = [str(f) for f in clip_files[:5]]

    print(f"🔊 Voice file: {voice_path}")
    print(f"🎬 Clips count: {len(clips)}")

    print("\n⏳ Render start ho raha hai with Captions FORCE ON...")

    # Ye raha actual render call
    output = render_long_batch_memory(
        voice_path=voice_path,
        clips=clips,
        add_captions=True,           # Isko True karte hi captions ON ho jayenge
        caption_mode="phrase",       # "phrase" style use karein
        style_id="phrase_premium_white",  # Koi bhi valid style daal dein
        quality="480p",
        final_quality="480p"
    )

    print(f"\n✅ Render complete! Video saved at: {output}")

if __name__ == "__main__":
    main()