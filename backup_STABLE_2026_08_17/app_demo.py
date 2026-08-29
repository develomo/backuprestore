import streamlit as st
from creatorflow_navbar_patch import render_creatorflow_navbar

# ═══ CREATORFLOW NAVBAR ═══
st.set_page_config(page_title="CreatorFlow", page_icon="🎬", layout="wide")
page = render_creatorflow_navbar()

if page == "Video Generator":
    # ===== VIDEO GENERATOR PAGE =====
    st.title("My Creation Video Generator")

    st.markdown("### 🎬 Editing Style Preset")

    cols = st.columns(4)
    styles = ["Style 1", "Style 2", "Style 3", "Style 4", 
              "Style 5", "Style 6", "Style 7", "Style 8"]

    for i, style in enumerate(styles):
        with cols[i % 4]:
            if i == 0:
                st.button(f"● {i+1}. {style}", use_container_width=True, type="primary")
            else:
                st.button(f"○ {i+1}. {style}", use_container_width=True)

    st.markdown("**Selected: Preset #1 — Style 1**")
    st.divider()

    st.markdown("### ⏣ Auto-Detect Mode")
    with st.expander("Auto-Detect Niche & Style from Script"):
        st.text_area("Paste your script here...", height=150)
        st.button("Analyze Script", type="primary")

    with st.expander("⚙️ Advanced Custom Settings"):
        st.slider("Video Duration", 15, 60, 30)
        st.selectbox("Resolution", ["1080x1920 (9:16)", "1920x1080 (16:9)", "1080x1080 (1:1)"])
        st.toggle("Auto Captions", value=True)

elif page == "Reels Upload Studio":
    # ===== REELS UPLOAD STUDIO PAGE =====
    st.title("🎬 Reels Upload Studio")

    st.markdown("### Upload & Schedule Your Reels")

    uploaded = st.file_uploader("Drop video files here", type=["mp4", "mov"], accept_multiple_files=True)

    if uploaded:
        st.success(f"{len(uploaded)} file(s) uploaded successfully!")

        for vid in uploaded:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.text_input("Caption", key=f"cap_{vid.name}", placeholder="Enter reel caption...")
            with col2:
                st.text_input("Hashtags", key=f"tags_{vid.name}", placeholder="#viral #trending")
            with col3:
                st.button("Schedule", key=f"sched_{vid.name}", type="primary")

    st.divider()
    st.markdown("### 📊 Upload Queue")
    st.info("No scheduled uploads yet. Add videos above to get started.")