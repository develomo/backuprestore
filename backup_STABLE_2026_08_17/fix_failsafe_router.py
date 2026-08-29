import os
import ast

print("🚀 Patching master_pipeline.py cleanly with Fail-Safe Auto-Router...")

file_path = "master_pipeline.py"

if not os.path.exists(file_path):
    print("❌ Error: master_pipeline.py file not found.")
    exit(1)

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Backup
with open("master_pipeline.py.bak_router_clean", "w", encoding="utf-8") as f_bak:
    f_bak.writelines(lines)

code_text = "".join(lines)

if "AUTO-DETECTED LONG VIDEO" in code_text:
    print("⚠️ Fail-safe router is already present in master_pipeline.py.")
else:
    router_block = '''    # --- FAIL-SAFE LONG VIDEO AUTOMATIC ROUTER ---
    try:
        import subprocess, json, batch_long_renderer
        _probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(voice)], capture_output=True, text=True)
        _dur = float(json.loads(_probe.stdout)['format']['duration'])
        if _dur > 180.0:
            print('\\n======================================================================')
            print(f'⚡ AUTO-DETECTED LONG VIDEO ({_dur:.1f}s > 180s)')
            print('⚡ BYPASSING MOVIEPY 30,000 FRAMES -> ROUTING TO FFMPEG BATCH ENGINE')
            print('======================================================================\\n')
            return batch_long_renderer.render_long_batch_memory(voice_path=voice, clips=clips, output_path=output_file if 'output_file' in locals() else 'final_renders/long_video.mp4')
    except Exception as _e:
        print(f'Auto-route check notice: {_e}')
'''

    new_lines = []
    inserted = False
    for line in lines:
        new_lines.append(line)
        if "def process_multi_clip_render" in line and not inserted:
            new_lines.append(router_block + "\n")
            inserted = True

    patched_code = "".join(new_lines)
    
    try:
        ast.parse(patched_code)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(patched_code)
        print("✅ AST PASSED! master_pipeline.py updated with Fail-Safe Auto-Router.")
    except SyntaxError as e:
        print(f"❌ Syntax Error during patch: {e}")