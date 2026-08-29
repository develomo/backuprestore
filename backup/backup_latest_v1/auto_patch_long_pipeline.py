import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent

def backup_file(filepath):
    if filepath.exists():
        backup = filepath.with_suffix(filepath.suffix + ".backup_pre_upgrade")
        shutil.copy2(filepath, backup)
        print(f"[OK] Backup created: {backup.name}")

def patch_safe_long():
    filepath = BASE_DIR / "safe_long_video_polished.py"
    if not filepath.exists():
        print(f"[SKIP] {filepath.name} not found.")
        return
    
    backup_file(filepath)
    content = filepath.read_text(encoding="utf-8")
    
    # FIX 1: Stop blind itertools.cycle repetition
    old_distribute = '''def _distribute_clips(clips, target_duration, voice_duration=None):
    """
    Clips ko exactly target_duration (voice length) ke hisaab se distribute karega.
    Agar clips ki total duration target se kam hai toh repeat karega, warna original return.
    """
    def _get_duration(video_path):
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video_path)]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(json.loads(r.stdout)["format"]["duration"])
        except:
            return 5.0

    if not clips:
        return clips

    durations = []
    total_duration = 0.0
    for c in clips:
        d = _get_duration(c)
        durations.append(d)
        total_duration += d

    if target_duration is None and voice_duration is not None:
        target_duration = voice_duration
    if target_duration is None:
        target_duration = 0.0

    print(f"[ClipDist] Total clips duration: {total_duration:.2f}s | Target: {target_duration:.2f}s")

    if total_duration >= target_duration:
        print("[ClipDist] Clips are sufficient. No repeat needed.")
        return clips

    if total_duration <= 0:
        repeats_needed = 2
    else:
        repeats_needed = int(target_duration // total_duration) + 2

    print(f"[ClipDist] Repeating clips {repeats_needed} times.")
    extended = list(itertools.islice(itertools.cycle(clips), len(clips) * repeats_needed))
    return extended'''

    new_distribute = '''def _distribute_clips(clips, target_duration, voice_duration=None):
    """
    FIXED: Ab clips ko blindly repeat NAHI karega. 
    Renderer (batch_long_renderer.py) khud sequential parts banayega aur 
    150 clips ko 150 unique parts ke tor pe use karega. 
    Sirf tab wrap-around hoga jab saare clips exhaust ho jayen.
    """
    if not clips:
        return clips
    print(f"[ClipDist] Passing {len(clips)} unique clips to renderer for sequential processing.")
    return list(clips)'''

    if old_distribute in content:
        content = content.replace(old_distribute, new_distribute)
        print("[OK] Patched _distribute_clips in safe_long_video_polished.py")
    else:
        print("[WARN] Could not find exact _distribute_clips block.")

    # FIX 2: Respect Caption Checkbox
    old_caption = '''def caption_enabled(add_captions,caption_mode,style_id=None):
    return True # FORCED CAPTIONS ON
    return True'''
    
    new_caption = '''def caption_enabled(add_captions, caption_mode, style_id=None):
    # FIXED: Ab UI ka checkbox respect hoga. Agar False hai toh Whisper/Caption skip hoga.
    return bool(add_captions)'''

    if old_caption in content:
        content = content.replace(old_caption, new_caption)
        print("[OK] Patched caption_enabled in safe_long_video_polished.py")
    else:
        print("[WARN] Could not find exact caption_enabled block.")

    filepath.write_text(content, encoding="utf-8")

