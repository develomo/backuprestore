"""FIXED REELS — function BEFORE main(), guarantee defined"""
from pathlib import Path
import shutil, time, re

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())
app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_final2_{ts}")
text = app.read_text(encoding="utf-8")

print("=" * 60)

# ============================================================
# STEP 1: Remove ENTIRE old reels function
# ============================================================
lines = text.split('\n')
out = []
skip = False
skip_ind = 0
for l in lines:
    if 'def reels_upload_studio_tab():' in l:
        skip = True
        skip_ind = len(l) - len(l.lstrip())
        continue
    if skip:
        if l.strip() and not l.strip().startswith('#'):
            if len(l) - len(l.lstrip()) <= skip_ind:
                skip = False
                out.append(l)
        continue
    out.append(l)
text = '\n'.join(out)
print("[1] Old function removed")

# ============================================================
# STEP 2: Remove old module-level REELS_ globals
# ============================================================
lines = text.split('\n')
out = []
for l in lines:
    s = l.strip()
    if s.startswith('REELS_') and '=' in s and 'def ' not in s and 'upload' not in s:
        if not l[0].isspace():
            continue  # skip entirely
    out.append(l)
text = '\n'.join(out)
print("[2] REELS_ globals removed")

# ============================================================
# STEP 3: Remove any OLD reels widget code from main()
# ============================================================
lines = text.split('\n')
out = []
for l in lines:
    # Skip lines with old reels keys (not rus_ keys)
    if re.search(r'key\s*=\s*["\']reels_(?!upload)', l):
        continue
    out.append(l)
text = '\n'.join(out)
print("[3] Old reels widgets removed")

# ============================================================
# STEP 4: Fix main() tabs to 2
# ============================================================
lines = text.split('\n')
in_main = False

for i, l in enumerate(lines):
    if 'def main():' in l.strip():
        in_main = True
    if in_main and 'st.tabs(' in l and 'Generator' in l:
        indent = ' ' * (len(l) - len(l.lstrip()))
        lines[i] = f'{indent}tab1, tab2 = st.tabs(["🎥 Video Generator", "🎬 Reels Studio"])'
        print(f"[4] Tabs: tab1, tab2")
        break

# Remove extra tab blocks (tab3/t3)
out2 = []
in_main = False
for l in lines:
    if 'def main():' in l.strip():
        in_main = True
    if in_main and ('with tab3:' in l or 'with t3:' in l):
        continue
    out2.append(l)
lines = out2

text = '\n'.join(lines)
print("[5] Extra tabs removed")

# ============================================================
# STEP 5: Insert fresh function BEFORE main()
# ============================================================
# Find "def main():"
main_idx = None
for i, l in enumerate(text.split('\n')):
    if l.strip() == 'def main():' or l.strip().startswith('def main():'):
        main_idx = i
        break

if main_idx is None:
    print("❌ def main(): not found!")
    exit(1)

