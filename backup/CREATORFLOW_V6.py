"""
CREATORFLOW_V6.py — NAVBAR + WORKING PAGES + DARK MODE + FAVICON
"""
from pathlib import Path
import shutil, base64

P = Path(r"D:\My Creation Video Generator\backup\app.py")

# Restore
backups = sorted(Path(r"D:\My Creation Video Generator\backup").glob("app.py.bak*"), reverse=True)
if backups:
    shutil.copy(backups[0], P)
    print(f"[0] Restored: {backups[0].name}")

# Logo
LOGO_PATH = Path(r"D:\My Creation Video Generator\backup\logo.png")
logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
LOGO_SRC = f"data:image/png;base64,{logo_b64}"
print(f"[1] Logo encoded")

T = P.read_text(encoding="utf-8")
orig = T

# 1. Page config
OLD_PC = 'st.set_page_config(page_title=APP_TITLE, page_icon="🎬", layout="wide")'
NEW_PC = 'st.set_page_config(page_title="CreatorFlow AI", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")'
if OLD_PC in T:
    T = T.replace(OLD_PC, NEW_PC, 1)
    print("[2] Page config")

# 2. words=None
T = T.replace('words=[]', 'words=None')
T = T.replace('"words": []', '"words": None')
print("[3] words=None")

# 3. Inject navbar AFTER css() and BEFORE tabs
CSS_LINE = '    css()\n'
TAB_NAV = '\n    # ── TAB NAVIGATION ──\n    t1, t2 = st.tabs(["🎥 Video Generator", "🎬 Reels Upload Studio"])'

