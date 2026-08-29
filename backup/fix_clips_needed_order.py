# fix_clips_needed_order.py - FIXES UnboundLocalError for clips_needed
from pathlib import Path

blr = Path("batch_long_renderer.py")
lines = blr.read_text(encoding="utf-8").split('\n')

fixed = False

for i in range(len(lines)):
    # Find the broken line where clips_needed is used before definition
    if 'base_clip_dur = total_voice_dur / max(1, clips_needed)' in lines[i]:
        indent = len(lines[i]) - len(lines[i].lstrip())
        
        # Find where clips_needed is actually defined (should be nearby)
        clips_needed_line = -1
        for j in range(max(0, i-10), min(len(lines), i+15)):
            if 'clips_needed = int(' in lines[j] or 'clips_needed =' in lines[j]:
                clips_needed_line = j
                break
        
        if clips_needed_line > i:
            # Move clips_needed definition BEFORE base_clip_dur usage
            clips_needed_def = lines[clips_needed_line]
            
            # Remove from original position
            del lines[clips_needed_line]
            
            # Insert before base_clip_dur line
            lines.insert(i, clips_needed_def)
            
            fixed = True
            print(f"✅ FIXED: Moved clips_needed definition (line {clips_needed_line+1}) BEFORE usage (line {i+1})")
        else:
            # clips_needed not found nearby, define it inline
            new_lines = [
                ' ' * indent + '# Calculate clips needed FIRST',
                ' ' * indent + 'clips_needed = int(total_voice_dur / 7.0) + 1',
                lines[i]  # Keep original base_clip_dur line
            ]
            lines[i:i+1] = new_lines
            fixed = True
            print(f"✅ FIXED: Added clips_needed calculation before line {i+1}")
        break

if not fixed:
    print("⚠️ Could not find base_clip_dur line. Searching...")
    for i, line in enumerate(lines):
        if 'clips_needed' in line:
            print(f"   Line {i+1}: {line.strip()}")

if fixed:
    blr.write_text('\n'.join(lines), encoding="utf-8")

# Verify syntax
try:
    compile(blr.read_text(encoding="utf-8"), str(blr), "exec")
    print("✅ Syntax verification PASSED!")
    print("💡 NEXT: Run 'streamlit run app.py'")
except SyntaxError as e:
    print(f"❌ Error at line {e.lineno}: {e.msg}")
    err_lines = blr.read_text(encoding="utf-8").split('\n')
    for j in range(max(0, e.lineno-3), min(len(err_lines), e.lineno+2)):
        marker = ">>>" if j == e.lineno - 1 else "   "
        print(f"{marker} {j+1}: {err_lines[j]}")