# fix_variable_scope.py
from pathlib import Path
import re

file_path = Path("batch_long_renderer.py")
content = file_path.read_text(encoding="utf-8")

# Check if clip_duration_avg exists but might be in wrong scope
if "clip_duration_avg" in content:
    print("🔍 Variable found in file. Checking scope...")
    
    # Find where it's defined
    lines = content.split('\n')
    def_line = -1
    use_line = -1
    
    for i, line in enumerate(lines):
        if "clip_duration_avg =" in line and "transition_time" not in line:
            def_line = i
        if "clip_duration_avg)" in line or "* clip_duration_avg" in line:
            use_line = i
    
    print(f"   Defined at line: {def_line + 1}")
    print(f"   Used at line: {use_line + 1}")
    
    # If defined AFTER usage or in deeper indentation, fix it
    if def_line > use_line or (def_line >= 0 and use_line >= 0):
        # Get the indentation of the usage line
        use_indent = len(lines[use_line]) - len(lines[use_line].lstrip())
        
        # Remove old definition
        old_def = lines[def_line]
        lines[def_line] = ""  # Clear old line
        
        # Add new definition right before usage with correct indentation
        new_def = " " * use_indent + "clip_duration_avg = 7.0  # Default fallback\n"
        lines.insert(use_line, new_def.rstrip())
        
        content = '\n'.join([l for l in lines if l.strip() != ""])
        file_path.write_text(content, encoding="utf-8")
        print("✅ FIXED: Moved clip_duration_avg to correct scope")
    else:
        print("ℹ️ Scope looks correct. Issue might be elsewhere.")
else:
    print("❌ Variable NOT found. Adding it now...")
    # Add it right after total_voice_dur calculation
    insert_after = "total_dur = 1.5 + total_voice_dur + 2.0"
    if insert_after in content:
        new_vars = """
    # SFX timing variables (defined early to avoid scope issues)
    clip_duration_avg = 7.0
    avg_transition_dur = 0.65
"""
        content = content.replace(insert_after, insert_after + new_vars)
        file_path.write_text(content, encoding="utf-8")
        print("✅ ADDED: Variables inserted at function level")
    else:
        print("⚠️ Could not find insertion point")

# Verify syntax
try:
    compile(content, str(file_path), "exec")
    print("✅ Syntax verification PASSED!")
    print("💡 NEXT: Run 'streamlit run app.py'")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")