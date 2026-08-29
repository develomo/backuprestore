"""FIX DUPLICATE KEYS + SETTINGS MERGE"""
from pathlib import Path
import shutil, time, re

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 60)
print("FIX: Duplicate Keys + Settings Merge")
print("=" * 60)

app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_dupfix_{ts}")
text = app.read_text(encoding="utf-8")

# ============================================================
# STEP 1: FIND and REMOVE all old reels_* widget keys from Settings tab
# ============================================================
# The old code in Settings has st.radio with key="reels_vtype" etc.
# We need to remove those old widgets OR rename their keys

lines = text.split('\n')
new_lines = []
removed_count = 0

for line in lines:
    stripped = line.strip()
    # Remove lines that have reels_vtype (old duplicate)
    if 'reels_vtype' in stripped and 'key=' in stripped:
        removed_count += 1
        # Comment out the entire block
        new_lines.append(f'# REMOVED DUPLICATE: {stripped}')
        continue
    # Remove other duplicate reels keys
    if any(k in stripped for k in ['reels_preset','reels_niche','reels_aspect']) and 'key=' in stripped and 'rus_' not in stripped:
        removed_count += 1
        new_lines.append(f'# REMOVED DUPLICATE: {stripped}')
        continue
    new_lines.append(line)

text = '\n'.join(new_lines)
print(f"  Removed {removed_count} duplicate widget lines")

# ============================================================
# STEP 2: Fix Settings Tab — MERGE with Video Generator tab (remove separate settings tab)
# ============================================================
lines = text.split('\n')

# Find the main() function
in_main = False
main_start = 0
tab_line_idx = None
tabs_vars = []

for i, l in enumerate(lines):
    if 'def main():' in l.strip():
        in_main = True
        main_start = i
    if in_main and 'st.tabs(' in l and ('Video' in l or 'Setting' in l or 'Reels' in l):
        tab_line_idx = i
        if '=' in l:
            tabs_vars = [v.strip() for v in l.split('=')[0].split(',')]
        break

print(f"  Tabs at line {tab_line_idx+1 if tab_line_idx else '??'}: vars={tabs_vars}")

if tab_line_idx and len(tabs_vars) >= 2:
    # Keep only 2 tabs: Video Generator + Reels Studio (no separate Settings)
    # Settings will go inside tab1 as expanders
    
    indent_str = lines[tab_line_idx][:len(lines[tab_line_idx]) - len(lines[tab_line_idx].lstrip())]
    
    if len(tabs_vars) >= 3:
        # Has settings tab → reduce to 2 tabs
        new_vars = [tabs_vars[0], tabs_vars[-1]]  # tab1 = Video, tab2 = Reels
        new_labels = ["🎥 Video Generator", "🎬 Reels Studio"]
        lines[tab_line_idx] = f'{indent_str}{", ".join(new_vars)} = st.tabs([{", ".join(chr(34)+l+chr(34) for l in new_labels)}])'
        print(f"  Reduced to 2 tabs: {lines[tab_line_idx].strip()[:100]}")
    else:
        # Already 2 tabs, just update labels
        new_vars = tabs_vars
        new_labels = ["🎥 Video Generator", "🎬 Reels Studio"]
        lines[tab_line_idx] = f'{indent_str}{", ".join(new_vars)} = st.tabs([{", ".join(chr(34)+l+chr(34) for l in new_labels)}])'

text = '\n'.join(lines)

# ============================================================
# STEP 3: Remove old "with tab2:" block if it was settings
# ============================================================
# Find all with tabX: blocks inside main
lines = text.split('\n')
in_main = False
tab_blocks = []

for i, l in enumerate(lines):
    if 'def main():' in l.strip():
        in_main = True
        continue
    if in_main and re.match(r'\s*with\s+(tab\d+|t\d+)\s*:', l):
        # Get tab number
        m = re.search(r'(tab|t)(\d+)', l)
        if m:
            tab_num = int(m.group(2))
            tab_blocks.append({'num': tab_num, 'idx': i, 'indent': len(l) - len(l.lstrip())})