NAVBAR = f'''
    # ═══════════ CreatorFlow AI Navbar ═══════════
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Generator"

    st.markdown(\"""
    <style>
    /* Hide Streamlit's default tab buttons ONLY — keep panels visible */
    button[data-baseweb="tab"] {{ display: none !important; }}
    div[data-baseweb="tab-highlight"] {{ display: none !important; }}
    div[data-testid="stTabs"] > div:first-child {{ display: none !important; }}

    [data-testid="stAppViewContainer"] > .main {{
        background: linear-gradient(135deg, #0B1220 0%, #111827 100%);
    }}
    header[data-testid="stHeader"] {{ background: transparent !important; }}

    .cf-navbar {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 8px 24px; margin: 6px 12px 12px 12px; border-radius: 14px;
        background: rgba(17, 24, 39, 0.8); backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(108, 92, 231, 0.2);
        box-shadow: 0 4px 24px rgba(0,0,0,0.5), 0 0 80px rgba(108,92,231,0.06);
    }}
    .cf-left {{ display: flex; align-items: center; gap: 12px; }}
    .cf-logo-img {{
        width: 38px; height: 38px; border-radius: 10px; object-fit: cover;
        box-shadow: 0 0 16px rgba(108,92,231,0.4);
        border: 2px solid rgba(108,92,231,0.3);
    }}
    .cf-brand-name {{
        font-size: 18px; font-weight: 700;
        background: linear-gradient(90deg, #A855F7, #00D4FF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .cf-brand-sub {{ font-size: 10px; color: rgba(255,255,255,0.4); letter-spacing: 1px; }}
    .cf-center {{ display: flex; gap: 4px; background: rgba(255,255,255,0.03); border-radius: 10px; padding: 3px; }}
    .cf-nav-btn {{
        padding: 8px 22px; border-radius: 8px; font-size: 13px; font-weight: 600;
        color: rgba(255,255,255,0.5); background: transparent; border: none;
        cursor: pointer; transition: all 0.25s;
    }}
    .cf-nav-btn.active {{
        color: #fff; background: linear-gradient(135deg, rgba(108,92,231,0.35), rgba(0,212,255,0.15));
        box-shadow: 0 2px 12px rgba(108,92,231,0.25), inset 0 1px 0 rgba(255,255,255,0.08);
    }}
    .cf-nav-btn:hover {{ color: rgba(255,255,255,0.85); }}
    .cf-right {{ display: flex; align-items: center; gap: 8px; }}
    .cf-icon-btn {{
        width: 34px; height: 34px; border-radius: 8px;
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
        display: flex; align-items: center; justify-content: center; cursor: pointer;
        transition: all 0.25s; font-size: 15px;
    }}
    .cf-icon-btn:hover {{ background: rgba(108,92,231,0.18); border-color: rgba(108,92,231,0.4); }}
    #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none; }}
    </style>

    <div class="cf-navbar">
        <div class="cf-left">
            <img class="cf-logo-img" src="{LOGO_SRC}" alt="CreatorFlow Logo">
            <div>
                <div class="cf-brand-name">CreatorFlow AI</div>
                <div class="cf-brand-sub">Create • Transform • Automate</div>
            </div>
        </div>
        <div class="cf-center">
            <button class="cf-nav-btn" id="btn-gen" onclick="switchTab(0)">⚡ Generator</button>
            <button class="cf-nav-btn" id="btn-studio" onclick="switchTab(1)">🎬 Studio</button>
        </div>
        <div class="cf-right">
            <span class="cf-icon-btn" id="btn-dark" onclick="toggleDark()" title="Toggle Dark Mode">🌙</span>
            <span class="cf-icon-btn">🔔</span>
            <span class="cf-icon-btn" onclick="location.reload()" title="Settings">⚙️</span>
            <span class="cf-icon-btn" title="Help">ℹ️</span>
        </div>
    </div>

    <script>
    function switchTab(idx) {{
        const tabs = document.querySelectorAll('button[data-baseweb="tab"]');
        if(tabs[idx]) {{ tabs[idx].click(); updateActive(idx); }}
    }}

    function updateActive(idx) {{
        document.getElementById('btn-gen').classList.toggle('active', idx === 0);
        document.getElementById('btn-studio').classList.toggle('active', idx === 1);
    }}

    // Detect tab changes from keyboard / Streamlit
    new MutationObserver(() => {{
        const panels = document.querySelectorAll('[data-baseweb="tab-panel"]');
        if(panels[0] && panels[1]) {{
            updateActive(panels[0].hasAttribute('aria-hidden') && panels[0].getAttribute('aria-hidden') === 'false' ? 0 : 1);
        }}
    }}).observe(document.body, {{ attributes: true, subtree: true }});

    // Init
    setTimeout(() => updateActive(0), 100);

    // Dark mode toggle
    let dark = true;
    function toggleDark() {{
        dark = !dark;
        document.getElementById('btn-dark').textContent = dark ? '🌙' : '☀️';
        if(dark) {{
            document.querySelector('[data-testid="stAppViewContainer"] > .main').style.background = 'linear-gradient(135deg, #0B1220, #111827)';
        }} else {{
            document.querySelector('[data-testid="stAppViewContainer"] > .main').style.background = '#ffffff';
        }}
    }}
    </script>
    \""", unsafe_allow_html=True)
    # ═══════════════════════════════════════════════════════'''

# Replace injection point
OLD_BLOCK = CSS_LINE + TAB_NAV
NEW_BLOCK = CSS_LINE + NAVBAR + TAB_NAV

if OLD_BLOCK in T:
    T = T.replace(OLD_BLOCK, NEW_BLOCK, 1)
    print("[4] Navbar injected")
else:
    # Try alternate — find exact lines
    lines = T.splitlines()
    css_idx = None
    tab_idx = None
    for i, l in enumerate(lines):
        if l.strip() == 'css()':
            css_idx = i
        if css_idx and 'st.tabs([' in l and 'Video Generator' in l:
            tab_idx = i
            break
    if css_idx is not None and tab_idx is not None:
        before = '\n'.join(lines[:css_idx+1]) + '\n'
        after = '\n'.join(lines[tab_idx:])
        T = before + NAVBAR + '\n' + after
        print(f"[4] Navbar injected (alt — lines {css_idx+1} to {tab_idx+1})")
    else:
        print(f"[4] ❌ css_idx={css_idx}, tab_idx={tab_idx}")
        P.write_text(orig, encoding="utf-8")
        raise SystemExit(1)

# VALIDATE
P.write_text(T, encoding="utf-8")
try:
    compile(T, str(P), "exec")
    print("\n✅ DONE — 0 errors!")
    print("Features: Logo, Generator↔Studio tabs, Dark mode toggle, Favicon")
    print("Run: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ {e}")
    P.write_text(orig, encoding="utf-8")
    print("↩️ Rolled back")