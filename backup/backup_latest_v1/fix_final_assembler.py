import re
from pathlib import Path

file_path = Path("final_assembler.py")
content = file_path.read_text(encoding="utf-8")

# 1. Define the new robust mux_video_audio function
new_mux_function = '''
def mux_video_audio(video_path, audio_path, output_path=None, mode="SHORT", duration=None, final_4k=True, quality="high", fps=30, complexity="normal"):
    """
    Robust muxer with error handling and fallback to silent audio.
    """
    video = Path(video_path)
    if not video.exists():
        raise FileNotFoundError(f"Video file not found: {video}")
    
    out = Path(output_path) if output_path else video.with_name(video.stem + "_muxed.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    
    audio = Path(audio_path)
    audio_duration = None
    if audio.exists():
        # Get audio duration
        try:
            from .audio_engine import probe_duration
            audio_duration = probe_duration(audio)
        except Exception:
            audio_duration = None
    else:
        # No audio file, create silent audio
        safe_print("[mux] Audio file missing; creating silent audio.")
        silent_audio = out.with_suffix(".silent.m4a")
        from .audio_engine import run_cmd
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-t", "1", "-c:a", "aac", str(silent_audio)]
        try:
            run_cmd(cmd, label="[mux] Create silent audio")
        except Exception:
            # fallback: use a existing audio file? but we skip
            safe_print("[mux] Could not create silent audio; continuing without audio (video only)")
            # We'll just copy video directly
            import shutil
            shutil.copy2(video, out)
            return str(out)
        audio = silent_audio
        audio_duration = 1.0
    
    # Determine duration: use provided or video duration
    try:
        from .audio_engine import probe_duration
        video_duration = probe_duration(video)
    except Exception:
        video_duration = None
    
    if duration is None:
        duration = video_duration or audio_duration or 30.0
    else:
        duration = float(duration)
    
    # Build ffmpeg command
    cmd = ["ffmpeg", "-y", "-i", str(video), "-i", str(audio)]
    cmd += ["-map", "0:v:0", "-map", "1:a:0"]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "160k"]
    cmd += ["-shortest"]
    cmd += ["-movflags", "+faststart"]
    cmd += [str(out)]
    
    try:
        from .audio_engine import run_cmd
        run_cmd(cmd, label="[mux] mux_video_audio")
    except Exception as e:
        # If mux fails, attempt to copy video as fallback
        safe_print(f"[mux] mux failed: {e}; falling back to video-only copy")
        import shutil
        shutil.copy2(video, out)
    
    return str(out)
'''

# 2. Find and replace the existing mux_video_audio function
# Pattern to match the whole function definition
pattern = r'def mux_video_audio\([^)]*\):.*?(?=\n\S|$)'
# Use DOTALL to match across lines
content = re.sub(pattern, new_mux_function, content, flags=re.DOTALL)

file_path.write_text(content, encoding="utf-8")
print("✅ final_assembler.py updated with robust mux_video_audio.")