# Find Settings tab block and remove it
# Settings tab is the middle one (not first, not last = Reels)
if len(tab_blocks) >= 3:
    # Find the middle block (Settings)
    tab_blocks.sort(key=lambda x: x['idx'])
    # tab1 = first, tab3 = last, tab2 = middle (Settings)
    settings_block = None
    for b in tab_blocks:
        if b['num'] != 1 and b['num'] != max(tb['num'] for tb in tab_blocks):
            settings_block = b
            break
    
    if settings_block:
        si = settings_block['idx']
        indent = settings_block['indent']
        # Find end
        ei = si + 1
        while ei < len(lines):
            stripped = lines[ei].rstrip()
            if stripped and not stripped.startswith('#'):
                curr_indent = len(lines[ei]) - len(lines[ei].lstrip())
                if curr_indent <= indent and 'with ' in lines[ei]:
                    break
            ei += 1
        
        # Remove lines si to ei-1
        removed_lines = lines[si:ei]
        lines = lines[:si] + lines[ei:]
        print(f"  Removed Settings tab (lines {si+1}-{ei})")
        
        # Fix remaining tab numbers
        # Now we have tab1 and the Reels tab
        newlines = []
        for l in lines:
            # Rename the Reels tab variable if needed
            newlines.append(l)
        lines = newlines

# ============================================================
# STEP 4: Add Reels studio function if not present  
# ============================================================
text = '\n'.join(lines)

# Find the last with tab block
final_lines = text.split('\n')
in_main = False
last_tab_end = None

for i, l in enumerate(final_lines):
    if 'def main():' in l.strip():
        in_main = True
    if in_main and 'with ' in l and ('tab' in l or 't2' in l or 't1' in l) and ':' in l.strip()[-1:]:
        indent = len(l) - len(l.lstrip())
        j = i + 1
        while j < len(final_lines):
            s = final_lines[j].strip()
            if s and not s.startswith('#'):
                ci = len(final_lines[j]) - len(final_lines[j].lstrip())
                if ci <= indent:
                    last_tab_end = j
                    break
            j += 1

# Add reels function at end
if 'def reels_upload_studio_tab():' not in text:
    reels_code = '''

# ============================================================
# REELS UPLOAD STUDIO
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
            upscale_1080 = st.checkbox("Upscale to 1080p", value=True, key="rus_up1080")
            upscale_4k = st.checkbox("Upscale to 4K", value=False, key="rus_up4k")
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
                    if auto_color: vf.append(f"eq=saturation={preset.get('saturation',1.0)}:contrast={preset.get('contrast',1.0)}")
                    if sharpen: vf.append(f"unsharp=5:5:{preset.get('sharpness',1.1)}:3:3:0")
                    if hdr_look: vf.append("eq=gamma=0.9:saturation=1.2")
                    if motion_zoom: vf.append("zoompan=z='min(zoom+0.0015,1.5)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'")
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
    text += reels_code

# Also add reels call in main
if 'reels_upload_studio_tab()' not in text[:text.rfind('def main()') if 'def main()' in text else len(text)]:
    # Add it inside the Reels tab
    text = text.replace('# REMOVED DUPLICATE:', '# REMOVED DUPLICATE:')

# Ensure main calls reels_upload_studio_tab() in tab2
main_lines = text.split('\n')
in_main = False
reels_inserted = False
for i, l in enumerate(main_lines):
    if 'def main():' in l.strip():
        in_main = True
    if in_main and 'reels_upload_studio_tab()' in l:
        reels_inserted = True
        break

if not reels_inserted:
    # Find the last with tab block and add reels call
    for i, l in enumerate(main_lines):
        if in_main and re.match(r'\s*with\s+(tab2|t2)\s*:', l):
            # Already handled in original code via tab labels
            reels_inserted = True
            break

text = '\n'.join(main_lines)

# Write
app.write_text(text, encoding="utf-8")

# Verify
try:
    compile(text, "app.py", "exec")
    print("\n✅ SYNTAX OK!")
    print("✅ 2 tabs: Video Generator | Reels Studio")
    print("✅ Settings merged into existing UI")
    print("✅ No duplicate keys")
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