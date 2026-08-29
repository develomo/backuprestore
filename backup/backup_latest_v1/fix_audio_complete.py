import re
from pathlib import Path

def patch_audio_engine():
    file_path = Path("audio_engine.py")
    content = file_path.read_text(encoding="utf-8")
    
    # 1. Force consistent encoding in master_voice_audio
    # Find the run_cmd line for master_voice_audio and ensure -ar 44100 -ac 2
    old_voice = r'run_cmd\(\[FFMPEG, "-y", "-i", str\(voice\), "-vn", "-af", voice_filter\([^)]+\), "-c:a", "aac", "-b:a", "160k", str\(out\)\]'
    new_voice = r'run_cmd([FFMPEG, "-y", "-i", str(voice), "-vn", "-af", voice_filter(profile, normalize=normalize_loudness), "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "192k", str(out)])'
    content = re.sub(old_voice, new_voice, content)
    
    # 2. Force consistent encoding in build_audio_mix_file
    # Find the final cmd line for audio mix
    old_mix = r'run_cmd\(cmd, label="\[AudioPhase13\] build full audio mix"\)'
    # We need to modify the cmd list before run_cmd.
    # Actually, we'll insert a line to ensure the output is clean.
    # Instead of complex regex, we'll insert a replacement for the -c:a line.
    # We'll add -ar 44100 -ac 2 to the cmd list before -c:a aac.
    # We'll search for "-c:a", "aac" in the cmd list and add -ar and -ac before it.
    # Simpler: we can add a line after the cmd construction.
    # But since we are patching with regex, we'll replace the whole function.
    # We'll define a new version of build_audio_mix_file and replace it.
    # However, that's lengthy. We'll do a targeted patch: add -ar and -ac in the mux_audio_with_video as well.
    
    # 3. Patch mux_audio_with_video to use clean encoding
    # Find the line: "-c:a", "aac", "-b:a", "160k",
    old_mux_aac = r'("-c:a", "aac", "-b:a", "160k",)'
    new_mux_aac = r'"-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "192k",'
    content = re.sub(old_mux_aac, new_mux_aac, content)
    
    # Also patch the similar in build_audio_mix_file's final cmd
    # We'll do a broader replace: "-c:a", "aac", "-b:a", "160k" with "-ar 44100 -ac 2 -c:a aac -b:a 192k"
    content = content.replace('"-c:a", "aac", "-b:a", "160k"', '"-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "192k"')
    
    file_path.write_text(content, encoding="utf-8")
    print("✅ audio_engine.py patched with consistent encoding parameters.")

def patch_final_assembler():
    file_path = Path("final_assembler.py")
    content = file_path.read_text(encoding="utf-8")
    
    # Add a function to re-encode audio cleanly before muxing
    # We'll insert a helper function after the imports
    helper = '''
def _clean_audio_file(audio_path, output_path):
    """Re-encode audio to clean AAC with consistent parameters to avoid corruption."""
    from pathlib import Path
    import subprocess
    import shutil
    try:
        from audio_engine import FFMPEG, run_cmd
    except:
        FFMPEG = "ffmpeg"
        def run_cmd(cmd, label=None):
            if label: print(label, flush=True)
            cmd = [str(x) for x in cmd]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
            if result.returncode != 0:
                raise RuntimeError((result.stderr or "")[-4500:])
            return result
    inp = Path(audio_path)
    if not inp.exists():
        raise FileNotFoundError(f"Audio file not found: {inp}")
    out = Path(output_path) if output_path else inp.with_suffix(".clean.m4a")
    # Re-encode with consistent parameters
    cmd = [FFMPEG, "-y", "-i", str(inp), "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "192k", str(out)]
    try:
        run_cmd(cmd, label="[CleanAudio] Re-encoding audio to clean AAC")
        return str(out)
    except Exception as e:
        print(f"[CleanAudio] Re-encode failed: {e}; using original file", flush=True)
        shutil.copy2(inp, out)
        return str(out)
'''
    # Insert after imports (find last import line)
    lines = content.splitlines()
    insert_idx = -1
    for i, line in enumerate(lines):
        if line.startswith(("import ", "from ")):
            insert_idx = i
    if insert_idx != -1:
        lines.insert(insert_idx + 1, helper)
        content = "\n".join(lines)
        print("✅ Inserted _clean_audio_file helper.")
    else:
        content = helper + "\n" + content
        print("✅ Added _clean_audio_file at top.")
    
    # Modify mux_video_audio to call _clean_audio_file before muxing
    # Find the part where audio_path is used, and insert a cleaning step.
    # We'll replace the line where audio is defined with a cleaning call.
    # Look for: audio = Path(audio_path)
    # We'll add a line after that: clean_audio = _clean_audio_file(audio_path, audio.parent / "clean_audio.m4a") and use that.
    pattern = r'(audio = Path\(audio_path\))'
    replacement = r'\1\n    # Clean audio to avoid corruption\n    clean_audio = _clean_audio_file(audio_path, audio.parent / "clean_audio.m4a")\n    audio = Path(clean_audio)'
    content = re.sub(pattern, replacement, content)
    
    # Also modify the mux command to use the cleaned audio (already using 'audio' variable)
    
    file_path.write_text(content, encoding="utf-8")
    print("✅ final_assembler.py patched with audio cleaning step.")

if __name__ == "__main__":
    print("🔧 Starting audio fix...")
    patch_audio_engine()
    patch_final_assembler()
    print("\n🎉 All patches applied. Restart Streamlit and test.")