import os
import ast
import re

print("🚀 Applying Fail-Safe Duration Auto-Router to master_pipeline.py...")

TARGET_FILE = "master_pipeline.py"

if not os.path.exists(TARGET_FILE):
    print("❌ Error: master_pipeline.py file not found!")
    exit(1)

with open(TARGET_FILE, "r", encoding="utf-8") as f:
    code = f.read()

# Backup
with open("master_pipeline.py.bak_failsafe", "w", encoding="utf-8") as dst:
    dst.write(code)

# Fail-Safe Auto Route Code (Intercepts any audio > 180s and forces FFmpeg Batch Engine)
interceptor_code = '''
    # --- FAIL-SAFE LONG VIDEO ROUTER (AUTOMATIC DURATION CHECK) ---
    try:
        import subprocess, json
        probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(voice)]
        r = subprocess.run(probe_cmd, capture_output=True, text=True)
        v_dur = float(json.loads(r.stdout)["format"]["duration"])
        if v_dur > 180.0:
            print("\\n" + "="*70)
            print(f"⚡ AUTO-DETECTED LONG VIDEO ({v_dur:.1f}s > 180s)")
            print("⚡ BYPASSING MOVIEPY 30,000 FRAMES -> ROUTING TO FFMPEG BATCH ENGINE")
            print("="*70 + "\\n")
            import batch_long_renderer
            return batch_long_renderer.render_long_batch_memory(
                voice_path=voice,
                clips=clips,
                output_path=output_file if 'output_file' in locals() else args[0] if args else "final_renders/long_video.mp4"
            )
    except Exception as _route_err:
        print(f"Auto-route check notice: {_route_err}")
'''

# Inject right inside process_multi_clip_render function
if "def process_multi_clip_render" in code:
    pattern = r'(def process_multi_clip_render\s*\(.*?\):)'
    code = re.sub(pattern, r'\1' + interceptor_code, code, count=1)

# Validate syntax
try:
    ast.parse(code)
    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.write(code)
    print("✅ AST PASSED! master_pipeline.py updated with Fail-Safe Auto-Router.")
except SyntaxError as e:
    print(f"❌ Syntax error during patch: {e}")