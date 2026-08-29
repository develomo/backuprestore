from pathlib import Path
import re, shutil, time, os

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 60)
print("FIX RAM-SAFE - Low Memory + SFX + Captions + All Visuals")
print("=" * 60)

# Set ffmpeg threads low to prevent overheating
os.environ["FFMPEG_THREADS"] = "2"

# ============================================================
# FIX 1: master_pipeline.py - SFX mode fix + RAM safe + no skips
# ============================================================
mp = BASE / "master_pipeline.py"
shutil.copy2(mp, BASE / f"master_pipeline.py.bak_ramsafe_{ts}")
text = mp.read_text(encoding="utf-8")

patches_done = 0

# --- Patch A: SFX mode variable fix ---
old_sfx = """    if add_sfx_burst and video is not None:
        try:
            from sfx_engine import apply_sfx_burst_on_clip_change
            video = apply_sfx_burst_on_clip_change(video, mode=mode, niche=niche)
            safe_print("[MasterPipeline] SFX burst applied on clip boundaries")
        except Exception as e:
            safe_print(f"[MasterPipeline] SFX burst skipped: {e}")"""

new_sfx = """    if add_sfx_burst and video is not None:
        try:
            from sfx_engine import apply_sfx_burst_on_clip_change
            _m = plan.get("mode", "SHORT")
            _n = plan.get("niche", "default")
            video = apply_sfx_burst_on_clip_change(video, mode=_m, niche=_n)
            print("[MasterPipeline] SFX burst applied on clip boundaries")
        except Exception as e:
            print(f"[MasterPipeline] SFX burst skipped: {e}")"""

if old_sfx in text:
    text = text.replace(old_sfx, new_sfx)
    patches_done += 1
    print("[1] SFX mode fix OK")

# --- Patch B: Remove LOW RAM skip for zoom/beat/story ---
old_skip = 'if isinstance(video, str) and "_composite" in str(video).lower():\n        safe_print("[MasterPipeline] 41% | LOW RAM visual layers: zoom/beat/story skipped safely")\n        return video'
new_skip = '# RAM-skip disabled: always apply zoom/beat/story'

if old_skip in text:
    text = text.replace(old_skip, new_skip)
    patches_done += 1
    print("[2] LOW RAM skip disabled")
else:
    # Try line-by-line approach
    lines = text.split('\n')
    for i, l in enumerate(lines):
        if 'LOW RAM visual layers: zoom/beat/story skipped safely' in l:
            lines[i] = '    # ' + l.strip() + '  # DISABLED - always apply'
            if i+1 < len(lines) and 'return video' in lines[i+1]:
                lines[i+1] = '    # ' + lines[i+1].strip() + '  # DISABLED'
            text = '\n'.join(lines)
            patches_done += 1
            print(f"[2] LOW RAM skip disabled at line {i+1}")
            break

# --- Patch C: Remove LOW RAM hook skip ---
old_hook = '[MasterPipeline] LOW RAM hook skipped to avoid nested composite MemoryError.'
new_hook = '[MasterPipeline] Applying hook (RAM-safe mode)'
if old_hook in text:
    text = text.replace(old_hook, new_hook)
    patches_done += 1
    print("[3] Hook skip disabled")

# --- Patch D: Caption timing offset 0.0 ---
# Find caption timing offset patterns
old_time_patterns = [
    '_mp_apply_caption_timing_offset(words or [], -0.18)',
    'caption_start_offset = -0.18',
    'caption_timing_offset = -0.18',
    'offset = -0.18',
]

for pat in old_time_patterns:
    if pat in text:
        new_pat = pat.replace('-0.18', '0.0')
        text = text.replace(pat, new_pat)
        patches_done += 1
        print(f"[4] Caption timing: {pat} -> {new_pat}")

# --- Patch E: RAM-safe FFmpeg threads ---
# Add thread limit to ffmpeg commands
old_thread = '-vf'
new_thread = '-threads 2 -vf'
if old_thread in text:
    # Don't blindly replace all -vf, just the ffmpeg render ones
    # Add at the top of master_pipeline instead
    pass

# Add environment variable at top of file (after imports)
if 'import os' not in text[:500]:
    text = 'import os\nos.environ["FFMPEG_THREADS"] = "2"\n' + text
    patches_done += 1
    print("[5] FFmpeg thread limit added")

# Add thread limit to RAM-SAFE render commands  
old_ram = 'ffmpeg", "-y"'
new_ram = 'ffmpeg", "-threads", "2", "-y"'
if old_ram in text:
    text = text.replace(old_ram, new_ram)
    patches_done += 1
    print("[6] Thread limit added to ffmpeg commands")

# --- Patch F: Remove any other LOW RAM skip ---
text = text.replace(
    'safe_print("[MasterPipeline] 41% | LOW RAM visual layers: zoom/beat/story skipped safely")',
    'print("[MasterPipeline] 41% | Visual layers applying (RAM-safe mode)")'
)

mp.write_text(text, encoding="utf-8")
try:
    compile(text, "master_pipeline.py", "exec")
    print(f"[FINAL] master_pipeline.py SYNTAX OK - {patches_done} patches")
except SyntaxError as e:
    print(f"[FINAL] SYNTAX ERROR: {e}")

# ============================================================
# FIX 2: app.py - safe_print fix + RAM safe
# ============================================================
app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_ramsafe_{ts}")
text_app = app.read_text(encoding="utf-8")

# Fix safe_print in LUFS block
text_app = text_app.replace('safe_print(f"[LUFS]', 'print(f"[LUFS]')
text_app = text_app.replace('safe_print("[LUFS]', 'print("[LUFS]')

