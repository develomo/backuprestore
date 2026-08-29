"""
============================================================================
FINAL MASTER FIX — All Issues Resolved (Phase 1 backup)
============================================================================
FIXES:
  1. Remove standalone auto_detect_section() + call from main()
  2. Remove caption_video_preview_section() completely
  3. preset_selector_section() with unique auto-detect keys
  4. settings_section() unified ONE expander
  5. Remove custom_editing_settings_section() 
  6. _page_generator() clean
  7. caption_offset = 0
  8. Premium CSS
  9. safe_long_video_polished.py: sfx_files, clips

INSTRUCTIONS:
  copy app.py.backup_phase1 app.py
  python final_master_fix.py
  streamlit run app.py
============================================================================
"""
import os, re

BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PATH = os.path.join(BACKUP_DIR, 'app.py')
SL_PATH = os.path.join(BACKUP_DIR, 'safe_long_video_polished.py')

def validate(c, label):
    try:
        compile(c, '<string>', 'exec')
        print(f"  [OK] {label}")
        return True
    except SyntaxError as e:
        lines = c.split('\n')
        lo, hi = max(0, e.lineno-3), min(len(lines), e.lineno+2)
        print(f"  [FAIL] {label} — L{e.lineno}: {e.msg}")
        for i in range(lo, hi):
            m = ">>>" if i == e.lineno-1 else "   "
            print(f"     {m} L{i+1}: {lines[i][:140]}")
        return False

