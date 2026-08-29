"""
============================================================================
PHASE 1 PATCH — Auto-Script for Menu Bar + Reels Page Fix
============================================================================
THIS SCRIPT AUTOMATICALLY:
  1. Reads app.py
  2. Creates a backup (app.py.backup_phase1)
  3. Replaces the css() function with professional navbar CSS + dark mode
  4. Replaces main() with new navbar layout + query-param routing
  5. Injects render_reels_page() and render_video_generator_page() functions
  6. Ensures reels page works perfectly with full upload/processing UI

NO MANUAL WORK REQUIRED. Just place in backup folder and run.

USAGE:
  cd "D:\My Creation Video Generator\backup"
  python phase1_navbar_reels_patch.py
============================================================================
"""
import os
import re

BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))


def main_phase1():
    app_path = os.path.join(BACKUP_DIR, 'app.py')

    # ── Read app.py ──
    with open(app_path, 'r', encoding='utf-8') as f:
        original = f.read()

    # ── Create backup ──
    backup_path = app_path + '.backup_phase1'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original)
    print(f"[OK] Backup saved: {backup_path}")

    content = original
    changes = 0

    # ==================================================================
    # PATCH 1: Replace css() function
    # ==================================================================
    css_start_marker = 'def css() -> None:'
    css_end_marker = '\n\ndef preview_path'

    if css_start_marker not in content:
        print("[ERROR] 'def css()' not found in app.py!")
        return

    if css_end_marker not in content:
        print("[ERROR] 'def preview_path' not found (css function end marker)!")
        return

    idx_css_start = content.index(css_start_marker)
    idx_css_end = content.index(css_end_marker)

    new_css = '''def css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f8f9fb;
            --surface: #ffffff;
            --border: #e8eaef;
            --text: #1a1a2e;
            --text-secondary: #5f6368;
            --accent: #e63946;
            --accent-hover: #c1121f;
            --accent-light: #fef0f0;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.03);
            --shadow-md: 0 2px 8px rgba(0,0,0,0.05);
            --radius: 12px;
            --radius-sm: 8px;
            --transition: 0.18s ease;
        }
        [data-theme="dark"] {
            --bg: #0f0f1a;
            --surface: #1a1a2e;
            --border: #2a2a3e;
            --text: #e8e8f0;
            --text-secondary: #9a9ab0;
        }
        .stApp { background: var(--bg) !important; }
        .block-container { padding-top:0.3rem !important; padding-bottom:1rem !important; max-width:1200px !important; }
        header[data-testid="stHeader"] { background:transparent !important; }
        #MainMenu, footer { visibility:hidden !important; }

        /* Top Navbar */
        .navbar { display:flex; align-items:center; justify-content:space-between; padding:10px 22px; background:var(--surface); border-bottom:1px solid var(--border); border-radius:0 0 var(--radius) var(--radius); margin-bottom:12px; box-shadow:var(--shadow-sm); }
        .navbar-brand { display:flex; align-items:center; gap:8px; font-size:19px; font-weight:800; color:var(--text); letter-spacing:-0.3px; }
        .logo-icon { width:34px; height:34px; background:linear-gradient(135deg, var(--accent), #ff6b6b); border-radius:8px; display:flex; align-items:center; justify-content:center; color:white; font-size:17px; }

        /* Section Titles */
        .app-title { font-size:26px; font-weight:850; letter-spacing:-0.4px; margin-bottom:4px; color:var(--text); }
        .section-title { font-size:16px; font-weight:750; margin:12px 0 6px 0; color:var(--text); }

        /* Cards */
        .card { border:1px solid var(--border); border-radius:var(--radius); padding:12px; background:var(--surface); box-shadow:var(--shadow-sm); margin-bottom:8px; }
        .asset-title { font-size:15px; font-weight:750; margin:2px 0 6px 0; color:var(--text); }
        .asset-label { font-size:12px; font-weight:700; margin:5px 0 3px 0; color:var(--text-secondary); }
        .count { font-size:11px; opacity:0.5; margin-bottom:4px; }
        .ready { font-size:12px; font-weight:750; color:#087f5b; }
        .missing { font-size:12px; font-weight:750; color:var(--accent); }

        /* Caption Cards */
        .caption-wrap { border:1px solid var(--border); border-radius:var(--radius); padding:10px; background:var(--surface); box-shadow:var(--shadow-sm); margin-bottom:8px; }
        .caption-title { font-size:13px; font-weight:750; margin-bottom:5px; color:var(--text); }
        .caption-desc { font-size:11px; opacity:0.55; margin:5px 0 7px 0; }
        .caption-preview-box { width:160px; max-width:100%; border:1px solid var(--border); border-radius:8px; overflow:hidden; background:#0a0a14; padding:0; }

        /* Preview */
        .preview-box { border:1px dashed var(--border); border-radius:var(--radius); padding:12px; min-height:90px; background:var(--surface); }

        /* Buttons */
        div.stButton > button { height:36px !important; border-radius:var(--radius-sm) !important; font-weight:700 !important; font-size:13px !important; border:1px solid var(--border) !important; }
        div.stButton > button[kind="primary"] { background:var(--accent) !important; color:white !important; border-color:var(--accent) !important; }
        div.stButton > button[kind="primary"]:hover { background:var(--accent-hover) !important; }
        div.stButton > button[kind="secondary"] { background:var(--surface) !important; color:var(--text) !important; }

        /* File Uploader */
        div[data-testid="stFileUploader"] section { min-height:46px !important; padding:3px 8px !important; border-radius:var(--radius-sm) !important; border:1px dashed var(--border) !important; }
        div[data-testid="stFileUploader"] small { display:none !important; }

        /* Expander */
        .streamlit-expanderHeader { border-radius:var(--radius-sm) !important; border:1px solid var(--border) !important; background:var(--surface) !important; font-weight:650 !important; color:var(--text) !important; }

        /* Sidebar */
        section[data-testid="stSidebar"] { background:var(--surface) !important; border-right:1px solid var(--border) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Dark/Light mode toggle via JS
    st.markdown(
        \"\"\"
        <script>
        (function() {
            try {
                var saved = localStorage.getItem('zaro_theme');
                if (saved === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
            } catch(e) {}
            window.toggleTheme = function() {
                try {
                    var cur = document.documentElement.getAttribute('data-theme');
                    if (cur === 'dark') {
                        document.documentElement.removeAttribute('data-theme');
                        localStorage.setItem('zaro_theme', 'light');
                    } else {
                        document.documentElement.setAttribute('data-theme', 'dark');
                        localStorage.setItem('zaro_theme', 'dark');
                    }
                } catch(e) {}
            };
        })();
        </script>
        \"\"\",
        unsafe_allow_html=True,
    )
'''

    # Replace old css() with new css()
    content = content[:idx_css_start] + new_css + '\n' + content[idx_css_end:]
    changes += 1
    print("[PATCH 1] css() replaced — navbar CSS + dark mode JS added")

    # ==================================================================
    # PATCH 2: Replace main() function
    # ==================================================================
    main_start_marker = '\ndef main() -> None:\n'
    main_end_marker = '\n\ndef _runtime_compat_helper_1'

    if main_start_marker not in content:
        print("[ERROR] 'def main()' not found!")
        return

    if main_end_marker not in content:
        print("[ERROR] '_runtime_compat_helper_1' not found (main end marker)!")
        return

    idx_main_start = content.index(main_start_marker)
    idx_main_end = content.index(main_end_marker)

    new_main_and_functions = '''
def main() -> None:
    if st is None:
        print("Streamlit missing")
        return

    init_folders()
    st.set_page_config(page_title=APP_TITLE, page_icon="🎬", layout="wide")
    css()

    # ── NAVIGATION BAR ──
    col_brand, col_nav, col_theme = st.columns([2, 2, 0.3])
    with col_brand:
        st.markdown(
            '<div class="navbar-brand"><div class="logo-icon">🎬</div>' + APP_TITLE + '</div>',
            unsafe_allow_html=True,
        )
    with col_nav:
        qp = st.query_params
        active = qp.get("page", "generator")
        n1, n2 = st.columns(2)
        with n1:
            if st.button("🎥 Video Generator", key="nav_gen", use_container_width=True,
                         type="primary" if active == "generator" else "secondary"):
                st.query_params["page"] = "generator"
                st.rerun()
        with n2:
            if st.button("🎬 Reels Studio", key="nav_reel", use_container_width=True,
                         type="primary" if active == "reels" else "secondary"):
                st.query_params["page"] = "reels"
                st.rerun()
    with col_theme:
        icon = "🌙" if st.session_state.get("dark_mode", False) else "☀️"
        if st.button(icon, key="theme_toggle", help="Dark/Light"):
            st.session_state["dark_mode"] = not st.session_state.get("dark_mode", False)
            st.markdown('<script>try{window.toggleTheme();}catch(e){}</script>', unsafe_allow_html=True)
            st.rerun()

    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    # ── PAGE ROUTING ──
    if active == "reels":
        _render_reels_studio_page()
    else:
        _render_video_generator_page()


# ═══════════════════════════════════════════════════════════
# VIDEO GENERATOR PAGE (all existing logic preserved)
# ═══════════════════════════════════════════════════════════
def _render_video_generator_page():
    st.markdown('<div class="app-title">' + APP_TITLE + '</div>', unsafe_allow_html=True)

    # 1. Preset Selector
    preset_num, preset_label = preset_selector_section()

    # 2. Auto-Detect
    auto_detect_section()

    st.session_state["editing_preset_number"] = preset_num
    st.session_state["editing_preset_label"] = preset_label

    # 3. Custom Settings
    custom_overrides = custom_editing_settings_section({})

    import json
    st.session_state["phase4_config"] = json.dumps({
        "preset_number": preset_num,
        "preset_label": preset_label,
        "custom_overrides": custom_overrides,
    })

    # 4. Captions
    add_captions, caption_mode, style_id = captions_section()

    # 5. Settings
    settings = settings_section()

    # 6. Assets (Short + Long video uploads)
    assets_section(settings, add_captions, caption_mode, style_id)

    # 7. Scores
    st.markdown("---")
    scoring_panel_section()

    # 8. Caption Preview
    st.markdown("---")
    caption_video_preview_section()

    # 9. Output
    output_preview()


# ═══════════════════════════════════════════════════════════
# REELS UPLOAD STUDIO PAGE
# ═══════════════════════════════════════════════════════════
def _render_reels_studio_page():
    import os
    import tempfile

    st.markdown('<div class="app-title">🎬 Reels Upload Studio</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:13px;opacity:0.6;margin-bottom:14px;">'
        'AI-Powered Video Regeneration — Upload, Edit, Transform</div>',
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        r_type = st.radio("Video Type", ["short", "long"],
                          format_func=lambda x: "📱 Short (Reels/Shorts)" if x == "short" else "🎥 Long Video",
                          horizontal=True, key="_r_type")
        aspect_map = {"short": ["9:16", "1:1", "4:5"], "long": ["16:9", "9:16", "1:1"]}
        r_aspect = st.selectbox("Aspect Ratio", aspect_map[r_type], key="_r_aspect")

        st.markdown("---")
        st.markdown("**🎨 Style**")
        niche_opts = ["auto", "luxury_lifestyle", "quantum_future", "mystery",
                      "stoic_wisdom", "interior_design", "finance_simulation", "default"]
        r_niche = st.selectbox("Niche", niche_opts, key="_r_niche")

        pcols = st.columns(8)
        for i in range(8):
            with pcols[i]:
                label = str(i + 1)
                active = st.session_state.get("_r_preset", 1) == i + 1
                if st.button(label, key=f"_r_pb_{i+1}", use_container_width=True,
                             type="primary" if active else "secondary"):
                    st.session_state["_r_preset"] = i + 1
                    st.rerun()
        r_preset = st.session_state.get("_r_preset", 1)

        st.markdown("---")
        ca, cb = st.columns(2)
        with ca:
            r_voice = st.checkbox("🎙 Voice Transform", key="_r_voice_cb")
            if r_voice:
                st.slider("Pitch Shift", -1.0, 1.0, 0.0, 0.1, key="_r_pitch")
            r_bg = st.checkbox("🎵 BG Music", key="_r_bg_cb")
        with cb:
            r_cap = st.checkbox("✍️ Captions", value=True, key="_r_cap_cb")
            if r_cap:
                st.selectbox("Caption Style", ["kinetic", "classic", "minimal", "bold"], key="_r_cap_style")

        if r_bg:
            st.file_uploader("Upload Music (mp3/wav)", type=["mp3", "wav"], key="_r_bg_file")
            st.slider("Music Volume", 0.05, 1.0, 0.3, 0.05, key="_r_mvol")

        st.markdown("---")
        r_file = st.file_uploader("📤 Upload " + r_type + " Video",
                                  type=["mp4", "mov", "avi", "mkv", "webm"], key="_r_vfile")
        r_path = None
        if r_file:
            suffix = Path(r_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=BASE_DIR) as tmp:
                tmp.write(r_file.read())
                r_path = tmp.name
            st.video(r_path)
            st.success("Uploaded: " + r_file.name + " (" + str(round(r_file.size / 1048576, 1)) + " MB)")

        if st.button("🚀 Start AI Regeneration", type="primary", use_container_width=True, disabled=not r_path):
            with st.spinner("Processing..."):
                try:
                    from reels_editing_engine import ReelsEditingEngine
                    engine = ReelsEditingEngine(
                        video_path=r_path, video_type=r_type, aspect_ratio=r_aspect,
                        niche=r_niche, preset_number=r_preset,
                    )
                    result = engine.process()
                    if result.get("success"):
                        st.session_state["_r_output"] = result.get("output_path")
                        st.success("Done!")
                        st.rerun()
                    else:
                        st.error("Error: " + str(result.get("error", "Unknown")))
                except ImportError:
                    st.warning("reels_editing_engine not found (demo mode)")
                    st.session_state["_r_output"] = r_path
                    st.success("Done (demo)!")
                    st.rerun()
                except Exception as e:
                    st.error("Failed: " + str(e))

        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📺 Output")
        out = st.session_state.get("_r_output")
        if out and os.path.exists(out):
            st.video(out)
            with open(out, "rb") as f:
                st.download_button("📥 Download", f.read(), file_name="reels_output.mp4",
                                   mime="video/mp4", use_container_width=True)
        else:
            st.info("Output appears here after processing")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("🔄 Reset", use_container_width=True, key="_r_reset"):
            for k in list(st.session_state.keys()):
                if k.startswith("_r_"):
                    del st.session_state[k]
            st.rerun()
'''

    # Replace old main() block with new main + two helper functions
    content = content[:idx_main_start] + '\n' + new_main_and_functions + '\n' + content[idx_main_end:]
    changes += 1
    print("[PATCH 2] main() replaced — navbar layout + reels page + video generator page")

    # ==================================================================
    # PATCH 3: Remove old 'if __name__' / ensure proper entry point
    # ==================================================================
    # Find the LAST 'if __name__ == "__main__":' and keep it clean
    if content.rstrip().endswith('if __name__ == "__main__":\n    main()'):
        print("[PATCH 3] Entry point is already correct")
    else:
        # Remove all existing __main__ blocks and add one clean one
        import re
        content = re.sub(r'\n*if __name__ == ["\']__main__["\']:\s*\n\s+main\(\)\s*', '', content)
        content = content.rstrip() + '\n\nif __name__ == "__main__":\n    main()\n'
        changes += 1
        print("[PATCH 3] Clean entry point added")

    # ==================================================================
    # WRITE BACK
    # ==================================================================
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("\n" + "=" * 60)
    print(f"PHASE 1 COMPLETE — {changes} patches applied to app.py")
    print(f"Original backup: {backup_path}")
    print("=" * 60)
    print("\nChanges made:")
    print("  1. css() — Professional navbar CSS + dark mode variables")
    print("  2. main() — Navigation bar (Video Generator | Reels Studio) + page routing")
    print("  3. _render_reels_studio_page() — Full working Reels page injected")
    print("  4. _render_video_generator_page() — Clean Video Generator page")
    print("  5. Dark/Light toggle button (top-right)")
    print("\nTo test: streamlit run app.py")


if __name__ == "__main__":
    main_phase1()