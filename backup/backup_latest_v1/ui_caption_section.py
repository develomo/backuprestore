# ui_caption_section.py
import streamlit as st
import os
from caption_style_registry import CAPTION_STYLES
from caption_engine import generate_mp4_preview

def render_caption_ui_section():
    """Renders the entire Caption UI Section in the web panel."""
    st.markdown("### 🎬 Dynamic Subtitle & Caption Engine")
    st.write("Customize short video subtitles with 30+ ultra styles and 6-8 second video previews.")

    col1, col2 = st.columns([1, 2])

    with col1:
        enable_captions = st.checkbox("Enable Captions on Short Render", value=True)
        
        caption_mode = st.selectbox(
            "Caption Mode",
            options=["line", "phrase", "word_by_word"],
            format_func=lambda x: x.replace("_", " ").title(),
            help="Choose between full line display, 2-4 word phrases, or single word tracking."
        )

        selected_style = st.selectbox(
            "Caption Style (30+ Premium Options)",
            options=list(CAPTION_STYLES.keys()),
            format_func=lambda x: x.replace("_", " ").title()
        )

        position_y = st.slider("Vertical Position (Y-Offset %)", min_value=50, max_value=90, value=75)
        font_scale = st.slider("Font Scaling Factor", min_value=0.5, max_value=2.0, value=1.0)

        generate_btn = st.button("🎥 Generate 6-8s MP4 Style Preview", use_container_width=True)

    with col2:
        st.markdown("#### Live 6-8s MP4 Style Video Preview")
        preview_placeholder = st.empty()
        
        preview_file = "caption_preview.mp4"
        
        if generate_btn:
            with st.spinner("Rendering 6-8 sec MP4 preview..."):
                generate_mp4_preview(selected_style, caption_mode, preview_file)
                st.success("Preview generated successfully!")
        
        if os.path.exists(preview_file):
            preview_placeholder.video(preview_file)
        else:
            preview_placeholder.info("Click 'Generate 6-8s MP4 Style Preview' to see how captions look.")

    # Return config dictionary for Master Pipeline consumption
    return {
        "enabled": enable_captions,
        "mode": caption_mode,
        "style_id": selected_style,
        "position_y": position_y,
        "scale": font_scale
    }