reels_code = '''
# ============================================================
# REELS STUDIO FUNCTION (before main)
# ============================================================

def reels_upload_studio_tab():
    st.header("🎬 Reels Upload Studio")
    st.caption("AI-Powered Video Regeneration — Upload, Edit, Transform")

    c1, c2, c3 = st.columns(3)
    c1.selectbox("Video Type", ["Short (Reels/Shorts)", "Long Video"], key="rus_vtype")
    c2.selectbox("Aspect Ratio", ["9:16","16:9","1:1","4:5"], key="rus_ar")

    presets = {
        "Cinematic":{"sat":1.2,"con":1.1,"pit":0,"spd":1.0},
        "Luxury":{"sat":0.9,"con":1.15,"pit":-1,"spd":1.0},
        "Modern":{"sat":1.1,"con":1.05,"pit":0,"spd":1.05},
        "Dynamic":{"sat":1.3,"con":1.2,"pit":1,"spd":1.1},
        "Minimal":{"sat":1.0,"con":1.0,"pit":0,"spd":1.0},
        "Documentary":{"sat":0.85,"con":1.1,"pit":-2,"spd":0.95},
        "Gaming":{"sat":1.4,"con":1.3,"pit":2,"spd":1.15},
        "Travel":{"sat":1.25,"con":1.08,"pit":0,"spd":1.02},
        "Podcast":{"sat":0.95,"con":1.0,"pit":0,"spd":1.0},
        "Viral":{"sat":1.5,"con":1.25,"pit":1,"spd":1.2},
    }
    preset_name = c3.selectbox("Preset", list(presets.keys()), key="rus_prst")
    preset = presets.get(preset_name, presets["Cinematic"])

    uploaded_file = st.file_uploader("Upload Video", type=["mp4","mov","avi","mkv","webm","mpeg4"], key="rus_upload")

    if uploaded_file:
        upload_dir = BASE / "uploads" / "reels_studio"
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / f"rus_{int(time.time())}.mp4"
        temp_path.write_bytes(uploaded_file.read())
        mb = temp_path.stat().st_size / (1024*1024)
        st.success(f"Uploaded: {uploaded_file.name} ({mb:.1f} MB)")

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

        st.divider()
        st.subheader("🎨 Editing")
        ca, cb = st.columns(2)
        with ca:
            auto_color = st.checkbox("Auto Color", True, key="rus_ac")
            sharpen = st.checkbox("Sharpen", True, key="rus_sh")
            hdr = st.checkbox("HDR Look", False, key="rus_hdr")
            vnr = st.checkbox("Noise Reduction", False, key="rus_vnr")
            face = st.checkbox("Face Enhancement", False, key="rus_face")
            stab = st.checkbox("Stabilization", False, key="rus_stab")
            flip = st.checkbox("Mirror Flip", False, key="rus_flip")
            up1080 = st.checkbox("1080p", True, key="rus_u1080")
            up4k = st.checkbox("4K", False, key="rus_u4k")
            mzoom = st.checkbox("Dynamic Zoom", True, key="rus_mz")
        with cb:
            pitch = st.slider("Pitch Shift", -12, 12, preset["pit"], key="rus_pit")
            speed = st.slider("Speed", 0.7, 1.5, preset["spd"], 0.05, key="rus_spd")
            vvol = st.slider("Voice Vol", 0.5, 2.0, 1.0, 0.1, key="rus_vvol")
            nr = st.checkbox("Noise Removal", True, key="rus_nr")
            trans = st.selectbox("Transition", ["fade","dissolve","slide_left","slide_right","slide_up","slide_down","flash","glitch","cross_zoom","whip","film_burn","zoom_in","spin","morph","smooth_blur","light_leak","dynamic_slide","circle_open","pixelate","doorway","radial","swirl","cube","fadegrayscale"], key="rus_tr")
            mpan = st.checkbox("Slow Pan", True, key="rus_mp")
            mshake = st.checkbox("Shake", False, key="rus_ms")
            mblur = st.checkbox("Motion Blur", False, key="rus_mb")

        st.divider()
        st.subheader("🏷 Branding")
        bc1,bc2,bc3=st.columns(3)
        logo_file = bc1.file_uploader("Logo PNG", type=["png"], key="rus_logo")
        intro_file = bc2.file_uploader("Intro", type=["mp4","mov"], key="rus_intro")
        outro_file = bc3.file_uploader("Outro", type=["mp4","mov"], key="rus_outro")
        bc4,bc5=st.columns(2)
        wm_text = bc4.text_input("Watermark", key="rus_wmtxt", placeholder="@handle")
        wm_pos = bc5.selectbox("WM Pos", ["bottom-right","bottom-left","top-right","top-left"], key="rus_wmpos")

        st.divider()
        st.subheader("💬 Captions")
        cap_en = st.checkbox("AI Captions", True, key="rus_cap")
        if cap_en:
            cc1,cc2,cc3=st.columns(3)
            cc1.selectbox("Style", ["minimal","luxury_gold","neon_glow","bold_white","colorful_pop","gaming_red","youtube_style","tiktok_viral","modern_clean","professional_dark"], key="rus_cst")
            cc2.selectbox("Position", ["bottom","center","top"], key="rus_cpos")
            cc3.selectbox("Size", ["small","medium","large"], key="rus_csz")
            cd1,cd2=st.columns(2)
            cd1.checkbox("Bg Box", True, key="rus_cbg")
            cd2.checkbox("Animated", True, key="rus_can")

        st.divider()
        cpu_safe = st.checkbox("🧊 CPU Safe Mode", True, key="rus_cpusafe")

        st.divider()
        if st.button("🚀 Generate", type="primary", use_container_width=True, key="rus_gen"):
            out_dir = BASE / "outputs" / "reels_studio"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"REGEN_{int(time.time())}.mp4"

            with st.status("Processing...", expanded=True) as stat:
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
                    if flip: vf.append("hflip")
                    if stab: vf.append("deshake")
                    if vnr: vf.append("hqdn3d=4:3:6:4")
                    if face: vf.append("unsharp=3:3:1.5:3:3:0")
                    th = 2160 if up4k else (1920 if up1080 else 1080)
                    vf.append(f"scale=-2:{th}")
                    if auto_color: vf.append(f"eq=saturation={preset['sat']}:contrast={preset['con']}")
                    if sharpen: vf.append("unsharp=5:5:1.1:3:3:0")
                    if hdr: vf.append("eq=gamma=0.9:saturation=1.2")
                    if mzoom: vf.append("zoompan=z='min(zoom+0.0015,1.5)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'")
                    if wm_text:
                        wx = "w-tw-20" if "right" in wm_pos else "20"
                        wy = "h-th-20" if "bottom" in wm_pos else "20"
                        vf.append(f"drawtext=text='{wm_text}':x={wx}:y={wy}:fontsize=24:fontcolor=white@0.6")
                    cmd.extend(["-vf",",".join(vf) if vf else "null"])

                    af = []
                    if speed!=1.0: af.append(f"atempo={speed}")
                    if pitch!=0: af.append(f"asetrate=44100*2^({pitch}/12)")
                    if vvol!=1.0: af.append(f"volume={vvol}")
                    if nr: af.append("highpass=f=80,lowpass=f=8000")
                    cmd.extend(["-af",",".join(af) if af else "anull"])

                    cmd.extend(["-c:v","libx264","-preset","ultrafast" if cpu_safe else "medium","-crf","23","-c:a","aac","-b:a","128k","-movflags","+faststart",str(out_path)])
                    stat.write("Rendering...")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

                    if out_path.exists() and out_path.stat().st_size>1000:
                        stat.update(label="✅ Complete!", state="complete")
                        st.success(out_path.name)
                        st.video(str(out_path))
                        st.metric("Size",f"{out_path.stat().st_size/(1024*1024):.1f}MB")
                        with open(out_path,"rb") as f:
                            st.download_button("⬇ Download", f.read(), file_name=out_path.name, mime="video/mp4", use_container_width=True)
                    else:
                        stat.update(label="❌ Failed", state="error")
                        st.error(str(result.stderr)[:300])
                except subprocess.TimeoutExpired:
                    stat.update(label="⏱ Timeout", state="error")
                    st.error("Timeout - try shorter video")
                except Exception as e:
                    stat.update(label="❌ Error", state="error")
                    st.error(str(e))
    else:
        st.info("👆 Upload a video to start editing")
'''

