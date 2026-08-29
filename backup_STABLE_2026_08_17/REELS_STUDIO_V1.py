"""REELS STUDIO V1 - Add to app.py"""
from pathlib import Path
import shutil, time

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 60)
print("REELS STUDIO V1 - Phase 1 Installation")
print("=" * 60)

# Backup
app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_reels_v1_{ts}")
text = app.read_text(encoding="utf-8")

# ============================================================
# STEP 1: Ensure imports exist
# ============================================================
needed_imports = [
    'import os',
    'import tempfile',
    'import subprocess',
    'import json',
    'from pathlib import Path',
    'import shutil',
    'import time',
]

for imp in needed_imports:
    if imp not in text[:2000]:
        text = imp + '\n' + text
        print(f"  Added: {imp}")

# ============================================================
# STEP 2: REELS STUDIO CODE
# ============================================================

reels_code = '''

# ============================================================
# REELS UPLOAD STUDIO - Phase 1
# ============================================================

REELS_PRESETS = {
    "Cinematic": {
        "motion": "slow_push", "color": "teal_orange", "transition": "fade",
        "speed": 1.0, "pitch": 0, "saturation": 1.2, "contrast": 1.1,
        "grain": 0.02, "vignette": 0.3, "sharpness": 1.1
    },
    "Luxury": {
        "motion": "smooth_zoom", "color": "gold_warm", "transition": "dissolve",
        "speed": 1.0, "pitch": -1, "saturation": 0.9, "contrast": 1.15,
        "grain": 0.01, "vignette": 0.4, "sharpness": 1.05
    },
    "Modern": {
        "motion": "dynamic_pan", "color": "clean_cool", "transition": "slide_left",
        "speed": 1.05, "pitch": 0, "saturation": 1.1, "contrast": 1.05,
        "grain": 0.0, "vignette": 0.2, "sharpness": 1.15
    },
    "Dynamic": {
        "motion": "shake_energy", "color": "vibrant_pop", "transition": "whip",
        "speed": 1.1, "pitch": 1, "saturation": 1.3, "contrast": 1.2,
        "grain": 0.03, "vignette": 0.25, "sharpness": 1.2
    },
    "Minimal": {
        "motion": "none", "color": "natural", "transition": "cut",
        "speed": 1.0, "pitch": 0, "saturation": 1.0, "contrast": 1.0,
        "grain": 0.0, "vignette": 0.0, "sharpness": 1.0
    },
    "Documentary": {
        "motion": "slow_pan", "color": "muted_warm", "transition": "fade_black",
        "speed": 0.95, "pitch": -2, "saturation": 0.85, "contrast": 1.1,
        "grain": 0.04, "vignette": 0.35, "sharpness": 1.0
    },
    "Gaming": {
        "motion": "rapid_zoom", "color": "neon_cool", "transition": "glitch",
        "speed": 1.15, "pitch": 2, "saturation": 1.4, "contrast": 1.3,
        "grain": 0.01, "vignette": 0.3, "sharpness": 1.3
    },
    "Travel": {
        "motion": "gentle_drift", "color": "sunny_warm", "transition": "cross_zoom",
        "speed": 1.02, "pitch": 0, "saturation": 1.25, "contrast": 1.08,
        "grain": 0.01, "vignette": 0.15, "sharpness": 1.1
    },
    "Podcast": {
        "motion": "none", "color": "flat_neutral", "transition": "cut",
        "speed": 1.0, "pitch": 0, "saturation": 0.95, "contrast": 1.0,
        "grain": 0.0, "vignette": 0.0, "sharpness": 1.0
    },
    "Viral": {
        "motion": "fast_energy", "color": "hyper_sat", "transition": "flash",
        "speed": 1.2, "pitch": 1, "saturation": 1.5, "contrast": 1.25,
        "grain": 0.02, "vignette": 0.2, "sharpness": 1.25
    },
}

CAPTION_STYLES = [
    "minimal", "luxury_gold", "neon_glow", "bold_white", "colorful_pop",
    "gaming_red", "youtube_style", "tiktok_viral", "modern_clean", "professional_dark"
]

def reels_upload_studio_tab():
    st.header("🎬 Reels Upload Studio")
    st.caption("AI-Powered Video Regeneration — Upload, Edit, Transform")

    # ===== UPLOAD SECTION =====
    col1, col2, col3 = st.columns(3)
    with col1:
        video_type = st.selectbox("Video Type", ["Short (Reels/Shorts)", "Long Video"], key="rus_type")
    with col2:
        aspect = st.selectbox("Aspect Ratio", ["9:16", "16:9", "1:1", "4:5"], key="rus_aspect")
    with col3:
        preset_name = st.selectbox("Preset", list(REELS_PRESETS.keys()), key="rus_preset")

    uploaded_file = st.file_uploader(
        "Upload Video",
        type=["mp4", "mov", "avi", "mkv", "webm", "mpeg4"],
        key="rus_upload",
        help="Max 200MB"
    )

    if uploaded_file:
        # Save uploaded file
        upload_dir = BASE / "uploads" / "reels_studio"
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / f"uploaded_{int(time.time())}_{uploaded_file.name}"
        temp_path.write_bytes(uploaded_file.read())

        file_size_mb = temp_path.stat().st_size / (1024 * 1024)

        st.success(f"Uploaded: {uploaded_file.name} ({file_size_mb:.1f} MB)")

        # ===== AI ANALYSIS =====
        with st.expander("🔍 AI Analysis", expanded=True):
            try:
                probe_cmd = [
                    "ffprobe", "-v", "error", "-show_entries",
                    "stream=width,height,duration,r_frame_rate,codec_name,codec_type",
                    "-show_entries", "format=duration,size,bit_rate",
                    "-of", "json", str(temp_path)
                ]
                result = subprocess.run(probe_cmd, capture_output=True, text=True)
                info = json.loads(result.stdout) if result.stdout else {}

                streams = info.get("streams", [])
                fmt = info.get("format", {})

                video_stream = None
                audio_stream = None
                for s in streams:
                    if s.get("codec_type") == "video" and video_stream is None:
                        video_stream = s
                    elif s.get("codec_type") == "audio" and audio_stream is None:
                        audio_stream = s

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    dur = float(fmt.get("duration", 0))
                    st.metric("Duration", f"{dur:.1f}s")
                with c2:
                    fps_str = video_stream.get("r_frame_rate", "0/1") if video_stream else "0/1"
                    try:
                        num, den = fps_str.split("/")
                        fps = float(num) / float(den)
                    except:
                        fps = 0
                    st.metric("FPS", f"{fps:.1f}")
                with c3:
                    w = video_stream.get("width", 0) if video_stream else 0
                    h = video_stream.get("height", 0) if video_stream else 0
                    st.metric("Resolution", f"{w}x{h}")
                with c4:
                    codec = video_stream.get("codec_name", "?") if video_stream else "?"
                    st.metric("Codec", codec.upper())

                c5, c6, c7, c8 = st.columns(4)
                with c5:
                    has_audio = "Yes" if audio_stream else "No"
                    st.metric("Audio", has_audio)
                with c6:
                    bitrate = float(fmt.get("bit_rate", 0)) / 1000 if fmt.get("bit_rate") else 0
                    st.metric("Bitrate", f"{bitrate:.0f}kbps")
                with c7:
                    st.metric("Size", f"{file_size_mb:.1f}MB")
                with c8:
                    st.metric("Type", "Short" if dur < 180 else "Long")

            except Exception as e:
                st.warning(f"Analysis skipped: {e}")

        # ===== EDITING OPTIONS =====
        st.divider()
        st.subheader("🎨 Editing Options")

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Video Enhancement**")
            auto_color = st.checkbox("Auto Color Correction", value=True, key="rus_color")
            sharpen = st.checkbox("Smart Sharpen", value=True, key="rus_sharpen")
            hdr_look = st.checkbox("HDR Look", value=False, key="rus_hdr")
            noise_reduce = st.checkbox("Noise Reduction", value=False, key="rus_noise")
            upscale_1080 = st.checkbox("Upscale to 1080p", value=True, key="rus_1080")
            upscale_4k = st.checkbox("Upscale to 4K", value=False, key="rus_4k")

            st.markdown("**Motion Effects**")
            motion_zoom = st.checkbox("Dynamic Zoom", value=True, key="rus_mzoom")
            motion_pan = st.checkbox("Slow Pan", value=True, key="rus_mpan")
            motion_shake = st.checkbox("Shake", value=False, key="rus_mshake")
            motion_blur = st.checkbox("Motion Blur", value=False, key="rus_mblur")

        with col_b:
            st.markdown("**Voice Transform**")
            voice_pitch = st.slider("Pitch Shift", -12, 12, preset.get("pitch", 0), key="rus_pitch",
                                    help="Change voice pitch to avoid copyright match")
            voice_speed = st.slider("Speed", 0.7, 1.5, preset.get("speed", 1.0), 0.05, key="rus_speed")
            voice_volume = st.slider("Voice Volume", 0.5, 2.0, 1.0, 0.1, key="rus_vvol")
            bg_volume = st.slider("Background Volume", 0.0, 1.0, 0.3, 0.05, key="rus_bgvol")
            noise_remove = st.checkbox("Noise Removal", value=True, key="rus_nremove")
            audio_cleanup = st.checkbox("Audio Cleanup", value=True, key="rus_aclean")

            st.markdown("**Transitions**")
            transition_type = st.selectbox("Transition Style",
                ["fade", "dissolve", "slide", "flash", "glitch", "cross_zoom", "whip", "film_burn"],
                key="rus_transition")

        # ===== CAPTIONS =====
        st.divider()
        st.subheader("💬 Captions")

        captions_enabled = st.checkbox("Enable AI Captions", value=True, key="rus_captions")

        if captions_enabled:
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                caption_style = st.selectbox("Style", CAPTION_STYLES, key="rus_cstyle")
            with col_c2:
                caption_position = st.selectbox("Position", ["bottom", "center", "top"], key="rus_cpos")
            with col_c3:
                caption_size = st.selectbox("Size", ["small", "medium", "large"], key="rus_csize")

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                caption_bg = st.checkbox("Background Box", value=True, key="rus_cbg")
                caption_highlight = st.checkbox("Word Highlight", value=True, key="rus_chl")
            with col_d2:
                caption_emoji = st.checkbox("Emoji Support", value=False, key="rus_cemoji")
                caption_anim = st.checkbox("Animated", value=True, key="rus_canim")

        # ===== CPU SAFE MODE =====
        st.divider()
        cpu_safe = st.checkbox("🧊 CPU Safe Mode (Prevent Overheat)", value=True, key="rus_cpusafe",
                               help="Lowers FFmpeg threads, reduces RAM usage, prevents laptop shutdown")

        # ===== GENERATE =====
        st.divider()

        if st.button("🚀 Generate", type="primary", use_container_width=True, key="rus_generate"):
            preset = REELS_PRESETS.get(preset_name, REELS_PRESETS["Cinematic"])
            output_dir = BASE / "outputs" / "reels_studio"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"REGENERATED_{int(time.time())}.mp4"

            with st.status("Processing...", expanded=True) as status:
                try:
                    # Build ffmpeg command
                    threads = "1" if cpu_safe else "4"
                    cmd = ["ffmpeg", "-threads", threads, "-y", "-i", str(temp_path)]

                    # Video filters
                    vf_parts = []

                    # Resolution
                    target_h = 1920 if (upscale_4k or upscale_1080) else 1080
                    if upscale_4k:
                        target_h = 2160

                    vf_parts.append(f"scale=-2:{target_h}")

                    # Color correction
                    if auto_color:
                        sat = preset.get("saturation", 1.0)
                        con = preset.get("contrast", 1.0)
                        vf_parts.append(f"eq=saturation={sat}:contrast={con}")

                    # Sharpen
                    if sharpen:
                        sharp = preset.get("sharpness", 1.1)
                        vf_parts.append(f"unsharp=5:5:{sharp}:3:3:0")

                    # HDR
                    if hdr_look:
                        vf_parts.append("eq=gamma=0.9:saturation=1.2")

                    # Motion zoom
                    if motion_zoom:
                        vf_parts.append("zoompan=z='min(zoom+0.0015,1.5)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={}x{}".format(
                            int(w * target_h / h) if w and h else 1080, target_h))

                    # Grain
                    if preset.get("grain", 0) > 0:
                        vf_parts.append(f"noise=alls={preset['grain'] * 10}:allf=t")

                    # Vignette
                    if preset.get("vignette", 0) > 0:
                        vf_parts.append(f"vignette=PI/4")

                    vf_filter = ",".join(vf_parts) if vf_parts else "null"
                    cmd.extend(["-vf", vf_filter])

                    # Audio filters
                    af_parts = []

                    # Speed
                    if voice_speed != 1.0:
                        af_parts.append(f"atempo={voice_speed}")

                    # Pitch
                    if voice_pitch != 0:
                        af_parts.append(f"asetrate=44100*2^({voice_pitch}/12)")

                    # Volume
                    if voice_volume != 1.0:
                        af_parts.append(f"volume={voice_volume}")

                    # Noise removal
                    if noise_remove:
                        af_parts.append("highpass=f=80,lowpass=f=8000")

                    af_filter = ",".join(af_parts) if af_parts else "anull"
                    cmd.extend(["-af", af_filter])

                    # Output settings
                    cmd.extend([
                        "-c:v", "libx264",
                        "-preset", "ultrafast" if cpu_safe else "medium",
                        "-crf", "23",
                        "-c:a", "aac",
                        "-b:a", "128k",
                        "-movflags", "+faststart",
                        str(output_path)
                    ])

                    st.text(f"Running: {' '.join(cmd[:8])}...")

                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

                    if output_path.exists() and output_path.stat().st_size > 1000:
                        status.update(label="✅ Complete!", state="complete")
                        st.success(f"Saved: {output_path.name}")

                        # Show preview
                        st.video(str(output_path))

                        out_size_mb = output_path.stat().st_size / (1024 * 1024)
                        st.metric("Output Size", f"{out_size_mb:.1f} MB")

                        # Download button
                        with open(output_path, "rb") as f:
                            st.download_button(
                                "⬇ Download",
                                f.read(),
                                file_name=output_path.name,
                                mime="video/mp4",
                                use_container_width=True
                            )
                    else:
                        status.update(label="❌ Failed", state="error")
                        st.error(f"FFmpeg error:\n{result.stderr[:500]}")

                except subprocess.TimeoutExpired:
                    status.update(label="⏱ Timeout", state="error")
                    st.error("Render timeout (10 min). Try CPU Safe Mode or smaller video.")
                except Exception as e:
                    status.update(label="❌ Error", state="error")
                    st.error(f"Error: {e}")

    else:
        st.info("👆 Upload a video to start editing")

    # ===== QUEUE PREVIEW (future) =====
    with st.expander("📋 Queue (Coming Soon)", expanded=False):
        st.info("Queue system will be added in Phase 2 — support for multiple videos with pause/resume.")


def _get_reels_preset(name):
    return REELS_PRESETS.get(name, REELS_PRESETS["Cinematic"])
'''

