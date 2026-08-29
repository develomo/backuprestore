"""
CREATORFLOW_V7.py — FIX: Tabs content visible + working navbar
"""
from pathlib import Path
import shutil, base64

P = Path(r"D:\My Creation Video Generator\backup\app.py")

# Restore from clean backup
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

# 3. Inject navbar
CSS_LINE = '    css()\n'
TAB_NAV = '\n    # ── TAB NAVIGATION ──\n    t1, t2 = st.tabs(["🎥 Video Generator", "🎬 Reels Upload Studio"])'

NAVBAR = f'''
    # ═══════════ CreatorFlow AI Navbar ═══════════
    st.markdown(\"""<style>
    [data-testid="stAppViewContainer"] > .main {{ background: linear-gradient(135deg, #0B1220, #111827); }}
    header[data-testid="stHeader"] {{ background: transparent !important; }}

    /* Make tab header row tiny & invisible but keep panels */
    div[data-baseweb="tab-bar"] {{ overflow: hidden; height: 0px; opacity: 0; pointer-events: none; }}

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
    .cf-nav-btn.active {{ color: #fff; background: linear-gradient(135deg, rgba(108,92,231,0.35), rgba(0,212,255,0.15)); }}
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
            <img class="cf-logo-img" src="{LOGO_SRC}" alt="Logo">
            <div>
                <div class="cf-brand-name">CreatorFlow AI</div>
                <div class="cf-brand-sub">Create • Transform • Automate</div>
            </div>
        </div>
        <div class="cf-center">
            <button class="cf-nav-btn active" id="btn-gen" onclick="switchTab(0)">⚡ Generator</button>
            <button class="cf-nav-btn" id="btn-studio" onclick="switchTab(1)">🎬 Studio</button>
        </div>
        <div class="cf-right">
            <span class="cf-icon-btn" id="btn-dark" onclick="toggleDark()" title="Dark/Light">🌙</span>
            <span class="cf-icon-btn" title="Notifications">🔔</span>
            <span class="cf-icon-btn" onclick="location.reload()" title="Refresh">⚙️</span>
            <span class="cf-icon-btn" title="Help">ℹ️</span>
        </div>
    </div>

    <script>
    function switchTab(idx) {{
        var tabs = document.querySelectorAll('div[data-baseweb="tab-bar"] button[role="tab"]');
        if(tabs[idx]) {{ tabs[idx].click(); updateActive(idx); }}
    }}

    function updateActive(idx) {{
        document.getElementById('btn-gen').classList.toggle('active', idx === 0);
        document.getElementById('btn-studio').classList.toggle('active', idx === 1);
    }}

    // Watch Streamlit tab panel visibility changes
    var observer = new MutationObserver(function() {{
        var panels = document.querySelectorAll('div[data-baseweb="tab-panel"]');
        if(panels.length >= 2) {{
            var p0 = panels[0].getAttribute('aria-hidden');
            updateActive(p0 === 'false' ? 0 : 1);
        }}
    }});
    observer.observe(document.body, {{ attributes: true, subtree: true, attributeFilter: ['aria-hidden'] }});

    setTimeout(function() {{ updateActive(0); }}, 200);

    var dark = true;
    function toggleDark() {{
        dark = !dark;
        document.getElementById('btn-dark').textContent = dark ? '🌙' : '☀️';
        var main = document.querySelector('[data-testid="stAppViewContainer"] > .main');
        if(main) main.style.background = dark ? 'linear-gradient(135deg, #0B1220, #111827)' : '#f5f5f5';
    }}
    </script>
    \""", unsafe_allow_html=True)
    # ═══════════════════════════════════════════════════════'''

OLD_BLOCK = CSS_LINE + TAB_NAV
NEW_BLOCK = CSS_LINE + NAVBAR + TAB_NAV

if OLD_BLOCK in T:
    T = T.replace(OLD_BLOCK, NEW_BLOCK, 1)
    print("[4] Navbar injected")
else:
    print("[4] ⚠️ Exact match fail, trying line-based...")
    lines = T.splitlines()
    css_i = tab_i = None
    for i, l in enumerate(lines):
        if l.strip() == 'css()': css_i = i
        if css_i is not None and 'st.tabs([' in l: tab_i = i; break
    if css_i is not None and tab_i is not None:
        before = '\n'.join(lines[:css_i+1]) + '\n'
        after = '\n'.join(lines[tab_i:])
        T = before + NAVBAR + '\n' + after
        print(f"[4] Navbar injected (line-based: {css_i+1}→{tab_i+1})")
    else:
        print(f"[4] ❌ Failed: css={css_i}, tabs={tab_i}")
        P.write_text(orig, encoding="utf-8")
        raise SystemExit(1)

# VALIDATE
P.write_text(T, encoding="utf-8")
try:
    compile(T, str(P), "exec")
    print("\n✅ DONE — 0 errors!")
    print("Key fix: tab-bar hidden with height:0 + opacity:0, panels stay visible")
    print("\nRun: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ {e}")
    P.write_text(orig, encoding="utf-8")
    print("↩️ Rolled back")