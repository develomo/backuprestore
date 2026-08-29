# fix_sfx_variables.py
from pathlib import Path

file_path = Path("batch_long_renderer.py")
content = file_path.read_text(encoding="utf-8")

# Find the SFX burst section and add missing variables BEFORE it
old_sfx = "burst_len = 1.0"
new_sfx = """# Calculate average timing for SFX sync
            clip_duration_avg = sum(clip_durations) / len(clip_durations) if 'clip_durations' in dir() else 7.0
            avg_transition_dur = 0.65
            burst_len = 1.0"""

if old_sfx in content and "clip_duration_avg" not in content:
    content = content.replace(old_sfx, new_sfx, 1)
    file_path.write_text(content, encoding="utf-8")
    print("✅ FIXED: Added clip_duration_avg and avg_transition_dur variables")
    
    # Verify syntax
    try:
        compile(content, str(file_path), "exec")
        print("✅ Syntax verification PASSED!")
        print("💡 NEXT: Run 'streamlit run app.py'")
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
else:
    if "clip_duration_avg" in content:
        print("ℹ️ Variables already present")
    else:
        print("⚠️ Could not find insertion point")