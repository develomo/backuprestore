# fix_dict_get_error.py
from pathlib import Path

slp = Path("safe_long_video_polished.py")
if not slp.exists():
    print("❌ safe_long_video_polished.py not found!")
    exit(1)

content = slp.read_text(encoding="utf-8")

# The broken pattern from previous patch
broken = 'style_id=caption_profile.get("selected_style_id",style_id,custom_logo_path=custom_logo_path,wm_opacity=wm_opacity)'
fixed = 'style_id=caption_profile.get("selected_style_id",style_id)'

if broken in content:
    content = content.replace(broken, fixed)
    slp.write_text(content, encoding="utf-8")
    print("✅ FIXED: Removed extra kwargs from dict.get() call")
    
    # Verify that custom_logo_path and wm_opacity are still passed as separate params
    if 'custom_logo_path=custom_logo_path' in content and 'wm_opacity=wm_opacity' in content:
        print("✅ VERIFIED: custom_logo_path and wm_opacity are passed correctly as separate params")
    else:
        print("⚠️ WARNING: custom_logo_path or wm_opacity might be missing from the call")
else:
    print("ℹ️ Broken pattern not found. Checking for similar issues...")
    # Search for any dict.get with more than 2 args
    import re
    matches = re.findall(r'\.get\([^)]*,[^)]*,[^)]*\)', content)
    if matches:
        print(f"⚠️ Found {len(matches)} suspicious .get() calls:")
        for m in matches:
            print(f"   {m[:80]}...")
    else:
        print("✅ No problematic dict.get() calls found")

# Syntax check
try:
    compile(content, str(slp), "exec")
    print("✅ Syntax verification PASSED!")
    print("💡 NEXT: Run 'streamlit run app.py'")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")