lines = text.split('\n')
lines.insert(main_idx, reels_code)
text = '\n'.join(lines)
print(f"[6] Function inserted BEFORE main() at line {main_idx+1}")

# ============================================================
# STEP 6: Fix tab2 block to call reels_upload_studio_tab()
# ============================================================
lines = text.split('\n')
in_main = False
found_tab2 = False

for i, l in enumerate(lines):
    if 'def main():' in l.strip():
        in_main = True
    if in_main and re.match(r'\s*with\s+tab2\s*:', l):
        # Replace next line with reels call
        indent = ' ' * (len(l) - len(l.lstrip()) + 4)
        j = i + 1
        # Remove old tab2 body
        while j < len(lines):
            s = lines[j].strip()
            curr = len(lines[j]) - len(lines[j].lstrip()) if lines[j].strip() else 999
            if s and not s.startswith('#') and curr <= len(l) - len(l.lstrip()):
                break
            j += 1
        # Delete old body, insert new
        del lines[i+1:j]
        lines.insert(i+1, f'{indent}reels_upload_studio_tab()')
        found_tab2 = True
        print(f"[7] tab2 body replaced with reels call")
        break

if not found_tab2:
    # tab2 doesn't exist yet, find tab1 end and insert tab2
    in_main = False
    for i, l in enumerate(lines):
        if 'def main():' in l.strip():
            in_main = True
        if in_main and re.match(r'\s*with\s+tab1\s*:', l):
            tab1_indent = len(l) - len(l.lstrip())
            j = i + 1
            while j < len(lines):
                s = lines[j].rstrip()
                if s and not s.startswith('#'):
                    curr = len(lines[j]) - len(lines[j].lstrip())
                    if curr <= tab1_indent:
                        break
                j += 1
            tab_indent = ' ' * tab1_indent
            inner_indent = ' ' * (tab1_indent + 4)
            lines.insert(j, '')
            lines.insert(j+1, f'{tab_indent}with tab2:')
            lines.insert(j+2, f'{inner_indent}reels_upload_studio_tab()')
            found_tab2 = True
            print(f"[7] tab2 block created with reels call")
            break

if not found_tab2:
    print("❌ Could not insert tab2!")
    exit(1)

text = '\n'.join(lines)

# Write
app.write_text(text, encoding="utf-8")

# Verify
try:
    compile(text, "app.py", "exec")
    print("\n✅✅✅ SYNTAX OK! ✅✅✅")
    print("Function defined BEFORE main(), called in tab2.")
    print("Run: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ SYNTAX ERROR line {e.lineno}: {e.msg}")
    L = text.split('\n')
    lo = max(0, e.lineno-3)
    hi = min(len(L), e.lineno+2)
    for ln in range(lo, hi):
        print(f"  {'>>>' if ln+1==e.lineno else '   '} {ln+1}: {L[ln][:150]}")

print("=" * 60)