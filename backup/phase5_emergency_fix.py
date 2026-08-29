"""
============================================================================
PHASE 5 EMERGENCY FIX — SyntaxError: '(' was never closed
============================================================================
The Phase 5 css() replacement broke the file because of:
  1. Multi-line string quoting issues with triple quotes inside triple quotes
  2. The JS <script> block inside st.markdown uses \"\"\" which conflicts

THIS SCRIPT: Reads the current broken app.py, finds the broken css() function,
and surgically replaces it with a FIXED version using raw string r\"\"\"
to avoid any quoting conflicts.

USAGE:
  cd "D:\My Creation Video Generator\backup"
  python phase5_emergency_fix.py
  streamlit run app.py
============================================================================
"""
import os
import re

BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))


def main_emergency():
    app_path = os.path.join(BACKUP_DIR, 'app.py')

    with open(app_path, 'r', encoding='utf-8') as f:
        original = f.read()

    backup_path = app_path + '.backup_emergency'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original)
    print(f"[OK] Backup: {backup_path}")
    print(f"[INFO] {len(original.split(chr(10)))} lines")

    # Print lines around line 957 to see the issue
    lines = original.split('\n')
    print(f"\n[DEBUG] Lines 950-970:")
    for i in range(max(0, 948), min(len(lines), 972)):
        marker = ">>>" if i == 956 else "   "
        print(f"  {marker} L{i+1}: {lines[i][:100]}")

    content = original

    # Find all 'def css()' — there might be duplicates from overlapping patches
    css_occurrences = [m.start() for m in re.finditer(r'def css\(\) -> None:', content)]
    print(f"\n[DEBUG] Found {len(css_occurrences)} css() definitions")

    if len(css_occurrences) == 0:
        print("[ERROR] No css() function found!")
        return

    # ==================================================================
    # STRATEGY: Remove ALL css() definitions and inject ONE clean one
    # ==================================================================
    # First, remove the last (newest/broken) css() that Phase 5 injected
    # Keep the original one from Phase 1 as base, then replace it

    # Find the Phase 1 css() — it should be the first one
    first_css = css_occurrences[0]
    # Find the Phase 5 css() — it's the last one  
    last_css = css_occurrences[-1]

    # Remove ALL css functions except the first one
    # Find the first css() end — next function after it
    after_first = content[first_css:]
    next_func_after_first = re.search(r'\n(def |# ={10,})', after_first[20:])
    if next_func_after_first:
        first_css_end = first_css + 20 + next_func_after_first.start()
    else:
        print("[ERROR] Cannot find end of first css()")
        return

    # Find the last css() end
    after_last = content[last_css:]
    next_func_after_last = re.search(r'\n(def |# ={10,}|# PHASE)', after_last[20:])
    if next_func_after_last:
        last_css_end = last_css + 20 + next_func_after_last.start()
    else:
        print("[ERROR] Cannot find end of last css()")
        return

    # Remove everything between first_css_end and last_css_end (the broken duplicate + extras)
    # Actually, simpler approach: replace the FIRST css() entirely
    # Keep everything before first_css, add new css, skip everything between
    before = content[:first_css]
    after = content[last_css_end:]

    # The PREMIUM css function — using proper Python quoting with r-string
    new_css = r'''
def css() -> None:
    """Phase 5: Premium Minimal UI — Soft Light + Dark Mode."""
    st.markdown(
        """
        <style>
        /* === LIGHT MODE (DEFAULT) === */
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
        }

        /* === DARK MODE === */
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
        }

        /* === GLOBAL === */
        .stApp { background: var(--bg) !important; }
        .block-container { padding: 0.5rem 1.5rem 1.5rem 1.5rem !important; max-width: 1240px !important; }
        header[data-testid="stHeader"] { background: transparent !important; }
        #MainMenu, footer, .stDeployButton { visibility: hidden !important; display: none !important; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
        hr { border-color: var(--border) !important; margin: 8px 0 !important; opacity: 0.5 !important; }

        /* === TYPOGRAPHY === */
        .app-title { font-size: 28px; font-weight: 800; letter-spacing: -0.6px; margin-bottom: 6px; color: var(--text-primary); }
        .section-title { font-size: 16px; font-weight: 700; margin: 16px 0 8px 0; color: var(--text-primary); }

        /* === CARDS === */
        .card { border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; background: var(--surface); box-shadow: var(--shadow-sm); margin-bottom: 10px; transition: box-shadow var(--transition); }
        .card:hover { box-shadow: var(--shadow-md); }
        .asset-title { font-size: 15px; font-weight: 700; margin: 2px 0 8px 0; color: var(--text-primary); }
        .asset-label { font-size: 12px; font-weight: 600; margin: 6px 0 4px 0; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.3px; }
        .count { font-size: 11px; color: var(--text-tertiary); margin-bottom: 4px; }
        .ready { font-size: 12px; font-weight: 700; color: var(--green); padding: 4px 10px; background: var(--green-light); border-radius: 20px; display: inline-block; }
        .missing { font-size: 12px; font-weight: 700; color: var(--red); padding: 4px 10px; background: var(--red-light); border-radius: 20px; display: inline-block; }

        /* === CAPTION CARDS === */
        .caption-wrap { border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; background: var(--surface); box-shadow: var(--shadow-xs); margin-bottom: 10px; transition: all var(--transition); }
        .caption-wrap:hover { border-color: var(--border-light); box-shadow: var(--shadow-sm); }
        .caption-title { font-size: 13px; font-weight: 700; margin-bottom: 6px; color: var(--text-primary); }
        .caption-desc { font-size: 11px; color: var(--text-tertiary); margin: 6px 0 8px 0; line-height: 1.4; }
        .caption-preview-box { width: 150px; max-width: 100%; border: 1px solid var(--border); border-radius: var(--radius-xs); overflow: hidden; background: #0a0a18; padding: 0; box-shadow: var(--shadow-sm); }

        /* === PREVIEW === */
        .preview-box { border: 1px dashed var(--border); border-radius: var(--radius); padding: 16px; min-height: 100px; background: var(--surface); transition: border-color var(--transition); }
        .preview-box:hover { border-color: var(--accent); }

        /* === BUTTONS === */
        div.stButton > button { height: 38px !important; border-radius: var(--radius-sm) !important; font-weight: 600 !important; font-size: 13px !important; transition: all var(--transition) !important; border: 1px solid var(--border) !important; }
        div.stButton > button[kind="primary"] { background: var(--accent) !important; color: #ffffff !important; border-color: var(--accent) !important; box-shadow: 0 2px 8px rgba(230,57,70,0.25) !important; }
        div.stButton > button[kind="primary"]:hover { background: var(--accent-hover) !important; transform: translateY(-1px); box-shadow: 0 4px 14px rgba(230,57,70,0.35) !important; }
        div.stButton > button[kind="secondary"] { background: var(--surface) !important; color: var(--text) !important; }
        div.stButton > button[kind="secondary"]:hover { background: var(--surface-hover) !important; border-color: var(--accent) !important; color: var(--accent) !important; }

        /* === FILE UPLOADER === */
        div[data-testid="stFileUploader"] section { min-height: 48px !important; padding: 6px 10px !important; border-radius: var(--radius-sm) !important; border: 2px dashed var(--border) !important; background: var(--bg-alt) !important; transition: all var(--transition) !important; }
        div[data-testid="stFileUploader"] section:hover { border-color: var(--accent) !important; background: var(--accent-light) !important; }
        div[data-testid="stFileUploader"] small { display: none !important; }

        /* === EXPANDER === */
        .streamlit-expanderHeader { border-radius: var(--radius-sm) !important; border: 1px solid var(--border) !important; background: var(--surface) !important; font-weight: 650 !important; font-size: 14px !important; color: var(--text-primary) !important; padding: 12px 16px !important; transition: all var(--transition) !important; }
        .streamlit-expanderHeader:hover { border-color: var(--accent) !important; background: var(--surface-hover) !important; }
        .streamlit-expanderContent { border: 1px solid var(--border) !important; border-top: none !important; border-radius: 0 0 var(--radius-sm) var(--radius-sm) !important; background: var(--surface) !important; padding: 12px !important; }

        /* === SIDEBAR === */
        section[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border) !important; }

        /* === FORM ELEMENTS === */
        div[data-testid="stSelectbox"] label, div[data-testid="stRadio"] label { color: var(--text-secondary) !important; font-size: 12px !important; font-weight: 600 !important; }
        div[data-testid="stCheckbox"] label { color: var(--text) !important; font-size: 13px !important; }
        div[data-testid="stSlider"] > div > div > div > div { background: var(--accent) !important; }

        /* === STATUS BOXES === */
        div[data-testid="stSuccess"] { background: var(--green-light) !important; border: 1px solid var(--green) !important; border-radius: var(--radius-sm) !important; color: var(--green) !important; }
        div[data-testid="stError"] { background: var(--red-light) !important; border: 1px solid var(--red) !important; border-radius: var(--radius-sm) !important; color: var(--red) !important; }
        div[data-testid="stWarning"] { background: var(--amber-light) !important; border: 1px solid var(--amber) !important; border-radius: var(--radius-sm) !important; color: var(--amber) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <script>
        (function(){
            try {
                var s = localStorage.getItem('zaro_theme_v2');
                if (s === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
            } catch(e) {}
            window.toggleThemeV2 = function() {
                try {
                    var c = document.documentElement.getAttribute('data-theme');
                    if (c === 'dark') {
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
        """,
        unsafe_allow_html=True,
    )
'''

    # Rebuild: before[0:first_css] + new_css + after[last_css_end:]
    content = before + new_css + '\n' + after

    patches = 1
    print("[PATCH 1] css() — fully replaced with clean premium CSS (no quoting issues)")

    # ==================================================================
    # PATCH 2: Fix theme toggle JS function name in main()
    # ==================================================================
    # The main() function references toggleTheme or toggleThemeV2
    # Make sure all theme toggles use the SAME function name: toggleThemeV2
    old_toggle1 = 'window.toggleTheme();'
    new_toggle1 = 'window.toggleThemeV2();'

    if old_toggle1 in content:
        content = content.replace(old_toggle1, new_toggle1)
        patches += 1
        print("[PATCH 2] Theme toggle function name unified to toggleThemeV2")

    # Also fix the hidden st.markdown call for toggle
    old_hidden_toggle = "st.markdown('<script>try{window.toggleTheme();}catch(e){}</script>'"
    new_hidden_toggle = "st.markdown('<script>try{window.toggleThemeV2();}catch(e){}</script>'"
    if old_hidden_toggle in content:
        content = content.replace(old_hidden_toggle, new_hidden_toggle)
        patches += 1
        print("[PATCH 2b] Hidden toggle script updated")

    # ==================================================================
    # FINAL: Validate no SyntaxError
    # ==================================================================
    try:
        compile(content, app_path, 'exec')
        print("\n[OK] Python syntax check PASSED — no SyntaxError!")
    except SyntaxError as e:
        print(f"\n[ERROR] SyntaxError still present: {e}")
        # Show the problematic line
        lines2 = content.split('\n')
        if e.lineno:
            lo = max(0, e.lineno - 3)
            hi = min(len(lines2), e.lineno + 3)
            print(f"\nLines {lo+1}-{hi}:")
            for i in range(lo, hi):
                marker = ">>>" if i == e.lineno - 1 else "   "
                print(f"  {marker} L{i+1}: {lines2[i][:120]}")
        return

    # ==================================================================
    # WRITE
    # ==================================================================
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)

    new_lines = len(content.split('\n'))
    print(f"\n{'='*60}")
    print(f"PHASE 5 EMERGENCY FIX — COMPLETE ({patches} patches, {new_lines} lines)")
    print(f"Backup: {backup_path}")
    print(f"{'='*60}")
    print("\nTest: streamlit run app.py")
    print("Should now load without SyntaxError!")


if __name__ == "__main__":
    main_emergency()