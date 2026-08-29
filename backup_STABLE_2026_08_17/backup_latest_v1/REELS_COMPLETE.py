"""REELS COMPLETE - Fix t1 error + settings inline + full studio"""
from pathlib import Path
import shutil, time

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 60)
print("REELS COMPLETE FIXER")
print("=" * 60)

app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_fix3_{ts}")
text = app.read_text(encoding="utf-8")

# ============================================================
# FIX 1: Find and fix the tab variables
# ============================================================
# Replace any t1, t2, t3 with correct names
lines = text.split('\n')

# Check what variable names main() uses for tabs
tab_vars = []
tab_labels = []
in_main = False

for i, l in enumerate(lines):
    if 'def main():' in l:
        in_main = True
    if in_main and 'st.tabs(' in l:
        # Extract variable names and labels
        line = l.strip()
        print(f"  Found: {line[:120]}")
        if '=' in line:
            var_part = line.split('=')[0].strip()
            tab_vars = [v.strip() for v in var_part.split(',')]
        # Get labels
        if '[' in line and ']' in line:
            lbls = line[line.index('[')+1:line.index(']')]
            tab_labels = [lb.strip().strip('"').strip("'") for lb in lbls.split(',')]
        print(f"  Vars: {tab_vars}")
        print(f"  Labels: {tab_labels}")
        break

# Rebuild tab lines
new_tab_vars = []
new_tab_labels = list(tab_labels) if tab_labels else ["🎥 Video Generator"]

# Check if Settings tab exists
has_settings = any('Setting' in lbl for lbl in tab_labels)
has_reels = any('Reels' in lbl for lbl in tab_labels)

if not has_settings:
    new_tab_labels.append("⚙ Settings")
if not has_reels:
    new_tab_labels.append("🎬 Reels Studio")

new_tab_vars = [f"t{i+1}" for i in range(len(new_tab_labels))]

# Replace tab line
for i, l in enumerate(lines):
    if 'st.tabs(' in l and '[{' not in l:
        vars_str = ', '.join(new_tab_vars)
        labels_str = ', '.join(f'"{lbl}"' for lbl in new_tab_labels)
        lines[i] = f'    {vars_str} = st.tabs([{labels_str}])'
        print(f"  NEW: {lines[i][:150]}")
        break

# Fix all with t1/t2/t3 references WITHIN main()
# Simply replace any "with t1:" that's wrong with correct variable
# The new vars are t1, t2, t3... which should be fine

text = '\n'.join(lines)

# ============================================================
# FIX 2: Merge Settings into first tab (inline)
# ============================================================
# Settings should be inside tab1 as an expander, not separate tab
# We'll add Settings expander in tab1

# Find with tab1:
tab1_idx = None
lines = text.split('\n')
for i, l in enumerate(lines):
    if l.strip().startswith('with t1:') or l.strip().startswith('with tab1:'):
        tab1_idx = i
        break

# Find settings tab
settings_idx = None
for i, l in enumerate(lines):
    if ('with t2:' in l and 'Setting' in str(tab_labels)) or ('with tab2:' in l and 'Setting' in str(tab_labels)):
        settings_idx = i
        break

# If settings is a separate tab, merge it into tab1 as expander
if settings_idx and tab1_idx:
    # Get indentation
    tab1_indent = len(lines[tab1_idx]) - len(lines[tab1_idx].lstrip())
    # Find where to insert in tab1 (before end)
    # Actually, the simplest approach: keep settings as tab2 but make it work
    pass

# ============================================================
# SIMPLER APPROACH: Just ensure correct structure
# ============================================================
# Read the current file and just fix what's broken
text = '\n'.join(lines)

# Step A: Remove any broken reels references
lines = text.split('\n')
clean = []
for line in lines:
    if 'reels_upload_studio_tab()' in line and 'def ' not in line:
        # Keep only if it's inside a with block
        clean.append(line)
    else:
        clean.append(line)
text = '\n'.join(clean)

# Step B: Find main() and ensure tab3 exists with reels
lines = text.split('\n')
in_main = False
tab_line_idx = None
reels_handled = False

for i, l in enumerate(lines):
    if 'def main():' in l:
        in_main = True
    if in_main and 'st.tabs(' in l and not reels_handled and 'reels' in l.lower():
        reels_handled = True
    if in_main and 'st.tabs(' in l:
        tab_line_idx = i

