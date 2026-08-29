import shutil, time
from pathlib import Path

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_clean_{ts}")
text = app.read_text(encoding="utf-8")

# 1) Remove ALL non-printable characters except normal whitespace
import re
clean = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]', '', text)

# 2) Auto-Detect expander: expanded=False --> expanded=True
clean = clean.replace(
    'with st.expander("Auto-Detect Niche & Style from Script", expanded=False):',
    'with st.expander("Auto-Detect Niche & Style from Script", expanded=True):'
)

# 3) Comment out auto_detect_section() call
clean = clean.replace('\n        auto_detect_section()', '\n        # auto_detect_section()')

# 4) Comment out caption_video_preview_section()
clean = clean.replace('\n        caption_video_preview_section()', '\n        # caption_video_preview_section()')

# 5) Remove separator lines that are now orphaned
clean = clean.replace(
    'st.markdown("---")\n        # auto_detect_section()',
    '# auto_detect_section()'
)
clean = clean.replace(
    'st.markdown("---")\n        # caption_video_preview_section()',
    '# caption_video_preview_section()'
)

# 6) Add advanced settings after Render expander
old_return = '        "render_count": int(render_count),\n    }'
new_return = '''        "render_count": int(render_count),
    }

    st.markdown("---")
    st.markdown("**Advanced Motion and Transitions**")
    c1, c2, c3 = st.columns(3)
    motion_override = c1.checkbox("Override Motion", value=False)
    motion_intensity = c1.slider("Motion Intensity", 0.5, 2.0, 1.0, 0.05, disabled=not motion_override)
    trans_override = c2.checkbox("Override Transitions", value=False)
    trans_speed = c2.slider("Transition Speed", 0.1, 0.6, 0.25, 0.02, disabled=not trans_override)
    color_override = c3.checkbox("Override Color", value=False)
    color_warmth = c3.slider("Color Warmth", -0.1, 0.1, 0.0, 0.005, disabled=not color_override)

    st.markdown("**Advanced Audio and Voice**")
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
    }'''

if old_return in clean:
    clean = clean.replace(old_return, new_return)
    print("Advanced settings merged")
else:
    print("WARNING: old return not found")

# 7) Comment out custom_editing_settings_section() call
clean = clean.replace(
    '\n        custom_overrides = custom_editing_settings_section({})',
    '\n        # custom_overrides merged into settings section above'
)

app.write_text(clean, encoding="utf-8")

try:
    compile(clean, "app.py", "exec")
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")

print(f"Backup: app.py.bak_clean_{ts}")
print("Run: streamlit run app.py")