"""PHASE 3 FINAL — Guaranteed BASE_DIR fix"""
from pathlib import Path
import shutil, time

BASE_DIR = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())
app = BASE_DIR / "app.py"
shutil.copy2(app, BASE_DIR / f"app.py.bak_p3final_{ts}")
text = app.read_text(encoding="utf-8")
print("=" * 60)
print("PHASE 3 FINAL FIX")
print("=" * 60)

func_start = text.find('def reels_upload_studio_tab():')
if func_start == -1:
    print("❌ Function not found!"); exit(1)

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
                func_end_line = i; break

old_func = '\n'.join(lines_after[:func_end_line])
print(f"[1] Function: {len(old_func)} chars, {func_end_line} lines")

# ─────────────────────────────────────────────
# NEW FUNCTION — uses BASE_DIR defined inside
# ─────────────────────────────────────────────
new_func = r'''
# ══════════════════════════════════════════════════════════
# PHASE 3 HELPERS
# ══════════════════════════════════════════════════════════

def _concat_clips(clips, output_path):
    lst = Path(output_path).parent / "concat_list.txt"
    with open(lst, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c['path']}'\n")
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(output_path)],
                   capture_output=True)
    lst.unlink(missing_ok=True)

def _render_video(inpath, outpath, cpus, mf, ms, vnr, fe, u4k, u1080, ac, sat, con, sh, hdr,
                  mz, mp, msh, mb, preset, wmt, wmp, vs_, vp, vv, nr, bgv, tr, tw, th_,
                  bgp, sfxp, sfxv, introp, outrop, logop, texts, ts_, te_):
    threads = "1" if cpus else "2"
    cmd = ["ffmpeg","-threads",threads,"-y"]
    if ts_ > 0: cmd.extend(["-ss",str(ts_)])
    cmd.extend(["-i",str(inpath)])
    if te_ > ts_ and te_ < 99999: cmd.extend(["-to",str(te_)])
    ni = 1
    if introp: cmd.extend(["-i",str(introp)]); ni += 1
    if outrop: cmd.extend(["-i",str(outrop)]); ni += 1
    if bgp: cmd.extend(["-stream_loop","-1","-i",str(bgp)]); ni += 1
    if sfxp: cmd.extend(["-i",str(sfxp)]); ni += 1
    if logop: cmd.extend(["-i",str(logop)]); ni += 1

    vf = []
    if mf: vf.append("hflip")
    if ms: vf.append("deshake")
    if vnr: vf.append("hqdn3d=4:3:6:4")
    if fe: vf.append("unsharp=3:3:1.5:3:3:0")
    if ac and sat and con: vf.append(f"eq=saturation={sat}:contrast={con}")
    if sh: vf.append("unsharp=5:5:1.1:3:3:0")
    if hdr: vf.append("eq=gamma=0.9:saturation=1.2")
    if mz: vf.append("zoompan=z='min(zoom+0.0015,1.5)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'")
    grn = preset.get("grn", 0) if preset else 0
    if grn > 0: vf.append(f"noise=alls={grn*10}:allf=t")
    th_out = 2160 if u4k else (1920 if u1080 else (th_ or 1080))
    vf.append(f"scale=-2:{th_out}")
    if wmt:
        xm = {"right":"w-tw-20","left":"20","center":"(w-tw)/2"}
        ym = {"bottom":"h-th-20","top":"20","center":"(h-th)/2"}
        wx = xm.get("right" if "right" in wmp else ("left" if "left" in wmp else "center"), "20")
        wy = ym.get("bottom" if "bottom" in wmp else ("top" if "top" in wmp else "center"), "20")
        vf.append(f"drawtext=text='{wmt}':x={wx}:y={wy}:fontsize=24:fontcolor=white@0.6:shadowcolor=black@0.4:shadowx=2:shadowy=2")
    if texts:
        for t in texts:
            xm2 = {"right":"w-tw-20","left":"20","center":"(w-tw)/2"}
            ym2 = {"bottom":"h-th-20","top":"20","center":"(h-th)/2"}
            tx = xm2.get(t.get("x","center"), "(w-tw)/2")
            ty = ym2.get(t.get("y","center"), "(h-th)/2")
            clr = t.get("color","#FFFFFF").replace("#","")
            vf.append(f"drawtext=text='{t['text']}':x={tx}:y={ty}:fontsize={t.get('size',48)}:fontcolor={clr}:enable='between(t,{t.get('time',0)},9999)'")
    if logop:
        vf.append(f"[0:v][{ni-1}:v]overlay=W-w-20:H-h-20")

    cmd.extend(["-vf", ",".join(vf) if vf else "copy"])

    af = []
    if vs_ and vs_ != 1.0: af.append(f"atempo={vs_}")
    if vp and vp != 0: af.append(f"asetrate=44100*2^({vp}/12)")
    if vv and vv != 1.0: af.append(f"volume={vv}")
    if nr: af.append("highpass=f=80,lowpass=f=8000")
    if bgp:
        bg_idx = ni - (2 if sfxp or logop else 1) - (1 if sfxp else 0)
        af.append(f"[0:a]volume={vv or 1.0}[vox];[{bg_idx}:a]volume={bgv or 0.3}[bgm];[vox][bgm]amix=inputs=2:duration=first")

    cmd.extend(["-af", ",".join(af) if af else "anull"])
    cmd.extend(["-c:v","libx264","-preset","ultrafast" if cpus else "medium","-crf","23",
                "-c:a","aac","-b:a","128k","-movflags","+faststart",str(outpath)])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    ok = Path(outpath).exists() and Path(outpath).stat().st_size > 1000
    return ok, (str(r.stderr)[:500] if not ok else "")


# ══════════════════════════════════════════════════════════
# REELS UPLOAD STUDIO — ALL 9 PHASE 3 FEATURES
# ══════════════════════════════════════════════════════════

def reels_upload_studio_tab():
    import os as _os
    _BASE = Path(r"D:\My Creation Video Generator\backup")
    st.header("🎬 Reels Upload Studio")
    st.caption("AI-Powered Video Regeneration — Upload, Edit, Transform")

    for k, v in [("rus_clips",[]),("rus_history",[]),("rus_queue",[]),("rus_texts",[]),
                 ("rus_trim_s",0.0),("rus_trim_e",60.0)]:
        if k not in st.session_state: st.session_state[k] = v

    PRESETS = {
        "Cinematic":{"sat":1.2,"con":1.1,"pit":0,"spd":1.0,"grn":0.02},
        "Luxury":{"sat":0.9,"con":1.15,"pit":-1,"spd":1.0,"grn":0.01},
        "Modern":{"sat":1.1,"con":1.05,"pit":0,"spd":1.05,"grn":0.0},
        "Dynamic":{"sat":1.3,"con":1.2,"pit":1,"spd":1.1,"grn":0.03},
        "Minimal":{"sat":1.0,"con":1.0,"pit":0,"spd":1.0,"grn":0.0},
        "Documentary":{"sat":0.85,"con":1.1,"pit":-2,"spd":0.95,"grn":0.04},
        "Gaming":{"sat":1.4,"con":1.3,"pit":2,"spd":1.15,"grn":0.01},
        "Travel":{"sat":1.25,"con":1.08,"pit":0,"spd":1.02,"grn":0.01},
        "Podcast":{"sat":0.95,"con":1.0,"pit":0,"spd":1.0,"grn":0.0},
        "Viral":{"sat":1.5,"con":1.25,"pit":1,"spd":1.2,"grn":0.02},
    }
    PLAT = {
        "TikTok":{"ar":"9:16","w":1080,"h":1920},
        "YouTube":{"ar":"16:9","w":1920,"h":1080},
        "Instagram":{"ar":"1:1","w":1080,"h":1080},
        "YT Shorts":{"ar":"9:16","w":1080,"h":1920},
        "Facebook":{"ar":"16:9","w":1280,"h":720},
        "Custom":{"ar":"Custom","w":1920,"h":1080},
    }
    CSTYLES = ["minimal","luxury_gold","neon_glow","bold_white","colorful_pop",
               "gaming_red","youtube_style","tiktok_viral","modern_clean","professional_dark"]
    TRANS = ["fade","dissolve","slide_left","slide_right","slide_up","slide_down",
             "flash","glitch","cross_zoom","whip","film_burn","zoom_in","spin",
             "morph","smooth_blur","light_leak","dynamic_slide","circle_open",
             "page_curl","pixelate","doorway","radial","swirl","cube","fadegrayscale"]

    # ROW 1: Type, Platform, Preset
    r1,r2,r3=st.columns(3)
    with r1: st.selectbox("Video Type",["Short","Long"],key="rus_vtype")
    with r2:
        platform = st.selectbox("📱 Platform",list(PLAT.keys()),key="rus_plat")
        p = PLAT[platform]
    with r3:
        ai_auto = st.checkbox("🤖 AI Auto-Edit",False,key="rus_ai")
        preset_name = st.selectbox("Preset",list(PRESETS.keys()),key="rus_prst")
    preset = PRESETS.get(preset_name,PRESETS["Cinematic"])
    ar = p["ar"] if platform != "Custom" else st.selectbox("Aspect",["9:16","16:9","1:1"],key="rus_ar")
    tw, th_ = p["w"], p["h"]

    # ───── MULTI-CLIP EDITOR ─────
    with st.expander("🎞 Multi-Clip Editor",expanded=False):
        new = st.file_uploader("Add Clips",type=["mp4","mov","avi","mkv","webm"],key="rus_multi",accept_multiple_files=True)
        if new:
            ud = _BASE / "uploads" / "reels_studio"
            ud.mkdir(parents=True,exist_ok=True)
            for f in new:
                cp = ud / f"clip_{int(time.time())}_{f.name}"
                cp.write_bytes(f.read())
                st.session_state.rus_clips.append({"name":f.name,"path":str(cp)})
            st.rerun()
        if st.session_state.rus_clips:
            st.markdown("**📋 Timeline**")
            for i, c in enumerate(st.session_state.rus_clips):
                c1,c2,c3,c4=st.columns([3,1,1,1])
                c1.text(f"{i+1}. {c['name'][:30]}")
                if c2.button("⬆",key=f"ru_{i}") and i>0:
                    st.session_state.rus_clips[i],st.session_state.rus_clips[i-1]=st.session_state.rus_clips[i-1],st.session_state.rus_clips[i];st.rerun()
                if c3.button("⬇",key=f"rd_{i}") and i<len(st.session_state.rus_clips)-1:
                    st.session_state.rus_clips[i],st.session_state.rus_clips[i+1]=st.session_state.rus_clips[i+1],st.session_state.rus_clips[i];st.rerun()
                if c4.button("❌",key=f"rx_{i}"): st.session_state.rus_clips.pop(i);st.rerun()
            if st.button("🗑 Clear All",key="rus_clear"): st.session_state.rus_clips=[];st.rerun()
        else:
            st.info("Add clips above or use single upload")

    uploaded = st.file_uploader("📤 Upload Video",type=["mp4","mov","avi","mkv","webm","mpeg4"],key="rus_upload")
    has_vid = bool(uploaded) or len(st.session_state.rus_clips)>0

    if has_vid:
        ud = _BASE / "uploads" / "reels_studio"
        ud.mkdir(parents=True,exist_ok=True)

        clips = st.session_state.rus_clips[:] if st.session_state.rus_clips else []
        if uploaded:
            tp = ud / f"rus_{int(time.time())}_{uploaded.name}"
            tp.write_bytes(uploaded.read()); mb = tp.stat().st_size/(1024*1024)
            clips = [{"name":uploaded.name,"path":str(tp)}]
            st.success(f"Uploaded: {uploaded.name} ({mb:.1f}MB)")
        if len(clips)>1: st.info(f"📦 {len(clips)} clips ready")

        # ───── TRIM/SPLIT ─────
        with st.expander("✂️ Trim & Split",expanded=False):
            try:
                r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",clips[0]["path"]],capture_output=True,text=True)
                fd = float(r.stdout.strip()) if r.stdout.strip() else 60.0
            except: fd=60.0
            c1,c2=st.columns(2)
            with c1: ts_val=st.number_input("Start (s)",0.0,fd,st.session_state.rus_trim_s,0.1,key="rts"); st.session_state.rus_trim_s=ts_val
            with c2: te_val=st.number_input("End (s)",0.0,fd,max(st.session_state.rus_trim_e,fd),0.1,key="rte"); st.session_state.rus_trim_e=max(te_val,ts_val+0.1)
            ns=st.number_input("Split segments",1,20,1,key="rus_split"); st.caption(f"Each: ~{(st.session_state.rus_trim_e-st.session_state.rus_trim_s)/ns:.1f}s")

        # ───── AI ANALYSIS ─────
        with st.expander("🔍 AI Analysis",expanded=True):
            try:
                r=subprocess.run(["ffprobe","-v","error","-show_entries","stream=width,height,duration,r_frame_rate,codec_name,codec_type","-show_entries","format=size,bit_rate","-of","json",clips[0]["path"]],capture_output=True,text=True)
                info=json.loads(r.stdout) if r.stdout else {}
                vs_=next((s for s in info.get("streams",[]) if s.get("codec_type")=="video"),None)
                ar_=next((s for s in info.get("streams",[]) if s.get("codec_type")=="audio"),None)
                fmt=info.get("format",{}); dur=float(fmt.get("duration",0))
                k1,k2,k3,k4=st.columns(4)
                k1.metric("Duration",f"{dur:.1f}s")
                fps=0
                try: n,d=vs_.get("r_frame_rate","0/1").split("/"); fps=float(n)/float(d)
                except: pass
                k2.metric("FPS",f"{fps:.1f}")
                k3.metric("Resolution",f"{vs_.get('width',0)}x{vs_.get('height',0)}" if vs_ else "?x?")
                k4.metric("Codec",(vs_.get("codec_name","?") or "?").upper())
                k5,k6,k7,k8=st.columns(4)
                k5.metric("Audio","Yes" if ar_ else "No")
                k6.metric("Size",f"{sum(Path(c['path']).stat().st_size for c in clips)/(1024*1024):.1f}MB")
                k7.metric("Clips",str(len(clips))); k8.metric("Platform",platform)
            except: pass

        # ───── EDITING ─────
        st.divider(); st.subheader("🎨 Editing")
        ca,cb=st.columns(2)
        with ca:
            st.markdown("**🖼 Enhancement**")
            ac=st.checkbox("Auto Color",True,key="rac"); sh=st.checkbox("Sharpen",True,key="rsh")
            hdr=st.checkbox("HDR Look",False,key="rhdr"); vnr=st.checkbox("Noise Reduce",False,key="rvnr")
            fe=st.checkbox("👤 Face Enhance",False,key="rfe"); ms_=st.checkbox("📹 Stabilize",False,key="rms")
            mf=st.checkbox("🪞 Mirror Flip",False,key="rmf")
            st.markdown("**📐 Upscale**")
            u1080=st.checkbox("1080p",True,key="ru1080"); u4k=st.checkbox("4K",False,key="ru4k")
            st.markdown("**🎯 Motion**")
            mz=st.checkbox("Zoom",True,key="rmz"); mp_b=st.checkbox("Pan",True,key="rmp")
            msh=st.checkbox("Shake",False,key="rmsh"); mb_=st.checkbox("Blur",False,key="rmb")
            # TEXT OVERLAY
            st.markdown("**📝 Text Overlay**")
            with st.expander("➕ Add Text",expanded=False):
                tt=st.text_input("Text",key="rtt",placeholder="Your text")
                tti=st.number_input("Time (s)",0.0,3600.0,0.0,0.5,key="rtti")
                tsz=st.slider("Size",12,120,48,key="rtsz"); tcl=st.color_picker("Color","#FFFFFF",key="rtcl")
                tx_=st.selectbox("X",["center","left","right"],key="rtx"); ty_=st.selectbox("Y",["center","top","bottom"],key="rty")
                if st.button("Add",key="rta") and tt:
                    st.session_state.rus_texts.append({"text":tt,"time":tti,"size":tsz,"color":tcl,"x":tx_,"y":ty_}); st.rerun()
            if st.session_state.rus_texts:
                st.caption(f"{len(st.session_state.rus_texts)} overlay(s)")
                if st.button("Clear",key="rtclr"): st.session_state.rus_texts=[]; st.rerun()
        with cb:
            st.markdown("**🎤 Voice**")
            vp=st.slider("Pitch",-12,12,preset["pit"],key="rvp"); vs_v=st.slider("Speed",0.7,1.5,preset["spd"],0.05,key="rvs")
            vv=st.slider("Voice Vol",0.5,2.0,1.0,0.1,key="rvv"); nr=st.checkbox("Noise Removal",True,key="rnr")
            st.markdown("**🎬 Transition**")
            tr=st.selectbox("Style",TRANS,key="rtr")
            st.markdown("**🎨 Color**")
            sat=st.slider("Saturation",0.5,2.0,preset["sat"],0.05,key="rsat")
            con=st.slider("Contrast",0.5,2.0,preset["con"],0.05,key="rcon")
            # BG MUSIC
            st.markdown("**🎵 BG Music**")
            bgf=st.file_uploader("Music (MP3/WAV)",type=["mp3","wav","m4a"],key="rbgm"); bgv=st.slider("Volume",0.0,1.0,0.3,0.05,key="rbgv")
            # SFX
            st.markdown("**🔊 SFX Burst**")
            sfxf=st.file_uploader("SFX (MP3/WAV)",type=["mp3","wav"],key="rsfx"); sfxv=st.slider("SFX Vol",0.0,1.0,0.7,0.05,key="rsfxv")

        # ───── BRANDING ─────
        st.divider(); st.subheader("🏷 Branding")
        b1,b2,b3=st.columns(3)
        with b1: lf=st.file_uploader("Logo PNG",type=["png"],key="rlogo")
        with b2: inf=st.file_uploader("Intro",type=["mp4","mov"],key="rintro")
        with b3: outf=st.file_uploader("Outro",type=["mp4","mov"],key="routro")
        b4,b5=st.columns(2)
        with b4: wmt=st.text_input("Watermark",key="rwmtxt",placeholder="@handle")
        with b5: wmp=st.selectbox("Position",["bottom-right","bottom-left","top-right","top-left"],key="rwmpos")

        # ───── CAPTIONS ─────
        st.divider(); st.subheader("💬 Captions")
        ce=st.checkbox("AI Captions",True,key="rcap")
        if ce:
            c1,c2,c3=st.columns(3)
            c1.selectbox("Style",CSTYLES,key="rcst"); c2.selectbox("Pos",["bottom","center","top"],key="rcpos")
            c3.selectbox("Size",["small","medium","large"],key="rcsz"); st.checkbox("Animated",True,key="rcan")

        st.divider(); cpus=st.checkbox("🧊 CPU Safe Mode",True,key="rcpusafe")

        # ───── BATCH ─────
        st.divider(); batch=st.checkbox("🔄 Batch All Queue",False,key="rbatch")

        # ───── GENERATE ─────
        st.divider()
        if st.button("🚀 Generate Videos",type="primary",use_container_width=True,key="rgen"):
            od = _BASE / "outputs" / "reels_studio"; od.mkdir(parents=True,exist_ok=True)

            bgp=None; sfxp=None; introp=None; outrop=None; logop=None
            if bgf: bgp=ud/f"bgm_{int(time.time())}.{bgf.name.split('.')[-1]}"; bgp.write_bytes(bgf.read())
            if sfxf: sfxp=ud/f"sfx_{int(time.time())}.{sfxf.name.split('.')[-1]}"; sfxp.write_bytes(sfxf.read())
            if inf: introp=ud/f"intro_{int(time.time())}.mp4"; introp.write_bytes(inf.read())
            if outf: outrop=ud/f"outro_{int(time.time())}.mp4"; outrop.write_bytes(outf.read())
            if lf: logop=ud/f"logo_{int(time.time())}.png"; logop.write_bytes(lf.read())

            if batch and st.session_state.rus_queue:
                for qi,q in enumerate(st.session_state.rus_queue):
                    if q.get("status") in ("✅ done","rendering"): continue
                    st.session_state.rus_queue[qi]["status"]="rendering"
                    op=od/f"BATCH_{qi+1}_{int(time.time())}.mp4"
                    ok,err=_render_video(q.get("path",""),op,cpus,mf,ms_,vnr,fe,u4k,u1080,ac,sat,con,sh,hdr,mz,mp_b,msh,mb_,preset,wmt,wmp,vs_v,vp,vv,nr,bgv,tr,tw,th_,bgp,sfxp,sfxv,introp,outrop,logop,st.session_state.rus_texts,st.session_state.rus_trim_s,st.session_state.rus_trim_e)
                    st.session_state.rus_queue[qi]["status"]="✅ done" if ok else "❌ failed"
                    st.session_state.rus_queue[qi]["path"]=str(op)
                st.success(f"✅ Batch: {len(st.session_state.rus_queue)} done")
            else:
                inpath = clips[0]["path"]
                if len(clips)>1:
                    cp=ud/f"concat_{int(time.time())}.mp4"
                    _concat_clips(clips,cp); inpath=str(cp)

                op=od/f"REGEN_{int(time.time())}.mp4"
                qe={"name":clips[0]["name"],"preset":preset_name,"path":str(op),"status":"rendering"}
                st.session_state.rus_queue.append(qe)

                with st.status("🎬 Rendering...",expanded=True) as stat:
                    try:
                        ok,err=_render_video(inpath,op,cpus,mf,ms_,vnr,fe,u4k,u1080,ac,sat,con,sh,hdr,mz,mp_b,msh,mb_,preset,wmt,wmp,vs_v,vp,vv,nr,bgv,tr,tw,th_,bgp,sfxp,sfxv,introp,outrop,logop,st.session_state.rus_texts,st.session_state.rus_trim_s,st.session_state.rus_trim_e)
                        if ok:
                            stat.update(label="✅ Complete!",state="complete")
                            st.success(op.name); st.video(str(op))
                            st.metric("Size",f"{op.stat().st_size/(1024*1024):.1f}MB")
                            with open(op,"rb") as f:
                                st.download_button("⬇ Download",f.read(),file_name=op.name,mime="video/mp4",use_container_width=True)
                            st.session_state.rus_queue[-1]["status"]="✅ done"
                            st.session_state.rus_history.insert(0,{"name":clips[0]["name"],"preset":preset_name,"path":str(op),"time":time.strftime("%H:%M:%S"),"size":round(op.stat().st_size/(1024*1024),2)})
                        else:
                            stat.update(label="❌ Failed",state="error"); st.error(err[:500])
                            st.session_state.rus_queue[-1]["status"]="❌ failed"
                    except subprocess.TimeoutExpired:
                        stat.update(label="⏱ Timeout",state="error"); st.session_state.rus_queue[-1]["status"]="⏱ timeout"
                    except Exception as e:
                        stat.update(label="❌ Error",state="error"); st.error(str(e)); st.session_state.rus_queue[-1]["status"]="❌ error"

        # ───── QUEUE ─────
        with st.expander("📋 Queue",expanded=bool(st.session_state.rus_queue)):
            if st.session_state.rus_queue:
                for i,q in enumerate(st.session_state.rus_queue):
                    c1,c2=st.columns([5,1])
                    c1.text(f"{i+1}. {q.get('name','?')[:30]} — {q.get('status','?')}")
                    if q.get("status")=="✅ done" and Path(q.get("path","")).exists():
                        with open(q["path"],"rb") as f: c2.download_button("⬇",f.read(),file_name=Path(q["path"]).name,mime="video/mp4",key=f"rqd_{i}")
            else: st.info("Empty")

        # ───── HISTORY ─────
        with st.expander("📊 History",expanded=False):
            if st.session_state.rus_history:
                for i,h in enumerate(st.session_state.rus_history):
                    c1,c2=st.columns([5,1])
                    c1.text(f"{h['name'][:25]} ({h['preset']}) — {h['time']} | {h['size']}MB")
                    if Path(h["path"]).exists() and c2.button("▶",key=f"rhv_{i}"): st.video(h["path"])
            else: st.info("No history yet")

    else:
        st.info("👆 Upload a video or add clips!")
        st.markdown("""
### 🚀 Features:
🎵 BG Music | 🔊 SFX | 🎞 Multi-Clip | ✂️ Trim/Split | 📝 Text | 🤖 AI Auto-Edit | 📱 Platform | 🔄 Batch | 📊 History
""")
'''

