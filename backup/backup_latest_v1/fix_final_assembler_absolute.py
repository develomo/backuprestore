import re
from pathlib import Path

file_path = Path("final_assembler.py")
content = file_path.read_text(encoding="utf-8")

# Complete new version of mux_video_audio (with absolute imports)
new_mux = '''
def mux_video_audio(video_path, audio_path, output_path=None, mode="SHORT", duration=None, final_4k=True, quality="high", fps=30, complexity="normal"):
    """Robust muxer using absolute imports."""
    from pathlib import Path
    import subprocess
    import shutil
    # Use absolute import to avoid relative import issues
    try:
        from audio_engine import run_cmd, probe_duration, FFMPEG
    except ImportError:
        # fallback: define local equivalents
        def run_cmd(cmd, label=None):
            if label:
                print(label, flush=True)
            cmd = [str(x) for x in cmd]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
            if result.returncode != 0:
                raise RuntimeError((result.stderr or "")[-4500:])
            return result
        def probe_duration(path):
            try:
                r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
                if r.returncode == 0:
                    return max(0.05, float(r.stdout.strip()))
            except:
                pass
            return 6.0
        FFMPEG = "ffmpeg"

    video = Path(video_path)
    if not video.exists():
        raise FileNotFoundError(f"Video file not found: {video}")
    
    out = Path(output_path) if output_path else video.with_name(video.stem + "_muxed.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    
    audio = Path(audio_path)
    audio_duration = None
    if audio.exists():
        try:
            audio_duration = probe_duration(audio)
        except Exception:
            audio_duration = None
    else:
        # Audio missing: create silent audio
        print("[mux] Audio file missing; creating silent audio.", flush=True)
        silent_audio = out.with_suffix(".silent.m4a")
        cmd = [FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-t", "1", "-c:a", "aac", str(silent_audio)]
        try:
            run_cmd(cmd, label="[mux] Create silent audio")
        except Exception as e:
            print(f"[mux] Could not create silent audio: {e}; copying video only", flush=True)
            shutil.copy2(video, out)
            return str(out)
        audio = silent_audio
        audio_duration = 1.0
    
    # Determine duration
    try:
        video_duration = probe_duration(video)
    except Exception:
        video_duration = None
    
    if duration is None:
        duration = video_duration or audio_duration or 30.0
    else:
        duration = float(duration)
    
    # Build mux command
    cmd = [FFMPEG, "-y", "-i", str(video), "-i", str(audio)]
    cmd += ["-map", "0:v:0", "-map", "1:a:0"]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "160k"]
    cmd += ["-shortest"]
    cmd += ["-movflags", "+faststart"]
    cmd += [str(out)]
    
    try:
        run_cmd(cmd, label="[mux] mux_video_audio")
    except Exception as e:
        print(f"[mux] mux failed: {e}; falling back to video-only copy", flush=True)
        shutil.copy2(video, out)
    
    return str(out)
'''

# Replace the entire mux_video_audio function definition (from def line to the end of the function)
# We'll find where it starts and replace until a new line that is not indented (top-level)
# Using regex to match the whole function body.

pattern = r'def mux_video_audio\([^)]*\):.*?(?=\n\S|$)'
content = re.sub(pattern, new_mux, content, flags=re.DOTALL)

file_path.write_text(content, encoding="utf-8")
print("✅ final_assembler.py updated with absolute imports in mux_video_audio.")