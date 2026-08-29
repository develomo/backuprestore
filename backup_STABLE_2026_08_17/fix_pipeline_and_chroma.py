import os
import shutil
import re

pipeline_file = "master_pipeline.py"

if not os.path.exists(pipeline_file):
    print("❌ Error: master_pipeline.py file nahi mili.")
    exit()

# Backup create karein
shutil.copy(pipeline_file, "master_pipeline.py.before_chroma_fix")
print("✅ Backup created: master_pipeline.py.before_chroma_fix")

with open(pipeline_file, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Inject Robust Chroma Key Function for Green Screen Removal
chroma_function = '''
import numpy as np

def apply_green_screen_mask(cta_clip):
    """Removes green screen background from CTA overlay video clips."""
    try:
        def make_mask(frame):
            r = frame[:, :, 0].astype(float)
            g = frame[:, :, 1].astype(float)
            b = frame[:, :, 2].astype(float)
            # Detect green color pixels
            is_green = (g > 90) & (g > r * 1.25) & (g > b * 1.25)
            mask = np.ones((frame.shape[0], frame.shape[1]), dtype=float)
            mask[is_green] = 0.0
            return mask

        mask_clip = cta_clip.fl_image(make_mask)
        return cta_clip.set_mask(mask_clip)
    except Exception as e:
        print(f"⚠️ Chroma key mask warning: {e}")
        return cta_clip
'''

if "def apply_green_screen_mask" not in code:
    code = chroma_function + "\n\n" + code

# 2. Fix Green Screen Application on CTA Video Clips
if "subscribe_overlay" in code or "cta" in code.lower():
    # Wrap overlay clips with apply_green_screen_mask
    code = re.sub(
        r'(VideoFileClip\(.*(?:subscribe|cta).*\))',
        r'apply_green_screen_mask(\1)',
        code,
        flags=re.IGNORECASE
    )

# 3. Clean up older incorrect hooks
lines = code.splitlines()
cleaned_lines = []
skip = False
for line in lines:
    if "DYNAMIC CAPTION POST-PROCESSING HOOK" in line or "APPLYING DYNAMIC SUBTITLES" in line:
        skip = True
        continue
    if skip and ("except Exception" in line or "print(" in line and "CAPTION" in line):
        if "CAPTION ENGINE" in line or "cap_err" in line:
            skip = False
            continue
    if not skip:
        cleaned_lines.append(line)

code = "\n".join(cleaned_lines)

# 4. Inject Safe Export-Then-Caption Pipeline Logic
# Find write_videofile and execute caption post-processing AFTER export finishes
old_write_pattern = r'(\w+)\.write_videofile\s*\(\s*output_path'

caption_export_wrapper = r'''
temp_render_path = output_path.replace(".mp4", "_temp_base.mp4")
\1.write_videofile(temp_render_path'''

if re.search(old_write_pattern, code):
    code = re.sub(old_write_pattern, caption_export_wrapper, code, count=1)

    # Post-process call right after write_videofile completes
    post_process_logic = '''
# --- SAFE CAPTION POST-PROCESSING AFTER EXPORT ---
try:
    print("\\n💬 [STEP 6/6] BURNING DYNAMIC SUBTITLES & CAPTIONS INTO MP4...")
    cfg = caption_config if 'caption_config' in locals() and caption_config else {"enabled": True, "style_id": "clean_subtitle", "mode": "phrase"}
    
    if os.path.exists(temp_render_path):
        process_video_with_captions(temp_render_path, cfg, output_path)
        if os.path.exists(temp_render_path):
            os.remove(temp_render_path)
        print("✅ [CAPTION ENGINE]: Subtitles successfully burned into final MP4!\\n")
    else:
        print("⚠️ Base render temp file missing, skipping caption burn.")
except Exception as cap_err:
    print(f"⚠️ [CAPTION ENGINE WARNING]: {cap_err}\\n")
    if os.path.exists(temp_render_path) and not os.path.exists(output_path):
        os.rename(temp_render_path, output_path)
'''
    
    if "AUTHENTIC RENDER COMPLETE" in code:
        code = code.replace('print("======================================================================\n✅ AUTHENTIC RENDER COMPLETE!', post_process_logic + '\nprint("======================================================================\n✅ AUTHENTIC RENDER COMPLETE!')
    else:
        code += "\n" + post_process_logic

with open(pipeline_file, "w", encoding="utf-8") as f:
    f.write(code)

print("🚀 SUCCESS: Green Screen Removal & Caption Export Order fixed in master_pipeline.py!")