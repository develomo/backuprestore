import os
import shutil

pipeline_file = "master_pipeline.py"
backup_file = "master_pipeline.py.before_caption_connect"

if not os.path.exists(pipeline_file):
    print("❌ Error: master_pipeline.py nahi mili.")
    exit()

# Backup
shutil.copy(pipeline_file, backup_file)
print(f"✅ Backup created: {backup_file}")

with open(pipeline_file, "r", encoding="utf-8") as f:
    content = f.read()

# Check if hook already exists
if "process_video_with_captions(" in content and content.count("process_video_with_captions") > 1:
    print("⚠️ Captions render function pehle se connected hai.")
else:
    # Target where final video is saved or returned in master_pipeline
    # We wrap the output path before final return
    old_export_pattern = "write_videofile"
    
    if old_export_pattern in content:
        # Hook caption application right before returning or finishing render
        caption_hook_code = """
        # --- AUTO-CONNECTED CAPTION POST-PROCESSING ---
        try:
            if 'caption_config' in locals() or 'caption_config' in globals():
                cfg = caption_config
            else:
                cfg = {"enabled": True, "style_id": "clean_subtitle", "mode": "phrase"}
            
            print("💬 [STEP 6/6] APPLYING DYNAMIC SUBTITLES & CAPTIONS...")
            process_video_with_captions(output_path, cfg, output_path)
            print("✅ [CAPTION ENGINE]: Subtitles successfully burned into final MP4!")
        except Exception as cap_err:
            print(f"⚠️ [CAPTION ENGINE WARNING]: Could not apply captions: {cap_err}")
"""
        # Inject hook before final completion message
        if "AUTHENTIC RENDER COMPLETE" in content:
            content = content.replace("print(\"======================================================================\\n✅ AUTHENTIC RENDER COMPLETE!", caption_hook_code + "\n        print(\"======================================================================\\n✅ AUTHENTIC RENDER COMPLETE!")
        else:
            # Fallback: append at end of main render function
            content += "\n" + caption_hook_code

        with open(pipeline_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 SUCCESS: Caption Engine is now 100% connected into Master Pipeline render flow!")