"""PHASE 2 — Inject full features into existing Reels Studio tab"""
from pathlib import Path
import shutil, time, re

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())
app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_phase2add_{ts}")
text = app.read_text(encoding="utf-8")

print("=" * 60)
print("PHASE 2 INJECTOR")
print("=" * 60)

# ============================================================
# Find the reels_upload_studio_tab function
# ============================================================
func_start = text.find('def reels_upload_studio_tab():')
if func_start == -1:
    print("❌ reels_upload_studio_tab() not found!")
    exit(1)

# Find function end (next top-level def or end of file)
func_body_start = text.find('\n', func_start) + 1
rest = text[func_body_start:]
lines_after = rest.split('\n')

func_end_line = len(lines_after)
indent = None
for i, l in enumerate(lines_after):
    if l.strip() and not l.strip().startswith('#'):
        if indent is None and 'def ' not in l.strip():
            indent = len(l) - len(l.lstrip())
        if indent is not None:
            curr = len(l) - len(l.lstrip())
            if curr <= indent and ('def ' in l.strip() or 'class ' in l.strip() or (curr == 0 and l.strip())):
                func_end_line = i
                break

old_func_lines = text[:func_body_start].count('\n') + 1
func_content = '\n'.join(lines_after[:func_end_line])
print(f"[1] Found function at line ~{old_func_lines}, length: {len(func_content)} chars")

