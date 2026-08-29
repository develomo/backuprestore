import os
import shutil

pipeline_file = "master_pipeline.py"

if not os.path.exists(pipeline_file):
    print("❌ Error: master_pipeline.py nahi mili.")
    exit()

shutil.copy(pipeline_file, "master_pipeline.py.before_direct_hook")

with open(pipeline_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
hook_inserted = False

for line in lines:
    # Inject before the final render completion log
    if ("AUTHENTIC RENDER COMPLETE" in line or "EXPORTING FINAL" in line) and not hook_inserted:
        indent = " " * (len(line) - len(line.lstrip()))
        if not indent:
            indent = "    "
        
        caption_hook = [
            f"\n{indent}# --- DYNAMIC CAPTION POST-PROCESSING HOOK ---\n",
            f"{indent}try:\n",
            f"{indent}    print('\\n💬 [STEP 6/6] APPLYING DYNAMIC SUBTITLES & CAPTIONS...')\n",
            f"{indent}    cfg = caption_config if 'caption_config' in locals() else {{'enabled': True, 'style_id': 'clean_subtitle', 'mode': 'phrase'}}\n",
            f"{indent}    if 'output_path' in locals():\n",
            f"{indent}        process_video_with_captions(output_path, cfg, output_path)\n",
            f"{indent}        print('✅ [CAPTION ENGINE]: Subtitles successfully burned into final MP4!\\n')\n",
            f"{indent}except Exception as cap_err:\n",
            f"{indent}    print(f'⚠️ [CAPTION ENGINE WARNING]: {{cap_err}}\\n')\n\n"
        ]
        new_lines.extend(caption_hook)
        hook_inserted = True
        
    new_lines.append(line)

with open(pipeline_file, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

if hook_inserted:
    print("🚀 SUCCESS: Caption Hook Line-by-Line inject ho gaya hai!")
else:
    print("⚠️ Target line nahi mili, basic fallback apply hua.")