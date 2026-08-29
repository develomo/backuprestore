from pathlib import Path
import re, shutil, time

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 60)
print("FIX V3 - No Skip + SFX on Clip Change + Caption Timing")
print("=" * 60)

# ============================================================
# FIX 1: SFX - mode variable scope fix + clip-boundary SFX
# ============================================================
mp = BASE / "master_pipeline.py"
shutil.copy2(mp, BASE / f"master_pipeline.py.bak_v3_{ts}")
text = mp.read_text(encoding="utf-8")

# Fix: SFX block mein mode variable accessible hai - ensure it's in scope
old_sfx_block = """    if add_sfx_burst and video is not None:
        try:
            from sfx_engine import apply_sfx_burst_on_clip_change
            video = apply_sfx_burst_on_clip_change(video, mode=mode, niche=niche)
            safe_print("[MasterPipeline] SFX burst applied on clip boundaries")
        except Exception as e:
            safe_print(f"[MasterPipeline] SFX burst skipped: {e}")"""

new_sfx_block = """    if add_sfx_burst and video is not None:
        try:
            from sfx_engine import apply_sfx_burst_on_clip_change
            _sfx_mode = plan.get("mode", "SHORT")
            _sfx_niche = plan.get("niche", "default")
            video = apply_sfx_burst_on_clip_change(video, mode=_sfx_mode, niche=_sfx_niche)
            print("[MasterPipeline] SFX burst applied on clip boundaries")
        except Exception as e:
            print(f"[MasterPipeline] SFX burst skipped: {e}")"""

if old_sfx_block in text:
    text = text.replace(old_sfx_block, new_sfx_block)
    print("[1/5] SFX mode fix applied")
else:
    print("[1/5] SFX block not found, searching...")
    idx = text.find("if add_sfx_burst and video is not None:")
    if idx != -1:
        snippet = text[idx:idx+400]
        print(f"  Found at offset {idx}, preview: {snippet[:150]}...")

# ============================================================
# FIX 2: Remove LOW RAM skip - force zoom/beat/story always
# ============================================================
# Find LOW RAM skip blocks and force them to run
old_skip1 = '''    # LOW RAM: skip heavy visual layers (zoom/beat/story) when video is already composite
    if isinstance(video, str) and "_composite" in str(video).lower():
        safe_print("[MasterPipeline] 41% | LOW RAM visual layers: zoom/beat/story skipped safely")
        return video

    words = _mp_apply_caption_timing_offset(words or [], -0.18)'''

new_skip1 = '''    words = _mp_apply_caption_timing_offset(words or [], -0.18)'''

# Alternative patterns
old_skip2 = '''[MasterPipeline] 41% | LOW RAM visual layers: zoom/beat/story skipped safely'''
old_skip3 = '''if isinstance(video, str) and "_composite" in str(video).lower():
        safe_print("[MasterPipeline] 41% | LOW RAM visual layers: zoom/beat/story skipped safely")
        return video'''

# Try each pattern
if old_skip3 in text:
    text = text.replace(old_skip3, '# LOW RAM skip removed - always apply visual layers')
    print("[2/5] LOW RAM skip removed (pattern 1)")
elif old_skip1 in text:
    text = text.replace(old_skip1, new_skip1)
    print("[2/5] LOW RAM skip removed (pattern 2)")
else:
    print("[2/5] Searching LOW RAM skip pattern...")
    lines = text.split('\n')
    for i, l in enumerate(lines):
        if 'LOW RAM visual layers' in l:
            print(f"  Found at line {i+1}: {l.strip()[:120]}")
            # Comment out the return
            if 'return video' in lines[i+1] or 'return video' in lines[i+2]:
                lines[i] = '    # ' + lines[i] + '  # DISABLED - always apply'
                if 'return video' in lines[i+1]:
                    lines[i+1] = '    # ' + lines[i+1] + '  # DISABLED'
                if i+2 < len(lines) and 'return video' in lines[i+2]:
                    lines[i+2] = '    # ' + lines[i+2] + '  # DISABLED'
                text = '\n'.join(lines)
                print(f"  LOW RAM skip disabled at line {i+1}")
            break

