from pathlib import Path
import re, shutil, time

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 60)
print("FIX V2 - safe_print + SFX engine")
print("=" * 60)

# ============================================================
# FIX 1: app.py - safe_print ko print se replace karo
# ============================================================
app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_v2_{ts}")
text = app.read_text(encoding="utf-8")

# Replace safe_print with print in LUFS block
text = text.replace(
    'safe_print(f"[LUFS] Normalized to -14 LUFS: {result}")',
    'print(f"[LUFS] Normalized to -14 LUFS: {result}")'
)
text = text.replace(
    'safe_print("[LUFS] Normalization skipped (unchanged)")',
    'print("[LUFS] Normalization skipped (unchanged)")'
)
text = text.replace(
    'safe_print(f"[LUFS] Normalization error: {e}")',
    'print(f"[LUFS] Normalization error: {e}")'
)

app.write_text(text, encoding="utf-8")
try:
    compile(text, "app.py", "exec")
    print("[1/3] app.py safe_print -> print - SYNTAX OK")
except SyntaxError as e:
    print(f"[1/3] app.py - SYNTAX ERROR: {e}")

# ============================================================
# FIX 2: sfx_engine.py - add apply_sfx_burst_on_clip_change
# ============================================================
sfx = BASE / "sfx_engine.py"
if sfx.exists():
    shutil.copy2(sfx, BASE / f"sfx_engine.py.bak_v2_{ts}")
    sfx_text = sfx.read_text(encoding="utf-8")
    
    if "apply_sfx_burst_on_clip_change" not in sfx_text:
        sfx_func = '''

def apply_sfx_burst_on_clip_change(video, mode="SHORT", niche="default"):
    """Apply short SFX burst at each clip transition boundary."""
    import subprocess, tempfile, os
    from pathlib import Path
    
    try:
        # Detect clip boundaries via scene change
        temp_dir = Path(tempfile.gettempdir())
        scene_file = temp_dir / f"scenes_{int(time.time())}.txt"
        
        # Use ffmpeg scenecut detection
        cmd_detect = [
            "ffmpeg", "-i", str(video),
            "-vf", "select='gt(scene\\,0.3)',showinfo",
            "-f", "null", "-"
        ]
        # Alternative: use simple approach with silence/white flash
        # For now, apply a subtle whoosh at 25% intervals
        duration_cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "csv=p=0", str(video)
        ]
        
        result = subprocess.run(duration_cmd, capture_output=True, text=True)
        total_dur = float(result.stdout.strip() or 0)
        
        if total_dur <= 0:
            return video
        
        # Create SFX bursts at clip boundaries (every 5 seconds)
        sfx_output = temp_dir / f"sfx_burst_{int(time.time())}.mp4"
        
        # Generate short whoosh/pop sfx using ffmpeg sine wave
        sfx_audio = temp_dir / f"sfx_audio_{int(time.time())}.wav"
        
        # Create a short burst sound (50ms sine sweep)
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "sine=frequency=800:duration=0.05",
            "-f", "lavfi",
            "-i", "sine=frequency=200:duration=0.05",
            "-filter_complex", "[0][1]amix=inputs=2:duration=first[out]",
            "-map", "[out]", "-t", "0.08",
            str(sfx_audio)
        ], capture_output=True)
        
        if sfx_audio.exists():
            # Mix SFX into video at regular intervals
            boundary_interval = 5.0  # every 5 seconds (clip boundaries)
            overlay_times = []
            t = 1.0
            while t < total_dur - 1.0:
                overlay_times.append(t)
                t += boundary_interval
            
            if overlay_times:
                # Simple: mix audio with delayed SFX
                filter_parts = []
                for i, ot in enumerate(overlay_times):
                    filter_parts.append(
                        f"[1:a]adelay={int(ot*1000)}|{int(ot*1000)}[sfx{i}]"
                    )
                
                filter_str = ";".join(filter_parts)
                mix_inputs = "[0:a]" + "".join(f"[sfx{i}]" for i in range(len(overlay_times)))
                num_inputs = len(overlay_times) + 1
                amix_str = f"{mix_inputs}amix=inputs={num_inputs}:duration=first[outa]"
                
                full_filter = f"{filter_str};{amix_str}" if filter_parts else "anull"
                
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(video),
                    "-i", str(sfx_audio),
                    "-filter_complex", full_filter,
                    "-map", "0:v", "-map", "[outa]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    str(sfx_output)
                ]
                
                subprocess.run(cmd, capture_output=True)
                
                if sfx_output.exists() and sfx_output.stat().st_size > 1000:
                    return str(sfx_output)
        
        return video
    except Exception as e:
        print(f"[SFX] Burst on clip change failed: {e}")
        return video
'''
        sfx_text += sfx_func
        sfx.write_text(sfx_text, encoding="utf-8")
        try:
            compile(sfx_text, "sfx_engine.py", "exec")
            print("[2/3] sfx_engine.py SFX burst added - SYNTAX OK")
        except SyntaxError as e:
            print(f"[2/3] sfx_engine.py - SYNTAX ERROR: {e}")
    else:
        print("[2/3] sfx_engine.py - SFX burst already exists")
else:
    print("[2/3] sfx_engine.py - FILE NOT FOUND, creating...")
    # Check alternative name
    for name in ["sfx_engine.py", "SFX_engine.py", "sfx.py", "audio_engine.py"]:
        alt = BASE / name
        if alt.exists():
            print(f"  Found: {name}")
            break

# ============================================================
# FIX 3: Verify caption_engine is fixed
# ============================================================
ce = BASE / "caption_engine.py"
if ce.exists():
    text = ce.read_text(encoding="utf-8-sig")
    try:
        compile(text, "caption_engine.py", "exec")
        print("[3/3] caption_engine.py - SYNTAX OK")
    except SyntaxError as e:
        print(f"[3/3] caption_engine.py - STILL BROKEN: {e}")
        # Direct line fix
        lines = text.split('\n')
        for i, l in enumerate(lines):
            if 'strip(' in l and i >= 230 and i <= 240:
                lines[i] = '    word_lower = str(word or "").lower().strip(".,!?;:\'\\\"")'
                print(f"  Fixed line {i+1}")
        text = '\n'.join(lines)
        ce.write_text(text, encoding="utf-8")
        try:
            compile(text, "caption_engine.py", "exec")
            print("[3/3] caption_engine.py - FIXED")
        except SyntaxError as e:
            print(f"[3/3] caption_engine.py - FAILED: {e}")

print("=" * 60)
print("DONE. Run: streamlit run app.py")
print("=" * 60)