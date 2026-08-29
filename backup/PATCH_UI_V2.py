import shutil, time
from pathlib import Path

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 70)
print("  PATCH UI V2 — Merge + Remove")
print("=" * 70)

app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_uiv2_{ts}")
code = app.read_text(encoding="utf-8")

# ================================================================
# FIX 1: main() → completely rewrite the middle section
# Merge: Custom Settings + Settings + Voice + Render → ONE "Editing and Voice Setting"
# Remove: Auto-Detect section call
# Remove: Caption Preview section call
# ================================================================

# TARGET: Find the block from "CUSTOM SETTINGS" to "ASSETS"
# And replace everything between with ONE combined section

# Old block to find and replace
old_marker = "# 3. CUSTOM SETTINGS (collapsed by default)"
new_marker_after = "# 5. ASSETS (video uploads)"

if old_marker in code and new_marker_after in code:
    block_start = code.find(old_marker)
    block_end = code.find(new_marker_after, block_start)
    
    # NEW combined section
    new_section = '''        # 3. COMBINED SETTINGS SECTION
        custom_overrides = {}
        import json
        st.session_state["phase4_config"] = json.dumps({
            "preset_number": preset_num,
            "preset_label": preset_label,
            "custom_overrides": custom_overrides,
        })

        st.markdown("---")
        st.markdown('<div class="section-title">Editing and Voice Setting</div>', unsafe_allow_html=True)

        with st.expander("All Settings", expanded=True):
            # Row 1: Niche & Quality
            c1, c2, c3, c4 = st.columns(4)
            niche = c1.selectbox("Niche", NICHES, key="niche_main")
            quality = c2.selectbox("Quality", ["balanced", "high", "max"], index=0)
            fps = c3.select_slider("FPS", options=[24, 25, 30], value=24)
            final_4k = c4.toggle("4K Export", value=False)

            # Row 2: Voice Editing
            st.markdown("---")
            st.markdown("**🎤 Voice Editing**")
            c1, c2, c3, c4 = st.columns(4)
            clean_silence = c1.toggle("Clean Silence", value=False)
            voice_level = c2.slider("Voice Level", 0.5, 2.0, 1.0, 0.05)
            music_level = c3.slider("Music Level", 0.0, 0.3, 0.04, 0.01)
            sfx_level = c4.slider("SFX Level", 0.0, 0.3, 0.06, 0.01)

            # Row 3: Render
            st.markdown("---")
            st.markdown("**🎬 Render**")
            c1, c2, c3, c4 = st.columns(4)
            use_hook = c1.toggle("Hook", value=True)
            motion = c2.toggle("Motion", value=True)
            overlays = c3.toggle("Overlays", value=True)
            render_count = c4.number_input("Variation", 0, 9999, 0)

            # Row 4: Advanced Motion & Transitions
            st.markdown("---")
            st.markdown("**🎥 Advanced Motion & Transitions**")
            c1, c2, c3 = st.columns(3)
            motion_override = c1.checkbox("Override Motion", value=False)
            motion_intensity = c1.slider("Motion Intensity", 0.5, 2.0, 1.0, 0.05, disabled=not motion_override)
            trans_override = c2.checkbox("Override Transitions", value=False)
            trans_speed = c2.slider("Transition Speed", 0.1, 0.6, 0.25, 0.02, disabled=not trans_override)
            color_override = c3.checkbox("Override Color", value=False)
            color_warmth = c3.slider("Color Warmth", -0.1, 0.1, 0.0, 0.005, disabled=not color_override)

            # Row 5: Advanced Audio & Voice
            st.markdown("---")
            st.markdown("**🔊 Advanced Audio & Voice**")
            c1, c2 = st.columns(2)
            audio_override = c1.checkbox("Override Audio", value=False)
            music_vol = c1.slider("Music Volume Override", 0.0, 0.3, 0.04, 0.005, disabled=not audio_override)
            voice_override = c2.checkbox("Override Voice Style", value=False)
            voice_profiles_list = ["auto", "calm_deliberate", "warm_measured", "energetic_bright", "dramatic_tense", "clean_aesthetic", "sharp_decisive", "documentary_authority", "soft_emotional"]
            voice_profile = c2.selectbox("Voice Profile", voice_profiles_list, index=0, disabled=not voice_override)

            # Build custom_overrides dict
            if motion_override:
                custom_overrides["motion_intensity"] = motion_intensity
            if trans_override:
                custom_overrides["transition_duration"] = trans_speed
            if color_override:
                custom_overrides["color_warmth"] = color_warmth
            if audio_override:
                custom_overrides["music_volume"] = music_vol
            if voice_override and voice_profile != "auto":
                custom_overrides["voice_profile"] = voice_profile

            st.session_state["phase4_config"] = json.dumps({
                "preset_number": preset_num,
                "preset_label": preset_label,
                "custom_overrides": custom_overrides,
            })

        settings = {
            "niche": niche, "quality": quality, "fps": fps, "final_4k": final_4k,
            "clean_silence": clean_silence, "voice_level": voice_level,
            "music_level": music_level, "sfx_level": sfx_level,
            "use_hook": use_hook, "motion": motion, "overlays": overlays,
            "render_count": int(render_count),
        }

        # 4. CAPTIONS
        st.markdown("---")
        add_captions, caption_mode, style_id = captions_section()

'''

    code = code[:block_start] + new_section + code[block_end:]
    print("  [1] All sections merged into ONE ✅")

