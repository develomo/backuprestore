import os
import re

print("🚀 Fixing Long Video Routing, RAM Memory Error & UI Controls...")

# 1. Backups
files = ["app.py", "safe_long_video_polished.py", "batch_long_renderer.py"]
for f in files:
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as src, open(f"{f}.bak_route", "w", encoding="utf-8") as dst:
            dst.write(src.read())

# 2. PATCH app.py -> Route Long Video away from master_pipeline to safe_long_video_polished
if os.path.exists("app.py"):
    with open("app.py", "r", encoding="utf-8") as f:
        app_code = f.read()

    # Add Subscribe Overlay and Captions Checkbox UI components if missing
    subscribe_ui_snippet = '''
                st.subheader("Subscribe Call-to-Action & Overlays")
                long_subscribe_file = st.file_uploader("Upload Subscribe Overlay (.mp4, .mov, .png)", type=["mp4", "mov", "png", "jpg"], key="long_subscribe_up")
                add_captions_toggle = st.checkbox("Enable Subtitles / Captions", value=True, key="long_cap_toggle")
'''
    if "long_subscribe_up" not in app_code and "Intro" in app_code:
        app_code = re.sub(
            r'(st\.file_uploader\(.*?"Upload Outro.*?\))',
            r'\1\n' + subscribe_ui_snippet,
            app_code,
            flags=re.DOTALL
        )

    # Force Long Video execution through safe_long_video_polished
    routing_patch = '''
        # LONG VIDEO ROUTING ENGINE (RAM SAFE FFMPEG BATCHES)
        if is_long_format or ("16:9" in str(selected_format)) or ("Long" in str(selected_format)):
            print("\\n======================================================================")
            print("⚡ ROUTING TO LONG VIDEO FFmpeg BATCH ENGINE (No MoviePy RAM Crash)")
            print("======================================================================\\n")
            import safe_long_video_polished
            return safe_long_video_polished.run_integrated_long_pipeline(
                voice_path=_save_streamlit_upload_to_temp(voice_file) if 'voice_file' in locals() else None,
                clips=[_save_streamlit_upload_to_temp(c) for c in clip_files] if 'clip_files' in locals() and clip_files else [],
                music_path=_save_streamlit_upload_to_temp(music_file) if 'music_file' in locals() else None,
                sfx_files=[_save_streamlit_upload_to_temp(s) for s in sfx_files] if 'sfx_files' in locals() and sfx_files else [],
                intro_path=_save_streamlit_upload_to_temp(intro_file) if 'intro_file' in locals() else None,
                outro_path=_save_streamlit_upload_to_temp(outro_file) if 'outro_file' in locals() else None,
                subscribe_overlay=_save_streamlit_upload_to_temp(long_subscribe_file) if 'long_subscribe_file' in locals() else None,
                custom_logo_path=_save_streamlit_upload_to_temp(logo_file) if 'logo_file' in locals() else None,
                add_captions=add_captions_toggle if 'add_captions_toggle' in locals() else True,
                output_path=str(output_file),
                fps=24,
                quality="480p"
            )
'''
    if "process_multi_clip_render" in app_code and "safe_long_video_polished" not in app_code:
        app_code = app_code.replace(
            "rendered_path = process_multi_clip_render(clips, voice, str(output_file), settings=merged_settings)",
            routing_patch + "\n        rendered_path = process_multi_clip_render(clips, voice, str(output_file), settings=merged_settings)"
        )

    with open("app.py", "w", encoding="utf-8") as f:
        f.write(app_code)
    print("⚡ Fixed Routing & Added Long Video UI Elements in app.py")

# 3. PATCH batch_long_renderer.py -> Enhanced Live Terminal Logging
if os.path.exists("batch_long_renderer.py"):
    with open("batch_long_renderer.py", "r", encoding="utf-8") as f:
        batch_code = f.read()

    # Inject Terminal Progress Logs for SFX, Music, and Batching
    log_enhancement = '''
    print("\\n======================================================================")
    print("⚡ ULTRA-FAST FFMPEG BATCH ENGINE STARTED (RAM SAFE - NO MOVIEPY CRASH)")
    print(f"➔ Voice Track Duration: {total_v:.2f}s")
    print(f"➔ Total Input Clips: {len(clips_to_use)}")
    print(f"➔ Background Music: {'CONNECTED (Non-stop Loop)' if music_path else 'NONE'}")
    print(f"➔ Sound Effects (SFX): {'CONNECTED (Mixed at transitions)' if sfx_files else 'NONE'}")
    print(f"➔ Subscribe Overlay: {'CONNECTED (Green screen removed)' if subscribe_overlay else 'NONE'}")
    print(f"➔ Auto Captions: {'ENABLED' if add_captions else 'DISABLED (Fast Mode)'}")
    print("======================================================================\\n")
'''
    if "render_long_batch_memory" in batch_code and "ULTRA-FAST FFMPEG BATCH ENGINE STARTED" not in batch_code:
        batch_code = re.sub(
            r'(def render_long_batch_memory.*?:)',
            r'\1\n' + log_enhancement,
            batch_code,
            count=1
        )

    with open("batch_long_renderer.py", "w", encoding="utf-8") as f:
        f.write(batch_code)
    print("⚡ Added Live Progress Logging to batch_long_renderer.py")

print("\n✅ MASTER ROUTING & UI PATCH COMPLETED SUCCESSFULLY!")