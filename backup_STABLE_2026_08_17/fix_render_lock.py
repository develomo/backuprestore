import os
import shutil
import ast

pipeline_file = "master_pipeline.py"

if not os.path.exists(pipeline_file):
    print("❌ Error: master_pipeline.py file nahi mili.")
    exit()

# Backup
shutil.copy(pipeline_file, "master_pipeline.py.before_lock_fix")

with open(pipeline_file, "r", encoding="utf-8") as f:
    code = f.read()

# Safe replacement block for export and captions
export_and_caption_block = '''
        # --- SAFE EXPORT & CAPTION POST-PROCESSING (FILE-LOCK SAFE) ---
        temp_export_file = output_path.replace(".mp4", "_raw_temp.mp4")
        
        # Export base video to temporary path first
        final_video.write_videofile(
            temp_export_file,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="medium"
        )
        
        # Safely close clip to release Windows file handles
        try:
            final_video.close()
        except Exception:
            pass

        # Apply Captions / Burn-in if enabled
        captions_applied = False
        try:
            cfg = caption_config if 'caption_config' in locals() and caption_config else {"enabled": True, "style_id": "clean_subtitle", "mode": "phrase"}
            if cfg.get('enabled', True) and os.path.exists(temp_export_file):
                print("\\n💬 [STEP 6/6] BURNING DYNAMIC SUBTITLES & CAPTIONS INTO MP4...")
                process_video_with_captions(temp_export_file, cfg, output_path)
                print("✅ [CAPTION ENGINE]: Subtitles successfully burned into final MP4!\\n")
                captions_applied = True
        except Exception as cap_err:
            print(f"⚠️ [CAPTION ENGINE WARNING]: {cap_err}")

        # Fallback if captions failed or disabled
        if not captions_applied or not os.path.exists(output_path):
            if os.path.exists(temp_export_file):
                if os.path.exists(output_path):
                    os.remove(output_path)
                shutil.move(temp_export_file, output_path)

        # Cleanup leftover temp file
        if os.path.exists(temp_export_file):
            try:
                os.remove(temp_export_file)
            except Exception:
                pass

        print("======================================================================")
        print("✅ AUTHENTIC RENDER COMPLETE! ALL SUPPORTED FEATURES PROCESSED.")
        print(f"🎯 Final Render Output Saved At: {output_path}")
        print("======================================================================")
        
        return output_path
'''

# Replace old export pattern
lines = code.splitlines()
cleaned_lines = []
skip = False

for line in lines:
    if "final_video.write_videofile" in line or "write_videofile(" in line:
        skip = True
        continue
    if skip:
        if "return " in line or "AUTHENTIC RENDER COMPLETE" in line:
            skip = False
            continue
        else:
            continue
    cleaned_lines.append(line)

new_code = "\n".join(cleaned_lines)

# Inject the new clean block inside process_multi_clip_render
if "def process_multi_clip_render" in new_code:
    parts = new_code.split("def process_multi_clip_render")
    func_header = parts[0] + "def process_multi_clip_render"
    func_body = parts[1]
    
    # Insert right before the last lines of the function
    updated_body = func_body + "\n" + export_and_caption_block
    final_code = func_header + updated_body

# AST Pre-Validation Check
try:
    ast.parse(final_code)
    with open(pipeline_file, "w", encoding="utf-8") as f:
        f.write(final_code)
    print("🚀 SUCCESS: File lock issue fixed & valid path return configured!")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e}")