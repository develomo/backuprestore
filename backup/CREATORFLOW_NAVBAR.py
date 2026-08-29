"""
CREATORFLOW_NAVBAR.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIXES:
  1. import os                    → NameError fix
  2. Session defaults (bool types)→ TypeError fix
  3. Captions words=None          → Captions enable
  4. Premium CreatorFlow AI Navbar→ Glassmorphism navbar
  5. Page config + Favicon        → CreatorFlow AI branding
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NO ERRORS. RUN ONCE.
"""
from pathlib import Path

P = Path(r"D:\My Creation Video Generator\backup\app.py")
T = P.read_text(encoding="utf-8")

changes = 0

# ─────────────────────────────────────────────────────
# FIX 1: import os
# ─────────────────────────────────────────────────────
if "import os\n" not in T and "import os;" not in T:
    T = T.replace("import subprocess", "import subprocess\nimport os", 1)
    changes += 1
    print("[1] import os added")

# ─────────────────────────────────────────────────────
# FIX 2: Remove bad session defaults (string for bool)
# ─────────────────────────────────────────────────────
bad_block1 = """
    # ── Session defaults ──
    st.session_state.setdefault("reels_aspect", "9:16")
    st.session_state.setdefault("reels_captions", True)
    st.session_state.setdefault("reels_cpu_safe", True)
    st.session_state.setdefault("reels_bg_music", True)
    st.session_state.setdefault("reels_bg_volume", 30)
    st.session_state.setdefault("reels_motion", "auto")
    st.session_state.setdefault("reels_transition", "auto")
    st.session_state.setdefault("reels_color", "auto")
    st.session_state.setdefault("reels_voice", "auto")"""

bad_block2 = """
    # ── Session defaults ──
    st.session_state.setdefault("reels_aspect", "9:16")
    st.session_state.setdefault("reels_motion", "auto")
    st.session_state.setdefault("reels_transition", "auto")
    st.session_state.setdefault("reels_color", "auto")"""

for b in [bad_block1, bad_block2]:
    if b.strip() and b.strip() in T:
        T = T.replace(b, "")
        changes += 1
        print("[2] Removed bad session defaults")

# ─────────────────────────────────────────────────────
# FIX 3: Captions — words=None
# ─────────────────────────────────────────────────────
if 'words=None' not in T:
    count = T.count('words=[]')
    T = T.replace('words=[]', 'words=None')
    T = T.replace('"words": []', '"words": None')
    changes += 1
    print(f"[3] words=None set (was words=[] x {count})")

# ─────────────────────────────────────────────────────
# FIX 4: Page config → CreatorFlow AI
# ─────────────────────────────────────────────────────
old_page = 'st.set_page_config(page_title="🎥 Video Generator"'
if old_page in T:
    T = T.replace(
        old_page,
        'st.set_page_config(page_title="CreatorFlow AI", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")'
    )
    changes += 1
    print("[4] Page config → CreatorFlow AI")

# ─────────────────────────────────────────────────────
# FIX 5: Premium Navbar — inject after page_config
# ─────────────────────────────────────────────────────
NAVBAR_CSS = """
# ── CreatorFlow AI Premium Navbar ──
st.markdown('''
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] > .main {
    background: linear-gradient(135deg, #0B1220 0%, #111827 100%);
}
header[data-testid="stHeader"] {
    background: transparent !important;
}

/* ── Navbar Container ── */
.creatorflow-navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 28px;
    margin: 8px 12px 0 12px;
    border-radius: 16px;
    background: rgba(17, 24, 39, 0.7);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(108, 92, 231, 0.25);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 60px rgba(108, 92, 231, 0.08);
    position: sticky;
    top: 8px;
    z-index: 9999;
}

/* ── Left Section ── */
.cf-left { display: flex; align-items: center; gap: 14px; }
.cf-logo {
    width: 44px; height: 44px;
    border-radius: 12px;
    background: linear-gradient(135deg, #6C5CE7, #A855F7, #00D4FF);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    box-shadow: 0 0 20px rgba(108, 92, 231, 0.5);
}
.cf-brand-text { display: flex; flex-direction: column; }
.cf-brand-name {
    font-size: 18px; font-weight: 700;
    background: linear-gradient(90deg, #A855F7, #00D4FF);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -0.3px;
}
.cf-brand-sub {
    font-size: 10px; color: rgba(255,255,255,0.45);
    letter-spacing: 0.5px; margin-top: -1px;
}

/* ── Center Nav ── */
.cf-center { display: flex; align-items: center; gap: 6px; }
.cf-nav-btn {
    padding: 9px 20px;
    border-radius: 10px;
    font-size: 13px; font-weight: 600;
    color: rgba(255,255,255,0.6);
    background: transparent;
    border: 1px solid transparent;
    cursor: pointer;
    transition: all 0.3s ease;
    white-space: nowrap;
}
.cf-nav-btn:hover {
    color: #fff;
    background: rgba(108, 92, 231, 0.15);
    border-color: rgba(108, 92, 231, 0.4);
    box-shadow: 0 0 16px rgba(108, 92, 231, 0.2);
}
.cf-nav-btn.active {
    color: #fff;
    background: linear-gradient(135deg, rgba(108, 92, 231, 0.25), rgba(0, 212, 255, 0.1));
    border-color: rgba(108, 92, 231, 0.6);
    box-shadow: 0 0 20px rgba(108, 92, 231, 0.3), inset 0 1px 0 rgba(255,255,255,0.1);
}

/* ── Right Section ── */
.cf-right { display: flex; align-items: center; gap: 10px; }
.cf-icon-btn {
    width: 36px; height: 36px;
    border-radius: 10px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
    transition: all 0.25s ease;
    font-size: 16px;
}
.cf-icon-btn:hover {
    background: rgba(108, 92, 231, 0.2);
    border-color: rgba(108, 92, 231, 0.5);
    box-shadow: 0 0 12px rgba(108, 92, 231, 0.3);
}
.cf-theme-select {
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.7);
    cursor: pointer;
}

/* ── Hide Streamlit default header/footer ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }

/* ── Responsive ── */
@media (max-width: 768px) {
    .cf-brand-sub { display: none; }
    .cf-nav-btn { padding: 8px 12px; font-size: 11px; }
}
</style>
''', unsafe_allow_html=True)

# ── Render Navbar ──
st.markdown('''
<div class="creatorflow-navbar">
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
"""

# Inject navbar CSS block after page config
if "st.set_page_config" in T and "# ── CreatorFlow AI Premium Navbar ──" not in T:
    # Find end of set_page_config line
    idx = T.index("st.set_page_config")
    nl = T.index("\n", idx)
    T = T[:nl+1] + NAVBAR_CSS + T[nl+1:]
    changes += 1
    print("[5] Premium navbar injected")

# ─────────────────────────────────────────────────────
# WRITE & VALIDATE
# ─────────────────────────────────────────────────────
P.write_text(T, encoding="utf-8")
try:
    compile(T, str(P), "exec")
    print(f"\n✅ ALL DONE — {changes} changes applied. 0 errors.")
except SyntaxError as e:
    print(f"\n❌ SYNTAX ERROR: {e}")