def main():
    if not os.path.exists(APP_PATH):
        print(f"[ERROR] {APP_PATH} not found!"); return
    with open(APP_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    init = len(content.split('\n'))
    print(f"[INFO] {init} lines")
    if not validate(content, "Initial"):
        print("\n[FATAL] Restore: copy app.py.backup_phase1 app.py"); return
    fxs = 0

    # --- 1: REMOVE auto_detect_section function ---
    print("\n--- Fix 1: Remove auto_detect_section ---")
    idx = content.find('\ndef auto_detect_section()')
    if idx >= 0:
        after = content[idx+1:]; nf = re.search(r'\n(def \w+|# ={10,})', after)
        if nf:
            end = idx + 1 + nf.start()
            content = content[:idx] + content[end:]
            fxs += 1; print("  [1a] Removed function")
            if not validate(content, "After 1a"): return
    # Remove call
    for call in ['\n    auto_detect_section()', '    auto_detect_section()']:
        if call in content:
            content = content.replace(call, ''); fxs += 1
            print(f"  [1b] Removed call"); break

    # --- 2: REMOVE caption_video_preview_section ---
    print("\n--- Fix 2: Remove caption_video_preview_section ---")
    idx = content.find('\ndef caption_video_preview_section()')
    if idx >= 0:
        after = content[idx+1:]; nf = re.search(r'\n(def \w+|# ={10,})', after)
        if nf:
            end = idx + 1 + nf.start()
            content = content[:idx] + content[end:]
            fxs += 1; print("  [2] Removed function")
            if not validate(content, "After 2"): return

    # --- 3: Remove custom_editing_settings_section ---
    print("\n--- Fix 3: Remove custom_editing_settings ---")
    idx = content.find('\ndef custom_editing_settings_section(')
    if idx >= 0:
        after = content[idx+1:]; nf = re.search(r'\n(def \w+|# ={10,})', after)
        if nf:
            end = idx + 1 + nf.start()
            content = content[:idx] + content[end:]
            fxs += 1; print("  [3] Removed function")
            if not validate(content, "After 3"): return

    # --- 4: Replace preset_selector ---
    print("\n--- Fix 4: preset_selector_section ---")
    idx = content.find('\ndef preset_selector_section() -> tuple:')
    if idx >= 0:
        after = content[idx+1:]; nf = re.search(r'\n(def \w+|# ={10,})', after)
        if nf:
            end = idx + 1 + nf.start()
            new = r'''
def preset_selector_section() -> tuple:
    st.markdown('<div class="section-title">🎬 Editing Style Preset</div>', unsafe_allow_html=True)
    c_niche, c_auto, c_conf = st.columns([1.5, 0.8, 0.8])
    with c_niche:
        if "selected_niche" not in st.session_state:
            st.session_state["selected_niche"] = "default"
        current_niche = st.selectbox("🎯 Niche", NICHES,
            index=NICHES.index(st.session_state["selected_niche"]) if st.session_state["selected_niche"] in NICHES else 6,
            key="niche_selector_main")
        st.session_state["selected_niche"] = current_niche
    with c_auto:
        st.markdown('<div style="height:5px;"></div>', unsafe_allow_html=True)
        show_auto = st.checkbox("🤖 Auto-Detect", value=False, key="auto_detect_toggle_v2")
    with c_conf:
        conf_val = st.session_state.get("auto_detect_confidence")
        if conf_val is not None and show_auto:
            st.metric("Confidence", f"{conf_val:.0%}")
    if show_auto:
        with st.container():
            script_input = st.text_area("Paste your script text:", height=100,
                placeholder="In the world of luxury, exclusivity is everything...",
                key="auto_detect_script_v2")
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                if st.button("🔍 Auto-Detect Now", use_container_width=True, type="primary", key="auto_detect_btn_v2"):
                    if script_input.strip():
                        with st.spinner("Analyzing..."):
                            niche, preset, confidence, reasoning = auto_detect_niche_and_preset(script_text=script_input)
                            st.session_state["selected_niche"] = niche
                            st.session_state["editing_preset_number"] = preset
                            st.session_state["auto_detect_confidence"] = confidence
                            st.session_state["auto_detect_reasoning"] = reasoning
                            st.success(f"✅ **{niche.upper()}** → Preset #{preset} ({confidence:.0%})")
                            st.info(reasoning); st.rerun()
                    else:
                        st.warning("Please paste some script text first.")
            with col_a2:
                if st.button("📋 Clear", use_container_width=True, key="auto_detect_clear_v2"):
                    for k in ["auto_detect_script_v2", "auto_detect_confidence", "auto_detect_reasoning"]:
                        st.session_state.pop(k, None); st.rerun()
    try:
        if PRESET_ENGINE_AVAILABLE: labels = get_preset_labels(current_niche)
        else: labels = PRESET_LABELS_FALLBACK.get(current_niche, PRESET_LABELS_FALLBACK["default"])
    except Exception:
        labels = PRESET_LABELS_FALLBACK.get(current_niche, PRESET_LABELS_FALLBACK["default"])
    if "editing_preset_number" not in st.session_state:
        st.session_state["editing_preset_number"] = 1
    preset_num = st.session_state["editing_preset_number"]
    cols_r1 = st.columns(4)
    for i in range(4):
        with cols_r1[i]:
            ls = labels[i][:22] if i < len(labels) else f"Style {i+1}"
            sel = (preset_num == i + 1)
            if st.button(f"{'●' if sel else '○'} {i+1}. {ls}", key=f"preset_btn_{i+1}_v3", use_container_width=True,
                         type="primary" if sel else "secondary"):
                st.session_state["editing_preset_number"] = i + 1; st.rerun()
    cols_r2 = st.columns(4)
    for i in range(4, 8):
        with cols_r2[i - 4]:
            ls = labels[i][:22] if i < len(labels) else f"Style {i+1}"
            sel = (preset_num == i + 1)
            if st.button(f"{'●' if sel else '○'} {i+1}. {ls}", key=f"preset_btn_{i+1}_v3", use_container_width=True,
                         type="primary" if sel else "secondary"):
                st.session_state["editing_preset_number"] = i + 1; st.rerun()
    selected_label = labels[preset_num - 1] if preset_num <= len(labels) else f"Style {preset_num}"
    st.markdown(f"**Selected:** Preset #{preset_num} — *{selected_label}*")
    if PRESET_ENGINE_AVAILABLE:
        try:
            p = get_preset_by_number(current_niche, preset_num)
            if p and hasattr(p, 'description'):
                with st.expander("📝 About this preset", expanded=False):
                    st.markdown(p.description)
        except Exception: pass
    return preset_num, selected_label
'''
            content = content[:idx] + new + '\n' + content[end:]
            fxs += 1; print("  [4] preset_selector with unique keys")
            if not validate(content, "After 4"): return

    # --- 5: Replace settings_section ---
    print("\n--- Fix 5: settings_section ---")
    idx = content.find('\ndef settings_section() -> Dict[str, Any]:')
    if idx >= 0:
        after = content[idx+1:]; nf = re.search(r'\n(def \w+|# ={10,})', after)
        if nf:
            end = idx + 1 + nf.start()
            new = r'''
def settings_section() -> Dict[str, Any]:
    st.markdown('<div class="section-title">⚙️ Settings</div>', unsafe_allow_html=True)
    with st.expander("⚙️ All Settings", expanded=False):
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
        st.markdown("**🎙 Voice & Audio**")
        v1, v2, v3, v4 = st.columns(4)
        clean_silence = v1.toggle("Clean Silence", value=False)
        voice_level = v2.slider("Voice", 0.5, 2.0, 1.0, 0.05)
        music_level = v3.slider("Music", 0.0, 0.3, 0.04, 0.01)
        sfx_level = v4.slider("SFX", 0.0, 0.3, 0.06, 0.01)
        st.markdown("---")
        st.markdown("**🔄 Render**")
        render_count = st.number_input("Variations", 0, 9999, 0)
        st.info("480p Mode — All editing ON. Each step renders separately. 4K OFF.")
        st.markdown("---")
        st.markdown("**🎛️ Advanced Overrides**")
        st.caption("Fine-tune motion, transitions, colors. Leave at default for preset control.")
        a1, a2, a3 = st.columns(3)
        with a1:
            mo_override = st.checkbox("Override Motion", value=False, key="override_motion_v3")
            motion_intensity = st.slider("Motion Intensity", 0.5, 2.0, 1.0, 0.05, key="mo_int_v3", disabled=not mo_override)
        with a2:
            to_override = st.checkbox("Override Transitions", value=False, key="override_trans_v3")
            trans_speed = st.slider("Transition Speed", 0.1, 0.6, 0.25, 0.02, key="trans_spd_v3", disabled=not to_override)
        with a3:
            co_override = st.checkbox("Override Color", value=False, key="override_color_v3")
            color_warmth = st.slider("Color Warmth", -0.1, 0.1, 0.0, 0.005, key="col_warm_v3", disabled=not co_override)
        b1, b2 = st.columns(2)
        with b1:
            ao_override = st.checkbox("Override Audio", value=False, key="override_audio_v3")
            music_vol = st.slider("Music Volume", 0.0, 0.3, st.session_state.get("music_level", 0.04), 0.005, key="mvol_v3", disabled=not ao_override)
        with b2:
            vo_override = st.checkbox("Override Voice", value=False, key="override_voice_v3")
            voice_profiles = ["auto", "calm_deliberate", "warm_measured", "energetic_bright", "dramatic_tense", "clean_aesthetic", "sharp_decisive", "documentary_authority", "soft_emotional"]
            voice_profile = st.selectbox("Voice Profile", voice_profiles, index=0, key="voice_prf_v3", disabled=not vo_override)
    overrides = {}
    if mo_override: overrides["motion_intensity"] = motion_intensity
    if to_override: overrides["transition_duration"] = trans_speed
    if co_override: overrides["color_warmth"] = color_warmth
    if ao_override: overrides["music_volume"] = music_vol
    if vo_override and voice_profile != "auto": overrides["voice_profile"] = voice_profile
    return {"niche": niche, "quality": quality, "fps": fps, "final_4k": final_4k,
        "clean_silence": clean_silence, "voice_level": voice_level, "music_level": music_level,
        "sfx_level": sfx_level, "use_hook": use_hook, "motion": motion, "overlays": overlays,
        "render_count": int(render_count), "custom_overrides": overrides}
'''
            content = content[:idx] + new + '\n' + content[end:]
            fxs += 1; print("  [5] Unified settings")
            if not validate(content, "After 5"): return

    # --- 6: Replace _page_generator ---
    print("\n--- Fix 6: _page_generator ---")
    idx = content.find('\ndef _page_generator():')
    if idx >= 0:
        after = content[idx+1:]; nf = re.search(r'\n(def |# ={10,})', after)
        if nf:
            end = idx + 1 + nf.start()
            new = r'''
def _page_generator():
    st.markdown('<div class="app-title">' + APP_TITLE + '</div>', unsafe_allow_html=True)
    preset_num, preset_label = preset_selector_section()
    st.session_state["editing_preset_number"] = preset_num
    st.session_state["editing_preset_label"] = preset_label
    import json
    settings = settings_section()
    st.session_state["phase4_config"] = json.dumps({"preset_number": preset_num, "preset_label": preset_label, "custom_overrides": settings.get("custom_overrides", {})})
    add_captions, caption_mode, style_id = captions_section()
    assets_section(settings, add_captions, caption_mode, style_id)
    st.markdown("---")
    scoring_panel_section()
    output_preview()
'''
            content = content[:idx] + new + '\n' + content[end:]
            fxs += 1; print("  [6] Clean _page_generator")
            if not validate(content, "After 6"): return

    # --- 7: caption_offset = 0 ---
    print("\n--- Fix 7: Caption timing ---")
    old = '        update(20, "Loading pipeline")'
    if old in content:
        inj = '        kwargs["caption_offset"] = 0.0\n        kwargs["caption_timing_precision"] = True\n        '
        content = content.replace(old, inj + old, 1)
        fxs += 1; print("  [7] caption_offset=0.0")
    # niche_editing_presets
    nep = os.path.join(BACKUP_DIR, 'niche_editing_presets.py')
    if os.path.exists(nep):
        with open(nep, 'r', encoding='utf-8') as f: nd = f.read()
        no = nd
        for o in ['"caption_start_offset": -0.12', '"caption_start_offset": -0.16', '"caption_start_offset": -0.18']:
            if o in nd: nd = nd.replace(o, '"caption_start_offset": 0.0')
        if nd != no:
            with open(nep, 'w', encoding='utf-8') as f: f.write(nd)
            print("  [7b] caption_start_offset in presets")

    # --- 8: Premium CSS ---
    print("\n--- Fix 8: Premium CSS ---")
    idx = content.find('\ndef css() -> None:')
    if idx >= 0:
        after = content[idx+20:]; nf = re.search(r'\n(def \w+|# ={10,})', after)
        end = idx + 20 + (nf.start() if nf else len(after))
        premium = r'''
def css() -> None:
    st.markdown("""<style>
:root{--bg:#f5f6f8;--bg-alt:#edeff3;--surface:#fff;--surface-hover:#f9fafb;--border:#e0e3e8;--border-light:#ebeef2;--text:#1a1a2e;--text-primary:#111122;--text-secondary:#6b7280;--text-tertiary:#9ca3af;--accent:#e63946;--accent-hover:#c1121f;--accent-light:#fef2f3;--accent-soft:#fce4e6;--green:#059669;--green-light:#ecfdf5;--amber:#d97706;--amber-light:#fffbeb;--red:#dc2626;--red-light:#fef2f2;--shadow-xs:0 1px 2px rgba(0,0,0,.03);--shadow-sm:0 1px 3px rgba(0,0,0,.05),0 1px 2px rgba(0,0,0,.03);--shadow-md:0 4px 12px rgba(0,0,0,.06),0 1px 3px rgba(0,0,0,.04);--shadow-lg:0 8px 24px rgba(0,0,0,.08),0 2px 6px rgba(0,0,0,.04);--radius-xs:6px;--radius-sm:8px;--radius:12px;--radius-lg:16px;--transition:.2s cubic-bezier(.4,0,.2,1)}
[data-theme="dark"]{--bg:#0b0b18;--bg-alt:#12122a;--surface:#181835;--surface-hover:#1e1e40;--border:#2a2a4a;--border-light:#222244;--text:#e8e8f5;--text-primary:#f0f0ff;--text-secondary:#9a9ab8;--text-tertiary:#6a6a88;--accent:#ff4d5a;--accent-hover:#ff6b6b;--accent-light:rgba(255,77,90,.12);--accent-soft:rgba(255,77,90,.08);--green:#34d399;--green-light:rgba(52,211,153,.12);--amber:#fbbf24;--amber-light:rgba(251,191,36,.12);--red:#f87171;--red-light:rgba(248,113,113,.12)}
.stApp{background:var(--bg)!important}
.block-container{padding:.5rem 1.5rem 1.5rem!important;max-width:1240px!important}
header[data-testid="stHeader"]{background:transparent!important}
#MainMenu,footer,.stDeployButton{visibility:hidden!important;display:none!important}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
hr{border-color:var(--border)!important;margin:8px 0!important;opacity:.5!important}
.app-title{font-size:28px;font-weight:800;letter-spacing:-.6px;margin-bottom:6px;color:var(--text-primary)}
.section-title{font-size:16px;font-weight:700;margin:16px 0 8px;color:var(--text-primary)}
.card{border:1px solid var(--border);border-radius:var(--radius);padding:16px;background:var(--surface);box-shadow:var(--shadow-sm);margin-bottom:10px;transition:box-shadow var(--transition)}
.card:hover{box-shadow:var(--shadow-md)}
.asset-title{font-size:15px;font-weight:700;margin:2px 0 8px;color:var(--text-primary)}
.asset-label{font-size:12px;font-weight:600;margin:6px 0 4px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.3px}
.count{font-size:11px;color:var(--text-tertiary);margin-bottom:4px}
.ready{font-size:12px;font-weight:700;color:var(--green);padding:4px 10px;background:var(--green-light);border-radius:20px;display:inline-block}
.missing{font-size:12px;font-weight:700;color:var(--red);padding:4px 10px;background:var(--red-light);border-radius:20px;display:inline-block}
.caption-wrap{border:1px solid var(--border);border-radius:var(--radius);padding:14px;background:var(--surface);box-shadow:var(--shadow-xs);margin-bottom:10px;transition:all var(--transition)}
.caption-wrap:hover{border-color:var(--border-light);box-shadow:var(--shadow-sm)}
.caption-title{font-size:13px;font-weight:700;margin-bottom:6px;color:var(--text-primary)}
.caption-desc{font-size:11px;color:var(--text-tertiary);margin:6px 0 8px;line-height:1.4}
.caption-preview-box{width:150px;max-width:100%;border:1px solid var(--border);border-radius:var(--radius-xs);overflow:hidden;background:#0a0a18;padding:0;box-shadow:var(--shadow-sm)}
.preview-box{border:1px dashed var(--border);border-radius:var(--radius);padding:16px;min-height:100px;background:var(--surface);transition:border-color var(--transition)}
.preview-box:hover{border-color:var(--accent)}
div.stButton>button{height:38px!important;border-radius:var(--radius-sm)!important;font-weight:600!important;font-size:13px!important;transition:all var(--transition)!important;border:1px solid var(--border)!important}
div.stButton>button[kind="primary"]{background:var(--accent)!important;color:#fff!important;border-color:var(--accent)!important;box-shadow:0 2px 8px rgba(230,57,70,.25)!important}
div.stButton>button[kind="primary"]:hover{background:var(--accent-hover)!important;transform:translateY(-1px);box-shadow:0 4px 14px rgba(230,57,70,.35)!important}
div.stButton>button[kind="secondary"]{background:var(--surface)!important;color:var(--text)!important}
div.stButton>button[kind="secondary"]:hover{background:var(--surface-hover)!important;border-color:var(--accent)!important;color:var(--accent)!important}
div[data-testid="stFileUploader"] section{min-height:48px!important;padding:6px 10px!important;border-radius:var(--radius-sm)!important;border:2px dashed var(--border)!important;background:var(--bg-alt)!important;transition:all var(--transition)!important}
div[data-testid="stFileUploader"] section:hover{border-color:var(--accent)!important;background:var(--accent-light)!important}
div[data-testid="stFileUploader"] small{display:none!important}
.streamlit-expanderHeader{border-radius:var(--radius-sm)!important;border:1px solid var(--border)!important;background:var(--surface)!important;font-weight:650!important;font-size:14px!important;color:var(--text-primary)!important;padding:12px 16px!important;transition:all var(--transition)!important}
.streamlit-expanderHeader:hover{border-color:var(--accent)!important;background:var(--surface-hover)!important}
.streamlit-expanderContent{border:1px solid var(--border)!important;border-top:none!important;border-radius:0 0 var(--radius-sm) var(--radius-sm)!important;background:var(--surface)!important;padding:12px!important}
section[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border)!important}
div[data-testid="stSelectbox"] label,div[data-testid="stRadio"] label{color:var(--text-secondary)!important;font-size:12px!important;font-weight:600!important}
div[data-testid="stCheckbox"] label{color:var(--text)!important;font-size:13px!important}
div[data-testid="stSlider"]>div>div>div>div{background:var(--accent)!important}
div[data-testid="stSuccess"]{background:var(--green-light)!important;border:1px solid var(--green)!important;border-radius:var(--radius-sm)!important}
div[data-testid="stError"]{background:var(--red-light)!important;border:1px solid var(--red)!important;border-radius:var(--radius-sm)!important}
div[data-testid="stWarning"]{background:var(--amber-light)!important;border:1px solid var(--amber)!important;border-radius:var(--radius-sm)!important}
</style>""", unsafe_allow_html=True)
    st.markdown("""<script>
(function(){try{var s=localStorage.getItem('zaro_theme_v2');if(s==='dark')document.documentElement.setAttribute('data-theme','dark');}catch(e){}
window.toggleThemeV2=function(){try{var c=document.documentElement.getAttribute('data-theme');if(c==='dark'){document.documentElement.removeAttribute('data-theme');localStorage.setItem('zaro_theme_v2','light');}else{document.documentElement.setAttribute('data-theme','dark');localStorage.setItem('zaro_theme_v2','dark');}}catch(e){}}})();
</script>""", unsafe_allow_html=True)
'''
        content = content[:idx] + premium + '\n' + content[end:]
        fxs += 1; print("  [8] Premium CSS")
        if not validate(content, "After 8"): return

    # --- 9: Theme toggle JS ---
    for t in ['window.toggleTheme();', 'try{window.toggleTheme();}catch(e){}']:
        if t in content:
            content = content.replace(t, t.replace('toggleTheme', 'toggleThemeV2'))
            fxs += 1; print(f"  [9] Theme JS: toggleTheme→toggleThemeV2")

    # --- 10: safe_long_video_polished.py ---
    print("\n--- Fix 10: Long pipeline ---")
    if os.path.exists(SL_PATH):
        with open(SL_PATH, 'r', encoding='utf-8') as f: sl = f.read()
        with open(SL_PATH + '.backup_final', 'w', encoding='utf-8') as f: f.write(sl)
        sfix = 0
        # FIX sfx_files → sfx_path
        for o, n in [('clips=clip_list', 'clip_paths=clip_list'), ('sfx_files,', 'sfx_path,'), ('sfx_files)', 'sfx_path)'), ('sfx_files ', 'sfx_path ')]:
            if o in sl:
                sl = sl.replace(o, n)
                sfix += 1; print(f"  [10a] {o} → {n}")
        if 'sfx=choose_sfx(' in sl and 'sfx_files' in sl:
            sl = sl.replace('sfx_files', 'sfx_path')
            sfix += 1; print("  [10b] sfx_files → sfx_path (inline)")
        if 'sfx_files' in sl and 'sfx=' not in sl:
            # Find and replace all remaining sfx_files
            sl = sl.replace('sfx_files', 'sfx_path')
            sfix += 1; print("  [10c] All remaining sfx_files replaced")
        if 'final_quality=' in sl:
            sl = re.sub(r',?\s*final_quality\s*=\s*"[^"]*"', '', sl)
            sfix += 1; print("  [10d] Removed final_quality=")
        if 'cleanup=True' in sl:
            sl = sl.replace('cleanup=True', 'keep_temp=False')
            sfix += 1; print("  [10e] cleanup=True → keep_temp=False")
        if sfix:
            try:
                compile(sl, SL_PATH, 'exec')
                with open(SL_PATH, 'w', encoding='utf-8') as f: f.write(sl)
                fxs += sfix; print(f"  [10] Written: {sfix} fixes")
            except SyntaxError as e:
                print(f"  [10 ERROR] {e}")
    else:
        print("  [SKIP] safe_long_video_polished.py not found")

    # FINAL
    print("\n" + "=" * 60)
    if validate(content, "FINAL"):
        with open(APP_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        print("=" * 60)
        print(f"\n[SUCCESS] {fxs} fixes, {init} → {len(content.split(chr(10)))} lines")
        print("\n▶ streamlit run app.py")
    else:
        print("=" * 60 + "\n[FAILED] app.py NOT modified.")


if __name__ == "__main__":
    main()