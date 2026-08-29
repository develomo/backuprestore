import ast
import os
import shutil

pipeline_file = "master_pipeline.py"

if not os.path.exists(pipeline_file):
  print("❌ Error: master_pipeline.py missing.")
  exit()

shutil.copy(pipeline_file, "master_pipeline.py.bak_cta_sub")

with open(pipeline_file, "r", encoding="utf-8", errors="ignore") as f:
  code = f.read()

# Replace or Auto-Detect CTA overlay file if missing from UI dict
old_cta_block = """    if cta_path and os.path.exists(str(cta_path)):"""
new_cta_block = """    # Fallback to local CTA file if UI didn't pass valid path
    if not cta_path or not os.path.exists(str(cta_path)):
        for possible_cta in ["subscribe_overlay.mp4", "assets/subscribe_overlay.mp4", "cta.mp4"]:
            if os.path.exists(possible_cta):
                cta_path = possible_cta
                break

    if cta_path and os.path.exists(str(cta_path)):"""

if old_cta_block in code:
  code = code.replace(old_cta_block, new_cta_block)

# Fix Caption Engine call to pass audio path for transcription & burn-in
old_sub_block = """process_video_with_captions(temp_export, caption_cfg, output_path)"""
new_sub_block = """# Pass audio_path in config so caption engine can transcribe voiceover
            caption_cfg["audio_path"] = audio_path
            process_video_with_captions(temp_export, caption_cfg, output_path)"""

if old_sub_block in code:
  code = code.replace(old_sub_block, new_sub_block)

try:
  ast.parse(code)
  with open(pipeline_file, "w", encoding="utf-8") as f:
    f.write(code)
  print(
      "🚀 SUCCESS: CTA Overlay Auto-fallback and Captions audio connection"
      " applied!"
  )
except SyntaxError as syn_err:
  print(f"❌ Syntax Error: {syn_err}")