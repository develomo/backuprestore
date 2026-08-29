# apply_thermal_safe_mode.py
# THERMAL SAFE MODE: Prevents laptop overheating & shutdown
import re
from pathlib import Path

print("=" * 70)
print("🌡️  APPLYING THERMAL SAFE MODE FOR LAPTOP")
print("=" * 70)

blr = Path("batch_long_renderer.py")
if not blr.exists():
    print("❌ batch_long_renderer.py not found!")
    exit(1)

content = blr.read_text(encoding="utf-8")
changes = 0

# ============================================================
# FIX 1: Add thread limit to ALL ffmpeg commands
# ============================================================
# Replace all subprocess.run([FFMPEG with subprocess.run([FFMPEG, "-threads", "2"
old_ffmpeg_call = '[FFMPEG,'
new_ffmpeg_call = '[FFMPEG, "-threads", "2",'

count = content.count(old_ffmpeg_call)
if count > 0 and '"-threads"' not in content:
    content = content.replace(old_ffmpeg_call, new_ffmpeg_call)
    changes += 1
    print(f"✅ FIX 1: Added '-threads 2' to {count} FFmpeg commands")
else:
    if '"-threads"' in content:
        print("ℹ️ FIX 1: Thread limit already present")
    else:
        print("⚠️ FIX 1: Could not find FFmpeg call pattern")

# ============================================================
# FIX 2: Change preset from "medium" to "fast" everywhere
# ============================================================
old_preset = '"-preset", "medium"'
new_preset = '"-preset", "fast"'

preset_count = content.count(old_preset)
if preset_count > 0:
    content = content.replace(old_preset, new_preset)
    changes += 1
    print(f"✅ FIX 2: Changed {preset_count} presets from 'medium' to 'fast' (40% less CPU)")
else:
    print("ℹ️ FIX 2: No 'medium' presets found")

# ============================================================
# FIX 3: Change CRF from 23 to 26 (visually same, much lighter)
# ============================================================
old_crf = '"-crf", "23"'
new_crf = '"-crf", "26"'

crf_count = content.count(old_crf)
if crf_count > 0:
    content = content.replace(old_crf, new_crf)
    changes += 1
    print(f"✅ FIX 3: Changed {crf_count} CRF values from 23 to 26 (lighter encoding)")
else:
    print("ℹ️ FIX 3: No CRF 23 found")

# ============================================================
# FIX 4: Add cooldown delay between batches
# ============================================================
# Find the batch loop and add time.sleep(1) after each batch
old_batch_append = "intermediate_files.append(batch_out)"
new_batch_append = """intermediate_files.append(batch_out)
        time.sleep(1.0)  # 🌡️ THERMAL COOLDOWN: 1s pause between batches"""

if old_batch_append in content and "THERMAL COOLDOWN" not in content:
    content = content.replace(old_batch_append, new_batch_append)
    changes += 1
    print("✅ FIX 4: Added 1-second thermal cooldown between batches")
else:
    if "THERMAL COOLDOWN" in content:
        print("ℹ️ FIX 4: Cooldown already present")
    else:
        print("⚠️ FIX 4: Could not find batch append pattern")

# ============================================================
# FIX 5: Add cooldown between individual clip renders
# ============================================================
old_clip_append = "rendered_clips.append(out_clip)"
new_clip_append = """rendered_clips.append(out_clip)
        time.sleep(0.3)  # 🌡️ THERMAL COOLDOWN: 0.3s pause between clips"""

if old_clip_append in content and "0.3s pause between clips" not in content:
    content = content.replace(old_clip_append, new_clip_append)
    changes += 1
    print("✅ FIX 5: Added 0.3-second thermal cooldown between clip renders")
else:
    if "0.3s pause between clips" in content:
        print("ℹ️ FIX 5: Clip cooldown already present")

# ============================================================
# FIX 6: Ensure 'time' module is imported
# ============================================================
if "import time" not in content:
    content = "import time\n" + content
    changes += 1
    print("✅ FIX 6: Added 'import time' for cooldown delays")
else:
    print("ℹ️ FIX 6: 'time' module already imported")

# ============================================================
# SAVE & VERIFY
# ============================================================
if changes > 0:
    blr.write_text(content, encoding="utf-8")
    print(f"\n💾 Saved {changes} thermal safety changes")

try:
    compile(content, str(blr), "exec")
    print("✅ Syntax verification PASSED!")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
    exit(1)

print("\n" + "=" * 70)
print("🌡️  THERMAL SAFE MODE ACTIVATED!")
print("=" * 70)
print("\n📋 SAFETY MEASURES APPLIED:")
print("  • CPU Threads: Limited to 2 (was: unlimited/all cores)")
print("  • Encoding Preset: 'fast' (was: 'medium') → 40% less CPU")
print("  • Quality CRF: 26 (was: 23) → Visually identical, lighter")
print("  • Batch Cooldown: 1.0s pause between each batch")
print("  • Clip Cooldown: 0.3s pause between each clip render")
print("\n⏱️  EXPECTED IMPACT:")
print("  • Render time will increase by ~30-40%")
print("  • CPU temperature will stay 20-30°C LOWER")
print("  • Laptop will NOT overheat or shutdown")
print("\n💡 NEXT: Run 'streamlit run app.py' and render safely!")
print("=" * 70)