def patch_app_py():
    filepath = BASE_DIR / "app.py"
    if not filepath.exists():
        print(f"[SKIP] {filepath.name} not found.")
        return
    
    backup_file(filepath)
    content = filepath.read_text(encoding="utf-8")
    
    old_long_assets = '''def long_assets(settings, add_captions, caption_mode, style_id) -> None:
    st.markdown('<div class="asset-title">Long Video Assets</div>', unsafe_allow_html=True)
    voice = upload_single("Voice Upload", "LONG", "voices", AUDIO_EXTS, "long")
    clips = upload_multi("Clips Upload", "LONG", "clips", VIDEO_EXTS, "long")
    music = upload_single("BG Music Upload", "LONG", "music", AUDIO_EXTS, "long")
    sfx = upload_multi("SFX Upload", "LONG", "sfx", AUDIO_EXTS, "long")
    intro = upload_single("Intro Overlay", "LONG", "intro", VIDEO_EXTS | IMAGE_EXTS, "long")
    subscribe = upload_single("Subscribe Overlay", "LONG", "overlays", VIDEO_EXTS | IMAGE_EXTS, "long_sub")
    outro = upload_single("Outro Overlay", "LONG", "outro", VIDEO_EXTS | IMAGE_EXTS, "long")
    assets = {
        "voice": voice,
        "clips": clips,
        "music": music,
        "sfx": sfx,
        "intro": intro,
        "subscribe": subscribe,
        "outro": outro,
    }
    ready = asset_ready_status(voice, clips)
    progress_bar = st.progress(0)
    status = st.empty()
    if st.button("Generate Long Video", width="stretch", type="primary", disabled=not ready):
        run_render("LONG", settings, assets, add_captions, caption_mode, style_id, progress_bar, status)
    if not ready:
        status.write("Waiting for long assets")'''

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
        "voice": voice, "clips": clips, "music": music, "sfx": sfx,
        "intro": intro, "outro": outro, "subscribe": subscribe,
        "wm_logo": wm_logo, "wm_opacity": wm_opacity,
    }
    ready = asset_ready_status(voice, clips)
    progress_bar = st.progress(0)
    status = st.empty()
    
    final_add_captions = enable_long_captions
    
    if st.button("Generate Long Video", width="stretch", type="primary", disabled=not ready):
        run_render("LONG", settings, assets, final_add_captions, caption_mode, style_id, progress_bar, status)
    if not ready:
        status.write("Waiting for long assets")'''

    if old_long_assets in content:
        content = content.replace(old_long_assets, new_long_assets)
        print("[OK] Patched long_assets UI in app.py")
    else:
        print("[WARN] Could not find exact long_assets block in app.py.")

    # Patch build_render_kwargs to pass watermark data
    old_kwargs = '''    if mode_u == "LONG":
        kwargs.update({
            "intro_path": assets.get("intro"),
            "outro_path": assets.get("outro"),
            "subscribe_overlay": assets.get("subscribe"),
            "subscribe_overlay_path": assets.get("subscribe"),
            "overlay": assets.get("subscribe"),
        })'''
    
    new_kwargs = '''    if mode_u == "LONG":
        kwargs.update({
            "intro_path": assets.get("intro"),
            "outro_path": assets.get("outro"),
            "subscribe_overlay": assets.get("subscribe"),
            "subscribe_overlay_path": assets.get("subscribe"),
            "overlay": assets.get("subscribe"),
            "custom_logo_path": assets.get("wm_logo"),
            "wm_opacity": assets.get("wm_opacity", 0.6),
        })'''
        
    if old_kwargs in content:
        content = content.replace(old_kwargs, new_kwargs)
        print("[OK] Patched build_render_kwargs to pass watermark data in app.py")

    filepath.write_text(content, encoding="utf-8")

def patch_voice_humanization():
    filepath = BASE_DIR / "voice_humanization_orchestrator.py"
    if not filepath.exists():
        print(f"[SKIP] {filepath.name} not found.")
        return
    
    backup_file(filepath)
    content = filepath.read_text(encoding="utf-8")
    
    # Enhance EQ filter for SynthID disruption and robotic feel removal
    old_eq = '''def _eq_filter(profile, mode="short"):
    highpass = int(_clamp(_safe_float(profile.get("highpass_hz"), 80), 60, 140))
    lowpass = int(_clamp(_safe_float(profile.get("lowpass_hz"), 11500), 7500, 14000))

    # Mild harshness cleanup.
    if _mode_key(mode) == "long":
        harsh_cut = -0.8
    else:
        harsh_cut = -1.1

    return (
        f"highpass=f={highpass},"
        f"lowpass=f={lowpass},"
        f"equalizer=f=3300:t=q:w=1.2:g={harsh_cut},"
        f"equalizer=f=7800:t=q:w=1.0:g=-0.7"
    )'''

    new_eq = '''def _eq_filter(profile, mode="short"):
    highpass = int(_clamp(_safe_float(profile.get("highpass_hz"), 80), 60, 140))
    lowpass = int(_clamp(_safe_float(profile.get("lowpass_hz"), 11500), 7500, 14000))

    # Mild harshness cleanup + SynthID disruption (broadband subtle shift)
    if _mode_key(mode) == "long":
        harsh_cut = -0.8
        # Subtle chorus to break robotic phase alignment and disrupt basic audio watermarking
        chorus = "chorus=0.7:0.9:55:0.4:0.25:2,"
    else:
        harsh_cut = -1.1
        chorus = ""

    return (
        f"highpass=f={highpass},"
        f"lowpass=f={lowpass},"
        f"{chorus}"
        f"equalizer=f=3300:t=q:w=1.2:g={harsh_cut},"
        f"equalizer=f=7800:t=q:w=1.0:g=-0.7"
    )'''

    if old_eq in content:
        content = content.replace(old_eq, new_eq)
        print("[OK] Enhanced _eq_filter with chorus/SynthID disruption in voice_humanization_orchestrator.py")
    else:
        print("[WARN] Could not find exact _eq_filter block.")

    filepath.write_text(content, encoding="utf-8")

if __name__ == "__main__":
    print("🚀 Starting Automated Long Video Pipeline Upgrade...")
    patch_safe_long()
    patch_app_py()
    patch_voice_humanization()
    print("✅ Upgrade Complete! Check the .backup_pre_upgrade files if you need to revert.")
    print("💡 Next Step: Run `streamlit run app.py` and test the Long Video pipeline.")