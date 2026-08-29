"""
Reels Upload Studio - AI Video Regeneration Page
Standalone Streamlit page for short & long video upload with AI editing.
"""
import streamlit as st
import os
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="Reels Upload Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #888;
        margin-bottom: 2rem;
    }
    .section-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        border: 1px solid #2a2a4a;
    }
    .section-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #e0e0ff;
        margin-bottom: 16px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .status-ready { background: #1a3a1a; color: #4ade80; }
    .status-processing { background: #3a2a1a; color: #fbbf24; }
    .status-done { background: #1a2a3a; color: #60a5fa; }
    .upload-zone {
        border: 2px dashed #4a4a6a;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .upload-zone:hover {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.05);
    }
    .preset-btn {
        padding: 10px 18px;
        border-radius: 10px;
        border: 2px solid #3a3a5a;
        background: transparent;
        color: #ccc;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.9rem;
        margin: 4px;
    }
    .preset-btn:hover, .preset-btn.active {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.15);
        color: #fff;
    }
    .output-preview {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #2a2a4a;
    }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───
defaults = {
    "rs_video_type": "short",
    "rs_uploaded_file": None,
    "rs_uploaded_path": None,
    "rs_aspect_ratio": "9:16",
    "rs_niche": "auto",
    "rs_preset_number": 1,
    "rs_voice_transform": False,
    "rs_voice_pitch": 0.0,
    "rs_bg_music": False,
    "rs_bg_music_file": None,
    "rs_bg_music_volume": 0.3,
    "rs_captions_enabled": True,
    "rs_caption_style": "kinetic",
    "rs_processing": False,
    "rs_output_path": None,
    "rs_output_info": None,
    "rs_progress": 0,
    "rs_status_msg": "",
    "rs_logs": []
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Helper Functions ───
def add_log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.rs_logs.append(f"[{ts}] {msg}")

def reset_session():
    for k, v in defaults.items():
        st.session_state[k] = v

# ─── Main UI ───
st.markdown('<div class="main-header">🎬 Reels Upload Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Video Regeneration — Upload, Edit, Transform</div>', unsafe_allow_html=True)

# ─── Sidebar ───
with st.sidebar:
    st.markdown("### ⚙️ Video Settings")

    st.markdown("**📐 Video Type**")
    video_type = st.radio(
        "Video Type",
        options=["short", "long"],
        format_func=lambda x: "📱 Short Video (Reels/Shorts)" if x == "short" else "🎥 Long Video",
        key="rs_video_type",
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("**📏 Aspect Ratio**")
    if video_type == "short":
        aspect_options = ["9:16 (Vertical)", "1:1 (Square)", "4:5 (Portrait)"]
        aspect_values = ["9:16", "1:1", "4:5"]
    else:
        aspect_options = ["16:9 (Landscape)", "9:16 (Vertical)", "1:1 (Square)"]
        aspect_values = ["16:9", "9:16", "1:1"]
    aspect_idx = st.selectbox(
        "Aspect Ratio",
        options=range(len(aspect_options)),
        format_func=lambda i: aspect_options[i],
        index=0 if st.session_state.rs_aspect_ratio == "9:16" else
              1 if st.session_state.rs_aspect_ratio in ("1:1", "16:9") else 2,
        label_visibility="collapsed"
    )
    st.session_state.rs_aspect_ratio = aspect_values[aspect_idx]

    st.markdown("---")
    st.markdown("**🎨 Niche & Preset**")
    niche_options = [
        "auto", "motivation", "gaming", "cooking", "tech_review",
        "vlog", "fitness", "educational", "comedy"
    ]
    niche_labels = [
        "🤖 Auto Detect", "🔥 Motivation", "🎮 Gaming", "🍳 Cooking",
        "💻 Tech Review", "📹 Vlog", "💪 Fitness", "📚 Educational", "😂 Comedy"
    ]
    niche_idx = st.selectbox(
        "Niche",
        options=range(len(niche_options)),
        format_func=lambda i: niche_labels[i],
        index=0,
        label_visibility="collapsed"
    )
    st.session_state.rs_niche = niche_options[niche_idx]

    st.markdown("**Preset Style**")
    preset_cols = st.columns(4)
    for i in range(8):
        with preset_cols[i % 4]:
            label = f"Style {i+1}" if i % 4 == i % 4 else f"{i+1}"
            if st.button(str(i+1), key=f"preset_{i+1}",
                        use_container_width=True,
                        type="primary" if st.session_state.rs_preset_number == i+1 else "secondary"):
                st.session_state.rs_preset_number = i + 1

    st.markdown("---")
    st.markdown("**🎙️ Voice Transform**")
    voice_enabled = st.checkbox("Enable Voice Transformation", key="rs_voice_transform")
    if voice_enabled:
        st.session_state.rs_voice_pitch = st.slider(
            "Pitch Shift", min_value=-1.0, max_value=1.0, value=0.0, step=0.1
        )

    st.markdown("---")
    st.markdown("**🎵 Background Music**")
    bg_enabled = st.checkbox("Add Background Music", key="rs_bg_music")
    if bg_enabled:
        bg_file = st.file_uploader("Upload Music (mp3/wav)", type=["mp3", "wav"], key="rs_bg_music_file")
        st.session_state.rs_bg_music_volume = st.slider(
            "Music Volume", min_value=0.05, max_value=1.0, value=0.3, step=0.05
        )

    st.markdown("---")
    st.markdown("**✍️ Captions**")
    st.checkbox("Auto-Generate Captions", value=True, key="rs_captions_enabled")
    if st.session_state.rs_captions_enabled:
        st.selectbox(
            "Caption Style",
            options=["kinetic", "classic", "minimal", "bold"],
            format_func=lambda x: x.title(),
            key="rs_caption_style"
        )

    st.markdown("---")
    if st.button("🔄 Reset All Settings", use_container_width=True):
        reset_session()
        st.rerun()

# ─── Main Content ───
col1, col2 = st.columns([3, 2])

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📤 Upload Video</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        f"Drop your {video_type} video here",
        type=["mp4", "mov", "avi", "mkv", "webm"],
        key="rs_uploaded_file",
        label_visibility="collapsed"
    )

    if uploaded:
        # Save to temp
        suffix = Path(uploaded.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=PROJECT_ROOT) as tmp:
            tmp.write(uploaded.read())
            st.session_state.rs_uploaded_path = tmp.name

        file_size_mb = uploaded.size / (1024 * 1024)
        st.success(f"✅ Uploaded: **{uploaded.name}** ({file_size_mb:.1f} MB)")
        add_log(f"Uploaded: {uploaded.name} ({file_size_mb:.1f}MB)")

        # Show video preview
        st.video(st.session_state.rs_uploaded_path)
    else:
        st.info("👆 Upload a video to get started")

    st.markdown('</div>', unsafe_allow_html=True)

    # ─── Process Button ───
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🚀 Process Video</div>', unsafe_allow_html=True)

    can_process = st.session_state.rs_uploaded_path and not st.session_state.rs_processing

    if st.button("🎬 Start AI Regeneration", type="primary", use_container_width=True, disabled=not can_process):
        st.session_state.rs_processing = True
        st.session_state.rs_progress = 0
        st.session_state.rs_output_path = None
        st.session_state.rs_output_info = None
        st.rerun()

    if st.session_state.rs_processing:
        progress_bar = st.progress(st.session_state.rs_progress / 100)
        st.caption(f"Status: {st.session_state.rs_status_msg}")

        # ─── Run Processing ───
        try:
            from reels_editing_engine import ReelsEditingEngine

            engine = ReelsEditingEngine(
                video_path=st.session_state.rs_uploaded_path,
                video_type=st.session_state.rs_video_type,
                aspect_ratio=st.session_state.rs_aspect_ratio,
                niche=st.session_state.rs_niche,
                preset_number=st.session_state.rs_preset_number,
                voice_transform=st.session_state.rs_voice_transform,
                voice_pitch=st.session_state.rs_voice_pitch,
                bg_music_path=st.session_state.rs_bg_music_file,
                bg_music_volume=st.session_state.rs_bg_music_volume,
            )

            status = engine.process()

            if status.get("success"):
                st.session_state.rs_output_path = status.get("output_path")
                st.session_state.rs_output_info = status
                st.session_state.rs_progress = 100
                st.session_state.rs_status_msg = "✅ Complete!"
                add_log("Processing complete!")
            else:
                st.error(f"❌ Error: {status.get('error', 'Unknown')}")
                add_log(f"ERROR: {status.get('error', 'Unknown')}")
                st.session_state.rs_processing = False

        except ImportError:
            st.warning("⚠️ reels_editing_engine module not found. Running in demo mode...")
            # Simulate processing
            for pct in range(0, 101, 10):
                time.sleep(0.3)
                st.session_state.rs_progress = pct
                st.session_state.rs_status_msg = f"Processing... {pct}%"
                progress_bar.progress(pct / 100)
            # Demo output
            st.session_state.rs_output_path = st.session_state.rs_uploaded_path
            st.session_state.rs_output_info = {
                "success": True,
                "output_path": st.session_state.rs_uploaded_path,
                "seed": "demo-1234",
                "unique_id": "rs_demo_001",
                "size_mb": round(os.path.getsize(st.session_state.rs_uploaded_path) / (1024*1024), 1) if os.path.exists(st.session_state.rs_uploaded_path) else 0,
                "duration": 15.0
            }
            st.session_state.rs_progress = 100
            st.session_state.rs_status_msg = "✅ Complete (Demo)"
            add_log("Processing complete (demo mode)")

        except Exception as e:
            st.error(f"❌ Processing Error: {str(e)}")
            add_log(f"ERROR: {str(e)}")
            st.session_state.rs_processing = False

        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ─── Right Column - Output Preview ───
with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📺 Output Preview</div>', unsafe_allow_html=True)

    if st.session_state.rs_output_path and os.path.exists(st.session_state.rs_output_path):
        st.video(st.session_state.rs_output_path)
        st.success("✅ Regenerated Video Ready")
    else:
        st.info("⌛ Output will appear here after processing")

    # Show info if available
    if st.session_state.rs_output_info:
        output_info = st.session_state.rs_output_info
        st.markdown("---")
        st.markdown("**📋 Technical Details:**")
        st.caption(f"Render Seed: `{output_info.get('seed', 'N/A')}`")
        st.caption(f"Unique ID: `{output_info.get('unique_id', 'N/A')}`")
        st.caption(f"Output Size: {output_info.get('size_mb', 'N/A')} MB")
        st.caption(f"Duration: {output_info.get('duration', 0):.1f}s")

        # Download button
        if st.session_state.rs_output_path and os.path.exists(st.session_state.rs_output_path):
            with open(st.session_state.rs_output_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Video",
                    data=f,
                    file_name=f"reels_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
            st.markdown('<div style="margin-top:8px;"></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ─── Logs Panel ───
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📝 Processing Logs</div>', unsafe_allow_html=True)
    if st.session_state.rs_logs:
        for log in st.session_state.rs_logs[-10:]:  # last 10
            st.caption(log)
    else:
        st.caption("No logs yet...")
    st.markdown('</div>', unsafe_allow_html=True)

# ─── Footer ───
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#666;font-size:0.8rem;'>"
    "Reels Upload Studio v2.0 • AI Video Regeneration • "
    "Bypass YouTube Reused Content Policy with Unique AI Editing"
    "</div>",
    unsafe_allow_html=True
)
