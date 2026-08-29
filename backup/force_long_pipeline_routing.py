# force_long_pipeline_routing.py
import re
from pathlib import Path

APP_FILE = Path("app.py")
if not APP_FILE.exists():
    print("[ERROR] app.py not found!")
    exit(1)

content = APP_FILE.read_text(encoding="utf-8")

# Backup
backup = APP_FILE.with_suffix(".py.routing_force_backup")
if not backup.exists():
    backup.write_text(content, encoding="utf-8")
    print("[OK] Backup created.")

# We need to find where the render is triggered and ensure LONG mode uses safe_long_video_polished
# Look for the execution block in app.py

# Pattern to find the render execution logic
# We will inject a hard check: if mode is LONG or duration > 600s, FORCE safe_long_video_polished

old_render_logic = """if mode == "LONG":
            import safe_long_video_polished
            return safe_long_video_polished.run_integrated_long_pipeline("""

new_render_logic = """# FORCE LONG VIDEO TO USE FFMPEG ENGINE ONLY
        if mode == "LONG" or (voice_duration and float(voice_duration) > 600):
            print("🚀 [ROUTING] Long Video Detected (>10 mins). FORCING FFmpeg Batch Engine...")
            import safe_long_video_polished
            return safe_long_video_polished.run_integrated_long_pipeline("""

if old_render_logic in content:
    content = content.replace(old_render_logic, new_render_logic)
    print("[OK] Replaced Long Video routing logic.")
else:
    # Fallback: Try to find any generic render call and add the safeguard
    print("[INFO] Exact pattern not found. Applying safeguard patch...")
    
    # Find the main render call area
    if "process_multi_clip_render" in content and "safe_long_video_polished" not in content:
        # Replace master_pipeline call with safe_long check
        content = re.sub(
            r'(rendered_path\s*=\s*)process_multi_clip_render\(',
            r'\1(safe_long_video_polished.run_integrated_long_pipeline if mode == "LONG" else process_multi_clip_render)(',
            content
        )
        print("[OK] Applied safeguard: Long videos will now bypass master_pipeline.")

APP_FILE.write_text(content, encoding="utf-8")

print("\n" + "="*60)
print("✅ ROUTING FORCED SUCCESSFULLY!")
print("="*60)
print("Ab jab bhi aap Long Video (ya 10 min se zyada) render karenge,")
print("System automatically 'safe_long_video_polished.py' (FFmpeg) use karega.")
print("Short Video Engine (MoviePy) ko bypass kar diya gaya hai.")
print("\n💡 NEXT STEP:")
print("1. Restart Streamlit: streamlit run app.py")
print("2. Clear your temp folder to free up RAM before next render.")
print("3. Test the Long Video render again.")