# Also fix the LOW RAM integrated visual layers that skips hook
old_hook_skip = '''[MasterPipeline] LOW RAM hook skipped to avoid nested composite MemoryError.'''
new_hook_skip = '''[MasterPipeline] Applying hook (LOW RAM skip disabled)'''

if old_hook_skip in text:
    text = text.replace(old_hook_skip, new_hook_skip)
    print("[2b/5] LOW RAM hook skip disabled")

# ============================================================
# FIX 3: Caption timing - remove -0.18 offset, use 0.0
# ============================================================
old_time = "-0.18"
new_time = "0.0"

count = 0
while old_time in text:
    # Only replace in caption timing context
    if 'caption_start_offset' in text[text.find(old_time)-50:text.find(old_time)+50] or \
       'caption_timing' in text[text.find(old_time)-50:text.find(old_time)+50] or \
       '_mp_apply_caption_timing_offset' in text[text.find(old_time)-50:text.find(old_time)+50]:
        text = text.replace(old_time, new_time)
        count += 1
    else:
        break

print(f"[3/5] Caption timing offset changed to 0.0 ({count} replacements)")

# ============================================================
# FIX 4: SFX engine - proper clip-boundary SFX (only on clip change)
# ============================================================
sfx = BASE / "sfx_engine.py"
if sfx.exists():
    sfx_text = sfx.read_text(encoding="utf-8")
    
    # Replace the existing apply_sfx_burst_on_clip_change with better version
    old_func_start = "def apply_sfx_burst_on_clip_change"
    
    if old_func_start in sfx_text:
        # Find the function and replace it
        start_idx = sfx_text.find(old_func_start)
        # Find next def or end of file
        rest = sfx_text[start_idx:]
        next_def = rest.find("\ndef ", 10)
        if next_def == -1:
            next_def = len(rest)
        
        new_sfx_func = '''def apply_sfx_burst_on_clip_change(video, mode="SHORT", niche="default", sfx_files=None, max_sfx=5):
    """Apply SFX exactly at clip change boundaries, max unique SFX per video."""
    import subprocess, tempfile, random
    from pathlib import Path
    
    try:
        if video is None:
            return video
        
        temp_dir = Path(tempfile.gettempdir())
        
        # Get video duration
        dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)]
        result = subprocess.run(dur_cmd, capture_output=True, text=True)
        total_dur = float(result.stdout.strip() or 0)
        
        if total_dur <= 0:
            return video
        
        # Get clip count from the video (number of segments)
        seg_cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "stream=nb_read_packets", "-of", "csv=p=0", str(video)
        ]
        
        # Detect clip boundaries via scene changes
        scene_filter = "select='gt(scene\\\\,0.4)',metadata=print"
        scene_cmd = [
            "ffmpeg", "-i", str(video),
            "-vf", "select='gt(scene\\,0.35)',showinfo",
            "-vsync", "vfr", "-f", "null", "-"
        ]
        
        scene_result = subprocess.run(scene_cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)
        
        # Parse scene change times
        import re as _re
        change_times = []
        for line in scene_result.stdout.split('\n') if scene_result.stdout else []:
            m = _re.search(r'pts_time:([\d.]+)', line)
            if m:
                t = float(m.group(1))
                if t > 0.5 and t < total_dur - 0.5:
                    change_times.append(t)
        
        # If scene detection failed, use uniform intervals
        if not change_times:
            # Use clip count to estimate boundaries
            clip_dur = total_dur / 8  # default 8 clips
            change_times = [clip_dur * i for i in range(1, 8)]
        
        # Limit to max_sfx unique SFX
        change_times = change_times[:max_sfx]
        
        if not change_times:
            return video
        
        print(f"[SFX] Detected {len(change_times)} clip boundaries for SFX placement")
        
        # Find available SFX files
        sfx_dir = BASE / "assets" / ("shorts" if "SHORT" in str(mode).upper() else "longs") / "sfx"
        if not sfx_dir.exists():
            sfx_dir = BASE / "assets" / "shorts" / "sfx"
        
        available_sfx = list(sfx_dir.glob("*.mp3")) + list(sfx_dir.glob("*.wav")) + list(sfx_dir.glob("*.m4a"))
        
        if not available_sfx:
            print("[SFX] No SFX files found, generating synthetic bursts")
            # Generate simple whoosh sound
            sfx_audio = temp_dir / f"sfx_gen_{int(time.time())}.wav"
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", "sine=frequency=600:duration=0.08",
                "-af", "afade=t=out:st=0.04:d=0.04",
                str(sfx_audio)
            ], capture_output=True)
            if sfx_audio.exists():
                available_sfx = [sfx_audio]
        
        if not available_sfx:
            return video
        
        # Assign unique SFX to each boundary (cycle if fewer SFX than boundaries)
        random.seed(hash(str(video)) % 10000)
        sfx_assignments = []
        sfx_pool = list(available_sfx)
        for i, ct in enumerate(change_times):
            chosen = sfx_pool[i % len(sfx_pool)]
            sfx_assignments.append((ct, chosen))
        
        # Build ffmpeg filter complex for mixing SFX at clip boundaries
        inputs = ["-i", str(video)]
        filter_parts = []
        sfx_labels = []
        
        for i, (ct, sfx_path) in enumerate(sfx_assignments):
            inputs.extend(["-i", str(sfx_path)])
            sfx_labels.append(f"[{i+1}:a]")
            delay_ms = int(ct * 1000)
            filter_parts.append(f"[{i+1}:a]adelay={delay_ms}|{delay_ms}[sfx{i}]")
        
        # Mix all SFX with original audio
        all_sfx = "".join([f"[sfx{i}]" for i in range(len(sfx_assignments))])
        filter_parts.append(f"[0:a]{all_sfx}amix=inputs={len(sfx_assignments)+1}:duration=first:weights=1 {'1 ' * len(sfx_assignments)}[outa]")
        
        sfx_output = temp_dir / f"sfx_final_{int(time.time())}.mp4"
        
        cmd = [
            "ffmpeg", "-y"
        ] + inputs + [
            "-filter_complex", ";".join(filter_parts),
            "-map", "0:v", "-map", "[outa]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            str(sfx_output)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if sfx_output.exists() and sfx_output.stat().st_size > 1000:
            print(f"[SFX] Applied {len(sfx_assignments)} SFX bursts at clip boundaries")
            return str(sfx_output)
        
        return video
    except Exception as e:
        print(f"[SFX] Burst failed: {e}")
        return video
'''
        # Replace old function
        sfx_text = sfx_text[:start_idx] + new_sfx_func + sfx_text[start_idx+next_def:]
        sfx.write_text(sfx_text, encoding="utf-8")
        print("[4/5] SFX engine - clip-boundary SFX updated")
    else:
        # Append at end
        sfx_text += "\n" + new_sfx_func
        sfx.write_text(sfx_text, encoding="utf-8")
        print("[4/5] SFX engine - clip-boundary SFX added")
else:
    print("[4/5] SFX engine file not found")

# ============================================================
# FIX 5: app.py - safe_print fix for LUFS
# ============================================================
app = BASE / "app.py"
text_app = app.read_text(encoding="utf-8")

# Replace safe_print with print in the LUFS block
if 'safe_print(f"[LUFS]' in text_app:
    text_app = text_app.replace('safe_print(f"[LUFS]', 'print(f"[LUFS]')
    text_app = text_app.replace('safe_print("[LUFS]', 'print("[LUFS]')
    app.write_text(text_app, encoding="utf-8")
    print("[5/5] app.py LUFS safe_print -> print fixed")

# ============================================================
# Final: Write master_pipeline
# ============================================================
mp.write_text(text, encoding="utf-8")
try:
    compile(text, "master_pipeline.py", "exec")
    print("[FINAL] master_pipeline.py - SYNTAX OK")
except SyntaxError as e:
    print(f"[FINAL] master_pipeline.py - SYNTAX ERROR: {e}")

print("=" * 60)
print("ALL FIXES DONE. Run: streamlit run app.py")
print("=" * 60)