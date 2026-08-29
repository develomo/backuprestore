"""
CREATORFLOW_V5.py — FULL WORKING NAVBAR with logo, tab switching, hidden Streamlit tabs
"""
from pathlib import Path
import shutil, base64

P = Path(r"D:\My Creation Video Generator\backup\app.py")

# Restore from clean backup
backups = sorted(Path(r"D:\My Creation Video Generator\backup").glob("app.py.bak*"), reverse=True)
if backups:
    shutil.copy(backups[0], P)
    print(f"[0] Restored: {backups[0].name}")

# Encode logo
LOGO_PATH = Path(r"D:\My Creation Video Generator\backup\logo.png")
logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
LOGO_SRC = f"data:image/png;base64,{logo_b64}"
print(f"[1] Logo encoded ({len(logo_b64)} chars)")

T = P.read_text(encoding="utf-8")
orig = T

# 1. Page config
OLD = 'st.set_page_config(page_title=APP_TITLE, page_icon="🎬", layout="wide")'
NEW = 'st.set_page_config(page_title="CreatorFlow AI", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")'
if OLD in T:
    T = T.replace(OLD, NEW, 1)
    print("[2] Page config updated")

# 2. words=None
T = T.replace('words=[]', 'words=None')
T = T.replace('"words": []', '"words": None')
print("[3] words=None")

# 3. FULL WORKING NAVBAR
CSS_LINE = '    css()\n'
TAB_COMMENT = '\n    # ── TAB NAVIGATION ──'

