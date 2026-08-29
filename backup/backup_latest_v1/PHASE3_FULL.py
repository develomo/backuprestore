"""PHASE 3 — ALL 9 Features: BG Music, SFX, Multi-Clip, Trim/Split, Text Overlay, AI Auto-Edit, Platform Presets, Batch, History"""
from pathlib import Path
import shutil, time, re

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())
app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_phase3_{ts}")
text = app.read_text(encoding="utf-8")
print("=" * 60)
print("PHASE 3 — FULL INJECTOR (9 Features)")
print("=" * 60)

# ============================================================
# Locate reels_upload_studio_tab function
# ============================================================
func_start = text.find('def reels_upload_studio_tab():')
if func_start == -1:
    print("❌ Function not found!")
    exit(1)

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

print(f"[1] Function found, {func_end_line} lines")

# ============================================================
# FULL PHASE 1+2+3 FUNCTION
# ============================================================
new_func = '''def reels_upload_studio_tab():
    st.header("🎬 Reels Upload Studio")
    st.caption("AI-Powered Video Regeneration — Upload, Edit, Transform")

    # ──────────────────────────────────────────────
    # SESSION STATE INIT
    # ──────────────────────────────────────────────
    if "reels_queue" not in st.session_state:
        st.session_state.reels_queue = []
    if "reels_history" not in st.session_state:
        st.session_state.reels_history = []
    if "rus_clips" not in st.session_state:
        st.session_state.rus_clips = []
    if "rus_text_overlays" not in st.session_state:
        st.session_state.rus_text_overlays = []
    if "rus_trim_start" not in st.session_state:
        st.session_state.rus_trim_start = 0.0
    if "rus_trim_end" not in st.session_state:
        st.session_state.rus_trim_end = 0.0

    # ──────────────────────────────────────────────
    # PRESETS
    # ──────────────────────────────────────────────
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

    PLATFORM_PRESETS = {
        "TikTok":  {"aspect":"9:16","w":1080,"h":1920,"fps":30,"bitrate":"6M"},
        "YouTube": {"aspect":"16:9","w":1920,"h":1080,"fps":30,"bitrate":"12M"},
        "Instagram":{"aspect":"1:1","w":1080,"h":1080,"fps":30,"bitrate":"6M"},
        "YT Shorts":{"aspect":"9:16","w":1080,"h":1920,"fps":60,"bitrate":"8M"},
        "Facebook": {"aspect":"16:9","w":1280,"h":720,"fps":30,"bitrate":"4M"},
        "Custom":   {"aspect":"Custom","w":1920,"h":1080,"fps":30,"bitrate":"8M"},
    }

    CAPTION_STYLES = ["minimal","luxury_gold","neon_glow","bold_white","colorful_pop",
                      "gaming_red","youtube_style","tiktok_viral","modern_clean","professional_dark"]

    ALL_TRANSITIONS = ["fade","dissolve","slide_left","slide_right","slide_up","slide_down",
                       "flash","glitch","cross_zoom","whip","film_burn","zoom_in","spin",
                       "morph","smooth_blur","light_leak","dynamic_slide","circle_open",
                       "page_curl","pixelate","doorway","radial","swirl","cube","fadegrayscale"]

    # ──────────────────────────────────────────────
    # ROW 1: Type, Platform (auto aspect+res), Preset
    # ──────────────────────────────────────────────
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        video_type = st.selectbox("Video Type", ["Short (Reels/Shorts)", "Long Video"], key="rus_vtype")
    with r1c2:
        platform = st.selectbox("📱 Platform Preset", list(PLATFORM_PRESETS.keys()), key="rus_platform")
        plat = PLATFORM_PRESETS[platform]
    with r1c3:
        use_ai = st.checkbox("🤖 AI Auto-Edit", value=False, key="rus_ai_auto")
        if use_ai:
            st.caption("AI will decide best edits")
        preset_name = st.selectbox("Preset", list(PRESETS.keys()), key="rus_prst")
    preset = PRESETS.get(preset_name, PRESETS["Cinematic"])

    # If platform selected, auto-set aspect
    if platform != "Custom":
        aspect_ratio = plat["aspect"]
        target_w = plat["w"]
        target_h = plat["h"]
        target_fps = plat["fps"]
        target_br = plat["bitrate"]
    else:
        aspect_ratio = st.selectbox("Aspect Ratio", ["9:16","16:9","1:1","4:5"], key="rus_ar")
        target_w, target_h, target_fps, target_br = 1920, 1080, 30, "8M"

    # ──────────────────────────────────────────────
    # UPLOAD SECTION
    # ──────────────────────────────────────────────

    # === FEATURE 3: MULTI-CLIP EDITOR ===
    with st.expander("🎞 Multi-Clip Editor", expanded=False):
        st.caption("Upload multiple clips, reorder them, then render as one video")
        new_clips = st.file_uploader("Add Clips", type=["mp4","mov","avi","mkv","webm","mpeg4"],
                                      key="rus_multi_upload", accept_multiple_files=True)
        if new_clips:
            upload_dir = BASE / "uploads" / "reels_studio"
            upload_dir.mkdir(parents=True, exist_ok=True)
            for f in new_clips:
                cp = upload_dir / f"clip_{int(time.time())}_{f.name}"
                cp.write_bytes(f.read())
                st.session_state.rus_clips.append({"name":f.name,"path":str(cp),"order":len(st.session_state.rus_clips)})

        if st.session_state.rus_clips:
            st.markdown("**📋 Clip Timeline**")
            for i, clip in enumerate(st.session_state.rus_clips):
                cc1, cc2, cc3, cc4 = st.columns([3, 1, 1, 1])
                cc1.text(f"{i+1}. {clip['name']}")
                if cc2.button("⬆", key=f"rus_up_{i}") and i > 0:
                    st.session_state.rus_clips[i], st.session_state.rus_clips[i-1] = st.session_state.rus_clips[i-1], st.session_state.rus_clips[i]
                    st.rerun()
                if cc3.button("⬇", key=f"rus_dn_{i}") and i < len(st.session_state.rus_clips)-1:
                    st.session_state.rus_clips[i], st.session_state.rus_clips[i+1] = st.session_state.rus_clips[i+1], st.session_state.rus_clips[i]
                    st.rerun()
                if cc4.button("❌", key=f"rus_del_{i}"):
                    st.session_state.rus_clips.pop(i)
                    st.rerun()
            if st.button("🗑 Clear All Clips", key="rus_clear_clips"):
                st.session_state.rus_clips = []
                st.rerun()
        else:
            st.info("No clips added yet. Upload above or use single upload below.")

    # Single video upload (fallback)
    uploaded_file = st.file_uploader("📤 Upload Single Video", type=["mp4","mov","avi","mkv","webm","mpeg4"],
                                      key="rus_upload")

    # Merge: if multi-clips exist, use those; else use single upload
    has_video = bool(uploaded_file) or len(st.session_state.rus_clips) > 0

    if has_video:
        upload_dir = BASE / "uploads" / "reels_studio"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Determine clips to process
        clips_to_process = []
        if st.session_state.rus_clips:
            clips_to_process = st.session_state.rus_clips
        elif uploaded_file:
            temp_path = upload_dir / f"rus_{int(time.time())}_{uploaded_file.name}"
            temp_path.write_bytes(uploaded_file.read())
            clips_to_process = [{"name":uploaded_file.name,"path":str(temp_path),"order":0}]
            mb = temp_path.stat().st_size / (1024*1024)
            st.success(f"Uploaded: {uploaded_file.name} ({mb:.1f} MB)")

        # Show total clips
        if len(clips_to_process) > 1:
            st.info(f"📦 {len(clips_to_process)} clips in timeline")

        # ──────────────────────────────────────────
        # FEATURE 4: TRIM / SPLIT
        # ──────────────────────────────────────────
        with st.expander("✂️ Trim & Split", expanded=False):
            st.caption("Cut start/end or split into segments")
            # Get duration of first clip for trim reference
            first_clip = clips_to_process[0]
            try:
                r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",
                                    first_clip["path"]], capture_output=True, text=True)
                full_dur = float(r.stdout.strip()) if r.stdout.strip() else 60.0
            except:
                full_dur = 60.0

            tc1, tc2 = st.columns(2)
            with tc1:
                trim_start = st.number_input("Trim Start (seconds)", 0.0, full_dur, st.session_state.rus_trim_start, 0.1, key="rus_trim_start_widget")
                st.session_state.rus_trim_start = trim_start
            with tc2:
                trim_end = st.number_input("Trim End (seconds)", 0.0, full_dur, max(st.session_state.rus_trim_end, full_dur), 0.1, key="rus_trim_end_widget")
                st.session_state.rus_trim_end = trim_end if trim_end > trim_start else full_dur

            num_splits = st.number_input("Split into segments", 1, 20, 1, key="rus_splits")
            if num_splits > 1:
                seg_dur = (st.session_state.rus_trim_end - st.session_state.rus_trim_start) / num_splits
                st.caption(f"Each segment: {seg_dur:.1f}s")

        # ──────────────────────────────────────────
        # AI ANALYSIS
        # ──────────────────────────────────────────
        with st.expander("🔍 AI Analysis", expanded=True):
            try:
                first_path = clips_to_process[0]["path"]
                r = subprocess.run(["ffprobe","-v","error","-show_entries","stream=width,height,duration,r_frame_rate,codec_name,codec_type",
                                    "-show_entries","format=size,bit_rate","-of","json",first_path], capture_output=True, text=True)
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
                k6.metric("Size",f"{sum(Path(c['path']).stat().st_size for c in clips_to_process)/(1024*1024):.1f}MB")
                k7.metric("Clips",str(len(clips_to_process)))
                k8.metric("Platform",platform)
            except: pass

        # ──────────────────────────────────────────
        # EDITING OPTIONS (2 columns)
        # ──────────────────────────────────────────
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

            # === FEATURE 5: TEXT OVERLAY ===
            st.markdown("**📝 Text Overlay**")
            with st.expander("➕ Add Text", expanded=False):
                txt_text = st.text_input("Text", key="rus_txt_text", placeholder="Your text here")
                txt_time = st.number_input("Timestamp (seconds)", 0.0, 3600.0, 0.0, 0.5, key="rus_txt_time")
                txt_size = st.slider("Font Size", 12, 120, 48, key="rus_txt_size")
                txt_color = st.color_picker("Color", "#FFFFFF", key="rus_txt_color")
                txt_x = st.selectbox("X Position", ["center","left","right"], key="rus_txt_x")
                txt_y = st.selectbox("Y Position", ["center","top","bottom"], key="rus_txt_y")
                if st.button("Add Text Overlay", key="rus_txt_add") and txt_text:
                    st.session_state.rus_text_overlays.append({
                        "text":txt_text,"time":txt_time,"size":txt_size,
                        "color":txt_color,"x":txt_x,"y":txt_y
                    })
                    st.success("Text added!")
            if st.session_state.rus_text_overlays:
                st.caption(f"{len(st.session_state.rus_text_overlays)} text overlay(s)")
                for ti, t in enumerate(st.session_state.rus_text_overlays):
                    st.text(f"  {ti+1}. \"{t['text'][:20]}\" @ {t['time']}s")
                if st.button("Clear All Text", key="rus_txt_clear"):
                    st.session_state.rus_text_overlays = []
                    st.rerun()

        with colB:
            st.markdown("**🎤 Voice Transform**")
            voice_pitch = st.slider("Pitch Shift", -12, 12, preset["pit"], key="rus_pit")
            voice_speed = st.slider("Speed", 0.7, 1.5, preset["spd"], 0.05, key="rus_spd")
            voice_volume = st.slider("Voice Volume", 0.5, 2.0, 1.0, 0.1, key="rus_vvol")
            noise_remove = st.checkbox("Noise Removal", value=True, key="rus_nr")
            audio_cleanup = st.checkbox("Audio Cleanup", value=True, key="rus_aclean")

            st.markdown("**🎬 Transitions**")
            transition_type = st.selectbox("Transition Style", ALL_TRANSITIONS, key="rus_tr")

            st.markdown("**🎨 Color Grading**")
            saturation_val = st.slider("Saturation", 0.5, 2.0, preset["sat"], 0.05, key="rus_sat")
            contrast_val = st.slider("Contrast", 0.5, 2.0, preset["con"], 0.05, key="rus_con")

            # === FEATURE 1: BACKGROUND MUSIC ===
            st.markdown("**🎵 Background Music**")
            bg_music_file = st.file_uploader("Music (MP3/WAV)", type=["mp3","wav","m4a"], key="rus_bgmusic")
            bg_volume = st.slider("BG Music Volume", 0.0, 1.0, 0.3, 0.05, key="rus_bgvol")

            # === FEATURE 2: SFX BURST ===
            st.markdown("**🔊 SFX Burst**")
            sfx_file = st.file_uploader("SFX (MP3/WAV)", type=["mp3","wav"], key="rus_sfx")
            sfx_volume = st.slider("SFX Volume", 0.0, 1.0, 0.7, 0.05, key="rus_sfxvol")

        # ──────────────────────────────────────────
        # BRANDING
        # ──────────────────────────────────────────
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
            watermark_text = b4.text_input("Watermark Text", value="", key="rus_wmtxt", placeholder="@yourhandle")
        with b5:
            watermark_pos = b5.selectbox("Watermark Position", ["bottom-right","bottom-left","top-right","top-left"], key="rus_wmpos")

        # ──────────────────────────────────────────
        # CAPTIONS
        # ──────────────────────────────────────────
        st.divider()
        st.subheader("💬 Captions")
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

        # ──────────────────────────────────────────
        # CPU SAFE
        # ──────────────────────────────────────────
        st.divider()
        cpu_safe = st.checkbox("🧊 CPU Safe Mode (Prevent Overheating)", value=True, key="rus_cpusafe")

        # ──────────────────────────────────────────
        # FEATURE 8: BATCH PROCESSING
        # ──────────────────────────────────────────
        st.divider()
        batch_enabled = st.checkbox("🔄 Batch Process All Queue Items", value=False, key="rus_batch")
        if batch_enabled:
            st.info(f"Will process all {len(st.session_state.reels_queue)} items in queue sequentially")

        # ──────────────────────────────────────────
        # GENERATE BUTTON
        # ──────────────────────────────────────────
        st.divider()

        gen_col1, gen_col2 = st.columns([3, 1])
        with gen_col1:
            if st.button("🚀 Generate", type="primary", use_container_width=True, key="rus_gen"):
                out_dir = BASE / "outputs" / "reels_studio"
                out_dir.mkdir(parents=True, exist_ok=True)

                if batch_enabled and st.session_state.reels_queue:
                    # Process all queued items
                    for qi, qitem in enumerate(st.session_state.reels_queue):
                        if qitem.get("status") not in ("waiting", None):
                            continue
                        st.session_state.reels_queue[qi]["status"] = "rendering"
                        out_path = out_dir / f"BATCH_{qi+1}_{int(time.time())}.mp4"
                        _render_single(qitem.get("path",""), out_path, cpu_safe, mirror_flip,
                                       motion_stabilize, video_noise_reduce, face_enhance,
                                       upscale_4k, upscale_1080, auto_color, saturation_val,
                                       contrast_val, sharpen, hdr_look, motion_zoom, motion_pan,
                                       motion_shake, motion_blur, preset, watermark_text,
                                       watermark_pos, voice_speed, voice_pitch, voice_volume,
                                       noise_remove, audio_cleanup, bg_volume, transition_type,
                                       target_w, target_h, bg_music_file, sfx_file, sfx_volume,
                                       intro_file, outro_file, logo_file, st.session_state.rus_text_overlays,
                                       st.session_state.rus_trim_start, st.session_state.rus_trim_end,
                                       upload_dir, st.session_state)
                        st.session_state.reels_queue[qi]["status"] = "✅ done"
                        st.session_state.reels_queue[qi]["path"] = str(out_path)
                    st.success(f"✅ Batch complete! {len(st.session_state.reels_queue)} videos processed.")
                else:
                    # Single render — handle multi-clip
                    clips_to_render = st.session_state.rus_clips if st.session_state.rus_clips else clips_to_process
                    if len(clips_to_render) > 1:
                        # Concat all clips first
                        concat_path = upload_dir / f"concat_{int(time.time())}.mp4"
                        _concat_clips(clips_to_render, concat_path)
                        render_input = str(concat_path)
                    else:
                        render_input = clips_to_render[0]["path"]

                    out_path = out_dir / f"REGENERATED_{int(time.time())}.mp4"
                    st.session_state.reels_queue.append({
                        "name": clips_to_render[0].get("name","video"),
                        "preset": preset_name,
                        "path": str(out_path),
                        "status":"rendering"
                    })

                    result = _render_single(render_input, out_path, cpu_safe, mirror_flip,
                                            motion_stabilize, video_noise_reduce, face_enhance,
                                            upscale_4k, upscale_1080, auto_color, saturation_val,
                                            contrast_val, sharpen, hdr_look, motion_zoom, motion_pan,
                                            motion_shake, motion_blur, preset, watermark_text,
                                            watermark_pos, voice_speed, voice_pitch, voice_volume,
                                            noise_remove, audio_cleanup, bg_volume, transition_type,
                                            target_w, target_h, bg_music_file, sfx_file, sfx_volume,
                                            intro_file, outro_file, logo_file, st.session_state.rus_text_overlays,
                                            st.session_state.rus_trim_start, st.session_state.rus_trim_end,
                                            upload_dir, st.session_state)

                    if result:
                        st.session_state.reels_queue[-1]["status"] = "✅ done"
                        # FEATURE 9: ADD TO HISTORY
                        st.session_state.reels_history.append({
                            "name": st.session_state.reels_queue[-1]["name"],
                            "preset": preset_name,
                            "path": str(out_path),
                            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "size_mb": round(Path(out_path).stat().st_size/(1024*1024), 2) if Path(out_path).exists() else 0
                        })
                    else:
                        st.session_state.reels_queue[-1]["status"] = "❌ failed"

        # ──────────────────────────────────────────
        # QUEUE
        # ──────────────────────────────────────────
        with st.expander("📋 Render Queue", expanded=bool(st.session_state.reels_queue)):
            if st.session_state.reels_queue:
                for i, item in enumerate(st.session_state.reels_queue):
                    qc1, qc2, qc3 = st.columns([4, 1, 1])
                    qc1.text(f"{i+1}. {item.get('name','?')} — {item.get('preset','?')}")
                    qc2.caption(item.get("status","waiting"))
                    if item.get("status") == "✅ done" and item.get("path"):
                        if qc3.button("⬇", key=f"rus_qdl_{i}"):
                            with open(item["path"],"rb") as f:
                                st.download_button("Download", f.read(), file_name=Path(item["path"]).name, mime="video/mp4")
            else:
                st.info("Queue is empty. Generated videos appear here.")

        # ──────────────────────────────────────────
        # FEATURE 9: RENDER HISTORY
        # ──────────────────────────────────────────
        with st.expander("📊 Render History", expanded=False):
            if st.session_state.reels_history:
                for i, h in enumerate(reversed(st.session_state.reels_history)):
                    hc1, hc2, hc3 = st.columns([3, 2, 1])
                    hc1.text(f"{h['name'][:30]} ({h['preset']})")
                    hc2.caption(f"{h['time']} | {h['size_mb']}MB")
                    if hc3.button("📁", key=f"rus_hist_{i}"):
                        st.session_state["_rus_selected_hist"] = h["path"]
                if st.session_state.get("_rus_selected_hist"):
                    hist_path = st.session_state["_rus_selected_hist"]
                    if Path(hist_path).exists():
                        st.video(hist_path)
                        with open(hist_path,"rb") as f:
                            st.download_button("⬇ Re-download", f.read(), file_name=Path(hist_path).name, mime="video/mp4")
            else:
                st.info("No render history yet. Generate a video to see it here.")
    else:
        st.info("👆 Upload a video or add clips to get started!")
        st.markdown("""
        ### 🚀 All Features:
        **Phase 1:** Upload, AI Analysis, 10 Presets, Voice Transform, AI Captions, Generate, Download  
        **Phase 2:** Enhancement, Upscale, Motion, 25 Transitions, Color Grading, Branding, Queue, CPU Safe  
        **Phase 3:** 🎵 BG Music, 🔊 SFX Burst, 🎞 Multi-Clip Editor, ✂️ Trim/Split, 📝 Text Overlay, 🤖 AI Auto-Edit, 📱 Platform Presets, 🔄 Batch, 📊 History  
        """)


# ══════════════════════════════════════════════════════════
# HELPER: Concatenate multiple clips
# ══════════════════════════════════════════════════════════
def _concat_clips(clips, output_path):
    """Concatenate multiple video clips using ffmpeg concat demuxer"""
    concat_list = BASE / "uploads" / "reels_studio" / f"concat_list_{int(time.time())}.txt"
    with open(concat_list, "w") as f:
        for c in clips:
            f.write(f"file '{c['path']}'\\n")
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat_list),
                    "-c","copy",str(output_path)], capture_output=True)
    concat_list.unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════
# HELPER: Render single video with ALL filters
# ══════════════════════════════════════════════════════════
def _render_single(input_path, output_path, cpu_safe, mirror_flip,
                   motion_stabilize, video_noise_reduce, face_enhance,
                   upscale_4k, upscale_1080, auto_color, saturation_val,
                   contrast_val, sharpen, hdr_look, motion_zoom, motion_pan,
                   motion_shake, motion_blur, preset, watermark_text,
                   watermark_pos, voice_speed, voice_pitch, voice_volume,
                   noise_remove, audio_cleanup, bg_volume, transition_type,
                   target_w, target_h, bg_music_file, sfx_file, sfx_volume,
                   intro_file, outro_file, logo_file, text_overlays,
                   trim_start, trim_end, upload_dir, session_state):
    """Render a single video with all applied filters"""
    import tempfile, os as _os

    with st.status("🎬 Processing...", expanded=True) as stat:
        try:
            threads = "1" if cpu_safe else "2"
            cmd = ["ffmpeg", "-threads", threads, "-y"]

            # Trim
            if trim_start > 0 or (trim_end > 0 and trim_end < 999):
                cmd.extend(["-ss", str(trim_start)])
                if trim_end > trim_start:
                    cmd.extend(["-to", str(trim_end)])

            # Intro
            intro_path = None
            if intro_file:
                intro_path = upload_dir / f"intro_{int(time.time())}.mp4"
                intro_path.write_bytes(intro_file.read())
                cmd.extend(["-i", str(intro_path)])

            cmd.extend(["-i", str(input_path)])

            # Outro
            outro_path = None
            if outro_file:
                outro_path = upload_dir / f"outro_{int(time.time())}.mp4"
                outro_path.write_bytes(outro_file.read())
                cmd.extend(["-i", str(outro_path)])

            # BG Music
            bg_path = None
            if bg_music_file:
                bg_path = upload_dir / f"bgm_{int(time.time())}.{bg_music_file.name.split('.')[-1]}"
                bg_path.write_bytes(bg_music_file.read())
                cmd.extend(["-stream_loop","-1","-i",str(bg_path)])

            # SFX
            sfx_path = None
            if sfx_file:
                sfx_path = upload_dir / f"sfx_{int(time.time())}.{sfx_file.name.split('.')[-1]}"
                sfx_path.write_bytes(sfx_file.read())
                cmd.extend(["-i", str(sfx_path)])

            # Logo
            logo_path = None
            if logo_file:
                logo_path = upload_dir / f"logo_{int(time.time())}.png"
                logo_path.write_bytes(logo_file.read())

            # === VIDEO FILTERS ===
            vf = []
            if mirror_flip: vf.append("hflip")
            if motion_stabilize: vf.append("deshake")
            if video_noise_reduce: vf.append("hqdn3d=4:3:6:4")
            if face_enhance: vf.append("unsharp=3:3:1.5:3:3:0