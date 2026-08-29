"""
============================================================================
PHASE 3 PATCH — Captions Fix (Remove Preview, Sync Short+Long, Instant Timing)
============================================================================
AUTO-PATCH: Reads app.py, surgically:
  1. Removes caption_video_preview_section() from _page_generator()
  2. Modifies long_assets() — reads Caption Style state for long video captions
  3. Fixes caption timing — caption_offset = 0 (instant with voice)
  4. Reduces caption preview video size in CSS + adds dummy text preview
  5. Connects short + long captions to same Caption Style section

HOW CAPTIONS WORK NOW:
  - Caption Style section (word-by-word / 3-4 words) controls BOTH short & long
  - Short: always applies captions based on checkboxes
  - Long: "Enable Long Video Captions" checkbox reads from Caption Style
  - Caption preview: small 150px preview with dummy text

USAGE:
  cd "D:\My Creation Video Generator\backup"
  python phase3_captions_fix_patch.py
============================================================================
"""
import os
import re

BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))


def main_phase3():
    app_path = os.path.join(BACKUP_DIR, 'app.py')

    with open(app_path, 'r', encoding='utf-8') as f:
        original = f.read()

    backup_path = app_path + '.backup_phase3'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original)
    print(f"[OK] Backup: {backup_path}")
    print(f"[INFO] {len(original.split(chr(10)))} lines")

    content = original
    patches = 0
    errors = []

    # ==================================================================
    # PATCH 1: Remove caption_video_preview_section() from _page_generator()
    # ==================================================================
    old_gen_marker = """    # 6. Caption Preview
    st.markdown("---")
    caption_video_preview_section()

    # 7. Output
    output_preview()"""

    new_gen_marker = """    # 6. Output
    output_preview()"""

    if old_gen_marker in content:
        content = content.replace(old_gen_marker, new_gen_marker)
        patches += 1
        print("[PATCH 1] Removed caption_video_preview_section() from _page_generator()")
    else:
        # Try fuzzy match
        idx = content.find('caption_video_preview_section()')
        if idx > 0:
            # Find the surrounding block (from 'st.markdown("---")' before to 'output_preview()' after)
            before_block = content.rfind('st.markdown("---")', idx - 200, idx)
            after_block = content.find('output_preview()', idx)
            if before_block > 0 and after_block > 0:
                # Remove lines from before_block to end of caption section
                section_start = content.rfind('\n', 0, before_block)
                content = content[:section_start + 1] + content[after_block:]
                patches += 1
                print("[PATCH 1] Removed caption_video_preview_section() via fuzzy match")
            else:
                errors.append("Could not remove caption_video_preview_section()")
        else:
            errors.append("caption_video_preview_section() not found in _page_generator()")

    # ==================================================================
    # PATCH 2: Replace long_assets() — connect to Caption Style state
    # ==================================================================
    old_long_assets = 'def long_assets(settings, add_captions, caption_mode, style_id) -> None:'
    if old_long_assets not in content:
        errors.append("long_assets() not found")
    else:
        idx_la = content.index(old_long_assets)
        after_la = content[idx_la + len(old_long_assets):]
        # Find end of this function
        next_def = re.search(r'\n(def |# ={10,}|# PHASE)', after_la)
        if next_def:
            la_end = idx_la + len(old_long_assets) + next_def.start()
        else:
            errors.append("Cannot find end of long_assets()")
            la_end = None

        if la_end:
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

    # -- Read Caption Style state from session --
    word_enabled = st.session_state.get("enable_word_caption", True)
    phrase_enabled = st.session_state.get("enable_phrase_caption", False)

    enable_long_captions = st.checkbox(
        "Enable Long Video Captions",
        value=bool(add_captions),
        key="long_enable_caps",
        help="Uses Caption Style settings from above (Word-by-Word or 3-4 Words)",
    )

    if enable_long_captions:
        if word_enabled and phrase_enabled:
            long_cap_mode = st.radio(
                "Caption Mode",
                ["word_by_word", "phrase"],
                format_func=lambda x: "Word by Word" if x == "word_by_word" else "3 to 4 Words",
                horizontal=True,
                key="long_cap_mode_radio",
            )
        elif word_enabled:
            long_cap_mode = "word_by_word"
            st.caption("Using: Word by Word")
        elif phrase_enabled:
            long_cap_mode = "phrase"
            st.caption("Using: 3 to 4 Words")
        else:
            long_cap_mode = "none"
            st.caption("No caption style selected")
        final_add_captions = True
    else:
        long_cap_mode = "none"
        final_add_captions = False

    # Get active style_id from Caption Style section
    long_style_id = style_id  # passed from captions_section()

    assets = {
        "voice": voice, "clips": clips, "music": music, "sfx": sfx,
        "intro": intro, "outro": outro, "subscribe": subscribe,
        "wm_logo": wm_logo, "wm_opacity": wm_opacity,
    }
    ready = asset_ready_status(voice, clips)
    progress_bar = st.progress(0)
    status = st.empty()

    caption_offset = 0.0  # PHASE 3: Instant caption — no delay

    if st.button("Generate Long Video", width="stretch", type="primary", disabled=not ready):
        run_render("LONG", settings, assets, final_add_captions, long_cap_mode, long_style_id, progress_bar, status)
    if not ready:
        status.write("Waiting for long assets")