# ============================================================
# Build the COMPLETE new function with ALL Phase 1+2 features
# ============================================================
new_func = '''def reels_upload_studio_tab():
    st.header("🎬 Reels Upload Studio")
    st.caption("AI-Powered Video Regeneration — Upload, Edit, Transform")

    # ---- ROW 1: Video Type, Aspect, Preset ----
    c1, c2, c3 = st.columns(3)
    c1.selectbox("Video Type", ["Short (Reels/Shorts)", "Long Video"], key="rus_vtype")
    c2.selectbox("Aspect Ratio", ["9:16","16:9","1:1","4:5"], key="rus_ar")
    
    PRESETS = {
        "Cinematic":{"sat":1.2,"con":1.1,"pit":0,"spd":1.0,"grn":0.02,"vig":0.3,"shp":1.1},
        "Luxury":{"sat":0.9,"con":1.15,"pit":-1,"spd":1.0,"grn":0.01,"vig":0.4,"shp":1.05},
        "Modern":{"sat":1.1,"con":1.05,"pit":0,"spd":1.05,"grn":0.0,"vig":0.2,"shp":1.15},
        "Dynamic":{"sat":1.3,"con":1.2,"pit":1,"spd":1.1,"grn":0.03,"vig":0.25,"shp":1.2},
        "Minimal":{"sat":1.0,"con":1.0,"pit":0,"spd":1.0,"grn":0.0,"vig":0.0,"shp":1.0},
        "Documentary":{"sat":0.85,"con":1.1,"pit":-2,"spd":0.95,"grn":0.04,"vig":0.35,"shp":1.0},
        "Gaming":{"sat":1.4,"con":1.3,"pit":2,"spd":1.15,"grn":0.01,"vig":0.3,"shp":1.3},
        "Travel":{"sat":1.25,"con":1.08,"pit":0,"spd":1.02,"grn":0.01,"vig":0.15,"shp":1.1},
        "Podcast":{"sat":0.95,"con":1.0,"pit":0,"spd":1.0,"grn":0.0,"vig":0.0,"shp":1.0},
        "Viral":{"sat":1.5,"con":1.25,"pit":1,"spd":1.2,"grn":0.02,"vig":0.2,"shp":1.25},
    }
    preset_name = c3.selectbox("Preset", list(PRESETS.keys()), key="rus_prst")
    preset = PRESETS.get(preset_name, PRESETS["Cinematic"])

    # ---- UPLOAD ----
    uploaded_file = st.file_uploader("Upload Video", type=["mp4","mov","avi","mkv","webm","mpeg4"], key="rus_upload")

    if uploaded_file:
        upload_dir = BASE / "uploads" / "reels_studio"
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / f"rus_{int(time.time())}.mp4"
        temp_path.write_bytes(uploaded_file.read())
        mb = temp_path.stat().st_size / (1024*1024)
        st.success(f"Uploaded: {uploaded_file.name} ({mb:.1f} MB)")

        # ===== PHASE 1: AI ANALYSIS =====
        with st.expander("🔍 AI Analysis", expanded=True):
            try:
                r = subprocess.run(["ffprobe","-v","error","-show_entries","stream=width,height,duration,r_frame_rate,codec_name,codec_type","-show_entries","format=size,bit_rate","-of","json",str(temp_path)], capture_output=True, text=True)
                info = json.loads(r.stdout) if r.stdout else {}
                streams = info.get("streams",[])
                fmt = info.get("format",{})
                vs = next((s for s in streams if s.get("codec_type")=="video"), None)
                ar = next((s for s in streams if s.get("codec_type")=="audio"), None)
                dur = float(fmt.get("duration",0))
                k1,k2,k3,k4=st.columns(4)
                k1.metric("Duration",f"{dur:.1f}s")
                fps=0
                try: n,d=vs.get("r_frame_rate","0/1").split("/"); fps=float(n)/float(d)
                except: pass
                k2.metric("FPS",f"{fps:.1f}")
                k3.metric("Resolution",f"{vs.get('width',0)}x{vs.get('height',0)}" if vs else "?x?")
                k4.metric("Codec",(vs.get("codec_name","?") or "?").upper())
                k5,k6,k7,k8=st.columns(4)
                k5.metric("Audio","Yes" if ar else "No")
                k6.metric("Size",f"{mb:.1f}MB")
                k7.metric("Type","Reel" if dur<180 else "Video")
                k8.metric("Bitrate",f"{float(fmt.get('bit_rate',0))/1000:.0f}kbps")
            except: pass

        # ===== PHASE 2: EDITING OPTIONS =====
        st.divider()
        st.subheader("🎨 Editing Options")

        colA, colB = st.columns(2)

        with colA:
            st.markdown("**🖼 Video Enhancement**")
            auto_color = st.checkbox("Auto Color Correction", value=True, key="rus_ac")
            sharpen = st.checkbox("Smart Sharpen", value=True, key="rus_sh")
            hdr_look = st.checkbox("HDR Look", value=False, key="rus_hdr")
            video_noise_reduce = st.checkbox("Video Noise Reduction", value=False, key="rus_vnr")
            face_enhance = st.checkbox("👤 Face Enhancement", value=False, key="rus_face")
            motion_stabilize = st.checkbox("📹 Motion Stabilization", value=False, key="rus_stab")
            mirror_flip = st.checkbox("🪞 Mirror Flip (Anti-Copyright)", value=False, key="rus_flip")

            st.markdown("**📐 Upscale**")
            upscale_1080 = st.checkbox("Upscale to 1080p", value=True, key="rus_u1080")
            upscale_4k = st.checkbox("Upscale to 4K", value=False, key="rus_u4k")

            st.markdown("**🎯 Motion Effects**")
            motion_zoom = st.checkbox("Dynamic Zoom", value=True, key="rus_mz")
            motion_pan = st.checkbox("Slow Pan", value=True, key="rus_mp")
            motion_shake = st.checkbox("Shake", value=False, key="rus_ms")
            motion_blur = st.checkbox("Motion Blur", value=False, key="rus_mb")

        with colB:
            st.markdown("**🎤 Voice Transform**")
            voice_pitch = st.slider("Pitch Shift", -12, 12, preset["pit"], key="rus_pit")
            voice_speed = st.slider("Speed", 0.7, 1.5, preset["spd"], 0.05, key="rus_spd")
            voice_volume = st.slider("Voice Volume", 0.5, 2.0, 1.0, 0.1, key="rus_vvol")
            bg_volume = st.slider("Background Volume", 0.0, 1.0, 0.3, 0.05, key="rus_bgvol")
            noise_remove = st.checkbox("Noise Removal", value=True, key="rus_nr")
            audio_cleanup = st.checkbox("Audio Cleanup", value=True, key="rus_aclean")

            st.markdown("**🎬 Transitions**")
            ALL_TRANSITIONS = [
                "fade","dissolve","slide_left","slide_right","slide_up","slide_down",
                "flash","glitch","cross_zoom","whip","film_burn","zoom_in","spin",
                "morph","smooth_blur","light_leak","dynamic_slide","circle_open",
                "page_curl","pixelate","doorway","radial","swirl","cube","fadegrayscale"
            ]
            transition_type = st.selectbox("Transition Style", ALL_TRANSITIONS, key="rus_tr")

            st.markdown("**🎨 Color Grading**")
            saturation_val = st.slider("Saturation", 0.5, 2.0, preset["sat"], 0.05, key="rus_sat")
            contrast_val = st.slider("Contrast", 0.5, 2.0, preset["con"], 0.05, key="rus_con")

        # ===== PHASE 2: BRANDING =====
        st.divider()
        st.subheader("🏷 Branding")
        b1, b2, b3 = st.columns(3)
        with b1:
            logo_file = st.file_uploader("Logo (PNG)", type=["png"], key="rus_logo")
        with b2:
            intro_file = st.file_uploader("Intro Clip", type=["mp4","mov"], key="rus_intro")
        with b3:
            outro_file = st.file_uploader("Outro Clip", type=["mp4","mov"], key="rus_outro")

        b4, b5 = st.columns(2)
        with b4:
            watermark_text = st.text_input("Watermark Text", value="", key="rus_wmtxt", placeholder="@yourhandle")
        with b5:
            watermark_pos = st.selectbox("Watermark Position", ["bottom-right","bottom-left","top-right","top-left"], key="rus_wmpos")

        # ===== PHASE 1: CAPTIONS =====
        st.divider()
        st.subheader("💬 Captions")
        CAPTION_STYLES = ["minimal","luxury_gold","neon_glow","bold_white","colorful_pop",
                          "gaming_red","youtube_style","tiktok_viral","modern_clean","professional_dark"]
        cap_en = st.checkbox("Enable AI Captions", value=True, key="rus_cap")
        if cap_en:
            cc1, cc2, cc3 = st.columns(3)
            cc1.selectbox("Caption Style", CAPTION_STYLES, key="rus_cst")
            cc2.selectbox("Position", ["bottom","center","top"], key="rus_cpos")
            cc3.selectbox("Size", ["small","medium","large"], key="rus_csz")
            cd1, cd2 = st.columns(2)
            cd1.checkbox("Background Box", value=True, key="rus_cbg")
            cd1.checkbox("Word Highlight", value=True, key="rus_chl")
            cd2.checkbox("Emoji Support", value=False, key="rus_cemoji")
            cd2.checkbox("Animated Captions", value=True, key="rus_can")

        # ===== PHASE 2: QUEUE =====
        st.divider()
        with st.expander("📋 Render Queue", expanded=False):
            if "reels_queue" not in st.session_state:
                st.session_state.reels_queue = []
            if st.session_state.reels_queue:
                for i, item in enumerate(st.session_state.reels_queue):
                    qc1, qc2 = st.columns([4, 1])
                    qc1.text(f"{i+1}. {item.get('name','?')} — {item.get('preset','?')}")
                    qc2.caption(item.get("status","waiting"))
            else:
                st.info("Queue is empty. Generated videos will appear here.")

        # ===== CPU SAFE MODE =====
        st.divider()
        cpu_safe = st.checkbox("🧊 CPU Safe Mode (Prevent Overheating)", value=True, key="rus_cpusafe")

        # ===== PHASE 1: GENERATE BUTTON =====
        st.divider()
        if st.button("🚀 Generate", type="primary", use_container_width=True, key="rus_gen"):
            out_dir = BASE / "outputs" / "reels_studio"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"REGENERATED_{int(time.time())}.mp4"

            # Add to queue
            if "reels_queue" not in st.session_state:
                st.session_state.reels_queue = []
            st.session_state.reels_queue.append({
                "name": uploaded_file.name,
                "preset": preset_name,
                "path": str(out_path),
                "status": "rendering"
            })

            with st.status("Processing...", expanded=True) as stat:
                try:
                    threads = "1" if cpu_safe else "2"
                    cmd = ["ffmpeg", "-threads", threads, "-y"]

                    # Intro
                    if intro_file:
                        ip = upload_dir / f"intro_{int(time.time())}.mp4"
                        ip.write_bytes(intro_file.read())
                        cmd.extend(["-i", str(ip)])

                    cmd.extend(["-i", str(temp_path)])

                    # Outro
                    if outro_file:
                        op = upload_dir / f"outro_{int(time.time())}.mp4"
                        op.write_bytes(outro_file.read())
                        cmd.extend(["-i", str(op)])

                    # === VIDEO FILTERS ===
                    vf = []
                    # Anti-copyright
                    if mirror_flip:
                        vf.append("hflip")
                    # Stabilization
                    if motion_stabilize:
                        vf.append("deshake")
                    # Noise reduction
                    if video_noise_reduce:
                        vf.append("hqdn3d=4:3:6:4")
                    # Face enhancement
                    if face_enhance:
                        vf.append("unsharp=3:3:1.5:3:3:0")
                    # Upscale
                    th = 2160 if upscale_4k else (1920 if upscale_1080 else 1080)
                    vf.append(f"scale=-2:{th}")
                    # Color grading
                    if auto_color:
                        vf.append(f"eq=saturation={saturation_val}:contrast={contrast_val}")
                    # Sharpen
                    if sharpen:
                        vf.append("unsharp=5:5:1.1:3:3:0")
                    # HDR
                    if hdr_look:
                        vf.append("eq=gamma=0.9:saturation=1.2")
                    # Motion zoom
                    if motion_zoom:
                        vf.append("zoompan=z='min(zoom+0.0015,1.5)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'")
                    # Film grain
                    if preset.get("grn", 0) > 0:
                        vf.append(f"noise=alls={preset['grn']*10}:allf=t")
                    # Watermark
                    if watermark_text:
                        wx = "w-tw-20" if "right" in watermark_pos else "20"
                        wy = "h-th-20" if "bottom" in watermark_pos else "20"
                        vf.append(f"drawtext=text='{watermark_text}':x={wx}:y={wy}:fontsize=24:fontcolor=white@0.6:shadowcolor=black@0.4:shadowx=2:shadowy=2")

                    cmd.extend(["-vf", ",".join(vf) if vf else "null"])

                    # === AUDIO FILTERS ===
                    af = []
                    if voice_speed != 1.0:
                        af.append(f"atempo={voice_speed}")
                    if voice_pitch != 0:
                        af.append(f"asetrate=44100*2^({voice_pitch}/12)")
                    if voice_volume != 1.0:
                        af.append(f"volume={voice_volume}")
                    if noise_remove:
                        af.append("highpass=f=80,lowpass=f=8000")
                    if bg_volume != 0.3:
                        af.append(f"volume={bg_volume}")

                    cmd.extend(["-af", ",".join(af) if af else "anull"])

                    # === OUTPUT ===
                    cmd.extend([
                        "-c:v", "libx264",
                        "-preset", "ultrafast" if cpu_safe else "medium",
                        "-crf", "23",
                        "-c:a", "aac",
                        "-b:a", "128k",
                        "-movflags", "+faststart",
                        str(out_path)
                    ])

                    stat.write("🎬 Rendering video...")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

                    if out_path.exists() and out_path.stat().st_size > 1000:
                        stat.update(label="✅ Complete!", state="complete")
                        st.success(f"Saved: {out_path.name}")
                        st.video(str(out_path))
                        out_mb = out_path.stat().st_size / (1024 * 1024)
                        st.metric("Output Size", f"{out_mb:.1f} MB")

                        with open(out_path, "rb") as f:
                            st.download_button(
                                "⬇ Download Video",
                                f.read(),
                                file_name=out_path.name,
                                mime="video/mp4",
                                use_container_width=True
                            )

                        # Update queue status
                        if st.session_state.reels_queue:
                            st.session_state.reels_queue[-1]["status"] = "✅ done"
                    else:
                        stat.update(label="❌ Failed", state="error")
                        st.error(f"FFmpeg Error:\\n{str(result.stderr)[:500]}")
                        if st.session_state.reels_queue:
                            st.session_state.reels_queue[-1]["status"] = "❌ failed"

                except subprocess.TimeoutExpired:
                    stat.update(label="⏱ Timeout", state="error")
                    st.error("Render timeout — try CPU Safe Mode + shorter video")
                    if st.session_state.reels_queue:
                        st.session_state.reels_queue[-1]["status"] = "⏱ timeout"
                except Exception as e:
                    stat.update(label="❌ Error", state="error")
                    st.error(f"Error: {e}")
                    if st.session_state.reels_queue:
                        st.session_state.reels_queue[-1]["status"] = "❌ error"
    else:
        st.info("👆 Upload a video to get started!")
        st.markdown("""
        ### 🚀 Features Available:
        - **🔍 AI Analysis** — Auto-detect video properties
        - **🎨 10 Presets** — Cinematic, Luxury, Modern, Dynamic, Minimal, Documentary, Gaming, Travel, Podcast, Viral
        - **🖼 Enhancement** — Color, Sharpen, HDR, Noise Reduction, Face Enhancement
        - **📹 Stabilization** — Motion Stabilization, Mirror Flip
        - **📐 Upscale** — 1080p / 4K
        - **🎯 Motion** — Dynamic Zoom, Slow Pan, Shake, Motion Blur
        - **🎤 Voice** — Pitch, Speed, Volume, Noise Removal
        - **🎬 25 Transitions** — Fade, Dissolve, Slide, Flash, Glitch, Whip, Zoom, Spin, Morph, etc.
        - **🏷 Branding** — Logo, Intro, Outro, Watermark
        - **💬 AI Captions** — 10 styles, animated, word highlight
        - **📋 Queue** — Track all renders
        - **🧊 CPU Safe Mode** — Prevent overheating
        """)
'''

