# ui_caption_section.py
import os
import streamlit as st
from caption_style_registry import CAPTION_STYLES
from caption_engine import generate_mp4_preview

def render_caption_ui_section():
    st.markdown("---")
    st.markdown("### 🎬 Dynamic Subtitle & Caption Engine")
    st.caption("Customize short video subtitles with 30+ ultra styles and 6-8 second video previews.")

    col1, col2 = st.columns([1, 1])

    with col1:
        enable_captions = st.checkbox("Enable Captions on Short Render", value=True, key="dyn_caption_enable")
        
        caption_mode = st.selectbox(
            "Caption Mode",
            options=["Phrase", "Word-by-Word", "Line"],
            index=0,
            key="dyn_caption_mode"
        )
        
        style_names = list(CAPTION_STYLES.keys())
        selected_style = st.selectbox(
            "Caption Style (30+ Premium Options)",
            options=style_names,
            index=0,
            key="dyn_caption_style"
        )
        
        y_offset = st.slider("Vertical Position (Y-Offset %)", 50, 90, 75, key="dyn_caption_yoffset")
        font_scale = st.slider("Font Scaling Factor", 0.5, 2.0, 1.0, 0.1, key="dyn_caption_scale")

        btn_generate = st.button("🎬 Generate 6-8s MP4 Style Preview", key="dyn_caption_btn_preview")

    with col2:
        st.markdown("#### Live 6-8s MP4 Style Video Preview")
        preview_path = "caption_preview.mp4"
        
        if btn_generate:
            with st.spinner("Rendering short video preview..."):
                try:
                    style_id_clean = selected_style.lower().replace(" ", "_")
                    mode_clean = caption_mode.lower().replace("-", "_")
                    generate_mp4_preview(style_id=style_id_clean, mode=mode_clean, output_path=preview_path)
                    st.success("Preview generated successfully!")
                except Exception as e:
                    st.error(f"Preview generation failed: {e}")

        # Compact video size fix (using nested sub-column)
        if os.path.exists(preview_path):
            v_col1, v_col2, v_col3 = st.columns([1, 2, 1])
            with v_col2:
                st.video(preview_path)
        else:
            st.info("Click 'Generate Preview' to view a 6-8s sample video.")

    return {
        "enabled": enable_captions,
        "mode": caption_mode.lower().replace("-", "_"),
        "style_id": selected_style.lower().replace(" ", "_"),
        "y_offset": y_offset,
        "font_scale": font_scale
    }