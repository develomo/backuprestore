"""
CREATORFLOW_V4.py — Perfect injection: navbar after css(), before tabs
"""
from pathlib import Path
import shutil

P = Path(r"D:\My Creation Video Generator\backup\app.py")

# Restore clean
backups = sorted(Path(r"D:\My Creation Video Generator\backup").glob("app.py.bak*"), reverse=True)
if backups:
    shutil.copy(backups[0], P)
    print(f"[0] Restored: {backups[0].name}")

T = P.read_text(encoding="utf-8")
orig = T

# 1. Page config
OLD = 'st.set_page_config(page_title=APP_TITLE, page_icon="🎬", layout="wide")'
NEW = 'st.set_page_config(page_title="CreatorFlow AI", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")'
if OLD in T:
    T = T.replace(OLD, NEW, 1)
    print("[1] Page config updated")

# 2. words=None
T = T.replace('words=[]', 'words=None')
T = T.replace('"words": []', '"words": None')
print("[2] words=None")

# 3. Inject navbar BETWEEN css() and # TAB NAVIGATION
CSS_LINE = '    css()\n'
TAB_COMMENT = '\n    # ── TAB NAVIGATION ──'

NAVBAR_BLOCK = '''
    # ═══════════ CreatorFlow AI ═══════════
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] > .main { background: linear-gradient(135deg, #0B1220, #111827); }
    header[data-testid="stHeader"] { background: transparent !important; }
    .cf-navbar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 10px 28px; margin: 8px 12px 0 12px; border-radius: 16px;
        background: rgba(17,24,39,0.7); backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(108,92,231,0.25);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 60px rgba(108,92,231,0.08);
    }
    .cf-left { display: flex; align-items: center; gap: 14px; }
    .cf-logo {
        width: 44px; height: 44px; border-radius: 12px;
        background: linear-gradient(135deg, #6C5CE7, #A855F7, #00D4FF);
        display: flex; align-items: center; justify-content: center;
        font-size: 22px; box-shadow: 0 0 20px rgba(108,92,231,0.5);
    }
    .cf-brand-name {
        font-size: 18px; font-weight: 700;
        background: linear-gradient(90deg, #A855F7, #00D4FF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .cf-brand-sub { font-size: 10px; color: rgba(255,255,255,0.45); }
    .cf-center { display: flex; align-items: center; gap: 6px; }
    .cf-nav-btn {
        padding: 9px 20px; border-radius: 10px; font-size: 13px; font-weight: 600;
        color: rgba(255,255,255,0.6); background: transparent; border: 1px solid transparent;
        cursor: pointer; transition: all 0.3s; white-space: nowrap;
    }
    .cf-nav-btn:hover { color: #fff; background: rgba(108,92,231,0.15); border-color: rgba(108,92,231,0.4); }
    .cf-nav-btn.active { color: #fff; background: linear-gradient(135deg, rgba(108,92,231,0.25), rgba(0,212,255,0.1)); border-color: rgba(108,92,231,0.6); }
    .cf-right { display: flex; align-items: center; gap: 10px; }
    .cf-icon-btn {
        width: 36px; height: 36px; border-radius: 10px;
        background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
        display: flex; align-items: center; justify-content: center; cursor: pointer;
    }
    .cf-icon-btn:hover { background: rgba(108,92,231,0.2); border-color: rgba(108,92,231,0.5); }
    .cf-theme-select {
        padding: 6px 10px; border-radius: 8px; font-size: 12px;
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12);
        color: rgba(255,255,255,0.7); cursor: pointer;
    }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }
    </style>
    <div class="cf-navbar">
        <div class="cf-left"><div class="cf-logo">🎬</div><div><span class="cf-brand-name">CreatorFlow AI</span><br><span class="cf-brand-sub">Create • Transform • Automate</span></div></div>
        <div class="cf-center"><span class="cf-nav-btn active">🎬 Generator</span><span class="cf-nav-btn">🚀 Studio</span></div>
        <div class="cf-right"><span class="cf-theme-select">🌙 Dark</span><span class="cf-icon-btn">🔔</span><span class="cf-icon-btn">⚙️</span><span class="cf-icon-btn">❓</span></div>
    </div>
    """, unsafe_allow_html=True)
    # ═══════════════════════════════════════'''

# Replace: css() + blank line + TAB_COMMENT → css() + navbar + TAB_COMMENT
OLD_BLOCK = CSS_LINE + TAB_COMMENT
NEW_BLOCK = CSS_LINE + NAVBAR_BLOCK + TAB_COMMENT

if OLD_BLOCK in T:
    T = T.replace(OLD_BLOCK, NEW_BLOCK, 1)
    print("[3] Navbar injected after css()")
else:
    print("[3] ⚠️ Pattern not found, trying alternate...")
    # Try: css()\n\n    # ── TAB
    ALT_OLD = '    css()\n\n    # ── TAB NAVIGATION ──'
    if ALT_OLD in T:
        T = T.replace(ALT_OLD, '    css()\n' + NAVBAR_BLOCK + '\n    # ── TAB NAVIGATION ──', 1)
        print("[3] Navbar injected (alt)")
    else:
        print("[3] ❌ Cannot find injection point")

# VALIDATE
P.write_text(T, encoding="utf-8")
try:
    compile(T, str(P), "exec")
    print("\n✅ ALL DONE — 0 errors! Run: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ SYNTAX ERROR: {e}")
    P.write_text(orig, encoding="utf-8")
    print("↩️ Rolled back")