"""
====================================================================
SURGICAL PATCH: app.py — Phase 4 UI Overhaul (Part 2: UI Sections)
====================================================================
PURPOSE: Add NEW UI sections to app.py WITHOUT removing anything.
         Preset selector, 10/10 scoring, caption video preview,
         auto-detect button, custom settings expanders.

USAGE:   python surgical_patch_app_phase4_part2.py
         (RUN AFTER Part 1 is complete)

WHAT IT ADDS (new functions injected):
  - preset_selector_section()  → Niche × 8 preset selector UI
  - scoring_panel_section()    → 10/10 video/voice/combined scores
  - auto_detect_section()      → Script input → auto niche+preset
  - caption_video_preview_section() → 6-sec MP4 caption previews
  - custom_settings_section()  → Advanced sliders for tuning
  - These are called from main() via new injection point
====================================================================
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
APP_PATH = BASE_DIR / "app.py"
BACKUP_PATH = BASE_DIR / "app.py.backup_phase4_part2"


def safe_print(msg):
    print(f"[SurgicalPatch:app_p4p2] {msg}", flush=True)


def patch_app_ui_sections():
    if not APP_PATH.exists():
        raise FileNotFoundError(f"app.py not found at {APP_PATH}")

    safe_print("Reading app.py (after Part 1)...")
    original = APP_PATH.read_text(encoding="utf-8")
    BACKUP_PATH.write_text(original, encoding="utf-8")
    safe_print(f"Backup saved: {BACKUP_PATH}")

    modified = original

    # ================================================================
    # INJECTION 4: Add UI helper functions BEFORE output_preview()
    # Anchor: "def output_preview() -> None:"
    # ================================================================
    anchor_4 = "def output_preview() -> None:"
    injection_4 = '''# ================================================================
# PHASE 4: PRESET SELECTOR UI (Surgical Addition)
# ================================================================
def preset_selector_section() -> tuple:
    """
    Shows niche → 8 preset buttons. Each niche has DIFFERENT presets.
    Returns: (selected_preset_number, selected_preset_label)
    """
    st.markdown('<div class="section-title">🎬 Editing Style Preset</div>', unsafe_allow_html=True)

    current_niche = st.session_state.get("selected_niche", "default")

    # Get preset labels for current niche
    try:
        if PRESET_ENGINE_AVAILABLE:
            labels = get_preset_labels(current_niche)
        else:
            labels = PRESET_LABELS_FALLBACK.get(current_niche, PRESET_LABELS_FALLBACK["default"])
    except Exception:
        labels = PRESET_LABELS_FALLBACK.get(current_niche, PRESET_LABELS_FALLBACK["default"])

    # Initialize preset selection in session state
    if "editing_preset_number" not in st.session_state:
        st.session_state["editing_preset_number"] = 1

    # Show 8 preset buttons in 2 rows of 4
    cols = st.columns(4)
    preset_num = st.session_state["editing_preset_number"]

    for i in range(8):
        col_idx = i % 4
        row_idx = i // 4
        if row_idx == 0:
            with cols[col_idx]:
                label_short = labels[i][:22] if i < len(labels) else f"Style {i+1}"
                is_selected = (preset_num == i + 1)
                btn_style = "primary" if is_selected else "secondary"
                if st.button(
                    f"{'●' if is_selected else '○'} {i+1}. {label_short}",
                    key=f"preset_btn_{i+1}",
                    use_container_width=True,
                    type=btn_style if is_selected else "secondary",
                ):
                    st.session_state["editing_preset_number"] = i + 1
                    st.rerun()

    # Second row
    cols2 = st.columns(4)
    for i in range(4, 8):
        with cols2[i - 4]:
            label_short = labels[i][:22] if i < len(labels) else f"Style {i+1}"
            is_selected = (preset_num == i + 1)
            if st.button(
                f"{'●' if is_selected else '○'} {i+1}. {label_short}",
                key=f"preset_btn_{i+1}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            ):
                st.session_state["editing_preset_number"] = i + 1
                st.rerun()

    # Show current selection details
    selected_label = labels[preset_num - 1] if preset_num <= len(labels) else f"Style {preset_num}"
    st.markdown(f"**Selected:** Preset #{preset_num} — *{selected_label}*")

    # Show preset description if available
    if PRESET_ENGINE_AVAILABLE:
        try:
            preset = get_preset_by_number(current_niche, preset_num)
            if preset and hasattr(preset, 'description'):
                with st.expander("📝 About this preset", expanded=False):
                    st.markdown(preset.description)
        except Exception:
            pass

    return preset_num, selected_label


# ================================================================
# PHASE 4: AUTO-DETECT SECTION (Surgical Addition)
# ================================================================
def auto_detect_section() -> bool:
    """
    Text area for script input → auto-detects niche + best preset.
    Returns True if auto-detect was triggered.
    """
    st.markdown('<div class="section-title">🤖 Auto-Detect Mode</div>', unsafe_allow_html=True)

    with st.expander("Auto-Detect Niche & Style from Script", expanded=False):
        script_input = st.text_area(
            "Paste your video script/text here:",
            height=120,
            placeholder="Example: In the world of luxury, exclusivity is everything. From private jets to million-dollar mansions...",
            key="auto_detect_script_input",
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("🔍 Auto-Detect", use_container_width=True, type="primary", key="auto_detect_btn"):
                if script_input.strip():
                    with st.spinner("Analyzing script..."):
                        niche, preset, confidence, reasoning = auto_detect_niche_and_preset(
                            script_text=script_input
                        )
                        # Update session state
                        st.session_state["selected_niche"] = niche
                        st.session_state["editing_preset_number"] = preset
                        st.session_state["auto_detect_confidence"] = confidence
                        st.session_state["auto_detect_reasoning"] = reasoning
                        st.success(f"✅ Detected: **{niche.upper()}** → Preset #{preset} ({confidence:.0%} confidence)")
                        st.info(reasoning)
                        st.rerun()
                else:
                    st.warning("Please paste some script text first.")
        with col2:
            if st.button("📋 Clear", use_container_width=True, key="auto_detect_clear"):
                st.session_state.pop("auto_detect_script_input", None)
                st.session_state.pop("auto_detect_confidence", None)
                st.session_state.pop("auto_detect_reasoning", None)
                st.rerun()

        # Show last detection result if available
        conf = st.session_state.get("auto_detect_confidence")
        if conf is not None:
            st.metric("Detection Confidence", f"{conf:.0%}")

    return True


# ================================================================
# PHASE 4: 10/10 SCORING PANEL (Surgical Addition)
# ================================================================
def scoring_panel_section():
    """Displays 10/10 video, voice, and combined scores."""
    video_score = SCORING_STATE.get("video_score", 0.0)
    voice_score = SCORING_STATE.get("voice_score", 0.0)
    combined = SCORING_STATE.get("combined_score", 0.0)
    last_mode = SCORING_STATE.get("last_render_mode", "—")

    if combined <= 0:
        st.markdown(
            '<div class="section-title">📊 Quality Scores</div>'
            '<div style="opacity:0.5;font-size:13px;margin:8px 0;">'
            'Generate a video to see scores here.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="section-title">📊 Quality Scores</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    def score_color(val):
        if val >= 8.5: return "#087f5b"  # green
        if val >= 7.0: return "#e67700"  # orange
        return "#c92a2a"  # red

    def score_label(val):
        if val >= 9.0: return "🏆 PERFECT"
        if val >= 8.5: return "⭐ EXCELLENT"
        if val >= 7.5: return "👍 GREAT"
        if val >= 6.5: return "👌 GOOD"
        if val >= 5.0: return "📋 FAIR"
        return "⚠️ NEEDS WORK"

    with col1:
        st.markdown(
            f'<div style="text-align:center;padding:12px;border-radius:12px;'
            f'background:rgba(8,127,91,0.08);border:1px solid {score_color(video_score)}">'
            f'<div style="font-size:12px;opacity:0.7;">VIDEO SCORE</div>'
            f'<div style="font-size:36px;font-weight:900;color:{score_color(video_score)};">'
            f'{video_score:.1f}<span style="font-size:16px;">/10</span></div>'
            f'<div style="font-size:11px;color:{score_color(video_score)};">{score_label(video_score)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f'<div style="text-align:center;padding:12px;border-radius:12px;'
            f'background:rgba(8,127,91,0.08);border:1px solid {score_color(voice_score)}">'
            f'<div style="font-size:12px;opacity:0.7;">VOICE SCORE</div>'
            f'<div style="font-size:36px;font-weight:900;color:{score_color(voice_score)};">'
            f'{voice_score:.1f}<span style="font-size:16px;">/10</span></div>'
            f'<div style="font-size:11px;color:{score_color(voice_score)};">{score_label(voice_score)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f'<div style="text-align:center;padding:12px;border-radius:12px;'
            f'background:rgba(8,127,91,0.08);border:1px solid {score_color(combined)}">'
            f'<div style="font-size:12px;opacity:0.7;">COMBINED</div>'
            f'<div style="font-size:36px;font-weight:900;color:{score_color(combined)};">'
            f'{combined:.1f}<span style="font-size:16px;">/10</span></div>'
            f'<div style="font-size:11px;color:{score_color(combined)};">{score_label(combined)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Show tips/warnings
    tips = SCORING_STATE.get("tips", [])
    warnings = SCORING_STATE.get("warnings", [])
    if tips or warnings:
        with st.expander("📋 Details & Tips", expanded=False):
            if tips:
                st.markdown("**💡 Improvement Tips:**")
                for tip in tips[:5]:
                    st.markdown(f"- {tip}")
            if warnings:
                st.markdown("**⚠️ Warnings:**")
                for w in warnings[:5]:
                    st.markdown(f"- {w}")

    st.caption(f"Last render: {last_mode}")


# ================================================================
# PHASE 4: CAPTION VIDEO PREVIEW (Surgical Addition)
# ================================================================
def caption_video_preview_section():
    """
    Shows 6-second VIDEO preview of captions (NOT static image).
    Uses caption_preview_generator.py to generate MP4 previews.
    """
    st.markdown('<div class="section-title">🎬 Caption Preview</div>', unsafe_allow_html=True)

    # Get preview paths from caption_preview_generator
    preview_dir = PREVIEW_DIR  # from existing code

    with st.expander("Caption Style Previews (6-sec video)", expanded=False):
        tabs = st.tabs(["Word-by-Word", "3-4 Word Phrases"])

        with tabs[0]:
            st.caption("Single-word caption previews")
            word_cols = st.columns(2)
            word_styles = [
                ("wbw_pure_white_premium", "Pure White Premium"),
                ("wbw_royal_sapphire", "Royal Sapphire"),
                ("wbw_emerald_lux", "Emerald Lux"),
                ("wbw_crystal_cyan", "Crystal Cyan"),
                ("wbw_luxury_gold", "Luxury Gold"),
                ("wbw_ruby_impact", "Ruby Impact"),
            ]
            for i, (sid, label) in enumerate(word_styles):
                with word_cols[i % 2]:
                    st.caption(label)
                    p = preview_path(sid)
                    if p.exists() and p.stat().st_size > 2500:
                        st.video(str(p))
                    else:
                        st.warning(f"Preview missing for {label}")

        with tabs[1]:
            st.caption("3-4 word phrase previews")
            phrase_cols = st.columns(2)
            phrase_styles = [
                ("phrase_premium_white", "Premium White Phrase"),
                ("phrase_royal_blue", "Royal Blue Phrase"),
                ("phrase_emerald_finance", "Emerald Finance"),
                ("phrase_crystal_cyan", "Crystal Cyan Phrase"),
                ("phrase_luxury_gold", "Luxury Gold Phrase"),
                ("phrase_ruby_impact", "Ruby Impact Phrase"),
            ]
            for i, (sid, label) in enumerate(phrase_styles):
                with phrase_cols[i % 2]:
                    st.caption(label)
                    p = preview_path(sid)
                    if p.exists() and p.stat().st_size > 2500:
                        st.video(str(p))
                    else:
                        st.warning(f"Preview missing for {label}")

        # Generate missing previews button
        if st.button("🔄 Generate Missing Caption Previews", use_container_width=True):
            try:
                from caption_preview_generator import generate_all
                with st.spinner("Generating caption previews..."):
                    results = generate_all(force=False)
                st.success(f"✅ Generated/verified {len(results)} previews")
            except Exception as e:
                st.error(f"Preview generation failed: {e}")


# ================================================================
# PHASE 4: CUSTOM SETTINGS EXPANDERS (Surgical Addition)
# ================================================================
def custom_editing_settings_section(settings: dict) -> dict:
    """
    Advanced custom settings that override preset defaults.
    User can fine-tune motion, transitions, colors, audio.
    Returns updated settings dict.
    """
    with st.expander("🎛️ Advanced Custom Settings", expanded=False):
        st.caption("Override preset defaults. Leave at default for preset-controlled values.")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("**🎥 Motion**")
            motion_override = st.checkbox("Override Motion", value=False, key="override_motion")
            motion_intensity = st.slider(
                "Motion Intensity", 0.5, 2.0,
                value=settings.get("motion_intensity_override", 1.0),
                step=0.05,
                key="motion_intensity_slider",
                disabled=not motion_override,
            )

        with c2:
            st.markdown("**🔄 Transitions**")
            trans_override = st.checkbox("Override Transitions", value=False, key="override_transitions")
            trans_speed = st.slider(
                "Transition Speed", 0.1, 0.6,
                value=settings.get("transition_speed_override", 0.25),
                step=0.02,
                key="trans_speed_slider",
                disabled=not trans_override,
            )

        with c3:
            st.markdown("**🎨 Color**")
            color_override = st.checkbox("Override Color Grade", value=False, key="override_color")
            color_warmth = st.slider(
                "Color Warmth", -0.1, 0.1,
                value=settings.get("color_warmth_override", 0.0),
                step=0.005,
                key="color_warmth_slider",
                disabled=not color_override,
            )

        c4, c5 = st.columns(2)
        with c4:
            st.markdown("**🔊 Audio**")
            audio_override = st.checkbox("Override Audio Levels", value=False, key="override_audio")
            music_vol = st.slider(
                "Music Volume", 0.0, 0.3,
                value=settings.get("music_vol_override", settings.get("music_level", 0.04)),
                step=0.005,
                key="music_vol_slider2",
                disabled=not audio_override,
            )

        with c5:
            st.markdown("**🎤 Voice**")
            voice_override = st.checkbox("Override Voice Style", value=False, key="override_voice")
            voice_profiles = ["auto", "calm_deliberate", "warm_measured", "energetic_bright", "dramatic_tense", "clean_aesthetic", "sharp_decisive", "documentary_authority", "soft_emotional"]
            voice_profile = st.selectbox(
                "Voice Profile",
                voice_profiles,
                index=0,
                key="voice_profile_select",
                disabled=not voice_override,
            )

    # Build overrides dict
    overrides = {}
    if motion_override:
        overrides["motion_intensity"] = motion_intensity
    if trans_override:
        overrides["transition_duration"] = trans_speed
    if color_override:
        overrides["color_warmth"] = color_warmth
    if audio_override:
        overrides["music_volume"] = music_vol
    if voice_override and voice_profile != "auto":
        overrides["voice_profile"] = voice_profile

    return overrides


# ================================================================
# PHASE 4: QUALITY TIER BADGE (Surgical Addition)
# ================================================================
def render_quality_badge(score: float):
    """Render quality tier badge based on score."""
    if score <= 0:
        return ""
    if score >= 9.0:
        badge = "🏆 PERFECT TIER"
        color = "#eab308"
    elif score >= 8.5:
        badge = "⭐ EXCELLENT TIER"
        color = "#22c55e"
    elif score >= 7.5:
        badge = "👍 GREAT TIER"
        color = "#3b82f6"
    elif score >= 6.5:
        badge = "👌 GOOD TIER"
        color = "#8b5cf6"
    elif score >= 5.0:
        badge = "📋 FAIR TIER"
        color = "#f97316"
    else:
        badge = "⚠️ NEEDS WORK"
        color = "#ef4444"

    return (
        f'<div style="text-align:center;padding:6px 16px;border-radius:20px;'
        f'background:{color}15;border:1px solid {color}40;margin:8px 0;display:inline-block;">'
        f'<span style="font-weight:850;color:{color};font-size:13px;">{badge}</span></div>'
    )
# ================================================================

def output_preview() -> None:'''

    if anchor_4 in modified:
        modified = modified.replace(anchor_4, injection_4)
        safe_print("✅ Injection 4: UI helper functions ADDED (preset selector, scoring, auto-detect, previews, custom settings)")
    else:
        safe_print("❌ Injection 4 FAILED — 'def output_preview()' not found")

    # ================================================================
    # INJECTION 5: Add new UI sections to main() function
    # Anchor: "add_captions, caption_mode, style_id = captions_section()"
    # We inject BEFORE this line to add preset selector + auto-detect
    # ================================================================
    anchor_5 = "    add_captions, caption_mode, style_id = captions_section()"
    injection_5 = '''    # ================================================================
    # PHASE 4: NEW UI SECTIONS (Surgical Addition — Before Captions)
    # ================================================================

    # Preset selector (niche × 8 styles)
    st.markdown("---")
    preset_num, preset_label = preset_selector_section()

    # Auto-detect section
    st.markdown("---")
    auto_detect_section()

    # Store preset info in session for pipelines
    st.session_state["editing_preset_number"] = preset_num
    st.session_state["editing_preset_label"] = preset_label

    # Custom settings
    custom_overrides = custom_editing_settings_section({})

    # Share preset info with render functions via session
    import json
    st.session_state["phase4_config"] = json.dumps({
        "preset_number": preset_num,
        "preset_label": preset_label,
        "custom_overrides": custom_overrides,
    })
    # ================================================================

    add_captions, caption_mode, style_id = captions_section()'''

    if anchor_5 in modified:
        modified = modified.replace(anchor_5, injection_5)
        safe_print("✅ Injection 5: UI sections CALLED from main() ADDED")
    else:
        safe_print("❌ Injection 5 FAILED — 'add_captions, caption_mode, style_id = captions_section()' not found")

    # ================================================================
    # INJECTION 6: Add scoring panel + caption preview BEFORE output_preview()
    # in main(), anchor: "output_preview()"
    # ================================================================
    anchor_6 = "    output_preview()"
    injection_6 = '''    # ================================================================
    # PHASE 4: SCORING PANEL + CAPTION PREVIEW (Surgical Addition)
    # ================================================================
    st.markdown("---")
    scoring_panel_section()

    st.markdown("---")
    caption_video_preview_section()
    # ================================================================

    output_preview()'''

    if anchor_6 in modified:
        modified = modified.replace(anchor_6, injection_6)
        safe_print("✅ Injection 6: Scoring panel + caption preview CALLS ADDED to main()")
    else:
        safe_print("❌ Injection 6 FAILED — 'output_preview()' in main not found")

    # ================================================================
    # INJECTION 7: Add scoring compute after successful render
    # in run_render(), anchor: "st.success(str(result))"
    # ================================================================
    anchor_7 = "        st.success(str(result))"
    injection_7 = '''        st.success(str(result))

        # ================================================================
        # PHASE 4: AUTO-COMPUTE SCORES AFTER RENDER (Surgical Addition)
        # ================================================================
        try:
            preset_num = st.session_state.get("editing_preset_number", 1)
            niche = settings.get("niche", "default")
            compute_render_scores(
                render_result_path=str(result),
                mode=mode,
                niche=niche,
                preset_number=preset_num
            )
        except Exception as score_err:
            print(f"[Phase4] Score compute skipped: {score_err}", flush=True)
        # ================================================================'''

    if anchor_7 in modified:
        modified = modified.replace(anchor_7, injection_7)
        safe_print("✅ Injection 7: Auto-score compute after render ADDED")
    else:
        safe_print("❌ Injection 7 FAILED — 'st.success(str(result))' not found")

    # ================================================================
    # INJECTION 8: Make preset number pass through to pipelines
    # in build_render_kwargs(), add preset_number to kwargs
    # anchor: '"niche": settings["niche"],'
    # ================================================================
    anchor_8 = '''        "niche": settings["niche"],
        "render_count": settings["render_count"],'''
    injection_8 = '''        "niche": settings["niche"],
        "preset_number": st.session_state.get("editing_preset_number", 1),
        "preset_label": st.session_state.get("editing_preset_label", "Style 1"),
        "custom_overrides": st.session_state.get("phase4_config", "{}"),
        "render_count": settings["render_count"],'''

    if anchor_8 in modified:
        modified = modified.replace(anchor_8, injection_8)
        safe_print("✅ Injection 8: Preset number flows to render kwargs ADDED")
    else:
        safe_print("❌ Injection 8 FAILED — render kwargs anchor not found")

    # ================================================================
    # WRITE MODIFIED FILE
    # ================================================================
    if modified != original:
        APP_PATH.write_text(modified, encoding="utf-8")
        safe_print(f"✅ app.py UPDATED (Part 2) — {len(modified)} chars")
        return True
    else:
        safe_print("⚠️ No changes made — app.py unchanged")
        return False


def verify_patch():
    content = APP_PATH.read_text(encoding="utf-8")
    checks = {
        "preset_selector_section": "def preset_selector_section" in content,
        "scoring_panel_section": "def scoring_panel_section" in content,
        "auto_detect_section": "def auto_detect_section" in content,
        "caption_video_preview_section": "def caption_video_preview_section" in content,
        "custom_editing_settings_section": "def custom_editing_settings_section" in content,
        "render_quality_badge": "def render_quality_badge" in content,
        "phase4_config": "phase4_config" in content,
        "preset_num_in_kwargs": "preset_number" in content and "preset_label" in content,
    }
    for name, status in checks.items():
        print(f"   {'✅' if status else '❌'} {name}: {'FOUND' if status else 'MISSING'}")
    return all(checks.values())


if __name__ == "__main__":
    print("=" * 60)
    print("SURGICAL PATCH: app.py Phase 4 Part 2 — UI Sections")
    print("=" * 60)

    if not APP_PATH.exists():
        print("❌ app.py not found! Run Part 1 first.")
    else:
        success = patch_app_ui_sections()
        if success:
            print("\n📋 Verification:")
            verify_patch()
            print("\n🎯 NEXT: Run surgical_patch_master_pipeline.py")
        else:
            print("\n❌ Patch did NOT apply.")