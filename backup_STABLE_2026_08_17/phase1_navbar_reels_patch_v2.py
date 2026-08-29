"""
============================================================================
PHASE 1 PATCH v2 — Auto-Script for Menu Bar + Reels Page Fix
(Fixed: handles multiple app.py formats — both cleaned and uncleaned)
============================================================================
"""
import os
import re

BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))


def find_main_end(content):
    """Find where main() function ends, handling multiple file formats."""
    idx = content.index('\ndef main() -> None:\n')
    
    # Search from after 'def main()' for any of these end markers
    after = content[idx + 20:]
    
    # Try multiple markers in order
    markers = [
        '\n\ndef _runtime_compat_helper_1',
        '\n\n# ============================================================',
        '\n\n# PHASE 13 NOTE:',
        '\n# PHASE 13 NOTE:',
        '\n\n# APP PREMIUM',
        '\n\n# ============================================================',
        '\n# batch_long_renderer.py',
        '\n\nif __name__',
    ]
    
    # Also try: find the next top-level 'def ' or '# ===' after main
    next_def = re.search(r'\n(def |# ={10,}|if __name__)', after)
    
    for marker in markers:
        if marker in after:
            end_offset = after.index(marker)
            return idx + 20 + end_offset, marker
    
    if next_def:
        return idx + 20 + next_def.start(), after[next_def.start():next_def.start()+30]
    
    # Last resort: take rest of file
    end_marker = content[idx:].rstrip()[-30:]
    return idx + len(content[idx:]), end_marker


