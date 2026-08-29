import shutil, time
from pathlib import Path

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_v4_{ts}")
text = app.read_text(encoding="utf-8")

# ============================================================
# FIND AND REPLACE: settings_section function
# ============================================================

old_func_marker = "def settings_section() -> Dict[str, Any]:"
# Find start and end of the function
func_idx = text.find(old_func_marker)
if func_idx == -1:
    print("ERROR: settings_section not found")
    exit(1)

# Find beginning of next function after settings_section
# Next function starts with "def upload_single"
next_func = text.find("\ndef upload_single", func_idx + 10)
if next_func == -1:
    next_func = text.find("\ndef ", func_idx + 500)

print(f"Found settings_section at {func_idx}, next at {next_func}")

# ============================================================
# NEW FUNCTION
# ============================================================
new_func = """def settings_section() -> Dict[str, Any]:
    st.markdown('<div class="section-title">Editing and Voice Setting</div>', unsafe_allow_html=True)

    with st.expander("All Settings", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        niche = c1.selectbox("Niche", NICHES)
        quality = c2.selectbox("Quality", ["balanced", "high", "max"], index=0)
        fps = c3.select_slider("FPS", options=[24, 25, 30], value=24)
        final_4k = c4.toggle("4K Export", value=False, help="OFF recommended for 8GB RAM laptops")

        st.info("480p Mode: saari editing steps ON (Motion, Zoom, Beat, Story, Hook, Captions). Har step alag render hoti hai.")

        st.markdown("---")

        c1, c2, c3, c4 = st.columns(4)
        clean_silence = c1.toggle("Clean Silence", value=False)
        voice_level = c2.slider("Voice Level", 0.5, 2.0, 1.0, 0.05)
        music_level = c3.slider("Music Level", 0.0, 0.3, 0.04, 0.01)
        sfx_level = c4.slider("SFX Level", 0.0, 0.3, 0.06, 0.01)

        c1, c2, c3, c4 = st.columns(4)
        use_hook = c1.toggle("Hook", value=True)
        motion = c2.toggle("Motion", value=True)
        overlays = c3.toggle("Overlays", value=True)
        render_count = c4.number_input("Variation", 0, 9999, 0)

        st.markdown("---")
        st.markdown("**Advanced Motion & Transitions**")
        c1, c2, c3 = st.columns(3)
        motion_override = c1.checkbox("Override Motion", value=False)
        motion_intensity = c1.slider("Motion Intensity", 0.5, 2.0, 1.0, 0.05, disabled=not motion_override)
        trans_override = c2.checkbox("Override Transitions", value=False)
        trans_speed = c2.slider("Transition Speed", 0.1, 0.6, 0.25, 0.02, disabled=not trans_override)
        color_override = c3.checkbox("Override Color", value=False)
        color_warmth = c3.slider("Color Warmth", -0.1, 0.1, 0.0, 0.005, disabled=not color_override)

        st.markdown("**Advanced Audio & Voice**")
        c1, c2 = st.columns(2)
        audio_override = c1.checkbox("Override Audio", value=False)
        music_vol = c1.slider("Music Volume Override", 0.0, 0.3, 0.04, 0.005, disabled=not audio_override)
        voice_override = c2.checkbox("Override Voice Style", value=False)
        voice_profiles_list = ["auto", "calm_deliberate", "warm_measured", "energetic_bright", "dramatic_tense", "clean_aesthetic", "sharp_decisive", "documentary_authority", "soft_emotional"]
        voice_profile = c2.selectbox("Voice Profile", voice_profiles_list, index=0, disabled=not voice_override)

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
        "motion_override": motion_override,
        "motion_intensity": motion_intensity,
        "trans_override": trans_override,
        "trans_speed": trans_speed,
        "color_override": color_override,
        "color_warmth": color_warmth,
        "audio_override": audio_override,
        "music_vol": music_vol,
        "voice_override": voice_override,
        "voice_profile": voice_profile,
    }

"""

# Replace
text = text[:func_idx] + new_func + text[next_func:]
print("settings_section replaced")

# ============================================================
# FIX main(): comment out removed sections
# ============================================================
text = text.replace(
    'custom_overrides = custom_editing_settings_section({})',
    'custom_overrides = {}'
)
text = text.replace(
    '\n        auto_detect_section()',
    '\n        # REMOVED: auto_detect_section()'
)
text = text.replace(
    '\n        caption_video_preview_section()',
    '\n        # REMOVED: caption_video_preview_section()'
)

# Clean orphan separators
text = text.replace(
    'st.markdown("---")\n        # REMOVED: auto_detect_section()',
    '# REMOVED: auto_detect_section()'
)
text = text.replace(
    'st.markdown("---")\n        # REMOVED: caption_video_preview_section()',
    '# REMOVED: caption_video_preview_section()'
)

print("main() cleaned")

# ============================================================
# SAVE
# ============================================================
app.write_text(text, encoding="utf-8")

try:
    compile(text, "app.py", "exec")
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")

print(f"Backup: app.py.bak_v4_{ts}")
print("Run: streamlit run app.py")