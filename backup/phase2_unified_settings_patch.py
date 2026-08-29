"""
============================================================================
PHASE 2 PATCH — Unified Settings (Auto-Detect + Settings = ONE Section)
============================================================================
AUTO-PATCH: Reads app.py, surgically replaces:
  1. preset_selector_section() — Adds auto-detect button inside niche dropdown
  2. settings_section() — Merges custom settings + all settings into ONE unified section
  3. _page_generator() — Removes standalone auto_detect_section() call
  4. Removes duplicate sections, keeps single clean layout

USAGE:
  cd "D:\My Creation Video Generator\backup"
  python phase2_unified_settings_patch.py
============================================================================
"""
import os
import re

BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))


def main_phase2():
    app_path = os.path.join(BACKUP_DIR, 'app.py')

    with open(app_path, 'r', encoding='utf-8') as f:
        original = f.read()

    # Backup
    backup_path = app_path + '.backup_phase2'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original)
    print(f"[OK] Backup: {backup_path}")
    print(f"[INFO] {len(original.split(chr(10)))} lines")

    content = original
    patches = 0
    errors = []

    # ==================================================================
    # PATCH 1: Replace preset_selector_section() — add auto-detect inside
    # ==================================================================
    old_preset_start = 'def preset_selector_section() -> tuple:'
    if old_preset_start not in content:
        errors.append("preset_selector_section() not found")
    else:
        # Find where this function ends — next top-level 'def '
        idx_ps = content.index(old_preset_start)
        after_ps = content[idx_ps + len(old_preset_start):]
        # Find next top-level def
        next_def = re.search(r'\n(def |# ={10,})', after_ps)
        if next_def:
            ps_end = idx_ps + len(old_preset_start) + next_def.start()
        else:
            errors.append("Cannot find end of preset_selector_section()")
            ps_end = None

        if ps_end:
            new_preset_func = '''def preset_selector_section() -> tuple:
    """
    Shows niche dropdown (with auto-detect button) + 8 preset buttons.
    Returns: (selected_preset_number, selected_preset_label)
    """
    st.markdown('<div class="section-title">🎬 Editing Style Preset</div>', unsafe_allow_html=True)

    # -- ROW 1: Niche selector + Auto-detect button --
    c_niche, c_auto, c_conf = st.columns([1.5, 0.8, 0.8])

    with c_niche:
        # Initialize niche in session
        if "selected_niche" not in st.session_state:
            st.session_state["selected_niche"] = "default"
        current_niche = st.selectbox(
            "🎯 Niche",
            NICHES,
            index=NICHES.index(st.session_state["selected_niche"])
            if st.session_state["selected_niche"] in NICHES else 6,
            key="niche_selector_main",
        )
        st.session_state["selected_niche"] = current_niche

    with c_auto:
        st.markdown('<div style="height:5px;"></div>', unsafe_allow_html=True)
        show_auto = st.checkbox("🤖 Auto-Detect", value=False, key="auto_detect_toggle",
                                 help="Paste script and auto-detect best niche & preset")

    with c_conf:
        conf_val = st.session_state.get("auto_detect_confidence")
        if conf_val is not None and show_auto:
            st.metric("Confidence", f"{conf_val:.0%}")

    # -- Expandable Auto-Detect area --
    if show_auto:
        with st.container():
            script_input = st.text_area(
                "Paste your script text:",
                height=100,
                placeholder="In the world of luxury, exclusivity is everything...",
                key="auto_detect_script_input",
            )
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                if st.button("🔍 Auto-Detect Now", use_container_width=True, type="primary",
                             key="auto_detect_btn_inline"):
                    if script_input.strip():
                        with st.spinner("Analyzing..."):
                            niche, preset, confidence, reasoning = auto_detect_niche_and_preset(
                                script_text=script_input
                            )
                            st.session_state["selected_niche"] = niche
                            st.session_state["editing_preset_number"] = preset
                            st.session_state["auto_detect_confidence"] = confidence
                            st.session_state["auto_detect_reasoning"] = reasoning
                            st.success(
                                f"✅ **{niche.upper()}** → Preset #{preset} "
                                f"({confidence:.0%} confidence)"
                            )
                            st.info(reasoning)
                            st.rerun()
                    else:
                        st.warning("Please paste some script text first.")
            with col_a2:
                if st.button("📋 Clear", use_container_width=True, key="auto_detect_clear_inline"):
                    st.session_state.pop("auto_detect_script_input", None)
                    st.session_state.pop("auto_detect_confidence", None)
                    st.session_state.pop("auto_detect_reasoning", None)
                    st.rerun()

    # -- PRESET BUTTONS --
    # Get labels for current niche
    try:
        if PRESET_ENGINE_AVAILABLE:
            labels = get_preset_labels(current_niche)
        else:
            labels = PRESET_LABELS_FALLBACK.get(current_niche, PRESET_LABELS_FALLBACK["default"])
    except Exception:
        labels = PRESET_LABELS_FALLBACK.get(current_niche, PRESET_LABELS_FALLBACK["default"])

    if "editing_preset_number" not in st.session_state:
        st.session_state["editing_preset_number"] = 1

    preset_num = st.session_state["editing_preset_number"]

    # Row 1: buttons 1-4
    cols_r1 = st.columns(4)
    for i in range(4):
        with cols_r1[i]:
            label_short = labels[i][:22] if i < len(labels) else f"Style {i+1}"
            is_sel = (preset_num == i + 1)
            if st.button(
                f"{'●' if is_sel else '○'} {i+1}. {label_short}",
                key=f"preset_btn_{i+1}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
            ):
                st.session_state["editing_preset_number"] = i + 1
                st.rerun()

    # Row 2: buttons 5-8
    cols_r2 = st.columns(4)
    for i in range(4, 8):
        with cols_r2[i - 4]:
            label_short = labels[i][:22] if i < len(labels) else f"Style {i+1}"
            is_sel = (preset_num == i + 1)
            if st.button(
                f"{'●' if is_sel else '○'} {i+1}. {label_short}",
                key=f"preset_btn_{i+1}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
            ):
                st.session_state["editing_preset_number"] = i + 1
                st.rerun()

    selected_label = labels[preset_num - 1] if preset_num <= len(labels) else f"Style {preset_num}"
    st.markdown(f"**Selected:** Preset #{preset_num} — *{selected_label}*")

    # Preset description if available
    if PRESET_ENGINE_AVAILABLE:
        try:
            p = get_preset_by_number(current_niche, preset_num)
            if p and hasattr(p, 'description'):
                with st.expander("📝 About this preset", expanded=False):
                    st.markdown(p.description)
        except Exception:
            pass

    return preset_num, selected_label
'''

            content = content[:idx_ps] + new_preset_func + '\n' + content[ps_end:]
            patches += 1
            print("[PATCH 1] preset_selector_section() — auto-detect merged into niche selector")

    # ==================================================================
    # PATCH 2: Replace settings_section() — merge all settings + custom
    # ==================================================================
    old_settings_start = 'def settings_section() -> Dict[str, Any]:'
    if old_settings_start not in content:
        errors.append("settings_section() not found")
    else:
        idx_ss = content.index(old_settings_start)
        after_ss = content[idx_ss + len(old_settings_start):]
        next_def = re.search(r'\n(def |# ={10,})', after_ss)
        if next_def:
            ss_end = idx_ss + len(old_settings_start) + next_def.start()
        else:
            errors.append("Cannot find end of settings_section()")
            ss_end = None

        if ss_end:
            new_settings_func = '''def settings_section() -> Dict[str, Any]:
    """UNIFIED SETTINGS: Video + Voice + Render + Custom all in ONE expander."""
    st.markdown('<div class="section-title">⚙️ Settings</div>', unsafe_allow_html=True)

    # Main Settings expander
    with st.expander("⚙️ All Settings", expanded=False):

        # -- VIDEO EDITING --
        st.markdown("**🎥 Video**")
        c1, c2, c3, c4 = st.columns(4)
        niche = c1.selectbox("Niche", NICHES)
        quality = c2.selectbox("Quality", ["balanced", "high", "max"], index=0)
        fps = c3.select_slider("FPS", options=[24, 25, 30], value=24)
        final_4k = c4.toggle("4K Export", value=False, help="OFF for 8GB RAM")
        use_hook = c1.toggle("Hook", value=True)
        motion = c2.toggle("Motion", value=True)
        overlays = c3.toggle("Overlays", value=True)

        st.markdown("---")

        # -- VOICE EDITING --
        st.markdown("**🎙 Voice & Audio**")
        v1, v2, v3, v4 = st.columns(4)
        clean_silence = v1.toggle("Clean Silence", value=False)
        voice_level = v2.slider("Voice", 0.5, 2.0, 1.0, 0.05)
        music_level = v3.slider("Music", 0.0, 0.3, 0.04, 0.01)
        sfx_level = v4.slider("SFX", 0.0, 0.3, 0.06, 0.01)

        st.markdown("---")

        # -- RENDER --
        st.markdown("**🔄 Render**")
        render_count = st.number_input("Variations", 0, 9999, 0)

        st.info("480p Mode — All editing ON. Each step renders separately. 4K OFF.")

        st.markdown("---")

        # -- ADVANCED CUSTOM OVERRIDES --
        st.markdown("**🎛️ Advanced Overrides**")
        st.caption("Fine-tune motion, transitions, colors. Leave at default for preset control.")

        a1, a2, a3 = st.columns(3)
        with a1:
            mo_override = st.checkbox("Override Motion", value=False, key="override_motion2")
            motion_intensity = st.slider("Motion Intensity", 0.5, 2.0, 1.0, 0.05,
                                          key="motion_intensity_slider2",
                                          disabled=not mo_override)
        with a2:
            to_override = st.checkbox("Override Transitions", value=False, key="override_trans2")
            trans_speed = st.slider("Transition Speed", 0.1, 0.6, 0.25, 0.02,
                                     key="trans_speed_slider2",
                                     disabled=not to_override)
        with a3:
            co_override = st.checkbox("Override Color", value=False, key="override_color2")
            color_warmth = st.slider("Color Warmth", -0.1, 0.1, 0.0, 0.005,
                                      key="color_warmth_slider2",
                                      disabled=not co_override)

        b1, b2 = st.columns(2)
        with b1:
            ao_override = st.checkbox("Override Audio", value=False, key="override_audio2")
            music_vol = st.slider("Music Volume", 0.0, 0.3,
                                   st.session_state.get("music_level", 0.04), 0.005,
                                   key="music_vol_slider3", disabled=not ao_override)
        with b2:
            vo_override = st.checkbox("Override Voice", value=False, key="override_voice2")
            voice_profiles = ["auto", "calm_deliberate", "warm_measured", "energetic_bright",
                             "dramatic_tense", "clean_aesthetic", "sharp_decisive",
                             "documentary_authority", "soft_emotional"]
            voice_profile = st.selectbox("Voice Profile", voice_profiles, index=0,
                                         key="voice_profile_select2",
                                         disabled=not vo_override)

    # Build custom overrides dict
    overrides = {}
    if mo_override:
        overrides["motion_intensity"] = motion_intensity
    if to_override:
        overrides["transition_duration"] = trans_speed
    if co_override:
        overrides["color_warmth"] = color_warmth
    if ao_override:
        overrides["music_volume"] = music_vol
    if vo_override and voice_profile != "auto":
        overrides["voice_profile"] = voice_profile

    return {
        "niche": niche,
        "quality": quality,
        "fps": fps,
        "final_4k": final_4k,
        "clean_silence": clean_silence,
        "voice_level": voice_level,
        "music_level": music_level,
        "sfx_level": sfx_level,
        "use_hook": use_hook,
        "motion": motion,
        "overlays": overlays,
        "render_count": int(render_count),
        "custom_overrides": overrides,
    }
'''

            content = content[:idx_ss] + new_settings_func + '\n' + content[ss_end:]
            patches += 1
            print("[PATCH 2] settings_section() — ALL settings + custom overrides merged into ONE expander")

    # ==================================================================
    # PATCH 3: Replace _page_generator() — remove old auto_detect call
    # ==================================================================
    old_page_gen = '''def _page_generator():
    st.markdown('<div class="app-title">' + APP_TITLE + '</div>', unsafe_allow_html=True)
    preset_num, preset_label = preset_selector_section()
    auto_detect_section()
    st.session_state["editing_preset_number"] = preset_num
    st.session_state["editing_preset_label"] = preset_label
    custom_overrides = custom_editing_settings_section({})
    import json
    st.session_state["phase4_config"] = json.dumps({
        "preset_number": preset_num, "preset_label": preset_label,
        "custom_overrides": custom_overrides,
    })
    add_captions, caption_mode, style_id = captions_section()
    settings = settings_section()
    assets_section(settings, add_captions, caption_mode, style_id)
    st.markdown("---")
    scoring_panel_section()
    st.markdown("---")
    caption_video_preview_section()
    output_preview()'''

    new_page_gen = '''def _page_generator():
    st.markdown('<div class="app-title">' + APP_TITLE + '</div>', unsafe_allow_html=True)

    # 1. Preset Selector (niche + auto-detect + preset buttons — all in ONE)
    preset_num, preset_label = preset_selector_section()

    st.session_state["editing_preset_number"] = preset_num
    st.session_state["editing_preset_label"] = preset_label

    # 2. Settings (ALL settings + custom overrides — ONE expander)
    import json
    settings = settings_section()
    st.session_state["phase4_config"] = json.dumps({
        "preset_number": preset_num,
        "preset_label": preset_label,
        "custom_overrides": settings.get("custom_overrides", {}),
    })

    # 3. Captions
    add_captions, caption_mode, style_id = captions_section()

    # 4. Assets (uploads)
    assets_section(settings, add_captions, caption_mode, style_id)

    # 5. Scores
    st.markdown("---")
    scoring_panel_section()

    # 6. Caption Preview
    st.markdown("---")
    caption_video_preview_section()

    # 7. Output
    output_preview()'''

    if old_page_gen in content:
        content = content.replace(old_page_gen, new_page_gen)
        patches += 1
        print("[PATCH 3] _page_generator() — removed standalone auto_detect, unified settings flow")
    else:
        # Try fuzzy match
        gen_start = content.find('def _page_generator():')
        if gen_start >= 0:
            after_gen = content[gen_start:]
            gen_end = after_gen.find('\ndef _page_reels')
            if gen_end > 0:
                new_with_markers = '\n' + new_page_gen + '\n'
                content = content[:gen_start] + new_with_markers + content[gen_start + gen_end:]
                patches += 1
                print("[PATCH 3] _page_generator() — replaced via fuzzy match")
            else:
                errors.append("_page_generator end marker not found")
        else:
            errors.append("_page_generator() not found")

    # ==================================================================
    # PATCH 4: Remove old auto_detect_section() call from render_reels_page
    #          (if it exists there — just ensure it doesn't crash)
    # ==================================================================
    # No change needed in reels page for now

    # ==================================================================
    # WRITE
    # ==================================================================
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)

    new_lines = len(content.split('\n'))
    print(f"\n{'='*60}")
    print(f"PHASE 2 — COMPLETE ({patches} patches, {new_lines} lines)")
    print(f"Backup: {backup_path}")
    if errors:
        print(f"\nWARNINGS:")
        for e in errors:
            print(f"  - {e}")
    print(f"{'='*60}")
    print("\nChanges:")
    print("  1. preset_selector_section() — Niche dropdown + Auto-Detect toggle + confidence")
    print("  2. settings_section() — ALL (Video+Voice+Render+Custom) in ONE expander")
    print("  3. _page_generator() — Clean flow, no duplicate sections")
    print("\nTest: streamlit run app.py")


if __name__ == "__main__":
    main_phase2()