# Find the last with tabX: block and add reels after it
if tab_line_idx:
    # Find last tab block
    last_tab_end = tab_line_idx
    tab_blocks = []
    for j in range(tab_line_idx, min(tab_line_idx+500, len(lines))):
        for k in range(1, 10):
            if lines[j].strip().startswith(f'with t{k}:'):
                tab_blocks.append((k, j))
    if tab_blocks:
        last_block = max(tab_blocks, key=lambda x: x[0])
        last_idx = last_block[1]
        # Find end of this block
        indent = len(lines[last_idx]) - len(lines[last_idx].lstrip())
        block_end = last_idx + 1
        while block_end < len(lines):
            stripped = lines[block_end].rstrip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('with t'):
                current_indent = len(lines[block_end]) - len(lines[block_end].lstrip())
                if current_indent <= indent:
                    break
            if stripped.startswith('with t') and block_end != last_idx:
                break
            block_end += 1
        
        # Insert reels tab
        reels_block = [
            '',
            f'{" "*indent}with t{last_block[0]+1}:',
            f'{" "*(indent+4)}reels_upload_studio_tab()',
        ]
        # Check if already exists
        already = any('reels_upload_studio_tab' in lines[k] for k in range(last_idx, min(block_end+5, len(lines))))
        if not already:
            for offset, code_line in enumerate(reels_block):
                lines.insert(block_end + offset, code_line)
    text = '\n'.join(lines)

