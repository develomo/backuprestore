import ast
import os
import re
import shutil

pipeline_file = 'master_pipeline.py'

if not os.path.exists(pipeline_file):
  print('❌ Error: master_pipeline.py file nahi mili.')
  exit()

# Backup
shutil.copy(pipeline_file, 'master_pipeline.py.bak_unicode')
print('✅ Backup created: master_pipeline.py.bak_unicode')

with open(pipeline_file, 'r', encoding='utf-8', errors='ignore') as f:
  code = f.read()

# 1. Clean all non-ASCII / Emoji corrupted characters
clean_code = re.sub(r'[^\x00-\x7F]+', ' ', code)

# 2. Add UTF-8 stdout configuration at top
utf8_header = """# -*- coding: utf-8 -*-
import sys
import io
import os
import shutil
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
"""

if "sys.stdout.reconfigure" not in clean_code:
  clean_code = utf8_header + "\n" + clean_code

# 3. Inject Green Screen / Chroma Key Mask Function
chroma_mask_func = """
def apply_green_screen_mask(cta_clip):
    \"\"\"Removes solid green screen background from CTA overlay clips.\"\"\"
    try:
        def make_mask(frame):
            r = frame[:, :, 0].astype(float)
            g = frame[:, :, 1].astype(float)
            b = frame[:, :, 2].astype(float)
            is_green = (g > 90) & (g > r * 1.25) & (g > b * 1.25)
            mask = np.ones((frame.shape[0], frame.shape[1]), dtype=float)
            mask[is_green] = 0.0
            return mask
        mask_clip = cta_clip.fl_image(make_mask)
        return cta_clip.set_mask(mask_clip)
    except Exception:
        return cta_clip
"""

if 'def apply_green_screen_mask' not in clean_code:
  clean_code = chroma_mask_func + '\n' + clean_code

# Wrap CTA overlay loading with green screen removal
clean_code = re.sub(
    r'(VideoFileClip\(.*(?:subscribe|cta).*\))',
    r'apply_green_screen_mask(\1)',
    clean_code,
    flags=re.IGNORECASE,
)

# 4. Strip duplicate rendering blocks at the bottom of the main function
if 'def process_multi_clip_render' in clean_code:
  parts = clean_code.split('def process_multi_clip_render')
  header_part = parts[0]
  body_part = parts[1]

  # Cut off any duplicated tail
  if 'AUTHENTIC RENDER COMPLETE' in body_part:
    first_occur = body_part.find('AUTHENTIC RENDER COMPLETE')
    # Find last write_videofile before this
    cutoff = body_part.rfind('final_video', 0, first_occur)
    if cutoff != -1:
      body_part = body_part[:cutoff]

  # Clean Export + Captions Engine Block
  export_block = """
        # --- SAFE FILE-LOCK FREE EXPORT & CAPTION ENGINE ---
        temp_export = output_path.replace(".mp4", "_raw_temp.mp4")
        if os.path.exists(temp_export):
            try:
                os.remove(temp_export)
            except Exception:
                pass

        print("\\n[EXPORT] ENCODING BASE VIDEO MP4...")
        try:
            final_video.write_videofile(
                temp_export,
                fps=30,
                codec="libx264",
                audio_codec="aac",
                threads=2,
                preset="medium"
            )
        except Exception as exp_err:
            print(f"[WARN] Primary export retry: {exp_err}")
            final_video.write_videofile(temp_export, fps=30, codec="libx264")

        # Close video clips to release Windows file locks
        try:
            final_video.close()
        except Exception:
            pass

        # Apply Dynamic Captions
        captions_applied = False
        if os.path.exists(temp_export):
            try:
                cfg = caption_config if 'caption_config' in locals() and caption_config else {"enabled": True, "style_id": "clean_subtitle", "mode": "phrase"}
                if cfg.get('enabled', True):
                    print("\\n[STEP 6/6] BURNING DYNAMIC SUBTITLES & CAPTIONS INTO MP4...")
                    if 'process_video_with_captions' in globals() or 'process_video_with_captions' in locals():
                        process_video_with_captions(temp_export, cfg, output_path)
                        print("[CAPTION ENGINE]: Subtitles successfully burned into final MP4!\\n")
                        captions_applied = True
            except Exception as cap_err:
                print(f"[CAPTION ENGINE WARNING]: {cap_err}")

        # Fallback if captions failed or disabled
        if not captions_applied or not os.path.exists(output_path):
            if os.path.exists(temp_export):
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except Exception:
                        pass
                shutil.move(temp_export, output_path)

        # Cleanup leftover temp
        if os.path.exists(temp_export):
            try:
                os.remove(temp_export)
            except Exception:
                pass

        print("======================================================================")
        print("[SUCCESS] AUTHENTIC RENDER COMPLETE! ALL SUPPORTED FEATURES PROCESSED.")
        print(f"[OUTPUT] Final Render Saved At: {output_path}")
        print("======================================================================")

        return output_path
"""

  clean_code = (
      header_part
      + 'def process_multi_clip_render'
      + body_part
      + '\n'
      + export_block
  )

# 5. AST Pre-Validation Check
try:
  ast.parse(clean_code)
  with open(pipeline_file, 'w', encoding='utf-8') as f:
    f.write(clean_code)
  print(
      '🚀 SUCCESS: master_pipeline.py cleaned of all Emoji/Unicode corruptions'
      ' and rebuilt with zero syntax errors!'
  )
except SyntaxError as syn_err:
  print(f'❌ Syntax Validation Error at line {syn_err.lineno}: {syn_err.msg}')