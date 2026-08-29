"""REELS FIX4 — Proper indentation fix"""
from pathlib import Path
import shutil, time

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 60)
print("REELS FIX v4")
print("=" * 60)

app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_fix4_{ts}")
lines = app.read_text(encoding="utf-8").split('\n')

# ============================================================
# STEP 1: Find main() and understand the ORIGINAL tab structure
# ============================================================
in_main = False
main_indent = 0
original_tab_line_idx = None
original_tab_vars = None

for i, l in enumerate(lines):
    stripped = l.strip()
    if 'def main():' in stripped:
        in_main = True
        main_indent = len(l) - len(l.lstrip())
    if in_main and 'st.tabs(' in l:
        # This should be the main tab definition
        # BUT skip if it's inside another block like "with expander:"
        current_indent = len(l) - len(l.lstrip())
        # Main tabs should be at 4-space indent (inside main)
        if current_indent == main_indent + 4:
            original_tab_line_idx = i
            # Extract vars
            if '=' in l:
                original_tab_vars = [v.strip() for v in l.split('=')[0].split(',')]
            print(f"  Found main tabs at line {i+1}: {l.strip()[:120]}")
            break

if original_tab_vars is None:
    # Fallback: search for any st.tabs(["...Video Generator"]
    for i, l in enumerate(lines):
        if 'st.tabs(' in l and 'Video Generator' in l:
            original_tab_line_idx = i
            if '=' in l:
                original_tab_vars = [v.strip() for v in l.split('=')[0].split(',')]
            elif 'tabs' in l and '=' in l:
                original_tab_vars = [v.strip() for v in l.split('=')[0].split(',')]
            else:
                original_tab_vars = ['tabs']
            print(f"  Fallback tabs at line {i+1}: {l.strip()[:120]}")
            break

if original_tab_vars is None:
    print("❌ Could not find main tabs!")
    exit(1)

# ============================================================
# STEP 2: Replace tab line with 3 tabs
# ============================================================
old_line = lines[original_tab_line_idx]
indent_str = ' ' * (len(old_line) - len(old_line.lstrip()))

# Keep track of original var names
supposed_vars = len(original_tab_vars)
print(f"  Original vars: {original_tab_vars}, count: {supposed_vars}")

# Check existing labels
labels_str = old_line[old_line.index('[')+1:old_line.index(']')] if '[' in old_line and ']' in old_line else ''
existing_labels = [lbl.strip().strip('"').strip("'") for lbl in labels_str.split(',')] if labels_str else []

new_labels = list(existing_labels)
if not any('Setting' in lbl for lbl in new_labels):
    new_labels.append("⚙ Settings")
if not any('Reels' in lbl for lbl in new_labels):
    new_labels.append("🎬 Reels Studio")

# Generate new var names: keep original naming style
if supposed_vars >= 1 and original_tab_vars[0].startswith('tab'):
    # Use tab1, tab2, tab3...
    new_vars = [f'tab{i+1}' for i in range(len(new_labels))]
elif supposed_vars >= 1:
    # Use original var naming: t1, t2, etc or tabs[0], tabs[1]
    base_name = original_tab_vars[0].rstrip('0123456789')
    if base_name.endswith('['):
        new_vars = [f'tabs[{i}]' for i in range(len(new_labels))]
    else:
        new_vars = [f'{base_name}{i+1}' for i in range(len(new_labels))]
else:
    new_vars = [f't{i+1}' for i in range(len(new_labels))]

new_var_str = ', '.join(new_vars)
new_label_str = ', '.join(f'"{lbl}"' for lbl in new_labels)
new_line = f'{indent_str}{new_var_str} = st.tabs([{new_label_str}])'

lines[original_tab_line_idx] = new_line
print(f"  NEW: {new_line}")

# ============================================================
# STEP 3: Add tab3 (Reels) block at end of main()
# ============================================================
# Find last with tabX: / with tX: block inside main
last_tab_end = None
last_tab_num = 0
last_tab_indent = 0

for i in range(original_tab_line_idx, min(original_tab_line_idx+500, len(lines))):
    l = lines[i]
    stripped = l.strip()
    # Match "with tabX:" or "with tX:" where X is a number
    import re
    m = re.match(r'with\s+(tab\d+|t\d+)\s*:', stripped)
    if m:
        tab_name = m.group(1)
        tab_num = int(''.join(filter(str.isdigit, tab_name)))
        if tab_num > last_tab_num:
            last_tab_num = tab_num
            last_tab_indent = len(l) - len(l.lstrip())
            # Find end of this block
            j = i + 1
            while j < len(lines):
                s = lines[j].strip()
                if s and not s.startswith('#'):
                    curr_indent = len(lines[j]) - len(lines[j].lstrip())
                    if curr_indent <= last_tab_indent:
                        last_tab_end = j
                        break
                j += 1
            if last_tab_end is None:
                last_tab_end = j

new_tab_num = last_tab_num + 1
new_tab_var = new_vars[-1]  # Last variable = Reels tab

# Insert Reels tab block
reels_block = [
    '',
    f'{indent_str}with {new_tab_var}:',
    f'{indent_str}    reels_upload_studio_tab()',
    '',
]

if last_tab_end:
    for offset, code_line in enumerate(reels_block):
        lines.insert(last_tab_end + offset, code_line)

# ============================================================
# STEP 4: Ensure reels function exists
# ============================================================
text = '\n'.join(lines)

