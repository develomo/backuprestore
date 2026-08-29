# fix_circle_logo_and_subscribe_position.py
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "batch_long_renderer.py"

content = TARGET.read_text(encoding="utf-8")

# FIX 1: Logo ko circle shape mein banana
# Current: "[1:v]scale=iw*0.09:-1,format=rgba,colorchannelmixer=aa=0.60[wm];"
# New: Circle mask add karna
old_logo_filter = '[1:v]scale=iw*0.09:-1,format=rgba,colorchannelmixer=aa=0.60[wm];'
new_logo_filter = '[1:v]scale=iw*0.09:-1,format=rgba,colorchannelmixer=aa=0.60,geq="p(X,Y)*alpha(X,Y)":\'if(lt((X-W/2)^2+(Y-H/2)^2,(min(W,H)/2)^2),255,0)\'[wm];'

if old_logo_filter in content:
    content = content.replace(old_logo_filter, new_logo_filter)
    print("[OK] Fix 1: Logo ab circle shape mein dikhega")
else:
    print("[WARN] Logo filter pattern nahi mila")

# FIX 2: Subscribe overlay ko bottom-center mein move karna
# Current: "bottom-right": ("main_w-overlay_w-24", "main_h-overlay_h-24"),
# New: bottom-center position
old_subscribe_pos = '"bottom-right": ("main_w-overlay_w-24", "main_h-overlay_h-24"),'
new_subscribe_pos = '"bottom-center": ("(main_w-overlay_w)/2", "main_h-overlay_h-80"),'

if old_subscribe_pos in content:
    content = content.replace(old_subscribe_pos, new_subscribe_pos)
    print("[OK] Fix 2: Subscribe overlay ab bottom-center (caption ke neeche) mein dikhega")
else:
    print("[WARN] Subscribe position pattern nahi mila")

# Also change the default corner parameter from bottom-right to bottom-center
old_corner_default = 'corner="bottom-right"'
new_corner_default = 'corner="bottom-center"'

if old_corner_default in content:
    content = content.replace(old_corner_default, new_corner_default)
    print("[OK] Fix 2b: Default corner ab bottom-center hai")

TARGET.write_text(content, encoding="utf-8")
print("\n✅ Done! Streamlit restart karein aur test karein.")