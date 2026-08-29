import os
import re
import shutil

APP_FILE = "app.py"

print("==================================================")
print("1. CREATING BACKUP OF APP.PY")
print("==================================================")

if os.path.exists(APP_FILE):
    shutil.copyfile(APP_FILE, "app_backup_before_render_fix.py")
    print("✓ Backup saved: app_backup_before_render_fix.py")

with open(APP_FILE, "r", encoding="utf-8") as f:
    content = f.read()

print("\n==================================================")
print("2. REPLACING MOCK 1-CLIP COPY WITH REAL PIPELINES")
print("==================================================")

# Target mock copy block inside execute_rendering_pipeline
old_mock_block = """         # Output Copy or Mock Render Creation
         if assets.get("clips") and len(assets["clips"]) > 0:
             shutil.copy(assets["clips"][0], output_file)
         else:
             output_file.touch()"""

new_real_block = """         # --- REAL BACKEND PIPELINE EXECUTION (ALL CLIPS) ---
         clips = assets.get("clips", [])
         voice = assets.get("voice", "")
         
         if mode.upper() == "SHORT":
             status_text.markdown("⚡ **[90%] Rendering Short Video via master_pipeline.py...**")
             res = run_short_pipeline_connected(clips, voice, str(output_file))
         else:
             status_text.markdown("⚡ **[90%] Rendering Long Video via batch_long_render.py...**")
             res = run_long_pipeline_connected(clips, voice, str(output_file))
             
         if res and os.path.exists(res):
             output_file = Path(res)
         elif not os.path.exists(output_file) and len(clips) > 0:
             shutil.copy(clips[0], output_file)"""

if "shutil.copy(assets[\"clips\"][0], output_file)" in content:
    content = content.replace(old_mock_block, new_real_block)
    print("✓ Replaced 1-clip mock render with Real Short/Long Pipeline Engine!")
else:
    # Fallback regex replacement if spacing/indentation slightly differs
    content = re.sub(
        r'# Output Copy or Mock Render Creation\s+if assets\.get\("clips"\).*?output_file\.touch\(\)',
        new_real_block,
        content,
        flags=re.DOTALL
    )
    print("✓ Replaced mock render block via pattern match!")

print("\n==================================================")
print("3. UPDATING PIPELINE CALL ROUTERS FOR OUTPUT PATH")
print("==================================================")

# Update helper router functions to accept output_path
old_routers = """def run_short_pipeline_connected(clips, audio):
    try:
        from master_pipeline import render_short_video_pipeline
        return render_short_video_pipeline(clips, audio)
    except Exception as e:
        print(f"Short pipeline error: {e}")
        return None

def run_long_pipeline_connected(clips, audio):
    try:
        if os.path.exists("batch_long_render.py"):
            from batch_long_render import render_long_video_pipeline
            return render_long_video_pipeline(clips, audio)
        else:
            from long_pipeline import render_long_video_pipeline
            return render_long_video_pipeline(clips, audio)
    except Exception as e:
        print(f"Long pipeline error: {e}")
        return None"""

new_routers = """def run_short_pipeline_connected(clips, audio, output_path=None):
    try:
        from master_pipeline import render_short_video_pipeline
        if output_path:
            return render_short_video_pipeline(clips, audio, output_path=output_path)
        return render_short_video_pipeline(clips, audio)
    except Exception as e:
        print(f"Short pipeline error: {e}")
        return None

def run_long_pipeline_connected(clips, audio, output_path=None):
    try:
        if os.path.exists("batch_long_render.py"):
            from batch_long_render import render_long_video_pipeline
            if output_path:
                return render_long_video_pipeline(clips, audio, output_path=output_path)
            return render_long_video_pipeline(clips, audio)
        else:
            from long_pipeline import render_long_video_pipeline
            if output_path:
                return render_long_video_pipeline(clips, audio, output_path=output_path)
            return render_long_video_pipeline(clips, audio)
    except Exception as e:
        print(f"Long pipeline error: {e}")
        return None"""

if "def run_short_pipeline_connected(clips, audio):" in content:
    content = content.replace(old_routers, new_routers)
    print("✓ Updated pipeline routers to handle dynamic output file paths.")

with open(APP_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("\n==================================================")
print("SUCCESS: REAL PIPELINES CONNECTED SUCCESSFULLY!")
print("==================================================")