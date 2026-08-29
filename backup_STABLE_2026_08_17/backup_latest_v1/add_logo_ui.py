import re
from pathlib import Path

app_path = Path("app.py")
content = app_path.read_text(encoding="utf-8")

# Pehle check karein ke logo upload already exist toh nahi
if "upload_single(\"Logo Overlay\"" in content:
    print("✅ Logo UI already present. Skipping.")
else:
    # Long assets section mein 'outro' ke baad 'logo' insert karna hai
    # Pattern: upload_single("Outro Overlay", "LONG", "outro", ...)
    pattern = r'(upload_single\("Outro Overlay",\s*"LONG",\s*"outro",\s*VIDEO_EXTS \| IMAGE_EXTS,\s*"long"\))'
    replacement = r'''\1
    logo = upload_single("Logo Overlay", "LONG", "logos", IMAGE_EXTS, "long_logo")'''
    
    new_content, count = re.subn(pattern, replacement, content)
    
    if count == 0:
        print("❌ Could not find Outro Upload line. Please add manually.")
    else:
        # Ab assets dictionary mein logo add karna hai
        # Pattern: assets = { ... } wali line dhoondho
        asset_pattern = r'(assets = \{\s*"voice": voice,\s*"clips": clips,\s*"music": music,\s*"sfx": sfx,\s*"intro": intro,\s*"subscribe": subscribe,\s*"outro": outro,\s*\})'
        asset_replacement = r'''\1
        "logo": logo,'''
        
        new_content, count2 = re.subn(asset_pattern, asset_replacement, new_content)
        
        app_path.write_text(new_content, encoding="utf-8")
        print(f"✅ Logo UI added successfully. (Assets dict updated: {count2})")