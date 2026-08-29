import os
import shutil

PIPELINE_FILE = "master_pipeline.py"
BACKUP_FILE = "master_pipeline.py.backup"

IMPORT_STATEMENT = "\nfrom caption_engine import apply_captions_to_video\n"

CAPTION_LOGIC_BLOCK = """
def process_video_with_captions(input_video_path, caption_config, final_output_path):
    \"\"\"
    Auto-injected wrapper: Applies captions if enabled, otherwise passes the video through.
    \"\"\"
    if caption_config and caption_config.get("enabled", False):
        print(f"[Auto-Patch] Applying Captions. Style: {caption_config.get('style_id')}")
        
        # Dummy timestamp data (Replace with Whisper engine data in production)
        caption_data = [
            {"text": "AUTO PATCH SUCCESSFUL", "start": 0.0, "end": 2.5},
            {"text": "CAPTIONS ARE WORKING", "start": 2.5, "end": 5.0}
        ]
        
        apply_captions_to_video(
            video_path=input_video_path,
            caption_data=caption_data,
            style_id=caption_config.get("style_id", "clean_subtitle"),
            mode=caption_config.get("mode", "phrase"),
            output_path=final_output_path
        )
        return final_output_path
    else:
        print("[Auto-Patch] Captions disabled. Passing original video.")
        # Just rename/copy to final output if no captions are needed
        if input_video_path != final_output_path:
            import shutil
            shutil.copy(input_video_path, final_output_path)
        return final_output_path
"""

def patch_master_pipeline():
    if not os.path.exists(PIPELINE_FILE):
        print(f"❌ Error: {PIPELINE_FILE} nahi mila. Make sure you are in the correct directory.")
        return

    # Create safe backup
    shutil.copy(PIPELINE_FILE, BACKUP_FILE)
    print(f"✅ Backup created: {BACKUP_FILE}")

    with open(PIPELINE_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if already patched
    if "process_video_with_captions" in content or "apply_captions_to_video" in content:
        print("⚠️ Master Pipeline pehle se patched hai. No changes made.")
        return

    # Add import at the top
    if "import apply_captions_to_video" not in content:
        content = IMPORT_STATEMENT + content

    # Append the caption logic block at the end of the file
    content += "\n" + CAPTION_LOGIC_BLOCK

    with open(PIPELINE_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print("🚀 Success: Master Pipeline auto-patched successfully!")
    print("👉 Ab aap apni existing render logic mein 'process_video_with_captions(temp_vid, caption_config, final_vid)' call kar sakte hain.")

if __name__ == "__main__":
    patch_master_pipeline()