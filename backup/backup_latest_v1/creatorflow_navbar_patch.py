"""
╔══════════════════════════════════════════════════════════════════════╗
║          CREATORFLOW NAVBAR + REELS STUDIO PATCH v8.0                ║
║  Auto-Patch Script for My Creation Video Generator                   ║
║  Is script ko apne app.py ke top pe import karo ya paste karo        ║
╚══════════════════════════════════════════════════════════════════════╝

USAGE:
    from creatorflow_navbar_patch import render_creatorflow_navbar

    # Sab se top pe call karo
    page = render_creatorflow_navbar()

    if page == "Video Generator":
        # Apna video generator code yahan
        pass
    elif page == "Reels Upload Studio":
        # Apna reels studio code yahan  
        pass
"""

import streamlit as st

def render_creatorflow_navbar():
    """
    Ye function top navbar render karta hai aur selected page return karta hai.
    Isko app.py ke bilkul start mein call karo.
    """

    # ─── SESSION STATE INIT ───
    if "cf_page" not in st.session_state:
        st.session_state.cf_page = "Video Generator"
    if "cf_dark" not in st.session_state:
        st.session_state.cf_dark = True

    # ─── CUSTOM CSS ───
    st.markdown("""
    <style>
    /* Hide default Streamlit header & menu */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {padding-top: 0 !important;}

    /* Navbar Container */
    .cf-navbar {
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.6rem 2rem;
        background: rgba(11, 18, 32, 0.95);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(255,255,255,0.06);
        height: 64px;
        box-sizing: border-box;
    }

    /* Left: Logo */
    .cf-left {
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 700;
        font-size: 1.15rem;
        color: #fff;
        letter-spacing: -0.3px;
    }
    .cf-logo-icon {
        width: 32px; height: 32px;
        background: linear-gradient(135deg, #FF4B4B, #FF6B6B);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
    }

    /* Center: Nav Buttons */
    .cf-center {
        display: flex;
        align-items: center;
        gap: 8px;
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
    }
    .cf-nav-btn {
        padding: 8px 22px;
        border-radius: 10px;
        border: none;
        background: transparent;
        color: rgba(255,255,255,0.55);
        font-size: 0.9rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.25s ease;
        display: flex;
        align-items: center;
        gap: 6px;
        white-space: nowrap;
    }
    .cf-nav-btn:hover {
        background: rgba(255,255,255,0.06);
        color: rgba(255,255,255,0.85);
    }
    .cf-nav-btn.active {
        background: linear-gradient(135deg, #FF4B4B, #FF6B6B);
        color: #fff !important;
        box-shadow: 0 4px 15px rgba(255,75,75,0.35);
    }

    /* Right: Icons */
    .cf-right {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .cf-icon-btn {
        width: 36px; height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 1rem;
        transition: all 0.2s ease;
        color: rgba(255,255,255,0.5);
        background: rgba(255,255,255,0.04);
    }
    .cf-icon-btn:hover {
        background: rgba(255,255,255,0.1);
        color: #fff;
        transform: translateY(-1px);
    }

    /* Push content below navbar */
    .main .block-container {
        padding-top: 5rem !important;
        max-width: 1100px;
    }

    /* Light mode overrides */
    .light-mode .cf-navbar {
        background: rgba(255,255,255,0.92);
        border-bottom: 1px solid rgba(0,0,0,0.06);
    }
    .light-mode .cf-left { color: #1a1a2e; }
    .light-mode .cf-nav-btn { color: rgba(0,0,0,0.45); }
    .light-mode .cf-nav-btn:hover { background: rgba(0,0,0,0.04); color: rgba(0,0,0,0.75); }
    .light-mode .cf-icon-btn { background: rgba(0,0,0,0.04); color: rgba(0,0,0,0.45); }
    .light-mode .cf-icon-btn:hover { background: rgba(0,0,0,0.08); color: #1a1a2e; }
    </style>
    """, unsafe_allow_html=True)

    # ─── NAVBAR HTML ───
    st.markdown("""
    <div class="cf-navbar" id="cfNavbar">
        <div class="cf-left">
            <div class="cf-logo-icon">🎬</div>
            <span>CreatorFlow</span>
        </div>
        <div class="cf-center">
            <button class="cf-nav-btn active" id="btn-gen">⚡ Video Generator</button>
            <button class="cf-nav-btn" id="btn-studio">🎬 Reels Studio</button>
        </div>
        <div class="cf-right">
            <span class="cf-icon-btn" title="Dark/Light" onclick="toggleCreatorTheme()">🌙</span>
            <span class="cf-icon-btn" title="Notifications">🔔</span>
            <span class="cf-icon-btn" title="Refresh" onclick="window.location.reload()">⚙️</span>
        </div>
    </div>

    <script>
    function toggleCreatorTheme() {
        const body = document.body;
        body.classList.toggle('light-mode');
        const isLight = body.classList.contains('light-mode');
        localStorage.setItem('cf-theme', isLight ? 'light' : 'dark');
    }
    if (localStorage.getItem('cf-theme') === 'light') {
        document.body.classList.add('light-mode');
    }
    </script>
    """, unsafe_allow_html=True)

    # ─── FUNCTIONAL BUTTONS ───
    nav_cols = st.columns([1, 2, 1])

    with nav_cols[1]:
        sub_cols = st.columns(2)
        with sub_cols[0]:
            gen_btn = st.button(
                "⚡ Video Generator", 
                key="nav_gen_btn",
                use_container_width=True,
                type="primary" if st.session_state.cf_page == "Video Generator" else "secondary"
            )
        with sub_cols[1]:
            studio_btn = st.button(
                "🎬 Reels Upload Studio",
                key="nav_studio_btn", 
                use_container_width=True,
                type="primary" if st.session_state.cf_page == "Reels Upload Studio" else "secondary"
            )

    if gen_btn:
        st.session_state.cf_page = "Video Generator"
        st.rerun()
    if studio_btn:
        st.session_state.cf_page = "Reels Upload Studio"
        st.rerun()

    # Hide functional buttons (visual only, HTML navbar covers them)
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"]:has(button[kind="primary"]) {
        margin-top: -3.5rem !important;
        opacity: 0;
        pointer-events: none;
        height: 0;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

    return st.session_state.cf_page