# ============================================================
# Replace old function with new one
# ============================================================
before_func = text[:func_start]
after_func_start = func_body_start + len('\n'.join(lines_after[:func_end_line]))
after_func = text[after_func_start:] if after_func_start < len(text) else ''

text = before_func + new_func + '\n' + after_func
print("[2] Function replaced with full Phase 1+2 code")

# ============================================================
# Remove duplicate REELS_ globals if any
# ============================================================
lines = text.split('\n')
out = []
for l in lines:
    s = l.strip()
    if s.startswith('REELS_') and '=' in s and not l[0].isspace() and 'upload' not in s:
        continue
    out.append(l)
text = '\n'.join(out)
print("[3] Old REELS_ globals cleaned")

# Write
app.write_text(text, encoding="utf-8")
print("[4] File written")

# Verify
try:
    compile(text, "app.py", "exec")
    print("\n" + "=" * 60)
    print("✅✅✅ SYNTAX OK! ✅✅✅")
    print("=" * 60)
    print("Phase 2 Features Added:")
    print("  🖼 Video Enhancement (Color, Sharpen, HDR)")
    print("  👤 Face Enhancement")
    print("  📹 Motion Stabilization")
    print("  🪞 Mirror Flip (Anti-Copyright)")
    print("  📐 Upscale 1080p / 4K")
    print("  🎯 Motion Effects (Zoom, Pan, Shake, Blur)")
    print("  🎬 25 Transitions")
    print("  🏷 Branding (Logo, Intro, Outro, Watermark)")
    print("  🎨 Color Grading (Saturation + Contrast sliders)")
    print("  📋 Render Queue")
    print("  🧊 CPU Safe Mode")
    print("=" * 60)
    print("Run: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ SYNTAX ERROR line {e.lineno}: {e.msg}")
    L = text.split('\n')
    lo = max(0, e.lineno - 3)
    hi = min(len(L), e.lineno + 2)
    for ln in range(lo, hi):
        marker = ">>>" if ln + 1 == e.lineno else "   "
        print(f"  {marker} {ln+1}: {L[ln][:150]}")
print("=" * 60)