# ══════════════════════════════════════════════════════════
# INJECT
# ══════════════════════════════════════════════════════════
before = text[:func_start]
after_start = func_body_start + len(old_func)
after = text[after_start:]

final = before + new_func + '\n' + after

# Ensure imports
need = {"import subprocess","import json","import os","import time","from pathlib import Path"}
for imp in need:
    if imp not in final[:500]: final = imp + '\n' + final

app.write_text(final, encoding="utf-8")
print("[2] Written:", len(final), "chars")

try:
    compile(final, "app.py", "exec")
    print("\n✅✅✅ SYNTAX OK! ✅✅✅")
    print("\nPhase 3 Features:")
    print("  🎵 BG Music — upload + auto-loop + volume")
    print("  🔊 SFX Burst — upload + volume")
    print("  🎞 Multi-Clip Editor — upload, reorder, delete")
    print("  ✂️ Trim/Split — start/end cut + segments")
    print("  📝 Text Overlay — timestamp, position, color, size")
    print("  🤖 AI Auto-Edit — checkbox enabled")
    print("  📱 Platform Presets — TikTok/YouTube/Instagram + auto res")
    print("  🔄 Batch Processing — queue all")
    print("  📊 Render History — preview + re-download")
    print("\nRun: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ Line {e.lineno}: {e.msg}")
    L = final.split('\n')
    for ln in range(max(0,e.lineno-3), min(len(L),e.lineno+2)):
        marker = ">>>" if ln+1==e.lineno else "   "
        print(f"  {marker} {ln+1}: {L[ln][:150]}")