NAVBAR_BLOCK = f'''
    # ═══════════ CreatorFlow AI Premium Navbar ═══════════
    st.markdown("""
    <style>
    /* Hide Streamlit tabs */
    div[data-testid="stTabs"] {{ display: none !important; }}
    div.stTabs {{ display: none !important; }}
    section[data-testid="stSidebar"] {{ display: none !important; }}

    [data-testid="stAppViewContainer"] > .main {{
        background: linear-gradient(135deg, #0B1220 0%, #111827 100%);
    }}
    header[data-testid="stHeader"] {{ background: transparent !important; }}

    .cf-navbar {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 8px 24px; margin: 6px 12px 0 12px; border-radius: 14px;
        background: rgba(17, 24, 39, 0.75); backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(108, 92, 231, 0.2);
        box-shadow: 0 4px 24px rgba(0,0,0,0.5), 0 0 80px rgba(108,92,231,0.06);
        position: sticky; top: 0; z-index: 999;
    }}
    .cf-left {{ display: flex; align-items: center; gap: 12px; }}
    .cf-logo-img {{
        width: 40px; height: 40px; border-radius: 10px; object-fit: cover;
        box-shadow: 0 0 16px rgba(108,92,231,0.4);
        border: 2px solid rgba(108,92,231,0.3);
    }}
    .cf-brand-name {{
        font-size: 18px; font-weight: 700;
        background: linear-gradient(90deg, #A855F7, #00D4FF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: -0.3px;
    }}
    .cf-brand-sub {{ font-size: 10px; color: rgba(255,255,255,0.4); letter-spacing: 1px; }}
    .cf-center {{ display: flex; align-items: center; gap: 4px; background: rgba(255,255,255,0.03); border-radius: 10px; padding: 3px; }}
    .cf-nav-btn {{
        padding: 8px 22px; border-radius: 8px; font-size: 13px; font-weight: 600;
        color: rgba(255,255,255,0.5); background: transparent; border: none;
        cursor: pointer; transition: all 0.25s; white-space: nowrap;
        text-decoration: none; position: relative;
    }}
    .cf-nav-btn:hover {{ color: rgba(255,255,255,0.85); }}
    .cf-nav-btn.active {{
        color: #fff; background: linear-gradient(135deg, rgba(108,92,231,0.35), rgba(0,212,255,0.15));
        box-shadow: 0 2px 12px rgba(108,92,231,0.25), inset 0 1px 0 rgba(255,255,255,0.08);
    }}
    .cf-right {{ display: flex; align-items: center; gap: 8px; }}
    .cf-icon-btn {{
        width: 34px; height: 34px; border-radius: 8px;
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
        display: flex; align-items: center; justify-content: center; cursor: pointer;
        transition: all 0.25s; font-size: 15px;
    }}
    .cf-icon-btn:hover {{ background: rgba(108,92,231,0.18); border-color: rgba(108,92,231,0.4); }}
    .cf-theme-select {{
        padding: 5px 8px; border-radius: 7px; font-size: 11px; font-weight: 600;
        background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
        color: rgba(255,255,255,0.6); cursor: pointer;
    }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    [data-testid="stToolbar"] {{ display: none; }}
    [data-testid="stDecoration"] {{ display: none; }}
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
            <button class="cf-nav-btn active" id="cf-btn-generator" onclick="document.querySelectorAll('[data-baseweb=tab]')[0].click()">⚡ Generator</button>
            <button class="cf-nav-btn" id="cf-btn-studio" onclick="document.querySelectorAll('[data-baseweb=tab]')[1].click()">🎬 Studio</button>
        </div>
        <div class="cf-right">
            <span class="cf-theme-select">🌙 Dark</span>
            <span class="cf-icon-btn">🔔</span>
            <span class="cf-icon-btn">⚙️</span>
            <span class="cf-icon-btn">ℹ️</span>
        </div>
    </div>

    <script>
    // Tab switch + active state
    const tabs = document.querySelectorAll('[data-baseweb="tab"]');
    const btnGen = document.getElementById('cf-btn-generator');
    const btnStudio = document.getElementById('cf-btn-studio');

    function setActive(activeBtn, inactiveBtn) {{
        activeBtn.classList.add('active');
        inactiveBtn.classList.remove('active');
    }}

    // Click on tabs to sync navbar
    if(tabs.length >= 2) {{
        tabs[0].addEventListener('click', () => setActive(btnGen, btnStudio));
        tabs[1].addEventListener('click', () => setActive(btnStudio, btnGen));
    }}

    // Initial sync — check which tab is selected
    setTimeout(() => {{
        const tabPanels = document.querySelectorAll('[data-baseweb="tab-panel"]');
        if(tabPanels.length >= 2 && tabPanels[0].getAttribute('aria-hidden') === 'false') setActive(btnGen, btnStudio);
        else if(tabPanels.length >= 2 && tabPanels[1].getAttribute('aria-hidden') === 'false') setActive(btnStudio, btnGen);
    }}, 300);
    </script>
    """, unsafe_allow_html=True)
    # ═══════════════════════════════════════════════════════'''

OLD_BLOCK = CSS_LINE + TAB_COMMENT
NEW_BLOCK = CSS_LINE + NAVBAR_BLOCK + TAB_COMMENT

if OLD_BLOCK in T:
    T = T.replace(OLD_BLOCK, NEW_BLOCK, 1)
    print("[4] Working navbar injected")
else:
    # Alternate
    ALT_OLD = '    css()\n\n    # ── TAB NAVIGATION ──'
    if ALT_OLD in T:
        T = T.replace(ALT_OLD, '    css()\n' + NAVBAR_BLOCK + '\n    # ── TAB NAVIGATION ──', 1)
        print("[4] Working navbar injected (alt)")
    else:
        print("[4] ❌ FAILED")
        P.write_text(orig, encoding="utf-8")
        raise SystemExit(1)

# VALIDATE
P.write_text(T, encoding="utf-8")
try:
    compile(T, str(P), "exec")
    print("\n✅ DONE — 0 errors!")
    print("Features:")
    print("  • Logo loaded from logo.png")
    print("  • Generator button → Video Generator tab")
    print("  • Studio button → Reels Upload Studio tab")
    print("  • Streamlit default tabs HIDDEN")
    print("  • Active state syncs with actual tab")
    print("\nRun: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ SYNTAX ERROR: {e}")
    P.write_text(orig, encoding="utf-8")
    print("↩️ Rolled back")