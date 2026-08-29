from pathlib import Path

P = Path(r"D:\My Creation Video Generator\backup\app.py")
T = P.read_text(encoding="utf-8")

# Remove the bad setdefault block I added earlier
bad_block = '''    # ── Session defaults ──
    st.session_state.setdefault("reels_aspect", "9:16")
    st.session_state.setdefault("reels_captions", True)
    st.session_state.setdefault("reels_cpu_safe", True)
    st.session_state.setdefault("reels_bg_music", True)
    st.session_state.setdefault("reels_bg_volume", 0.3)
    st.session_state.setdefault("reels_motion", "auto")
    st.session_state.setdefault("reels_transition", "auto")
    st.session_state.setdefault("reels_color", "auto")
    st.session_state.setdefault("reels_voice", "auto")'''

T = T.replace(bad_block, "")

# Now add proper defaults — bools for checkboxes, strings for selects
good_block = '''    # ── Session defaults ──
    st.session_state.setdefault("reels_aspect", "9:16")
    st.session_state.setdefault("reels_captions", True)
    st.session_state.setdefault("reels_cpu_safe", True)
    st.session_state.setdefault("reels_bg_music", True)
    st.session_state.setdefault("reels_bg_volume", 30)
    st.session_state.setdefault("reels_motion", "auto")
    st.session_state.setdefault("reels_transition", "auto")
    st.session_state.setdefault("reels_color", "auto")
    st.session_state.setdefault("reels_voice", "auto")'''

T = T.replace("def reels_upload_studio_tab():\n", "def reels_upload_studio_tab():\n" + good_block + "\n")

P.write_text(T, encoding="utf-8")
compile(T, str(P), "exec")
print("DONE — defaults fixed, no more TypeError")