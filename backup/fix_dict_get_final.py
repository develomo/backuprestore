# fix_dict_get_final.py - SURGICAL FIX FOR LINE 180
from pathlib import Path

slp = Path("safe_long_video_polished.py")
content = slp.read_text(encoding="utf-8")

# The EXACT broken pattern on line 180
broken = 'style_id=caption_profile.get("selected_style_id",style_id,custom_logo_path=custom_logo_path,wm_opacity=wm_opacity)'
fixed = 'style_id=caption_profile.get("selected_style_id",style_id)'

if broken in content:
    content = content.replace(broken, fixed)
    slp.write_text(content, encoding="utf-8")
    print("✅ FIXED: Removed extra kwargs from dict.get() on line 180")
else:
    # Try to find it with different spacing
    import re
    pattern = r'style_id=caption_profile\.get\("selected_style_id"\s*,\s*style_id\s*,\s*custom_logo_path=[^)]+\)'
    match = re.search(pattern, content)
    if match:
        content = content.replace(match.group(0), fixed)
        slp.write_text(content, encoding="utf-8")
        print("✅ FIXED via regex: Removed extra kwargs from dict.get()")
    else:
        print("⚠️ Broken pattern not found. Checking current state...")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'caption_profile.get' in line:
                print(f"   Line {i+1}: {line.strip()[:100]}")

# Verify syntax
try:
    compile(slp.read_text(encoding="utf-8"), str(slp), "exec")
    print("✅ Syntax verification PASSED!")
    print("💡 NEXT: Run 'streamlit run app.py'")
except SyntaxError as e:
    print(f"❌ Error at line {e.lineno}: {e.msg}")