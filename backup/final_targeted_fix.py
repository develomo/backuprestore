# final_targeted_fix.py
# ONLY fixes line 1188 + adds missing parameters
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "batch_long_renderer.py"

# Step 1: Backup
backup = TARGET.with_suffix(".py.final_targeted_backup")
if not backup.exists():
    shutil.copy2(TARGET, backup)
    print(f"[OK] Backup created: {backup.name}")

# Step 2: Read file
content = TARGET.read_text(encoding="utf-8")
lines = content.split('\n')

# Step 3: Fix line 1188 (0-indexed: 1187)
if len(lines) > 1187:
    old_line = lines[1187]
    if "outro_out=batch_dir" in old_line and ";" in old_line:
        # Split into proper multi-line code
        indent = "            "  # 12 spaces
        new_lines = [
            f"{indent}outro_out = batch_dir / f\"batch_{{len(outputs)+1:04d}}_outro.mp4\"",
            f"{indent}normalize_video_asset(outro, outro_out, size, fps, outro_sec, quality)",
            f"{indent}outputs.append(outro_out)"
        ]
        lines[1187:1188] = new_lines
        print("[OK] Fixed line 1188 syntax error")

# Step 4: Add custom_logo_path to function signature
# Find render_long_batch_memory function
for i, line in enumerate(lines):
    if "def render_long_batch_memory(" in line:
        # Find the end of signature
        for j in range(i, min(i+20, len(lines))):
            if "**kwargs" in lines[j]:
                if "custom_logo_path" not in lines[j]:
                    lines[j] = lines[j].replace("**kwargs", "custom_logo_path=None, **kwargs")
                    print(f"[OK] Added custom_logo_path to function signature (line {j+1})")
                break
        break

# Step 5: Add corner parameter to subscribe overlay
for i, line in enumerate(lines):
    if "apply_subscribe_overlay_reliable" in line and "corner=" not in line:
        # Add corner parameter
        if "duration_seconds=SUBSCRIBE_OVERLAY_DURATION_SECONDS," in line:
            lines[i] = line.replace(
                "duration_seconds=SUBSCRIBE_OVERLAY_DURATION_SECONDS,",
                "duration_seconds=SUBSCRIBE_OVERLAY_DURATION_SECONDS, corner=\"bottom-right\","
            )
            print(f"[OK] Added corner='bottom-right' to subscribe overlay (line {i+1})")
        break

# Step 6: Write back
TARGET.write_text('\n'.join(lines), encoding="utf-8")
print("[OK] File saved")

# Step 7: Verify syntax
try:
    import py_compile
    py_compile.compile(str(TARGET), doraise=True)
    print("[OK] ✅ Syntax verification PASSED - No errors!")
except py_compile.PyCompileError as e:
    print(f"[ERROR] Syntax error: {e}")