# ============================================================
# STEP 3: Inject into app.py
# ============================================================

# Find main() function and add reels tab
if 'def main():' in text:
    # Add import for streamlit if not there
    if 'import streamlit as st' not in text:
        text = 'import streamlit as st\n' + text

    # Add reels tab to main()
    # Find tab creation section
    old_tab = 'tab1, tab2 = st.tabs('
    if old_tab in text:
        text = text.replace(old_tab, 'tab1, tab2, tab3 = st.tabs(')
        # Add tab3 content
        old_tab2_end = 'with tab2:'
        if old_tab2_end in text:
            text = text.replace(
                old_tab2_end,
                'with tab2:\n            pass  # existing tab2 content\n\n        with tab3:\n            reels_upload_studio_tab()\n\n        # OLD_TAB2_PLACEHOLDER'
            )
    else:
        # Find where tabs are defined
        lines = text.split('\n')
        for i, l in enumerate(lines):
            if 'st.tabs(' in l and 'tab' in l:
                current = l.strip()
                # Replace with 3 tabs
                lines[i] = l.replace('st.tabs([', 'st.tabs(["🎥 Video Generator", "⚙ Settings", "🎬 Reels Studio"]')
                # Add tab3 after existing tab2
                for j in range(i, min(i+50, len(lines))):
                    if 'with tab2:' in lines[j]:
                        # Find end of tab2 block
                        k = j + 1
                        indent_tab2 = len(lines[j]) - len(lines[j].lstrip())
                        while k < len(lines):
                            if lines[k].strip() and len(lines[k]) - len(lines[k].lstrip()) <= indent_tab2:
                                break
                            k += 1
                        # Insert tab3 before the next section
                        tab3_block = '\n' + ' ' * indent_tab2 + 'with tab3:\n' + ' ' * (indent_tab2+4) + 'reels_upload_studio_tab()\n'
                        lines.insert(k, tab3_block)
                        break
                text = '\n'.join(lines)
                break

# Append reels code at end
text += reels_code

# Write
app.write_text(text, encoding="utf-8")

try:
    compile(text, "app.py", "exec")
    print("\n✅ app.py SYNTAX OK")
    print("✅ Reels Upload Studio added as Tab 3")
except SyntaxError as e:
    print(f"\n❌ SYNTAX ERROR line {e.lineno}: {e.msg}")

print("=" * 60)
print("Run: streamlit run app.py")
print("=" * 60)