# fix_clip_duration_final.py - DEFINITIVE FIX for clip_duration + clips_needed ordering
from pathlib import Path

blr = Path("batch_long_renderer.py")
content = blr.read_text(encoding="utf-8")

# STEP 1: Remove ALL existing broken definitions of clip_duration and clips_needed
# that are in wrong places (we will re-add them in correct order)
import re

# Remove any standalone clip_duration or clips_needed lines that are misplaced
lines = content.split('\n')
cleaned_lines = []
removed = 0
for line in lines:
    stripped = line.strip()
    # Skip these specific broken/misplaced lines
    if stripped.startswith('clip_duration = random.uniform('):
        removed += 1
        continue
    if stripped.startswith('base_clip_dur = total_voice_dur /'):
        removed += 1
        continue
    if stripped.startswith('clip_duration = max(4.0,'):
        removed += 1
        continue
    if stripped.startswith('clips_needed = int(total_voice_dur / clip_duration)'):
        removed += 1
        continue
    if stripped.startswith('clips_needed = int(total_voice_dur / 7.0)'):
        removed += 1
        continue
    if stripped.startswith('# Calculate exact clip duration to match voice perfectly'):
        removed += 1
        continue
    if stripped.startswith('# Calculate clips needed FIRST'):
        removed += 1
        continue
    cleaned_lines.append(line)

if removed > 0:
    print(f"🗑️  Removed {removed} misplaced variable definitions")

content = '\n'.join(cleaned_lines)

# STEP 2: Insert BOTH variables in CORRECT order right after total_voice_dur is known
# The anchor point is the line where total_dur is calculated
anchor = "total_dur = 1.5 + total_voice_dur + 2.0"

correct_block = """total_dur = 1.5 + total_voice_dur + 2.0

    # ============================================================
    # CLIP DURATION & COUNT CALCULATION (must be in this exact order)
    # ============================================================
    # Target ~7s per clip, but adjust so total matches voice exactly
    target_clip_dur = 7.0
    clips_needed = max(1, int(round(total_voice_dur / target_clip_dur)))
    clip_duration = total_voice_dur / clips_needed  # Exact duration per clip"""

if anchor in content:
    content = content.replace(anchor, correct_block)
    print("✅ INSERTED clip_duration + clips_needed in CORRECT order after total_dur")
else:
    print("⚠️ Anchor not found, trying alternative...")
    # Alternative anchor
    alt_anchor = "print(f\"\\n📊 [ANALYSIS]\")"
    alt_block = """# CLIP DURATION & COUNT (calculated before use)
    target_clip_dur = 7.0
    clips_needed = max(1, int(round(total_voice_dur / target_clip_dur)))
    clip_duration = total_voice_dur / clips_needed

    print(f"\\n📊 [ANALYSIS]")"""
    
    if alt_anchor in content:
        content = content.replace(alt_anchor, alt_block)
        print("✅ INSERTED via alternative anchor")
    else:
        print("❌ Could not find insertion point!")

# STEP 3: Ensure individual clip rendering uses clip_duration (not random)
old_individual = "this_clip_dur = random.uniform(6.5, 7.5)"
new_individual = "this_clip_dur = clip_duration"
if old_individual in content:
    content = content.replace(old_individual, new_individual)
    print("✅ Individual clips now use calculated clip_duration")

# Also handle variant
old_variant = "this_dur = random.uniform(6.5, 7.5)"
if old_variant in content:
    content = content.replace(old_variant, "this_dur = clip_duration")
    print("✅ Variant clip duration also fixed")

blr.write_text(content, encoding="utf-8")

# Verify syntax
try:
    compile(blr.read_text(encoding="utf-8"), str(blr), "exec")
    print("\n✅ Syntax verification PASSED!")
    print("💡 NEXT: Run 'streamlit run app.py'")
except SyntaxError as e:
    print(f"\n❌ Error at line {e.lineno}: {e.msg}")
    err_lines = blr.read_text(encoding="utf-8").split('\n')
    for j in range(max(0, e.lineno-3), min(len(err_lines), e.lineno+2)):
        marker = ">>>" if j == e.lineno - 1 else "   "
        print(f"{marker} {j+1}: {err_lines[j]}")