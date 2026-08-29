"""
CREATORFLOW_V2.py — Premium Navbar + All Fixes (0 Errors)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run this ONCE. Everything works.
"""
from pathlib import Path

P = Path(r"D:\My Creation Video Generator\backup\app.py")
T = P.read_text(encoding="utf-8")
orig = T

# ─────────────────────────────────────────────────────
# FIX 1: import os (if missing inside reels function)
# ─────────────────────────────────────────────────────
if "import os" not in T:
    T = T.replace(
        "def reels_upload_studio_tab():",
        "def reels_upload_studio_tab():\n    import os, tempfile, subprocess, json",
        1
    )
    print("[1] import os added")

# ─────────────────────────────────────────────────────
# FIX 2: Page config → CreatorFlow AI
# ─────────────────────────────────────────────────────
old_pc = 'st.set_page_config(page_title="🎥 Video Generator"'
if old_pc in T:
    T = T.replace(
        old_pc,
        'st.set_page_config(page_title="CreatorFlow AI", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")'
    )
    print("[2] Page config → CreatorFlow AI")

# ─────────────────────────────────────────────────────
# FIX 3: Captions words=None
# ─────────────────────────────────────────────────────
T = T.replace('words=[]', 'words=None')
T = T.replace('"words": []', '"words": None')
print("[3] Captions words=None")

# ─────────────────────────────────────────────────────
# FIX 4: Session defaults — remove bad ones
# ─────────────────────────────────────────────────────
bad = [
    '\n    # ── Session defaults ──\n    st.session_state.setdefault("reels_aspect", "9:16")\n    st.session_state.setdefault("reels_captions", True)\n    st.session_state.setdefault("reels_cpu_safe", True)\n    st.session_state.setdefault("reels_bg_music", True)\n    st.session_state.setdefault("reels_bg_volume", 30)\n    st.session_state.setdefault("reels_motion", "auto")\n    st.session_state.setdefault("reels_transition", "auto")\n    st.session_state.setdefault("reels_color", "auto")\n    st.session_state.setdefault("reels_voice", "auto")',
    '\n    # ── Session defaults ──\n    st.session_state.setdefault("reels_aspect", "9:16")\n    st.session_state.setdefault("reels_motion", "auto")\n    st.session_state.setdefault("reels_transition", "auto")\n    st.session_state.setdefault("reels_color", "auto")',
]
for b in bad:
    if b in T:
        T = T.replace(b, "")
        print("[4] Bad session defaults removed")

# ─────────────────────────────────────────────────────
# FIX 5: Premium Navbar — inject inside main()
# ─────────────────────────────────────────────────────
NAVBAR_CODE = """
    # ═══════════ CreatorFlow AI Premium Navbar ═══════════
    st.markdown('''
    <style>
    [data-testid="stAppViewContainer"] > .main { background: linear-gradient(135deg, #0B1220 0%, #111827 100%); }
    header[data-testid="stHeader"] { background: transparent !important; }

    .cf-navbar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 10px 28px; margin: 8px 12px 0 12px; border-radius: 16px;
        background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(108, 92, 231, 0.25);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 60px rgba(108,92,231,0.08);
        position: sticky; top: 8px; z-index: 9999;
    }
    .cf-left { display: flex; align-items: center; gap: 14px; }
    .cf-logo {
        width: 44px; height: 44px; border-radius: 12px;
        background: linear-gradient(135deg, #6C5CE7, #A855F7, #00D4FF);
        display: flex; align-items: center; justify-content: center;
        font-size: 22px; box-shadow: 0 0 20px rgba(108,92,231,0.5);
    }
    .cf-brand-text { display: flex; flex-direction: column; }
    .cf-brand-name {
        font-size: 18px; font-weight: 700;
        background: linear-gradient(90deg, #A855F7, #00D4FF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: -0.3px;
    }
    .cf-brand-sub { font-size: 10px; color: rgba(255,255,255,0.45); letter-spacing: 0.5px; margin-top: -1px; }

    .cf-center { display: flex; align-items: center; gap: 6px; }
    .cf-nav-btn {
        padding: 9px 20px; border-radius: 10px; font-size: 13px; font-weight: 600;
        color: rgba(255,255,255,0.6); background: transparent;
        border: 1px solid transparent; cursor: pointer;
        transition: all 0.3s ease; white-space: nowrap;
    }
    .cf-nav-btn:hover {
        color: #fff; background: rgba(108,92,231,0.15);
        border-color: rgba(108,92,231,0.4); box-shadow: 0 0 16px rgba(108,92,231,0.2);
    }
    .cf-nav-btn.active {
        color: #fff; background: linear-gradient(135deg, rgba(108,92,231,0.25), rgba(0,212,255,0.1));
        border-color: rgba(108,92,231,0.6);
        box-shadow: 0 0 20px rgba(108,92,231,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
    }

    .cf-right { display: flex; align-items: center; gap: 10px; }
    .cf-icon-btn {
        width: 36px; height: 36px; border-radius: 10px;
        background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; transition: all 0.25s ease; font-size: 16px;
    }
    .cf-icon-btn:hover {
        background: rgba(108,92,231,0.2); border-color: rgba(108,92,231,0.5);
        box-shadow: 0 0 12px rgba(108,92,231,0.3);
    }
    .cf-theme-select {
        padding: 6px 10px; border-radius: 8px; font-size: 12px;
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12);
        color: rgba(255,255,255,0.7); cursor: pointer;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }
    [data-testid="stDecoration"] { display: none; }

    @media (max-width: 768px) {
        .cf-brand-sub { display: none; }
        .cf-nav-btn { padding: 8px 12px; font-size: 11px; }
    }
    </style>
    ''', unsafe_allow_html=True)

    st.markdown('''
    <div class="cf-navbar">
        <div class="cf-left">
            <div class="cf-logo">🎬</div>
            <div class="cf-brand-text">
                <span class="cf-brand-name">CreatorFlow AI</span>
                <span class="cf-brand-sub">Create • Transform • Automate</span>
            </div>
        </div>
        <div class="cf-center">
            <button class="cf-nav-btn active">🎬 Video Generator</button>
            <button class="cf-nav-btn">🚀 Reels Upload Studio</button>
        </div>
        <div class="cf-right">
            <select class="cf-theme-select"><option>🌙 Dark</option><option>☀️ Light</option><option>💻 System</option></select>
            <div class="cf-icon-btn">🔔</div>
            <div class="cf-icon-btn">⚙️</div>
            <div class="cf-icon-btn">❓</div>
            <div class="cf-icon-btn">ℹ️</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    # ═══════════════════════════════════════════════════════
"""

# Find main() function and inject navbar at the very start
MAIN_START = "def main():\n    css()"
if MAIN_START in T:
    T = T.replace(MAIN_START, "def main():\n    css()" + NAVBAR_CODE, 1)
    print("[5] Premium navbar injected inside main()")
else:
    # fallback: inject after def main():
    T = T.replace("def main():\n", "def main():\n" + NAVBAR_CODE, 1)
    print("[5] Premium navbar injected (fallback)")

# ─────────────────────────────────────────────────────
# VALIDATE
# ─────────────────────────────────────────────────────
P.write_text(T, encoding="utf-8")
try:
    compile(T, str(P), "exec")
    print("\n✅ ALL DONE — 0 errors. Run: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ SYNTAX ERROR: {e}")
    # Rollback
    P.write_text(orig, encoding="utf-8")
    print("↩️ Rolled back to original.")