import shutil, time, re
from pathlib import Path

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_lufs_{ts}")
text = app.read_text(encoding="utf-8")

# Add LUFS normalization call after final video export in run_render
old = '        result = call_supported(fn, kwargs)'
new = '''        result = call_supported(fn, kwargs)
        # Normalize audio to -14 LUFS
        if result and Path(str(result)).suffix in (".mp4", ".mkv", ".mov"):
            try:
                import subprocess, shutil as _sh
                norm = str(Path(result).with_stem(Path(result).stem + "_LUFS14"))
                cmd = [
                    "ffmpeg", "-y", "-i", str(result),
                    "-af", "loudnorm=I=-14:LRA=11:TP=-1.5",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    norm
                ]
                _sh.copy2(result, str(result) + ".prelufs.bak")
                subprocess.run(cmd, capture_output=True, text=True)
                if Path(norm).exists() and Path(norm).stat().st_size > 1000:
                    _sh.move(norm, result)
                    safe_print(f"[LUFS] Normalized to -14 LUFS: {result}")
                else:
                    safe_print("[LUFS] Normalization skipped (unchanged)")
            except Exception as e:
                safe_print(f"[LUFS] Normalization error: {e}")'''

if old in text:
    text = text.replace(old, new)
    print("LUFS normalization added after final export")
else:
    print("NOT FOUND - searching...")
    idx = text.find('result = call_supported')
    if idx != -1:
        print(f"Found at line ~{text[:idx].count(chr(10))+1}: {text[idx:idx+80]}")
    else:
        print("call_supported not found")

app.write_text(text, encoding="utf-8")

try:
    compile(text, "app.py", "exec")
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")

print(f"Backup: app.py.bak_lufs_{ts}")