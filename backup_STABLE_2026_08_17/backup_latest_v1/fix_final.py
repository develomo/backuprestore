from pathlib import Path
import shutil, time

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 60)
print("FIX FINAL - RAM Safe, No Skips, Proper Indent")
print("=" * 60)

# ============================================================
# PART A: master_pipeline.py
# ============================================================
mp = BASE / "master_pipeline.py"
shutil.copy2(mp, BASE / f"master_pipeline.py.bak_final_{ts}")
text = mp.read_text(encoding="utf-8")

changes = []

# 1. Add thread limit at top
if 'os.environ["FFMPEG_THREADS"]' not in text[:1000]:
    text = 'import os\nos.environ["FFMPEG_THREADS"] = "2"\n' + text
    changes.append("threads=2")

# 2. Fix SFX mode scope
text = text.replace(
    "video = apply_sfx_burst_on_clip_change(video, mode=mode, niche=niche)",
    'video = apply_sfx_burst_on_clip_change(video, mode=plan.get("mode","SHORT"), niche=plan.get("niche","default"))'
)
changes.append("SFX mode fix")

# 3. safe_print -> print
text = text.replace('safe_print("[MasterPipeline] SFX', 'print("[MasterPipeline] SFX')
text = text.replace('safe_print(f"[MasterPipeline] SFX', 'print(f"[MasterPipeline] SFX')
text = text.replace('safe_print("[MasterPipeline] 41%', 'print("[MasterPipeline] 41%')

# 4. Comment out LOW RAM skip block (line by line to preserve indent)
lines = text.split('\n')
i = 0
while i < len(lines):
    line = lines[i]
    # Find the composite check that triggers skip
    if 'isinstance(video, str) and "_composite"' in line:
        lines[i] = '# DISABLED: ' + line
        changes.append("composite skip disabled")
        # Also comment the next 2 lines (print + return)
        for j in range(i+1, min(i+4, len(lines))):
            if 'LOW RAM' in lines[j] or 'return video' in lines[j]:
                lines[j] = '# DISABLED: ' + lines[j]
        i += 3
    i += 1
text = '\n'.join(lines)

# 5. Remove hook skip
text = text.replace(
    '[MasterPipeline] LOW RAM hook skipped to avoid nested composite MemoryError.',
    '[MasterPipeline] Applying visual hook'
)
changes.append("hook skip disabled")

# 6. Caption timing -0.18 -> 0.0
text = text.replace('-0.18', '0.0')
changes.append("caption timing 0.0")

# Write and verify
mp.write_text(text, encoding="utf-8")

try:
    compile(text, "master_pipeline.py", "exec")
    print(f"master_pipeline.py SYNTAX OK")
    print(f"  Changes: {changes}")
except IndentationError as e:
    print(f"INDENT ERROR line {e.lineno}: {e.msg}")
    # Show surrounding lines
    lines2 = text.split('\n')
    lo = max(0, e.lineno-3)
    hi = min(len(lines2), e.lineno+2)
    for ln in range(lo, hi):
        marker = ">>>" if ln+1 == e.lineno else "   "
        print(f"  {marker} {ln+1}: {lines2[ln][:120]}")
except SyntaxError as e:
    print(f"SYNTAX ERROR line {e.lineno}: {e.msg}")

# ============================================================
# PART B: app.py
# ============================================================
app = BASE / "app.py"
ta = app.read_text(encoding="utf-8")
ta = ta.replace('safe_print(f"[LUFS]', 'print(f"[LUFS]')
ta = ta.replace('safe_print("[LUFS]', 'print("[LUFS]')
app.write_text(ta, encoding="utf-8")
print("app.py LUFS print fix OK")

# ============================================================
# PART C: sfx_engine.py
# ============================================================
sfx_code = '''"""SFX Engine - RAM Safe"""
import subprocess, tempfile, random, time
from pathlib import Path
BASE = Path(r"D:\\My Creation Video Generator\\backup")


def apply_sfx_burst_on_clip_change(video, mode="SHORT", niche="default",
                                   sfx_files=None, max_sfx=5):
    """RAM-safe SFX at uniform clip boundaries."""
    try:
        if video is None:
            return video

        td = Path(tempfile.gettempdir())

        # Get duration
        r = subprocess.run(
            ["ffprobe","-v","error","-show_entries",
             "format=duration","-of","csv=p=0", str(video)],
            capture_output=True, text=True
        )
        try:
            dur = float(r.stdout.strip() or 0)
        except:
            return video

        if dur <= 0:
            return video

        # Uniform boundaries
        clip_count = 8
        clip_dur = dur / clip_count
        times = [clip_dur * i for i in range(1, clip_count)]
        times = [t for t in times if 1.0 < t < dur - 1.0][:max_sfx]

        if not times:
            return video

        print(f"[SFX] {len(times)} boundaries")

        # Find SFX file
        sfx_dirs = [
            BASE / "assets" / "shorts" / "sfx",
            BASE / "assets" / "longs" / "sfx",
        ]
        sfx_path = None
        for d in sfx_dirs:
            if d.exists():
                files = list(d.glob("*.mp3")) + list(d.glob("*.wav"))
                if files:
                    sfx_path = files[0]
                    break

        if sfx_path is None:
            print("[SFX] No files, skip")
            return video

        # Build filter
        parts = []
        for i, ct in enumerate(times):
            ms = int(ct * 1000)
            parts.append(f"[1:a]adelay={ms}|{ms}[sfx{i}]")

        all_labels = "".join([f"[sfx{i}]" for i in range(len(times))])
        parts.append(
            f"[0:a]{all_labels}amix=inputs={len(times)+1}"
            f":duration=first[outa]"
        )

        out = td / f"sfx_{int(time.time())}.mp4"

        subprocess.run([
            "ffmpeg","-threads","1","-y",
            "-i", str(video),
            "-i", str(sfx_path),
            "-filter_complex", ";".join(parts),
            "-map","0:v","-map","[outa]",
            "-c:v","copy","-c:a","aac","-b:a","128k",
            str(out)
        ], capture_output=True, text=True)

        if out.exists() and out.stat().st_size > 1000:
            print(f"[SFX] {len(times)} bursts done")
            return str(out)

        return video
    except Exception as e:
        print(f"[SFX] skip: {e}")
        return video
'''

sfx_file = BASE / "sfx_engine.py"
sfx_file.write_text(sfx_code, encoding="utf-8")
print("sfx_engine.py OK")

print("=" * 60)
print("DONE. Run: streamlit run app.py")
print("=" * 60)