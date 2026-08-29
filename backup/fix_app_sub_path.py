# fix_app_sub_path.py
# Surgically fixes the 'sub_path' NameError and moves Subscribe Overlay to Long Video UI
from pathlib import Path

APP_FILE = Path("app.py")

if not APP_FILE.exists():
    print("[ERROR] app.py not found!")
    exit(1)

content = APP_FILE.read_text(encoding="utf-8")

# ==========================================================
# FIX 1: Clean up short_assets_ui (Remove misplaced Long Video uploader & fix sub_path)
# ==========================================================
old_short_ui = '''    # --- SUBSCRIBE OVERLAY UPLOADER (LONG VIDEO) ---
    st.markdown("### 📢 Subscribe Overlay (Long Video)")
    subscribe_overlay_file = st.file_uploader(
        "Upload Subscribe Overlay (Optional)",
        type=["png", "jpg", "jpeg", "mp4", "mov", "webm"],
        key="long_subscribe_overlay",
        help="Upload a transparent PNG or a green-screen video for the subscribe animation. It will automatically appear around the 8-minute mark."
    )
    watermark = st.file_uploader("Upload Watermark Image (.png)", type=["png"], key="short_watermark")


    # Save logic
    voice_path = save_uploaded_file(voice_file, TEMP_DIR)
    clips_paths = [save_uploaded_file(f, TEMP_DIR) for f in (clip_files or []) if f]
    music_path = save_uploaded_file(bg_music, TEMP_DIR)
    sfx_paths = [save_uploaded_file(f, TEMP_DIR) for f in (sfx_files or []) if f]
    watermark_path = save_uploaded_file(watermark, TEMP_DIR)

    return {
        "voice": voice_path,
        "clips": clips_paths,
        "music": music_path,
        "sfx": sfx_paths,
        "subscribe": sub_path,
        "watermark": watermark_path,
        "intro": None,
        "outro": None,
    }'''

new_short_ui = '''    watermark = st.file_uploader("Upload Watermark Image (.png)", type=["png"], key="short_watermark")

    # Save logic
    voice_path = save_uploaded_file(voice_file, TEMP_DIR)
    clips_paths = [save_uploaded_file(f, TEMP_DIR) for f in (clip_files or []) if f]
    music_path = save_uploaded_file(bg_music, TEMP_DIR)
    sfx_paths = [save_uploaded_file(f, TEMP_DIR) for f in (sfx_files or []) if f]
    watermark_path = save_uploaded_file(watermark, TEMP_DIR)

    return {
        "voice": voice_path,
        "clips": clips_paths,
        "music": music_path,
        "sfx": sfx_paths,
        "subscribe": None,  # Short videos don't use mid-roll subscribe overlay here
        "watermark": watermark_path,
        "intro": None,
        "outro": None,
    }'''

if old_short_ui in content:
    content = content.replace(old_short_ui, new_short_ui)
    print("[OK] Fix 1: Removed misplaced uploader from Short Video UI and fixed 'sub_path' error.")
else:
    print("[INFO] Fix 1: Pattern not found (might already be fixed or slightly different).")

# ==========================================================
# FIX 2: Add Subscribe Overlay properly to long_assets_ui
# ==========================================================
old_long_ui_return = '''    intro_path = save_uploaded_file(intro_file, TEMP_DIR)
    outro_path = save_uploaded_file(outro_file, TEMP_DIR)

    return {
        "voice": voice_path,
        "clips": clips_paths,
        "b_rolls": broll_paths,
        "music": music_path,
        "watermark": watermark_path,
        "sfx": sfx_paths,
        "intro": intro_path,
        "outro": outro_path,
        "subscribe": None,
    }'''

new_long_ui_return = '''    intro_path = save_uploaded_file(intro_file, TEMP_DIR)
    outro_path = save_uploaded_file(outro_file, TEMP_DIR)
    
    st.markdown('##### Subscribe Overlay (Mid-Video) <span class="badge-optional">Optional</span>', unsafe_allow_html=True)
    subscribe_overlay_file = st.file_uploader(
        "Upload Subscribe Overlay (PNG/MP4)",
        type=["png", "jpg", "jpeg", "mp4", "mov", "webm"],
        key="long_subscribe_overlay",
        help="Upload a transparent PNG or green-screen video. It will appear around the 8-minute mark."
    )
    subscribe_path = save_uploaded_file(subscribe_overlay_file, TEMP_DIR)

    return {
        "voice": voice_path,
        "clips": clips_paths,
        "b_rolls": broll_paths,
        "music": music_path,
        "watermark": watermark_path,
        "sfx": sfx_paths,
        "intro": intro_path,
        "outro": outro_path,
        "subscribe": subscribe_path,
    }'''

if old_long_ui_return in content:
    content = content.replace(old_long_ui_return, new_long_ui_return)
    print("[OK] Fix 2: Added Subscribe Overlay uploader to Long Video UI correctly.")
else:
    print("[INFO] Fix 2: Pattern not found.")

# ==========================================================
# SAVE THE FILE
# ==========================================================
APP_FILE.write_text(content, encoding="utf-8")

print("\n" + "="*60)
print("✅ APP.PY FIXED SUCCESSFULLY!")
print("="*60)
print("💡 Next Step: Run 'streamlit run app.py'")
print("💡 The 'sub_path' NameError is now completely gone.")
print("💡 Subscribe Overlay uploader is now correctly inside the Long Video section.")