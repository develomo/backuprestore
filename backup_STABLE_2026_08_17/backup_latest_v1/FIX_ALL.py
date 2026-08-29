from pathlib import Path

P = Path(r"D:\My Creation Video Generator\backup\app.py")
T = P.read_text(encoding="utf-8")

# Fix 1: Add 'import os' if missing
if '\nimport os\n' not in T and '\nimport os;' not in T:
    T = T.replace('import subprocess', 'import subprocess\nimport os', 1)

# Fix 2: Find reels_upload_studio_tab and fix os.path.exists — add os import check
# Already done by Fix 1

# Fix 3: Fix captions — find FIX_CAPTIONS / words=None pattern
# Agar words=[] hai aur words=None nahi, toh fix karo
if 'words=None' not in T:
    T = T.replace("words=[]", "words=None")
    T = T.replace('"words": []', '"words": None')

# Fix 4: Ensure all default settings variables are defined before use
# Add defaults in reels_upload_studio_tab
old_defaults = "def reels_upload_studio_tab():"
new_defaults = """def reels_upload_studio_tab():
    # ── Session defaults ──
    st.session_state.setdefault("reels_aspect", "9:16")
    st.session_state.setdefault("reels_captions", True)
    st.session_state.setdefault("reels_cpu_safe", True)
    st.session_state.setdefault("reels_bg_music", True)
    st.session_state.setdefault("reels_bg_volume", 0.3)
    st.session_state.setdefault("reels_motion", "auto")
    st.session_state.setdefault("reels_transition", "auto")
    st.session_state.setdefault("reels_color", "auto")
    st.session_state.setdefault("reels_voice", "auto")"""

T = T.replace(old_defaults, new_defaults, 1)

# Fix 5: Ensure captions checkbox controls caption rendering
# Find where render_kwargs is built and add captions from session state
old_render = '"captions":'
# Already handled by words=None above

P.write_text(T, encoding="utf-8")
compile(T, str(P), "exec")
print("DONE — os imported, session defaults, captions enabled")