def inject_navbar_into_app_py(app_py_path="app.py"):
    """
    Auto-patch: app.py ke top pe navbar code inject karta hai.
    Backup bhi create karta hai.

    Usage:
        python creatorflow_navbar_patch.py --patch
    """
    import shutil
    from datetime import datetime

    try:
        with open(app_py_path, "r", encoding="utf-8") as f:
            original = f.read()

        if "render_creatorflow_navbar" in original:
            print("✅ Navbar already patched!")
            return

        backup_name = f"{app_py_path}.bak_navbar_{int(datetime.now().timestamp())}"
        shutil.copy2(app_py_path, backup_name)
        print(f"📦 Backup created: {backup_name}")

        lines = original.split("\n")
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                insert_idx = i + 1

        lines.insert(insert_idx, "from creatorflow_navbar_patch import render_creatorflow_navbar")

        call_insert_idx = insert_idx + 1
        for i in range(call_insert_idx, len(lines)):
            if lines[i].strip() and not lines[i].strip().startswith("#"):
                call_insert_idx = i
                break

        nav_call_lines = [
            "",
            "# ═══ CREATORFLOW NAVBAR ═══",
            "st.set_page_config(page_title=\"CreatorFlow\", page_icon=\"🎬\", layout=\"wide\")",
            "page = render_creatorflow_navbar()",
            "",
            "if page == \"Video Generator\":",
            "    # ===== VIDEO GENERATOR PAGE =====",
        ]

        remaining = lines[call_insert_idx:]
        lines = lines[:call_insert_idx] + nav_call_lines + remaining
        lines.append("")
        lines.append("elif page == \"Reels Upload Studio\":")
        lines.append("    # ===== REELS UPLOAD STUDIO PAGE =====")
        lines.append("    pass  # Apna Reels Studio code yahan add karo")

        with open(app_py_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print("✅ Navbar successfully patched into app.py!")
        print("🎬 Pages: Video Generator | Reels Upload Studio")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--patch":
        inject_navbar_into_app_py()
    else:
        print("Run with: python creatorflow_navbar_patch.py --patch")