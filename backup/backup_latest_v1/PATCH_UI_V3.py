"""PATCH_UI_V3.py — Safe targeted edits."""
import shutil, time
from pathlib import Path

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 70)
print("  PATCH UI V3 — Safe targeted edits")
print("=" * 70)

app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_uiv3_{ts}")
code = app.read_text(encoding="utf-8")
edits = 0

# [1] Auto-Detect expander → open by default
old = 'with st.expander("Auto-Detect Niche & Style from Script", expanded=False):'
new = 'with st.expander("Auto-Detect Niche & Style from Script", expanded=True):'
if old in code:
    code = code.replace(old, new)
    edits += 1
    print("  [1] Auto-Detect expander open ✅")

# [2] Comment out auto_detect_section() call in main()
if '\n        auto_detect_section()' in code:
    code = code.replace('\n        auto_detect_section()', '\n        # auto_detect_section()  # REMOVED')
    edits += 1
    print("  [2] Auto-Detect call removed ✅")

# [3] Remove separator before auto_detect comment
old = '        st.markdown("---")\n        # auto_detect_section()  # REMOVED'
new = '        # auto_detect_section()  # REMOVED'
if old in code:
    code = code.replace(old, new)
    edits += 1
    print("  [3] Separator cleaned ✅")

# [4] Comment out caption_video_preview_section() call
if '\n        caption_video_preview_section()' in code:
    code = code.replace('\n        caption_video_preview_section()', '\n        # caption_video_preview_section()  # REMOVED')
    edits += 1
    print("  [4] Caption Preview removed ✅")

# [5] Remove separator before caption preview comment
old = '        st.markdown("---")\n        # caption_video_preview_section()  # REMOVED'
new = '        # caption_video_preview_section()  # REMOVED'
if old in code:
    code = code.replace(old, new)
    edits += 1
    print("  [5] Separator cleaned ✅")

# [6] Add Advanced Custom to settings_section return
old = '''        "render_count": int(render_count),
    }'''

new = '''        "render_count": int(render_count),
    }

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
    }'''

if old in code:
    code = code.replace(old, new)
    edits += 1
    print("  [6] Advanced added to Settings ✅")

# [7] Comment out custom_editing_settings_section() call
if '\n        custom_overrides = custom_editing_settings_section({})' in code:
    code = code.replace('\n        custom_overrides = custom_editing_settings_section({})', '\n        # custom_overrides = custom_editing_settings_section({})  # MERGED into settings')
    edits += 1
    print("  [7] Custom section call removed ✅")

# SAVE
app.write_text(code, encoding="utf-8")

print(f"\n{'='*70}")
print(f"  EDITS: {edits}/7")
try:
    compile(code, "app.py", "exec")
    print("  ✅ SYNTAX OK")
except SyntaxError as e:
    print(f"  ❌ SYNTAX: {e}")
print(f"  Backup: app.py.bak_uiv3_{ts}")
print(f"{'='*70}")
print("\n  Run: streamlit run app.py")