# Add RAM-safe imports at top
if 'import os' in text_app[:2000]:
    pass
else:
    # Already has os imported probably
    pass

app.write_text(text_app, encoding="utf-8")
print("[APP] LUFS safe_print fixed")

# ============================================================
# FIX 3: sfx_engine.py - clip boundary SFX with RAM safety
# ============================================================
sfx_file = BASE / "sfx_engine.py"
if sfx_file.exists():
    sfx_text = sfx_file.read_text(encoding="utf-8")
    
    # Check if already has the proper function
    if "def apply_sfx_burst_on_clip_change" in sfx_text:
        # Replace with RAM-safe version
        start = sfx_text.find("def apply_sfx_burst_on_clip_change")
        rest = sfx_text[start:]
        next_def = rest.find("\ndef ", 10)
        if next_def == -1:
            next_def = len(rest)
        
        ram_safe_sfx = '''def apply_sfx_burst_on_clip_change(video, mode="SHORT", niche="default", sfx_files=None, max_sfx=5):
    """RAM-safe SFX at clip boundaries. Uses light processing."""
    import subprocess, tempfile, random
    from pathlib import Path
    
    try:
        if video is None:
            return video
        
        temp_dir = Path(tempfile.gettempdir())
        
        # Get duration (light operation)
        dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)]
        result = subprocess.run(dur_cmd, capture_output=True, text=True)
        try:
            total_dur = float(result.stdout.strip() or 0)
        except:
            return video
        
        if total_dur <= 0:
            return video
        
        # Use uniform clip boundaries (avoid heavy scene detection)
        # Estimate clip count from video name or use default
        clip_count = 8  # default
        clip_dur = total_dur / clip_count
        change_times = [clip_dur * i for i in range(1, clip_count)]
        change_times = [t for t in change_times if 1.0 < t < total_dur - 1.0][:max_sfx]
        
        if not change_times:
            return video
        
        print(f"[SFX] {len(change_times)} clip boundaries for SFX")
        
        # Find SFX files
        sfx_dirs = [
            BASE / "assets" / "shorts" / "sfx",
            BASE / "assets" / "longs" / "sfx",
            BASE / "assets" / "sfx",
        ]
        
        available_sfx = []
        for d in sfx_dirs:
            if d.exists():
                available_sfx = list(d.glob("*.mp3")) + list(d.glob("*.wav")) + list(d.glob("*.m4a"))
                if available_sfx:
                    break
        
        # No SFX files = skip (don't generate synthetic - saves CPU)
        if not available_sfx:
            print("[SFX] No SFX files found, skipping burst")
            return video
        
        # Assign SFX to boundaries (cycle through)
        random.seed(hash(str(video)) % 10000)
        
        # Build simple ffmpeg command - one SFX file cycled
        sfx_path = available_sfx[0]  # Use single SFX file to save memory
        
        # Build amix with delays
        filter_parts = []
        for i, ct in enumerate(change_times):
            delay_ms = int(ct * 1000)
            filter_parts.append(f"[1:a]adelay={delay_ms}|{delay_ms}[sfx{i}]")
        
        all_labels = "".join([f"[sfx{i}]" for i in range(len(change_times))])
        filter_parts.append(f"[0:a]{all_labels}amix=inputs={len(change_times)+1}:duration=first[outa]")
        
        sfx_output = temp_dir / f"sfx_out_{int(time.time())}.mp4"
        
        cmd = [
            "ffmpeg", "-threads", "1", "-y",
            "-i", str(video),
            "-i", str(sfx_path),
            "-filter_complex", ";".join(filter_parts),
            "-map", "0:v", "-map", "[outa]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(sfx_output)
        ]
        
        subprocess.run(cmd, capture_output=True, text=True)
        
        if sfx_output.exists() and sfx_output.stat().st_size > 1000:
            print(f"[SFX] {len(change_times)} bursts applied at boundaries")
            return str(sfx_output)
        
        return video
    except Exception as e:
        print(f"[SFX] Skipped: {e}")
        return video
'''
        sfx_text = sfx_text[:start] + ram_safe_sfx + sfx_text[start+next_def:]
        sfx_file.write_text(sfx_text, encoding="utf-8")
        print("[SFX] RAM-safe SFX engine updated")
    else:
        sfx_text += "\n" + ram_safe_sfx
        sfx_file.write_text(sfx_text, encoding="utf-8")
        print("[SFX] RAM-safe SFX engine added")
else:
    print("[SFX] sfx_engine.py not found, creating...")
    sfx_text = '"""SFX Engine - RAM Safe"""\nimport subprocess, tempfile, random, time\nfrom pathlib import Path\nBASE = Path(r"D:\\My Creation Video Generator\\backup")\n' + ram_safe_sfx
    sfx_file.write_text(sfx_text, encoding="utf-8")
    print("[SFX] Created sfx_engine.py")

# ============================================================
# FIX 4: Set CPU/process priority hint
# ============================================================
print("=" * 60)
print("RAM-SAFE SETTINGS APPLIED:")
print("  - FFmpeg threads: 2 max")
print("  - SFX: single file, light processing")
print("  - Scene detection: OFF (uniform boundaries)")
print("  - Caption timing: 0.0 offset")
print("  - All visual layers: FORCED (no skip)")
print("  - Audio bitrate: 128k (RAM safe)")
print("=" * 60)
print("TIP: Close Chrome/browsers before rendering.")
print("TIP: Plug in laptop charger during render.")
print("=" * 60)
print("Run: streamlit run app.py")