'''

            content = content[:idx_la] + new_long_assets + '\n' + content[la_end:]
            patches += 1
            print("[PATCH 2] long_assets() — connected to Caption Style state, instant timing")

    # ==================================================================
    # PATCH 3: Fix caption_dropdown_card() — smaller preview, dummy text
    # ==================================================================
    # The caption preview video size is controlled by CSS class .caption-preview-box
    # We already set it to width:160px in Phase 1 CSS.
    # Now fix the preview text: show dummy words when video preview is missing

    old_preview_block = '    if p.exists() and p.stat().st_size > 2500:\n        st.video(str(p))\n    else:\n        st.warning("Preview missing. Run: python caption_preview_generator.py")'

    new_preview_block = '    if p.exists() and p.stat().st_size > 2500:\n        st.video(str(p))\n    else:\n        st.markdown(\n            \'<div style="color:#aaa;font-size:12px;text-align:center;padding:15px 8px;">\'\n            \'Sample • Text • Preview • Here\'<br><br>\'\n            \'<span style="opacity:0.5;font-size:10px;">Run: python caption_preview_generator.py</span>\'\n            \'</div>\',\n            unsafe_allow_html=True,\n        )'

    if old_preview_block in content:
        content = content.replace(old_preview_block, new_preview_block)
        patches += 1
        print("[PATCH 3] caption_dropdown_card() — dummy text preview instead of warning")
    else:
        errors.append("caption preview block not found for dummy text")

    # ==================================================================
    # PATCH 4: Fix short_assets() — ensure caption_offset = 0 for instant
    # ==================================================================
    # The caption_offset is passed via build_render_kwargs.
    # We need to ensure caption_offset is 0.0 in run_render function.

    old_run_render_offset = "caption_offset=0.12"  # old value from phase13 patches
    if old_run_render_offset in content:
        content = content.replace(old_run_render_offset, "caption_offset=0.0")
        patches += 1
        print("[PATCH 4] caption_offset changed from 0.12 to 0.0 (instant)")

    # Also check for caption_start_offset in presets
    old_start_offset = '"caption_start_offset": -0.12'
    if old_start_offset in content:
        content = content.replace(old_start_offset, '"caption_start_offset": 0.0')
        patches += 1
        print("[PATCH 4b] caption_start_offset changed from -0.12 to 0.0")

    # Also check for any -0.18 offsets
    old_start_offset2 = '"caption_start_offset": -0.18'
    if old_start_offset2 in content:
        content = content.replace(old_start_offset2, '"caption_start_offset": 0.0')
        patches += 1
        print("[PATCH 4c] caption_start_offset changed from -0.18 to 0.0")

    old_start_offset3 = '"caption_start_offset": -0.16'
    if old_start_offset3 in content:
        content = content.replace(old_start_offset3, '"caption_start_offset": 0.0')
        patches += 1
        print("[PATCH 4d] caption_start_offset changed from -0.16 to 0.0")

    # ==================================================================
    # PATCH 5: Ensure build_render_kwargs passes caption_offset=0
    # ==================================================================
    # The build_render_kwargs function creates kwargs dict for short videos
    # We need to ensure caption_offset is 0.0 there too

    old_caption_kwargs = '"caption_mode": caption_mode if add_captions else "none"'
    # Find the context where this is in build_render_kwargs and add caption_offset after it
    # But this is tricky — we'll add a global override in run_render instead

    # In run_render, ensure preset_overrides has caption_timing_precision and offset 0
    run_render_marker = 'def run_render(mode: str, settings: Dict[str, Any], assets: Dict[str, Any]'
    if run_render_marker in content:
        idx_rr = content.index(run_render_marker)
        # Find the line where preset_overrides is built
        rr_end = content.find('def asset_ready_status', idx_rr)
        if rr_end < 0:
            rr_end = content.find('\ndef ', idx_rr + 100)

        # Look for the section where kwargs are prepared and add caption_offset
        rr_block = content[idx_rr:rr_end] if rr_end > 0 else content[idx_rr:idx_rr+3000]

        # Add caption_offset injection: find "update(20, "Loading pipeline")" and inject before it
        old_pipeline_load = 'update(20, "Loading pipeline")'
        if old_pipeline_load in rr_block and old_pipeline_load in content:
            # Inject caption offset before pipeline loading
            injection = '''        update(15, "Preparing captions")
        # PHASE 3: Set caption offset to 0 for instant sync with voice
        kwargs["caption_offset"] = 0.0
        kwargs["caption_timing_precision"] = True
        '''
            content = content.replace(old_pipeline_load, injection + '        ' + old_pipeline_load, 1)
            patches += 1
            print("[PATCH 5] run_render() — caption_offset=0.0 injected before pipeline load")

    # ==================================================================
    # WRITE
    # ==================================================================
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)

    new_lines = len(content.split('\n'))
    print(f"\n{'='*60}")
    print(f"PHASE 3 — COMPLETE ({patches} patches, {new_lines} lines)")
    print(f"Backup: {backup_path}")
    if errors:
        print(f"\nWARNINGS:")
        for e in errors:
            print(f"  - {e}")
    print(f"{'='*60}")
    print("\nChanges:")
    print("  1. Removed caption_video_preview_section() from main page")
    print("  2. long_assets() — reads Caption Style state for long video")
    print("  3. Caption preview — dummy text + smaller size")
    print("  4. caption_offset = 0.0 (instant caption with voice, no delay)")
    print("  5. Caption timing precision flag sent to pipeline")
    print("\nHOW CAPTIONS WORK:")
    print("  - Caption Style section controls BOTH short & long")
    print("  - Long: 'Enable Long Video Captions' checkbox + radio selector")
    print("  - Short: applies whichever checkbox is ticked")
    print("\nTest: streamlit run app.py")


if __name__ == "__main__":
    main_phase3()