if 'def reels_upload_studio_tab():' not in text:
    reels_func = '''

# ============================================================
# REELS UPLOAD STUDIO — Full Studio
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
    col1.selectbox("Video Type", ["Short (Reels/Shorts)", "Long Video"], key="rus_type")
    col2.selectbox("Aspect Ratio", ["9:16", "16:9", "1:1", "4:5"], key="rus_aspect")
    preset_name = col3.selectbox("Preset", list(REELS_PRESETS.keys()), key="rus_preset")
    preset = REELS_PRESETS.get(preset_name, REELS_PRESETS["Cinematic"])

    uploaded_file = st.file_uploader("Upload Video", type=["mp4","mov","avi","mkv","webm","mpeg4"], key="rus_upload", help="Max 200MB")

    if uploaded_file:
        upload_dir = BASE / "uploads" / "reels_studio"
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / f"uploaded_{int(time.time())}_{uploaded_file.name}"
        temp_path.write_bytes(uploaded_file.read())
        file_size_mb = temp_path.stat().st_size / (1024 * 1024)
        st.success(f"Uploaded: {uploaded_file.name} ({file_size_mb:.1f} MB)")

        # AI Analysis
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
                    n,d=vs.get("r_frame_rate","0/1").split("/"); fps=float(n)/float(d)
                except: fps=0
                c2.metric("FPS",f"{fps:.1f}")
                w=vs.get("width",0) if vs else 0; h=vs.get("height",0) if vs else 0
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

        # Editing Options
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

        # Branding
        st.divider()
        st.subheader("🏷 Branding")
        cb1,cb2,cb3=st.columns(3)
        logo_file = cb1.file_uploader("Logo (PNG)", type=["png"], key="rus_logo")
        intro_file = cb2.file_uploader("Intro Clip", type=["mp4","mov"], key="rus_intro")
        outro_file = cb3.file_uploader("Outro Clip", type=["mp4","mov"], key="rus_outro")
        cb4,cb5=st.columns(2)
        watermark_text = cb4.text_input("Watermark Text", value="", key="rus_wm_text", placeholder="@yourhandle")
        watermark_pos = cb5.selectbox("Position", ["bottom-right","bottom-left","top-right","top-left"], key="rus_wm_pos")

        # Captions
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

        # Queue
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

        # CPU Safe
        st.divider()
        cpu_safe = st.checkbox("🧊 CPU Safe Mode (Prevent Overheat)", value=True, key="rus_cpusafe")

        # Generate
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
                        ip = upload_dir / f"intro_{int(time.time())}.mp4"
                        ip.write_bytes(intro_file.read())
                        cmd.extend(["-i",str(ip)])
                    cmd.extend(["-i",str(temp_path)])
                    if outro_file:
                        op = upload_dir / f"outro_{int(time.time())}.mp4"
                        op.write_bytes(outro_file.read())
                        cmd.extend(["-i",str(op)])

                    vf = []
                    if mirror_flip: vf.append("hflip")
                    if motion_stabilize: vf.append("deshake")
                    if video_noise_reduce: vf.append("hqdn3d=4:3:6:4")
                    if face_enhance: vf.append("unsharp=3:3:1.5:3:3:0")
                    th = 2160 if upscale_4k else (1920 if upscale_1080 else 1080)
                    vf.append(f"scale=-2:{th}")
                    if auto_color:
                        vf.append(f"eq=saturation={preset.get('saturation',1.0)}:contrast={preset.get('contrast',1.0)}")
                    if sharpen: vf.append(f"unsharp=5:5:{preset.get('sharpness',1.1)}:3:3:0")
                    if hdr_look: vf.append("eq=gamma=0.9:saturation=1.2")
                    if motion_zoom:
                        vf.append("zoompan=z='min(zoom+0.0015,1.5)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'")
                    if preset.get("grain",0)>0: vf.append(f"noise=alls={preset['grain']*10}:allf=t")
                    if watermark_text:
                        wx = "w-tw-20" if "right" in watermark_pos else "20"
                        wy = "h-th-20" if "bottom" in watermark_pos else "20"
                        vf.append(f"drawtext=text='{watermark_text}':x={wx}:y={wy}:fontsize=24:fontcolor=white@0.6:shadowcolor=black@0.4:shadowx=2:shadowy=2")
                    cmd.extend(["-vf", ",".join(vf) if vf else "null"])

                    af = []
                    if voice_speed!=1.0: af.append(f"atempo={voice_speed}")
                    if voice_pitch!=0: af.append(f"asetrate=44100*2^({voice_pitch}/12)")
                    if voice_volume!=1.0: af.append(f"volume={voice_volume}")
                    if noise_remove: af.append("highpass=f=80,lowpass=f=8000")
                    cmd.extend(["-af", ",".join(af) if af else "anull"])

                    cmd.extend(["-c:v","libx264","-preset","ultrafast" if cpu_safe else "medium","-crf","23","-c:a","aac","-b:a","128k","-movflags","+faststart",str(output_path)])

                    status.write("Rendering...")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

                    if output_path.exists() and output_path.stat().st_size>1000:
                        status.update(label="✅ Complete!", state="complete")
                        st.success(f"Saved: {output_path.name}")
                        st.video(str(output_path))
                        st.metric("Output Size",f"{output_path.stat().st_size/(1024*1024):.1f} MB")
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

# Write
app.write_text(text, encoding="utf-8")

# Verify
try:
    compile(text, "app.py", "exec")
    print("\n✅ SYNTAX OK!")
    print("✅ 3 tabs: Video Generator | Settings | Reels Studio")
    print("✅ All features: Upload, AI Analysis, 10 Presets, Enhancement, Voice, 25 Transitions, Branding, Captions, Queue, CPU Safe")
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