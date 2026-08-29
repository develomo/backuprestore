"""
============================================================================
PHASE 5 PATCH — Premium Minimal UI + Dark/Light Mode Toggle + Soft Colors
============================================================================
AUTO-PATCH: Refines the CSS in app.py for:
  1. Premium soft light color palette (no dark by default)
  2. Smooth dark mode toggle (persisted in localStorage)
  3. Professional spacing, typography, shadows, transitions
  4. Clean minimal look with luxury feel
  5. Both pages (Generator + Reels) share the same premium theme

COLOR PALETTE:
  Light:   bg=#f5f6f8  surface=#ffffff  accent=#e63946  text=#1a1a2e
  Dark:    bg=#0f0f1a  surface=#1a1a2e  accent=#ff4d5a  text=#e8e8f0
============================================================================
"""
import os

BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))


def main_phase5():
    app_path = os.path.join(BACKUP_DIR, 'app.py')

    with open(app_path, 'r', encoding='utf-8') as f:
        original = f.read()

    backup_path = app_path + '.backup_phase5'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original)
    print(f"[OK] Backup: {backup_path}")
    print(f"[INFO] {len(original.split(chr(10)))} lines")

    content = original
    patches = 0

    # ==================================================================
    # PATCH 1: Replace the ENTIRE css() function with premium version
    # ==================================================================
    old_css_start = 'def css() -> None:'
    if old_css_start not in content:
        print("[ERROR] css() not found!")
        return

    idx_css = content.index(old_css_start)
    after_css = content[idx_css:]

    # Find where css() ends — next top-level def
    import re
    next_def = re.search(r'\n(def |# ={10,})', after_css[20:])
    if next_def:
        css_end_offset = 20 + next_def.start()
    else:
        print("[ERROR] Cannot find end of css()")
        return

    premium_css = '''def css() -> None:
    """
    PHASE 5: Premium Minimal UI — Soft Light + Dark Mode
    Color palette: Warm neutral light, rich dark, refined accent
    """
    st.markdown(
        """
        <style>
        /* ═════════════════════════════════════════
           CSS CUSTOM PROPERTIES (Light Default)
           ═════════════════════════════════════════ */
        :root {
            --bg: #f5f6f8;
            --bg-alt: #edeff3;
            --surface: #ffffff;
            --surface-hover: #f9fafb;
            --border: #e0e3e8;
            --border-light: #ebeef2;
            --text: #1a1a2e;
            --text-primary: #111122;
            --text-secondary: #6b7280;
            --text-tertiary: #9ca3af;
            --accent: #e63946;
            --accent-hover: #c1121f;
            --accent-light: #fef2f3;
            --accent-soft: #fce4e6;
            --green: #059669;
            --green-light: #ecfdf5;
            --amber: #d97706;
            --amber-light: #fffbeb;
            --red: #dc2626;
            --red-light: #fef2f2;
            --shadow-xs: 0 1px 2px rgba(0,0,0,0.03);
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
            --shadow-lg: 0 8px 24px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.04);
            --radius-xs: 6px;
            --radius-sm: 8px;
            --radius: 12px;
            --radius-lg: 16px;
            --transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        /* ═════════════════════════════════════════
           DARK MODE
           ═════════════════════════════════════════ */
        [data-theme="dark"] {
            --bg: #0b0b18;
            --bg-alt: #12122a;
            --surface: #181835;
            --surface-hover: #1e1e40;
            --border: #2a2a4a;
            --border-light: #222244;
            --text: #e8e8f5;
            --text-primary: #f0f0ff;
            --text-secondary: #9a9ab8;
            --text-tertiary: #6a6a88;
            --accent: #ff4d5a;
            --accent-hover: #ff6b6b;
            --accent-light: rgba(255,77,90,0.12);
            --accent-soft: rgba(255,77,90,0.08);
            --green: #34d399;
            --green-light: rgba(52,211,153,0.12);
            --amber: #fbbf24;
            --amber-light: rgba(251,191,36,0.12);
            --red: #f87171;
            --red-light: rgba(248,113,113,0.12);
            --shadow-xs: 0 1px 2px rgba(0,0,0,0.2);
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.4), 0 1px 3px rgba(0,0,0,0.3);
            --shadow-lg: 0 8px 24px rgba(0,0,0,0.5), 0 2px 6px rgba(0,0,0,0.3);
        }

        /* ═════════════════════════════════════════
           GLOBAL RESET
           ═════════════════════════════════════════ */
        .stApp {
            background: var(--bg) !important;
            font-family: var(--font-sans) !important;
        }
        .block-container {
            padding: 0.5rem 1.5rem 1.5rem 1.5rem !important;
            max-width: 1240px !important;
        }
        header[data-testid="stHeader"] {
            background: transparent !important;
            backdrop-filter: none !important;
        }
        #MainMenu, footer, .stDeployButton {
            visibility: hidden !important;
            display: none !important;
        }

        /* ═════════════════════════════════════════
           SCROLLBAR
           ═════════════════════════════════════════ */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-tertiary); }

        /* ═════════════════════════════════════════
           TYPOGRAPHY
           ═════════════════════════════════════════ */
        .app-title {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.6px;
            margin-bottom: 6px;
            color: var(--text-primary);
            line-height: 1.2;
        }
        .section-title {
            font-size: 16px;
            font-weight: 700;
            margin: 16px 0 8px 0;
            color: var(--text-primary);
            letter-spacing: -0.2px;
        }
        .section-subtitle {
            font-size: 13px;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 10px;
        }

        /* ═════════════════════════════════════════
           CARDS
           ═════════════════════════════════════════ */
        .card {
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 16px;
            background: var(--surface);
            box-shadow: var(--shadow-sm);
            margin-bottom: 10px;
            transition: box-shadow var(--transition);
        }
        .card:hover { box-shadow: var(--shadow-md); }
        .asset-title {
            font-size: 15px;
            font-weight: 700;
            margin: 2px 0 8px 0;
            color: var(--text-primary);
        }
        .asset-label {
            font-size: 12px;
            font-weight: 600;
            margin: 6px 0 4px 0;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .count {
            font-size: 11px;
            color: var(--text-tertiary);
            margin-bottom: 4px;
        }
        .ready {
            font-size: 12px;
            font-weight: 700;
            color: var(--green);
            padding: 4px 10px;
            background: var(--green-light);
            border-radius: 20px;
            display: inline-block;
        }
        .missing {
            font-size: 12px;
            font-weight: 700;
            color: var(--red);
            padding: 4px 10px;
            background: var(--red-light);
            border-radius: 20px;
            display: inline-block;
        }

        /* ═════════════════════════════════════════
           CAPTION CARDS
           ═════════════════════════════════════════ */
        .caption-wrap {
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 14px;
            background: var(--surface);
            box-shadow: var(--shadow-xs);
            margin-bottom: 10px;
            transition: all var(--transition);
        }
        .caption-wrap:hover { border-color: var(--border-light); box-shadow: var(--shadow-sm); }
        .caption-title {
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 6px;
            color: var(--text-primary);
        }
        .caption-desc {
            font-size: 11px;
            color: var(--text-tertiary);
            margin: 6px 0 8px 0;
            line-height: 1.4;
        }
        .caption-preview-box {
            width: 150px;
            max-width: 100%;
            border: 1px solid var(--border);
            border-radius: var(--radius-xs);
            overflow: hidden;
            background: #0a0a18;
            padding: 0;
            box-shadow: var(--shadow-sm);
        }

        /* ═════════════════════════════════════════
           PREVIEW BOX
           ═════════════════════════════════════════ */
        .preview-box {
            border: 1px dashed var(--border);
            border-radius: var(--radius);
            padding: 16px;
            min-height: 100px;
            background: var(--surface);
            transition: border-color var(--transition);
        }
        .preview-box:hover { border-color: var(--accent); }

        /* ═════════════════════════════════════════
           BUTTONS
           ═════════════════════════════════════════ */
        div.stButton > button {
            height: 38px !important;
            border-radius: var(--radius-sm) !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            letter-spacing: -0.1px !important;
            transition: all var(--transition) !important;
            border: 1px solid var(--border) !important;
            padding: 0 16px !important;
            line-height: 38px !important;
        }
        div.stButton > button[kind="primary"] {
            background: var(--accent) !important;
            color: #ffffff !important;
            border-color: var(--accent) !important;
            box-shadow: 0 2px 8px rgba(230,57,70,0.25) !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background: var(--accent-hover) !important;
            border-color: var(--accent-hover) !important;
            box-shadow: 0 4px 14px rgba(230,57,70,0.35) !important;
            transform: translateY(-1px);
        }
        div.stButton > button[kind="secondary"] {
            background: var(--surface) !important;
            color: var(--text) !important;
        }
        div.stButton > button[kind="secondary"]:hover {
            background: var(--surface-hover) !important;
            border-color: var(--accent) !important;
            color: var(--accent) !important;
        }

        /* ═════════════════════════════════════════
           FILE UPLOADER
           ═════════════════════════════════════════ */
        div[data-testid="stFileUploader"] section {
            min-height: 48px !important;
            padding: 6px 10px !important;
            border-radius: var(--radius-sm) !important;
            border: 2px dashed var(--border) !important;
            background: var(--bg-alt) !important;
            transition: all var(--transition) !important;
        }
        div[data-testid="stFileUploader"] section:hover {
            border-color: var(--accent) !important;
            background: var(--accent-light) !important;
        }
        div[data-testid="stFileUploader"] small { display: none !important; }

        /* ═════════════════════════════════════════
           EXPANDER
           ═════════════════════════════════════════ */
        .streamlit-expanderHeader {
            border-radius: var(--radius-sm) !important;
            border: 1px solid var(--border) !important;
            background: var(--surface) !important;
            font-weight: 650 !important;
            font-size: 14px !important;
            color: var(--text-primary) !important;
            padding: 12px 16px !important;
            transition: all var(--transition) !important;
        }
        .streamlit-expanderHeader:hover {
            border-color: var(--accent) !important;
            background: var(--surface-hover) !important;
        }
        .streamlit-expanderContent {
            border: 1px solid var(--border) !important;
            border-top: none !important;
            border-radius: 0 0 var(--radius-sm) var(--radius-sm) !important;
            background: var(--surface) !important;
            padding: 12px !important;
        }

        /* ═════════════════════════════════════════
           SIDEBAR (if used)
           ═════════════════════════════════════════ */
        section[data-testid="stSidebar"] {
            background: var(--surface) !important;
            border-right: 1px solid var(--border) !important;
            box-shadow: var(--shadow-sm) !important;
        }

        /* ═════════════════════════════════════════
           SELECT / RADIO / CHECKBOX
           ═════════════════════════════════════════ */
        div[data-testid="stSelectbox"] label,
        div[data-testid="stRadio"] label {
            color: var(--text-secondary) !important;
            font-size: 12px !important;
            font-weight: 600 !important;
        }
        div[data-testid="stCheckbox"] label {
            color: var(--text) !important;
            font-size: 13px !important;
        }
        div[data-testid="stCheckbox"] label span {
            color: var(--text) !important;
        }

        /* ═════════════════════════════════════════
           SLIDER
           ═════════════════════════════════════════ */
        div[data-testid="stSlider"] > div > div > div > div {
            background: var(--accent) !important;
        }

        /* ═════════════════════════════════════════
           SUCCESS / ERROR / INFO BOXES
           ═════════════════════════════════════════ */
        div[data-testid="stSuccess"] {
            background: var(--green-light) !important;
            border: 1px solid var(--green) !important;
            border-radius: var(--radius-sm) !important;
            color: var(--green) !important;
        }
        div[data-testid="stError"] {
            background: var(--red-light) !important;
            border: 1px solid var(--red) !important;
            border-radius: var(--radius-sm) !important;
            color: var(--red) !important;
        }
        div[data-testid="stWarning"] {
            background: var(--amber-light) !important;
            border: 1px solid var(--amber) !important;
            border-radius: var(--radius-sm) !important;
            color: var(--amber) !important;
        }

        /* ═════════════════════════════════════════
           DIVIDERS
           ═════════════════════════════════════════ */
        hr {
            border-color: var(--border) !important;
            margin: 8px 0 !important;
            opacity: 0.5 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Dark/Light mode JS (persisted in localStorage)
    st.markdown(
        \"\"\"
        <script>
        (function(){
            try {
                var saved = localStorage.getItem('zaro_theme_v2');
                if (saved === 'dark') {
                    document.documentElement.setAttribute('data-theme', 'dark');
                }
            } catch(e) {}
            window.toggleThemeV2 = function() {
                try {
                    var cur = document.documentElement.getAttribute('data-theme');
                    if (cur === 'dark') {
                        document.documentElement.removeAttribute('data-theme');
                        localStorage.setItem('zaro_theme_v2', 'light');
                    } else {
                        document.documentElement.setAttribute('data-theme', 'dark');
                        localStorage.setItem('zaro_theme_v2', 'dark');
                    }
                } catch(e) {}
            };
        })();
        </script>
        \"\"\",
        unsafe_allow_html=True,
    )
'''

    content = content[:idx_css] + premium_css + '\n' + content[idx_css + css_end_offset:]
    patches += 1
    print("[PATCH 1] css() — premium CSS with refined palette, shadows, transitions")

    # ==================================================================
    # PATCH 2: Update theme toggle to use v2 JS function
    # ==================================================================
    old_toggle = "window.toggleTheme();"
    new_toggle = "window.toggleThemeV2();"
    if old_toggle in content:
        content = content.replace(old_toggle, new_toggle)
        # Also replace in the dark_mode toggle button
        content = content.replace('st.markdown(\'<script>try{window.toggleTheme();}catch(e){}</script>\'', 
                                   'st.markdown(\'<script>try{window.toggleThemeV2();}catch(e){}</script>\'')
        patches += 1
        print("[PATCH 2] Theme toggle updated to use v2 JS function")

    # ==================================================================
    # WRITE
    # ==================================================================
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)

    new_lines = len(content.split('\n'))
    print(f"\n{'='*60}")
    print(f"PHASE 5 — COMPLETE ({patches} patches, {new_lines} lines)")
    print(f"Backup: {backup_path}")
    print(f"{'='*60}")
    print("\nPREMIUM UI FEATURES:")
    print("  🎨 Soft light palette: #f5f6f8 bg, #ffffff cards, #e63946 accent")
    print("  🌙 Dark mode: #0b0b18 bg, #181835 cards, #ff4d5a accent")
    print("  ✨ Professional shadows, smooth transitions, refined typography")
    print("  🎯 Hover effects: buttons lift, borders glow, cards elevate")
    print("  📦 Consistent spacing & border-radius throughout")
    print("  💾 Dark mode preference saved in localStorage")
    print("\nTest: streamlit run app.py")
    print("      Toggle ☀️ / 🌙 top-right to switch themes")


if __name__ == "__main__":
    main_phase5()