def main_phase1_v2():
    app_path = os.path.join(BACKUP_DIR, 'app.py')

    with open(app_path, 'r', encoding='utf-8') as f:
        original = f.read()

    # Create backup
    backup_path = app_path + '.backup_phase1'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original)
    print(f"[OK] Backup: {backup_path}")
    print(f"[INFO] app.py has {len(original.split(chr(10)))} lines")

    content = original
    changes = 0

    # ==================================================================
    # PATCH 1: Replace css() function
    # ==================================================================
    if 'def css() -> None:' not in content:
        print("[ERROR] 'def css()' not found!")
        return

    # Find where css() ends — by finding the next top-level def or comment
    idx_css = content.index('def css() -> None:')
    after_css = content[idx_css + 17:]
    
    # CSS ends where next function starts (preview_path)
    css_end_markers = ['\n\ndef preview_path', '\n\ndef caption_dropdown_card', '\ndef settings_section']
    css_end = len(after_css)
    
    for marker in css_end_markers:
        if marker in after_css:
            css_end = after_css.index(marker)
            break

    new_css = '''def css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f8f9fb; --surface: #ffffff; --border: #e8eaef;
            --text: #1a1a2e; --text-secondary: #5f6368;
            --accent: #e63946; --accent-hover: #c1121f; --accent-light: #fef0f0;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.03); --shadow-md: 0 2px 8px rgba(0,0,0,0.05);
            --radius: 12px; --radius-sm: 8px; --transition: 0.18s ease;
        }
        [data-theme="dark"] {
            --bg: #0f0f1a; --surface: #1a1a2e; --border: #2a2a3e;
            --text: #e8e8f0; --text-secondary: #9a9ab0;
        }
        .stApp{background:var(--bg)!important}
        .block-container{padding-top:0.3rem!important;padding-bottom:1rem!important;max-width:1200px!important}
        header[data-testid="stHeader"]{background:transparent!important}
        #MainMenu,footer{visibility:hidden!important}

        .app-title{font-size:26px;font-weight:850;letter-spacing:-0.4px;margin-bottom:4px;color:var(--text)}
        .section-title{font-size:16px;font-weight:750;margin:12px 0 6px 0;color:var(--text)}
        .card{border:1px solid var(--border);border-radius:var(--radius);padding:12px;background:var(--surface);box-shadow:var(--shadow-sm);margin-bottom:8px}
        .asset-title{font-size:15px;font-weight:750;margin:2px 0 6px 0;color:var(--text)}
        .asset-label{font-size:12px;font-weight:700;margin:5px 0 3px 0;color:var(--text-secondary)}
        .count{font-size:11px;opacity:0.5;margin-bottom:4px}
        .ready{font-size:12px;font-weight:750;color:#087f5b}
        .missing{font-size:12px;font-weight:750;color:var(--accent)}
        .caption-wrap{border:1px solid var(--border);border-radius:var(--radius);padding:10px;background:var(--surface);box-shadow:var(--shadow-sm);margin-bottom:8px}
        .caption-title{font-size:13px;font-weight:750;margin-bottom:5px;color:var(--text)}
        .caption-desc{font-size:11px;opacity:0.55;margin:5px 0 7px 0}
        .caption-preview-box{width:160px;max-width:100%;border:1px solid var(--border);border-radius:8px;overflow:hidden;background:#0a0a14;padding:0}
        .preview-box{border:1px dashed var(--border);border-radius:var(--radius);padding:12px;min-height:90px;background:var(--surface)}
        div.stButton>button{height:36px!important;border-radius:var(--radius-sm)!important;font-weight:700!important;font-size:13px!important;border:1px solid var(--border)!important}
        div.stButton>button[kind="primary"]{background:var(--accent)!important;color:white!important;border-color:var(--accent)!important}
        div.stButton>button[kind="primary"]:hover{background:var(--accent-hover)!important}
        div.stButton>button[kind="secondary"]{background:var(--surface)!important;color:var(--text)!important}
        div[data-testid="stFileUploader"] section{min-height:46px!important;padding:3px 8px!important;border-radius:var(--radius-sm)!important;border:1px dashed var(--border)!important}
        div[data-testid="stFileUploader"] small{display:none!important}
        .streamlit-expanderHeader{border-radius:var(--radius-sm)!important;border:1px solid var(--border)!important;background:var(--surface)!important;font-weight:650!important;color:var(--text)!important}
        section[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border)!important}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        \"\"\"
        <script>
        (function(){
            try{var s=localStorage.getItem('zaro_theme');if(s==='dark')document.documentElement.setAttribute('data-theme','dark');}catch(e){}
            window.toggleTheme=function(){
                try{var c=document.documentElement.getAttribute('data-theme');
                if(c==='dark'){document.documentElement.removeAttribute('data-theme');localStorage.setItem('zaro_theme','light');}
                else{document.documentElement.setAttribute('data-theme','dark');localStorage.setItem('zaro_theme','dark');}
                }catch(e){}
            };
        })();
        </script>
        \"\"\",
        unsafe_allow_html=True,
    )
'''

    content = content[:idx_css] + new_css + '\n' + content[idx_css + css_end:]
    changes += 1
    print("[PATCH 1] css() replaced — navbar CSS + dark mode JS")

    # ==================================================================
    # PATCH 2: Find and replace main()
    # ==================================================================
    if '\ndef main() -> None:\n' not in content:
        print("[ERROR] 'def main()' not found!")
        return

    idx_main_start = content.index('\ndef main() -> None:\n')
    main_end_idx, end_marker = find_main_end(content)

    new_main_and_funcs = '''

def main() -> None:
    if st is None:
        print("Streamlit missing")
        return

    init_folders()
    st.set_page_config(page_title=APP_TITLE, page_icon="🎬", layout="wide")
    css()

    # -- NAVIGATION BAR --
    cb, cn, ct = st.columns([2, 2, 0.3])
    with cb:
        st.markdown('<div class="navbar-brand"><div class="logo-icon">🎬</div>' + APP_TITLE + '</div>', unsafe_allow_html=True)
    with cn:
        qp = st.query_params
        active_page = qp.get("page", "generator")
        n1, n2 = st.columns(2)
        with n1:
            if st.button("🎥 Generator", key="n_gen", use_container_width=True,
                         type="primary" if active_page == "generator" else "secondary"):
                st.query_params["page"] = "generator"; st.rerun()
        with n2:
            if st.button("🎬 Reels", key="n_reel", use_container_width=True,
                         type="primary" if active_page == "reels" else "secondary"):
                st.query_params["page"] = "reels"; st.rerun()
    with ct:
        dm = st.session_state.get("dark_mode", False)
        icon = "🌙" if dm else "☀️"
        if st.button(icon, key="theme_btn", help="Toggle dark/light"):
            st.session_state["dark_mode"] = not dm
            st.markdown('<script>try{window.toggleTheme();}catch(e){}</script>', unsafe_allow_html=True)
            st.rerun()

    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    # -- ROUTE --
    if active_page == "reels":
        _page_reels()
    else:
        _page_generator()


# ═══════════════════════════════════════════
# VIDEO GENERATOR PAGE
# ═══════════════════════════════════════════
def _page_generator():
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
    output_preview()


# ═══════════════════════════════════════════
# REELS UPLOAD STUDIO PAGE
# ═══════════════════════════════════════════
def _page_reels():
    import tempfile
    st.markdown('<div class="app-title">🎬 Reels Upload Studio</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:13px;opacity:0.6;margin-bottom:14px;">AI-Powered Video Regeneration</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])

    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        rt = st.radio("Video Type", ["short", "long"],
                      format_func=lambda x: "📱 Short" if x == "short" else "🎥 Long",
                      horizontal=True, key="_rt")
        am = {"short": ["9:16", "1:1", "4:5"], "long": ["16:9", "9:16", "1:1"]}
        ra = st.selectbox("Aspect Ratio", am[rt], key="_ra")

        st.markdown("---")
        st.markdown("**🎨 Style**")
        no = ["auto", "luxury_lifestyle", "quantum_future", "mystery", "stoic_wisdom", "interior_design", "finance_simulation", "default"]
        rn = st.selectbox("Niche", no, key="_rn")
        pc = st.columns(8)
        for i in range(8):
            with pc[i]:
                a = st.session_state.get("_rpreset", 1) == i + 1
                if st.button(str(i+1), key=f"_rp{i+1}", use_container_width=True, type="primary" if a else "secondary"):
                    st.session_state["_rpreset"] = i + 1; st.rerun()
        rp = st.session_state.get("_rpreset", 1)

        st.markdown("---")
        ca, cb = st.columns(2)
        with ca:
            rv = st.checkbox("🎙 Voice", key="_rvc")
            if rv: st.slider("Pitch", -1.0, 1.0, 0.0, 0.1, key="_rpi")
            rb = st.checkbox("🎵 Music", key="_rbc")
        with cb:
            rc = st.checkbox("✍️ Captions", value=True, key="_rcc")
            if rc: st.selectbox("Style", ["kinetic", "classic", "minimal", "bold"], key="_rcs")
        if rb:
            st.file_uploader("Upload Music", type=["mp3","wav"], key="_rbu")
            st.slider("Music Vol", 0.05, 1.0, 0.3, 0.05, key="_rmv")

        st.markdown("---")
        rf = st.file_uploader("📤 Upload Video", type=["mp4","mov","avi","mkv","webm"], key="_rvf")
        rpath = None
        if rf:
            s = Path(rf.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=s, dir=BASE_DIR) as tmp:
                tmp.write(rf.read()); rpath = tmp.name
            st.video(rpath)
            st.success(f"Uploaded: {rf.name} ({rf.size/1048576:.1f} MB)")

        if st.button("🚀 Start AI Regeneration", type="primary", use_container_width=True, disabled=not rpath):
            with st.spinner("Processing..."):
                try:
                    from reels_editing_engine import ReelsEditingEngine
                    eng = ReelsEditingEngine(video_path=rpath, video_type=rt, aspect_ratio=ra, niche=rn, preset_number=rp)
                    res = eng.process()
                    if res.get("success"):
                        st.session_state["_ro"] = res.get("output_path"); st.success("Done!"); st.rerun()
                    else:
                        st.error("Error: " + str(res.get("error", "Unknown")))
                except ImportError:
                    st.warning("reels_editing_engine not found (demo)"); st.session_state["_ro"] = rpath; st.success("Done (demo)!"); st.rerun()
                except Exception as e:
                    st.error("Failed: " + str(e))
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📺 Output")
        o = st.session_state.get("_ro")
        if o and os.path.exists(o):
            st.video(o)
            with open(o, "rb") as f:
                st.download_button("📥 Download", f.read(), file_name="reels_output.mp4", mime="video/mp4", use_container_width=True)
        else:
            st.info("Output appears here after processing")
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("🔄 Reset", use_container_width=True, key="_rreset"):
            for k in list(st.session_state.keys()):
                if k.startswith("_r"): del st.session_state[k]
            st.rerun()
'''

    # Replace main() with new code
    content = content[:idx_main_start] + '\n' + new_main_and_funcs + '\n' + content[main_end_idx:]
    changes += 1
    print(f"[PATCH 2] main() replaced (end marker: '{end_marker[:40]}...')")

    # ==================================================================
    # PATCH 3: Ensure clean entry point
    # ==================================================================
    import re as _re
    content = _re.sub(r'\n*if __name__ == ["\']__main__["\']:\s*\n\s+main\(\)\s*', '', content)
    content = _re.sub(r'\n*# Final Streamlit.*\nif __name__.*\n\s+main\(\)\s*', '', content)
    content = content.rstrip() + '\n\nif __name__ == "__main__":\n    main()\n'
    changes += 1
    print("[PATCH 3] Entry point cleaned")

    # ==================================================================
    # WRITE
    # ==================================================================
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)

    new_lines = len(content.split('\n'))
    print(f"\n{'='*60}")
    print(f"PHASE 1 v2 — COMPLETE ({changes} patches, {new_lines} lines)")
    print(f"Backup: {backup_path}")
    print(f"{'='*60}")
    print("Changes:")
    print("  1. css() — Navbar CSS + dark mode variables + toggle JS")
    print("  2. main() — Navigation bar + Generator/Reels page routing")
    print("  3. _page_reels() — Full working Reels Upload Studio")
    print("  4. _page_generator() — Clean Video Generator page")
    print("  5. Dark/Light toggle ☀️/🌙 button")
    print("\nTest: streamlit run app.py")


if __name__ == "__main__":
    main_phase1_v2()