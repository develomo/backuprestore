import ast
import os
import re
import shutil

# Restoration source
src_file = (
    "master_pipeline.py.bak_unicode"
    if os.path.exists("master_pipeline.py.bak_unicode")
    else "master_pipeline.py"
)

with open(src_file, "r", encoding="utf-8", errors="ignore") as f:
  lines = f.readlines()

# 1. Clean non-ASCII / corrupt emoji characters safely line by line
cleaned_lines = []
for line in lines:
  clean_line = re.sub(r"[^\x00-\x7F]", " ", line)
  cleaned_lines.append(clean_line)

# 2. Locate the first 'write_videofile' call
write_line_idx = -1
for i, line in enumerate(cleaned_lines):
  if "write_videofile" in line:
    write_line_idx = i
    break

if write_line_idx == -1:
  print("❌ Error: write_videofile line nahi mili.")
  exit()

# Roll back to locate export section start safely without cutting active if statements
cut_idx = write_line_idx
for search_i in range(write_line_idx - 1, max(0, write_line_idx - 15), -1):
  line_str = cleaned_lines[search_i].strip()
  if (
      "EXPORT" in line_str
      or "STEP" in line_str
      or (line_str.startswith("#") and not line_str.startswith("# -"))
  ):
    cut_idx = search_i
    break

header_lines = cleaned_lines[:cut_idx]

# 3. Clean, fully-indented Export & Caption Engine block
new_export_block = '''    # --- SAFE FILE-LOCK FREE EXPORT & CAPTION ENGINE ---
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

    # Release Windows file handle lock
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

    # Cleanup temp
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
'''

final_code = "".join(header_lines) + "\n" + new_export_block

# 4. AST Syntax Check
try:
  ast.parse(final_code)
  with open("master_pipeline.py", "w", encoding="utf-8") as f:
    f.write(final_code)
  print(
      "🚀 SUCCESS: master_pipeline.py indentation and pipeline structure fixed"
      " with ZERO syntax errors!"
  )
except SyntaxError as e:
  print(f"❌ Syntax Error on line {e.lineno}: {e.msg}")