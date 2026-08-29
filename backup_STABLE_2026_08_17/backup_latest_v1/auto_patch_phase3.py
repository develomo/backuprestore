import re
from pathlib import Path
import shutil

BASE_DIR = Path(__file__).parent

def backup_file(filepath):
    if filepath.exists():
        backup = filepath.with_suffix(filepath.suffix + ".backup_phase3")
        shutil.copy2(filepath, backup)
        print(f"[OK] Backup created: {backup.name}")

def patch_app_py_phase3():
    filepath = BASE_DIR / "app.py"
    if not filepath.exists():
        print(f"[SKIP] {filepath.name} not found.")
        return
    
    backup_file(filepath)
    content = filepath.read_text(encoding="utf-8")
    
    # 1. Replace long_assets function with new Watermark and Caption UI
    new_long_assets = '''def long_assets(settings, add_captions, caption_mode, style_id) -> None:
    st.markdown('<div class="asset-title">Long Video Assets</div>', unsafe_allow_html=True)
    voice = upload_single("Voice Upload", "LONG", "voices", AUDIO_EXTS, "long")
    clips = upload_multi("Clips Upload", "LONG", "clips", VIDEO_EXTS, "long")
    music = upload_single("BG Music Upload", "LONG", "music", AUDIO_EXTS, "long")
    sfx = upload_multi("SFX Upload", "LONG", "sfx", AUDIO_EXTS, "long")
    intro = upload_single("Intro Overlay", "LONG", "intro", VIDEO_EXTS | IMAGE_EXTS, "long")
    outro = upload_single("Outro Overlay", "LONG", "outro", VIDEO_EXTS | IMAGE_EXTS, "long")
    subscribe = upload_single("Subscribe Overlay", "LONG", "overlays", VIDEO_EXTS | IMAGE_EXTS, "long_sub")
    
    st.markdown("---")
    st.markdown("### 🛡️ Long Video Logo Watermark")
    enable_watermark = st.checkbox("Enable Logo Watermark", value=False, key="long_enable_wm")
    wm_logo = None
    wm_opacity = 0.6
    if enable_watermark:
        wm_logo = upload_single("Upload Logo (PNG/JPG/WEBP)", "LONG", "watermark", IMAGE_EXTS, "long_wm")
        wm_opacity = st.slider("Watermark Opacity", 0.1, 1.0, 0.6, 0.1, key="long_wm_opacity")
    
    st.markdown("---")
    st.markdown("### 📝 Caption Settings")
    enable_long_captions = st.checkbox("Enable Long Video Captions", value=bool(add_captions), key="long_enable_caps")
    
    assets = {
        "voice": voice,
        "clips": clips,
        "music": music,
        "sfx": sfx,
        "intro": intro,
        "outro": outro,
        "subscribe": subscribe,
        "wm_logo": wm_logo,
        "wm_opacity": wm_opacity,
    }
    ready = asset_ready_status(voice, clips)
    progress_bar = st.progress(0)
    status = st.empty()
    
    final_add_captions = enable_long_captions
    
    if st.button("Generate Long Video", width="stretch", type="primary", disabled=not ready):
        run_render("LONG", settings, assets, final_add_captions, caption_mode, style_id, progress_bar, status)
    if not ready:
        status.write("Waiting for long assets")

'''

    # Regex to match and replace the old long_assets function safely
    pattern = r'def long_assets\(settings, add_captions, caption_mode, style_id\) -> None:.*?(?=\ndef [a-zA-Z_])'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_long_assets, content, flags=re.DOTALL)
        print("[OK] Patched long_assets UI in app.py with Watermark and Caption Checkbox")
    else:
        print("[WARN] Could not find exact long_assets function block using regex.")

    # 2. Update build_render_kwargs to pass watermark data to backend
    old_kwargs_block = '''    if mode_u == "LONG":
        kwargs.update({
            "intro_path": assets.get("intro"),
            "outro_path": assets.get("outro"),
            "subscribe_overlay": assets.get("subscribe"),
            "subscribe_overlay_path": assets.get("subscribe"),
            "overlay": assets.get("subscribe"),
        })'''
    
    new_kwargs_block = '''    if mode_u == "LONG":
        kwargs.update({
            "intro_path": assets.get("intro"),
            "outro_path": assets.get("outro"),
            "subscribe_overlay": assets.get("subscribe"),
            "subscribe_overlay_path": assets.get("subscribe"),
            "overlay": assets.get("subscribe"),
            "custom_logo_path": assets.get("wm_logo"),
            "wm_opacity": assets.get("wm_opacity", 0.6),
        })'''
        
    if old_kwargs_block in content:
        content = content.replace(old_kwargs_block, new_kwargs_block)
        print("[OK] Patched build_render_kwargs to pass watermark data in app.py")
    else:
        # Fallback regex for kwargs update in case of slight formatting differences
        pattern_kwargs = r'(if mode_u == "LONG":\s*kwargs\.update\(\{[^}]+\"overlay\": assets\.get\(\"subscribe\"\),\s*\})'
        if re.search(pattern_kwargs, content, re.DOTALL):
            content = re.sub(pattern_kwargs, new_kwargs_block, content, flags=re.DOTALL)
            print("[OK] Patched build_render_kwargs using regex fallback.")
        else:
            print("[INFO] build_render_kwargs LONG block might already be patched or needs manual check.")

    filepath.write_text(content, encoding="utf-8")

if __name__ == "__main__":
    print("🚀 Starting Phase 3: UI Watermark, Captions Checkbox & Backend Wiring...")
    patch_app_py_phase3()
    print("✅ Phase 3 Upgrade Complete! Check the .backup_phase3 files if you need to revert.")
    print("💡 Next Step: Run `streamlit run app.py` to see the new UI features.")