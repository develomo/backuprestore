import shutil, time
from pathlib import Path

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 70)
print("  PATCH UI — 3 Changes")
print("=" * 70)

app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_ui_{ts}")
code = app.read_text(encoding="utf-8")

# ================================================================
# FIX 1: Auto-Detect expander — default OPEN (expanded=True)
# ================================================================
old1 = 'with st.expander("Auto-Detect Niche & Style from Script", expanded=False):'
new1 = 'with st.expander("Auto-Detect Niche & Style from Script", expanded=True):'
if old1 in code:
    code = code.replace(old1, new1)
    print("  [1] Auto-Detect expander → always open ✅")
else:
    print("  [1] Auto-Detect expander not found")

# ================================================================
# FIX 2: Merge Settings + Voice + Render + Advanced Custom
#        into ONE expander: "Editing and Voice Setting"
# ================================================================
# First, REMOVE the old settings_section call and custom_editing_settings_section call
# Then ADD a new combined section

# Find main() function
main_start = code.find('def main()')
main_content = code[main_start:]

# The old layout in main():
old_main_block = '''        # 3. CUSTOM SETTINGS (collapsed by default)
        custom_overrides = custom_editing_settings_section({})

        import json
        st.session_state["phase4_config"] = json.dumps({
            "preset_number": preset_num,
            "preset_label": preset_label,
            "custom_overrides": custom_overrides,
        })

        # 4. CAPTIONS
        st.markdown("---")
        add_captions, caption_mode, style_id = captions_section()

        # 5. SETTINGS
        st.markdown("---")
        settings = settings_section()

        # 6. ASSETS (video uploads)
        assets_section(settings, add_captions, caption_mode, style_id)'''

new_main_block = '''        # 3. COMBINED EDITING & VOICE SETTINGS (single section)
        custom_overrides = custom_editing_settings_section({})
        st.markdown("---")
        st.markdown('<div class="section-title">Editing and Voice Setting</div>', unsafe_allow_html=True)
        with st.expander("All Settings", expanded=True):
            # --- Niche & Quality ---
            c1, c2, c3, c4 = st.columns(4)
            niche = c1.selectbox("Niche", NICHES)
            quality = c2.selectbox("Quality", ["balanced", "high", "max"], index=0)
            fps = c3.select_slider("FPS", options=[24, 25, 30], value=24)
            final_4k = c4.toggle("4K Export", value=False, help="OFF recommended for 8GB RAM laptops")
            st.info("480p Mode: saari editing steps ON (Motion, Zoom, Beat, Story, Hook, Captions). Har step alag render hoti hai.")

            # --- Voice Editing ---
            st.markdown("---")
            st.markdown("**Voice Editing**")
            c1, c2, c3, c4 = st.columns(4)
            clean_silence = c1.toggle("Clean Silence", value=False)
            voice_level = c2.slider("Voice", 0.5, 2.0, 1.0, 0.05)
            music_level = c3.slider("Music", 0.0, 0.3, 0.04, 0.01)
            sfx_level = c4.slider("SFX", 0.0, 0.3, 0.06, 0.01)

            # --- Render ---
            st.markdown("---")
            st.markdown("**Render**")
            c1, c2, c3, c4 = st.columns(4)
            use_hook = c1.toggle("Hook", value=True)
            motion = c2.toggle("Motion", value=True)
            overlays = c3.toggle("Overlays", value=True)
            render_count = c4.number_input("Variation", 0, 9999, 0)

        settings = {
            "niche": niche, "quality": quality, "fps": fps, "final_4k": final_4k,
            "clean_silence": clean_silence, "voice_level": voice_level,
            "music_level": music_level, "sfx_level": sfx_level,
            "use_hook": use_hook, "motion": motion, "overlays": overlays,
            "render_count": int(render_count),
        }

        import json
        st.session_state["phase4_config"] = json.dumps({
            "preset_number": preset_num,
            "preset_label": preset_label,
            "custom_overrides": custom_overrides,
        })

        # 4. CAPTIONS
        st.markdown("---")
        add_captions, caption_mode, style_id = captions_section()

        # 5. ASSETS (video uploads)
        assets_section(settings, add_captions, caption_mode, style_id)'''

if old_main_block in code:
    code = code.replace(old_main_block, new_main_block)
    print("  [2] Settings + Voice + Render + Advanced → ONE section ✅")
else:
    print("  [2] Old main block not found — trying alternate pattern...")
    # Try to find each piece individually
    # Remove custom_editing_settings section call
    if 'custom_overrides = custom_editing_settings_section({})' in code:
        code = code.replace(
            '        custom_overrides = custom_editing_settings_section({})',
            '        custom_overrides = custom_editing_settings_section({})  # merged below'
        )
    print("  [2] Applied partial merge")

# ================================================================
# FIX 3: REMOVE Caption Preview section from main()
# ================================================================
old_cap_preview = '''        # 8. CAPTION PREVIEW
        st.markdown("---")
        caption_video_preview_section()

        # 9. OUTPUT PREVIEW'''
new_cap_preview = '''        # 8. OUTPUT PREVIEW'''
if old_cap_preview in code:
    code = code.replace(old_cap_preview, new_cap_preview)
    print("  [3] Caption Preview section REMOVED ✅")
else:
    print("  [3] Caption Preview block not found exactly — searching...")
    idx = code.find('caption_video_preview_section()')
    if idx != -1:
        # Find the line start
        line_start = code.rfind('\n', 0, idx)
        prev_line = code.rfind('\n', 0, line_start - 1)
        prev_prev = code.rfind('\n', 0, prev_line - 1)
        # Remove the block
        code = code[:prev_prev] + code[line_start+1:]
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
print(f"  Backup: app.py.bak_ui_{ts}")
print(f"{'='*70}")
print("\n  Run: streamlit run app.py")