# ================================================================
# FIX 2: Remove Auto-Detect section from main()
# ================================================================
# Find the auto_detect block in main()
auto_markers = [
    '# 2. AUTO-DETECT\n        st.markdown("---")\n        auto_detect_section()',
    '# 2. AUTO-DETECT',
]

for marker in auto_markers:
    if marker in code:
        # Find the full block
        idx = code.find(marker)
        # Find end of this block (next comment or section)
        after = code.find('\n        #', idx + len(marker))
        if after == -1:
            after = code.find('\n        st.session_state', idx + len(marker))
        if after != -1:
            code = code[:idx] + code[after:]
            print("  [2] Auto-Detect section REMOVED ✅")
            break
else:
    # Try to remove auto_detect_section() call
    if 'auto_detect_section()' in code:
        idx = code.find('auto_detect_section()')
        line_start = code.rfind('\n', 0, idx)
        # Go back to the previous line that starts with #
        prev = code.rfind('# 2. AUTO-DETECT', 0, line_start)
        if prev == -1:
            prev = code.rfind('---', 0, line_start)
            prev = code.rfind('\n', 0, prev)
        code = code[:prev] + code[line_start+1:]
        print("  [2] Auto-Detect section REMOVED (fallback) ✅")

# ================================================================
# FIX 3: Remove Caption Preview from main()
# ================================================================
if 'caption_video_preview_section()' in code:
    idx = code.find('caption_video_preview_section()')
    line_start = code.rfind('\n', 0, idx)
    # Find the "# N. CAPTION PREVIEW" comment above
    comment = code.rfind('#', 0, line_start)
    sep = code.rfind('---', 0, comment)
    if sep != -1:
        sep_start = code.rfind('\n', 0, sep)
        code = code[:sep_start] + code[line_start+1:]
    else:
        code = code[:comment] + code[line_start+1:]
    print("  [3] Caption Preview section REMOVED ✅")

# ================================================================
# SAVE
# ================================================================
app.write_text(code, encoding="utf-8")

print(f"\n{'='*70}")
try:
    compile(code, "app.py", "exec")
    print("  ✅ SYNTAX OK")
except SyntaxError as e:
    print(f"  ❌ SYNTAX: {e}")
print(f"  Backup: app.py.bak_uiv2_{ts}")
print("=" * 70)
print("\n  Run: streamlit run app.py")