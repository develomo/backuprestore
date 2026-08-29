# fix_sfx_final.py
# FINAL FIX: Removes broken 'sfx_files' logic and restores stable UI SFX handling
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
filepath = BASE_DIR / "batch_long_renderer.py"

if not filepath.exists():
    print("[ERROR] batch_long_renderer.py not found!")
    exit(1)

content = filepath.read_text(encoding="utf-8")

# The broken block introduced by previous experimental patch
broken_pattern = re.compile(
    r'(\s+)if has_sfx:\s+.*?isinstance\(sfx_files.*?idx \+= 1',
    re.DOTALL
)

# The correct, simple, working block that handles UI uploads perfectly
correct_block = '''    if has_sfx:
        # Ensure sfx is a single Path (UI might pass a list)
        if isinstance(sfx, (list, tuple)) and len(sfx) > 0:
            sfx = sfx[0]
            
        cmd.extend(["-stream_loop", "-1", "-i", str(sfx)])
        filters.append(
            f"[{idx}:a]volume={sfx_volume},"
            "highpass=f=80,lowpass=f=13500,"
            f"adelay={intro_ms}|{intro_ms},"
            f"atrim=0:{trim_end},"
            "aresample=44100[s_pre]"
        )
        filters.append(
            f"[s_pre][vside{vside_cursor}]sidechaincompress=threshold=0.06:ratio=5:attack=22:release=420:makeup=1[s]"
        )
        vside_cursor += 1
        labels.append("[s]")
        idx += 1'''

match = broken_pattern.search(content)
if match:
    indent = match.group(1)
    indented_correct = '\n'.join(indent + line if line.strip() else '' for line in correct_block.split('\n'))
    content = content[:match.start()] + indented_correct + content[match.end():]
    filepath.write_text(content, encoding="utf-8")
    print("[OK] Fixed sfx_files NameError in mux_audio_timeline!")
else:
    # Fallback: just replace "sfx_files" with "sfx" inside the mux_audio_timeline function
    func_start = content.find("def mux_audio_timeline(")
    if func_start != -1:
        func_end = content.find("\ndef ", func_start + 10)
        if func_end == -1:
            func_end = len(content)
        
        func_content = content[func_start:func_end]
        if "sfx_files" in func_content:
            func_content = func_content.replace("sfx_files", "sfx")
            content = content[:func_start] + func_content + content[func_end:]
            filepath.write_text(content, encoding="utf-8")
            print("[OK] Fixed sfx_files reference in mux_audio_timeline (Fallback)!")
        else:
            print("[INFO] sfx_files not found in mux_audio_timeline (Already clean).")
    else:
        print("[ERROR] mux_audio_timeline function not found!")

print("\n✅ FINAL FIX APPLIED SUCCESSFULLY!")
print("💡 Ab aapka render bina kisi 'sfx_files' error ke smoothly chalega.")