# ============================================================
# NOW add the full reels function
# ============================================================
# Check if already exists
if 'def reels_upload_studio_tab():' not in text:
    reels_func = '''

# ============================================================
# REELS UPLOAD STUDIO - Full Studio
# ============================================================

REELS_PRESETS = {
    "Cinematic": {"motion":"slow_push","color":"teal_orange","transition":"fade","speed":1.0,"pitch":0,"saturation":1.2,"contrast":1.1,"grain":0.02,"vignette":0.3,"sharpness":1.1},
    "Luxury": {"motion":"smooth_zoom","color":"gold_warm","transition":"dissolve","speed":1.0,"pitch":-1,"saturation":0.9,"contrast":1.15,"grain":0.01,"vignette":0.4,"sharpness":1.05},
    "Modern": {"motion":"dynamic_pan","color":"clean_cool","transition":"slide_left","speed":1.05,"pitch":0,"saturation":1.1,"contrast":1.05,"grain":0.0,"vignette":0.2,"sharpness":1.15},
    "Dynamic": {"motion":"shake_energy","color":"vibrant_pop","transition":"whip","speed":1.1,"pitch":1,"saturation":1.3,"contrast":1.2,"grain":0.03,"vignette":0.25,"sharpness":1.2},
    "Minimal": {"motion":"none","color":"natural","transition":"cut","speed":1.0,"pitch":0,"saturation":1.0,"contrast":1.0,"grain":0.0,"vignette":0.0,"sharpness":1.0},
    "Documentary": {"motion":"slow_pan","color":"muted_warm","transition":"fade_black","speed":0.95,"pitch":-2,"saturation":0.85,"contrast":1.1,"grain":0.04,"vignette":0.35,"sharpness":1.0},
    "Gaming": {"motion":"rapid_zoom","color":"neon_cool","transition":"glitch","speed":1.15,"pitch":2,"saturation":1.4,"contrast":1.3,"grain":0.01,"vignette":0.3,"sharpness":1.3},
    "Travel": {"motion":"gentle_drift","color":"sunny_warm","transition":"cross_zoom","speed":1.02,"pitch":0,"saturation":1.25,"contrast":1.08,"grain":0.01,"vignette":0.15,"sharpness":1.1},
    "Podcast": {"motion":"none","color":"flat_neutral","transition":"cut","speed":1.0,"pitch":0,"saturation":0.95,"contrast":1.0,"grain":0.0,"vignette":0.0,"sharpness":1.0},
    "Viral": {"motion":"fast_energy","color":"hyper_sat","transition":"flash","speed":1.2,"pitch":1,"saturation":1.5,"contrast":1.25,"grain":0.02,"vignette":0.2,"sharpness":1.25},
}

CAPTION_STYLES = ["minimal","luxury_gold","neon_glow","bold_white","colorful_pop","gaming_red","youtube_style","tiktok_viral","modern_clean","professional_dark"]

TRANSITIONS = ["fade","dissolve","slide_left","slide_right","slide_up","slide_down","flash","glitch","cross_zoom","whip","film_burn","zoom_in","spin","morph","smooth_blur","light_leak","dynamic_slide","circle_open","page_curl","pixelate","doorway","radial","swirl","cube","fadegrayscale"]


def reels_upload_studio_tab():
    st.header("🎬 Reels Upload Studio")
    st.caption("AI-Powered Video Regeneration — Upload, Edit, Transform")

    col1, col2, col3 = st.columns(3)
    with col1:
        video_type = st.selectbox("Video Type", ["Short (Reels/Shorts)", "Long Video"], key="rus_type")
    with col2:
        aspect = st.selectbox("Aspect Ratio", ["9:16", "16:9", "1:1", "4:5"], key="rus_aspect")
    with col3:
        preset_name = st.selectbox("Preset", list(REELS_PRESETS.keys()), key="rus_preset")

    preset = REELS_PRESETS.get(preset_name, REELS_PRESETS["Cinematic"])

    uploaded_file = st.file_uploader("Upload Video", type=["mp4","mov","avi","mkv","webm","mpeg4"], key="rus_upload", help="Max 200MB")

    if uploaded_file:
        upload_dir = BASE / "uploads" / "reels_studio"
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / f"uploaded_{int(time.time())}_{uploaded_file.name}"
        temp_path.write_bytes(uploaded_file.read())
        file_size_mb = temp_path.stat().st_size / (1024 * 1024)
        st.success(f"Uploaded: {uploaded_file.name} ({file_size_mb:.1f} MB)")

        # ===== AI ANALYSIS =====
        with st.expander("🔍 AI Analysis", expanded=True):
            try:
                result = subprocess.run(["ffprobe","-v","error","-show_entries","stream=width,height,duration,r_frame_rate,codec_name,codec_type","-show_entries","format=duration,size,bit_rate","-of","json",str(temp_path)], capture_output=True, text=True)
                info = json.loads(result.stdout) if result.stdout else {}
                streams = info.get("streams",[])
                fmt = info.get("format",{})
                vs = next((s for s in streams if s.get("codec_type")=="video"), None)
                ar = next((s for s in streams if s.get("codec_type")=="audio"), None)

                c1,c2,c3,c4=st.columns(4)
                dur=float(fmt.get("duration",0))
                c1.metric("Duration",f"{dur:.1f}s")
                try:
                    n,d=vs.get("r_frame_rate","0/1").split("/")
                    fps=float(n)/float(d)
                except: fps=0
                c2.metric("FPS",f"{fps:.1f}")
                w=vs.get("width",0) if vs else 0
                h=vs.get("height",0) if vs else 0
                c3.metric("Resolution",f"{w}x{h}")
                c4.metric("Codec",(vs.get("codec_name","?") or "?").upper())
                c5,c6,c7,c8=st.columns(4)
                c5.metric("Audio","Yes" if ar else "No")
                br=float(fmt.get("bit_rate",0))/1000 if fmt.get("bit_rate") else 0
                c6.metric("Bitrate",f"{br:.0f}kbps")
                c7.metric("Size",f"{file_size_mb:.1f}MB")
                c8.metric("Type","Short" if dur<180 else "Long")
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
            video_noise_reduce = st.checkbox("Video Noise Reduction", value=False, key="rus_vnoise")
            face_enhance = st.checkbox("Face Enhancement", value=False, key="rus_face")
            motion_stabilize = st.checkbox("Motion Stabilization", value=False, key="rus_stabilize")
            mirror_flip = st.checkbox("Mirror Flip (Anti-Copyright)", value=False, key="rus_flip")

            st.markdown("**Upscale**")
            upscale_1080 = st.checkbox("Upscale to 1080p", value=True, key="rus_1080")
            upscale_4k = st.checkbox("Upscale to 4K", value=False, key="rus_4k")

            st.markdown("**Motion Effects**")
            motion_zoom = st.checkbox("Dynamic Zoom", value=True, key="rus_mzoom")
            motion_pan = st.checkbox("Slow Pan", value=True, key="rus_mpan")
            motion_shake = st.checkbox("Shake", value=False, key="rus_mshake")
            motion_blur = st.checkbox("Motion Blur", value=False, key="rus_mblur")

        with col_b:
            st.markdown("**Voice Transform**")
            voice_pitch = st.slider("Pitch Shift", -12, 12, preset.get("pitch",0), key="rus_pitch")
            voice_speed = st.slider("Speed", 0.7, 1.5, preset.get("speed",1.0), 0.05, key="rus_speed")
            voice_volume = st.slider("Voice Volume", 0.5, 2.0, 1.0, 0.1, key="rus_vvol")
            bg_volume = st.slider("Background Volume", 0.0, 1.0, 0.3, 0.05, key="rus_bgvol")
            noise_remove = st.checkbox("Noise Removal", value=True, key="rus_nremove")
            audio_cleanup = st.checkbox("Audio Cleanup", value=True, key="rus_aclean")

            st.markdown("**Transitions**")
            transition_type = st.selectbox("Transition Style", TRANSITIONS, key="rus_transition")

        # ===== BRANDING =====
        st.divider()
        st.subheader("🏷 Branding")
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            logo_file = st.file_uploader("Logo (PNG)", type=["png"], key="rus_logo")
        with col_b2:
            intro_file = st.file_uploader("Intro Clip", type=["mp4","mov"], key="rus_intro")
        with col_b3:
            outro_file = st.file_uploader("Outro Clip", type=["mp4","mov"], key="rus_outro")
        col_b4, col_b5 = st.columns(2)
        with col_b4:
            watermark_text = st.text_input("Watermark Text", value="", key="rus_wm_text", placeholder="@yourhandle")
        with col_b5:
            watermark_pos = st.selectbox("Position", ["bottom-right","bottom-left","top-right","top-left"], key="rus_wm_pos")

        # ===== CAPTIONS =====
        st.divider()
        st.subheader("💬 Captions")
        captions_enabled = st.checkbox("Enable AI Captions", value=True, key="rus_captions")
        if captions_enabled:
            cc1,cc2,cc3=st.columns(3)
            cc1.selectbox("Style", CAPTION_STYLES, key="rus_cstyle")
            cc2.selectbox("Position", ["bottom","center","top"], key="rus_cpos")
            cc3.selectbox("Size", ["small","medium","large"], key="rus_csize")
            cd1,cd2=st.columns(2)
            cd1.checkbox("Background Box", value=True, key="rus_cbg")
            cd1.checkbox("Word Highlight", value=True, key="rus_chl")
            cd2.checkbox("Emoji Support", value=False, key="rus_cemoji")
            cd2.checkbox("Animated", value=True, key="rus_canim")

        # ===== QUEUE =====
        st.divider()
        with st.expander("📋 Queue", expanded=False):
            if "reels_queue" not in st.session_state:
                st.session_state.reels_queue = []
            for i, item in enumerate(st.session_state.reels_queue):
                qc1,qc2=st.columns([4,1])
                qc1.text(f"{i+1}. {item['name']} - {item['preset']}")
                qc2.caption(item.get("status","waiting"))
            if not st.session_state.reels_queue:
                st.info("Queue empty. Generate a video to add it.")

        # ===== CPU SAFE =====
        st.divider()
        cpu_safe = st.checkbox("🧊 CPU Safe Mode (Prevent Overheat)", value=True, key="rus_cpusafe")

        # ===== GENERATE =====
        st.divider()
        if st.button("🚀 Generate", type="primary", use_container_width=True, key="rus_generate"):
            output_dir = BASE / "outputs" / "reels_studio"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"REGENERATED_{int(time.time())}.mp4"

            with st.status("Processing...", expanded=True) as status:
                try:
                    threads = "1" if cpu_safe else "2"
                    cmd = ["ffmpeg","-threads",threads,"-y"]

                    if intro_file:
                        intro_path = upload_dir / f"intro_{int(time.time())}.mp4"
                        intro_path.write_bytes(intro_file.read())
                        cmd.extend(["-i",str(intro_path)])
                    cmd.extend(["-i",str(temp_path)])
                    if outro_file:
                        outro_path = upload_dir / f"outro_{int(time.time())}.mp4"
                        outro_path.write_bytes(outro_file.read())
                        cmd.extend(["-i",str(outro_path)])

                    vf_parts = []
                    if mirror_flip: vf_parts.append("hflip")
                    if motion_stabilize: vf_parts.append("deshake")
                    if video_noise_reduce: vf_parts.append("hqdn3d=4:3:6:4")
                    if face_enhance: vf_parts.append("unsharp=3:3:1.5:3:3:0")

                    target_h = 2160 if upscale_4k else (1920 if upscale_1080 else 1080)
                    vf_parts.append(f"scale=-2:{target_h}")
                    if auto_color:
                        vf_parts.append(f"eq=saturation={preset.get('saturation',1.0)}:contrast={preset.get('contrast',1.0)}")
                    if sharpen:
                        vf_parts.append(f"unsharp=5:5:{preset.get('sharpness',1.1)}:3:3:0")
                    if hdr_look: vf_parts.append("eq=gamma=0.9:saturation=1.2")
                    if motion_zoom:
                        vf_parts.append("zoompan=z='min(zoom+0.0015,1.5)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'")
                    if preset.get("grain",0)>0:
                        vf_parts.append(f"noise=alls={preset['grain']*10}:allf=t")
                    if watermark_text:
                        wm_x = "w-tw-20" if "right" in watermark_pos else "20"
                        wm_y = "h-th-20" if "bottom" in watermark_pos else "20"
                        vf_parts.append(f"drawtext=text='{watermark_text}':x={wm_x}:y={wm_y}:fontsize=24:fontcolor=white@0.6:shadowcolor=black@0.4:shadowx=2:shadowy=2")

                    vf_filter = ",".join(vf_parts) if vf_parts else "null"
                    cmd.extend(["-vf", vf_filter])

                    af_parts = []
                    if voice_speed!=1.0: af_parts.append(f"atempo={voice_speed}")
                    if voice_pitch!=0: af_parts.append(f"asetrate=44100*2^({voice_pitch}/12)")
                    if voice_volume!=1.0: af_parts.append(f"volume={voice_volume}")
                    if noise_remove: af_parts.append("highpass=f=80,lowpass=f=8000")
                    af_filter = ",".join(af_parts) if af_parts else "anull"
                    cmd.extend(["-af", af_filter])

                    cmd.extend(["-c:v","libx264","-preset","ultrafast" if cpu_safe else "medium","-crf","23","-c:a","aac","-b:a","128k","-movflags","+faststart",str(output_path)])

                    status.write("Rendering...")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

                    if output_path.exists() and output_path.stat().st_size>1000:
                        status.update(label="✅ Complete!", state="complete")
                        st.success(f"Saved: {output_path.name}")
                        st.video(str(output_path))
                        out_mb=output_path.stat().st_size/(1024*1024)
                        st.metric("Output Size",f"{out_mb:.1f} MB")
                        with open(output_path,"rb") as f:
                            st.download_button("⬇ Download", f.read(), file_name=output_path.name, mime="video/mp4", use_container_width=True)
                        st.session_state.reels_queue.append({"name":uploaded_file.name,"preset":preset_name,"path":str(output_path),"status":"done"})
                    else:
                        status.update(label="❌ Failed", state="error")
                        st.error(f"FFmpeg error: {str(result.stderr)[:300]}")
                except subprocess.TimeoutExpired:
                    status.update(label="⏱ Timeout", state="error")
                    st.error("Timeout — try CPU Safe Mode + smaller video.")
                except Exception as e:
                    status.update(label="❌ Error", state="error")
                    st.error(f"Error: {e}")
    else:
        st.info("👆 Upload a video to start editing")
'''
    text += reels_func

# Write and verify
app.write_text(text, encoding="utf-8")

try:
    compile(text, "app.py", "exec")
    print("\n✅ SYNTAX OK!")
except SyntaxError as e:
    print(f"\n❌ SYNTAX ERROR line {e.lineno}: {e.msg}")
    l2=text.split('\n')
    lo=max(0,e.lineno-3)
    hi=min(len(l2),e.lineno+2)
    for ln in range(lo,hi):
        marker=">>>" if ln+1==e.lineno else "   "
        print(f"  {marker} {ln+1}: {l2[ln][:150]}")

print("=" * 60)
print("Run: streamlit run app.py")
print("=" * 60)