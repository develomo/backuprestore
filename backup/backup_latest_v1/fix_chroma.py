import os

with open('master_pipeline.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add MoviePy mask fx for chroma keying green screen
old_cta_code = "sub_clip = (VideoFileClip(sub_p)"
new_cta_code = "sub_raw = VideoFileClip(sub_p)\n                    # Apply Green Screen Chroma Key\n                    sub_raw = sub_raw.fx(vfx.mask_color, color=[0, 255, 0], thr=100, s=5)\n                    sub_clip = (sub_raw"

if "vfx.mask_color" not in code and old_cta_code in code:
    code = code.replace(old_cta_code, new_cta_code)
    with open('master_pipeline.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("✅ Chroma Key Fix Applied Successfully!")
else:
    print("⚠️ Already patched or pattern mismatch.")