
# low_memory_long_renderer.py
from pathlib import Path
import subprocess, time, json, shutil, gc

VIDEO_EXTS={".mp4",".mov",".mkv",".avi",".webm",".m4v"}
AUDIO_EXTS={".mp3",".wav",".m4a",".aac",".flac",".ogg"}

def log(x):
    try: print(str(x), flush=True)
    except Exception: pass

def fnum(x,d=0.0):
    try: return float(x)
    except Exception: return float(d)

def natural_key(path):
    s=Path(path).stem; out=[]; cur=""
    for ch in s:
        if ch.isdigit(): cur+=ch
        else:
            if cur: out.append((0,int(cur))); cur=""
            out.append((1,ch.lower()))
    if cur: out.append((0,int(cur)))
    return out

def existing(items,exts=None):
    r=[]
    for x in items or []:
        try:
            p=Path(x)
            if p.exists() and p.is_file() and (exts is None or p.suffix.lower() in exts): r.append(p)
        except Exception: pass
    return sorted(r,key=natural_key)

def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

FFMPEG=get_ffmpeg()
FFPROBE=str(Path(FFMPEG).with_name("ffprobe.exe")) if Path(FFMPEG).name.lower()=="ffmpeg.exe" else "ffprobe"

def run(cmd):
    r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,errors="ignore")
    if r.returncode!=0: raise RuntimeError((r.stderr or "")[-2200:])
    return r

def duration(path):
    try:
        r=subprocess.run([FFPROBE,"-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,errors="ignore")
        if r.returncode==0: return max(.05,float(r.stdout.strip()))
    except Exception: pass
    return 6.0

def size_for(q):
    q=str(q or "360p").lower()
    if "720" in q: return (1280,720)
    if "480" in q: return (854,480)
    return (640,360)

def first_audio(items):
    a=existing(items,AUDIO_EXTS)
    return a[0] if a else None

def duration_plan(total,n):
    total=max(.1,fnum(total,.1)); n=max(1,int(n or 1)); base=total/n
    pat=[4.0,4.8,5.4,6.2,6.8,7.3,5.7,6.4,7.0,5.2,6.0,6.7]
    if base<3.2: ds=[base]*n
    else: ds=[max(3.2,min(8.0,base*.74+pat[i%len(pat)]*.26)) for i in range(n)]
    scale=total/max(.1,sum(ds)); ds=[max(.25,x*scale) for x in ds]
    if ds: ds[-1]=max(.25,ds[-1]+(total-sum(ds)))
    return ds

def motion_filter(size,index,dur,fps=24):
    w,h=size
    z=1.010+(index%5)*.0025
    frames=max(1,int(dur*fps))
    if index%4==1: x="(iw-iw/zoom)*0.35"; y="(ih-ih/zoom)/2"
    elif index%4==2: x="(iw-iw/zoom)*0.65"; y="(ih-ih/zoom)/2"
    elif index%4==3: x="(iw-iw/zoom)/2"; y="(ih-ih/zoom)*0.42"
    else: x="(iw-iw/zoom)/2"; y="(ih-ih/zoom)/2"
    fade_dur = 0.28
    fade_filter = f",fade=in:st=0:d={fade_dur},fade=out:st={dur-fade_dur:.3f}:d={fade_dur}"
    return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},zoompan=z='min({z},zoom+0.00007)':x='{x}':y='{y}':d={frames}:s={w}x{h}:fps={fps},eq=contrast=1.042:saturation=1.035:brightness=0.002,vignette=angle=0.12,setsar=1{fade_filter}"

def render_segment(src,out,wanted,index,size,fps=24,quality="360p"):
    sd=duration(src); wanted=max(.25,fnum(wanted,.25)); start=0
    if sd>wanted+.25: start=(sd-wanted)*((index%7)/7.0)
    crf="31" if "360" in str(quality).lower() else "29"
    cmd=[FFMPEG,"-y","-ss",f"{start:.3f}","-t",f"{wanted:.3f}","-i",str(src),"-an","-vf",motion_filter(size,index,wanted,fps),"-r",str(fps),"-pix_fmt","yuv420p","-c:v","libx264","-preset","ultrafast","-crf",crf,"-movflags","+faststart",str(out)]
    run(cmd); return out

def normalize_asset(src,out,size,fps=24,duration_limit=None,quality="360p"):
    w,h=size; crf="31" if "360" in str(quality).lower() else "29"
    cmd=[FFMPEG,"-y"]
    if duration_limit: cmd+=["-t",f"{float(duration_limit):.3f}"]
    cmd+=["-i",str(src),"-an","-vf",f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},eq=contrast=1.025:saturation=1.02,setsar=1","-r",str(fps),"-pix_fmt","yuv420p","-c:v","libx264","-preset","ultrafast","-crf",crf,"-movflags","+faststart",str(out)]
    run(cmd); return out

def concat_segments(segs,out):
    lf=Path(out).with_suffix(".txt")
    with lf.open("w",encoding="utf-8") as f:
        for s in segs:
            fp=str(Path(s).resolve()).replace("\\","/").replace("'","'\\''")
            f.write(f"file '{fp}'\n")
    try: run([FFMPEG,"-y","-f","concat","-safe","0","-i",str(lf),"-c","copy",str(out)])
    except Exception: run([FFMPEG,"-y","-f","concat","-safe","0","-i",str(lf),"-c:v","libx264","-preset","ultrafast","-crf","31","-pix_fmt","yuv420p",str(out)])
    try: lf.unlink(missing_ok=True)
    except Exception: pass
    return out

def overlay_image(video,overlay,out,start=None,dur=6.0,scale_width=180):
    if not overlay or not Path(overlay).exists():
        shutil.copy2(video,out); return out
    vd=duration(video)
    if start is None: start=max(0,vd-dur-.25)
    end=min(vd,start+dur)
    filt=f"[1:v]scale={scale_width}:-1,format=rgba,colorchannelmixer=aa=0.92[ov];[0:v][ov]overlay=main_w-overlay_w-24:main_h-overlay_h-24:enable='between(t,{start:.3f},{end:.3f})'"
    run([FFMPEG,"-y","-i",str(video),"-loop","1","-i",str(overlay),"-filter_complex",filt,"-c:v","libx264","-preset","ultrafast","-crf","31","-pix_fmt","yuv420p","-an",str(out)])
    return out

def mux(video,voice,out,music=None,sfx=None,dur=None):
    dur=fnum(dur,duration(video)); cmd=[FFMPEG,"-y","-i",str(video),"-i",str(voice)]
    filters=["[1:a]volume=1.015,highpass=f=90,lowpass=f=9500,aresample=44100[v]"]; labels=["[v]"]
    if music and Path(music).exists():
        cmd+=["-stream_loop","-1","-i",str(music)]
        filters.append(f"[2:a]volume=0.052,afade=t=in:st=0:d=0.8,afade=t=out:st={max(0,dur-1):.3f}:d=1.0,aresample=44100[m]"); labels.append("[m]")
    if sfx and Path(sfx).exists():
        idx=3 if music and Path(music).exists() else 2
        cmd+=["-stream_loop","-1","-i",str(sfx)]
        filters.append(f"[{idx}:a]volume=0.062,aresample=44100[s]"); labels.append("[s]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0.3,alimiter=limit=0.97[aout]")
    cmd+=["-filter_complex",";".join(filters),"-map","0:v:0","-map","[aout]","-t",f"{dur:.3f}","-c:v","copy","-c:a","aac","-b:a","160k","-movflags","+faststart",str(out)]
    run(cmd); return out

def render_long_low_memory(voice_path,clips,output_path=None,music_path=None,sfx_files=None,intro_path=None,outro_path=None,subscribe_overlay=None,quality="360p",fps=24,temp_root=None,cleanup=True,progress_callback=None):
    start=time.time(); voice=Path(voice_path); cps=existing(clips,VIDEO_EXTS)
    if not voice.exists(): raise FileNotFoundError(f"Voice not found: {voice}")
    if not cps: raise FileNotFoundError("No valid clips found.")
    size=size_for(quality); vdur=duration(voice)
    out=Path(output_path) if output_path else Path.cwd()/ "outputs"/f"final_long_low_memory_v2_{int(time.time())}.mp4"
    out.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(temp_root) if temp_root else out.parent/f"_render_temp_v2_{int(time.time())}"
    segdir=temp/"segments"; segdir.mkdir(parents=True,exist_ok=True)
    log(f"[LowMemoryLongV2] start clips={len(cps)} voice={vdur:.2f}s quality={quality} size={size}")
    
    # Loop/repeat clips if we don't have enough to fill the duration with reasonable pacing (average 6.0 seconds per clip)
    target_clip_duration = 6.0
    needed_clips_count = int(vdur / target_clip_duration)
    if needed_clips_count > len(cps):
        multiplier = (needed_clips_count // len(cps)) + 1
        cps = (cps * multiplier)[:needed_clips_count]
        log(f"[LowMemoryLongV2] Clips looped to total count = {len(cps)} to avoid stretching")

    segs=[]
    try:
        intro_used=intro_path and Path(intro_path).exists()
        outro_used=outro_path and Path(outro_path).exists()
        if intro_used:
            seg=segdir/"seg_00000_intro.mp4"; log("[LowMemoryLongV2] render intro")
            normalize_asset(intro_path,seg,size,fps,3.0,quality); segs.append(seg)
        body=max(1.0,vdur-(3 if intro_used else 0)-(4 if outro_used else 0))
        plan=duration_plan(body,len(cps))
        for i,cp in enumerate(cps):
            if progress_callback:
                try: progress_callback(i+1,len(cps),str(cp))
                except Exception: pass
            seg=segdir/f"seg_{i+1:05d}.mp4"
            try:
                log(f"[LowMemoryLongV2] render {i+1}/{len(cps)} {cp.name}")
                render_segment(cp,seg,plan[i],i,size,fps,quality); segs.append(seg)
            except Exception as e: log(f"[LowMemoryLongV2] skipped unreadable/corrupt {cp.name}: {e}")
            gc.collect()
        if outro_used:
            seg=segdir/f"seg_{len(segs)+1:05d}_outro.mp4"; log("[LowMemoryLongV2] render outro")
            normalize_asset(outro_path,seg,size,fps,4.0,quality); segs.append(seg)
        if not segs: raise RuntimeError("No segments rendered.")
        no_overlay=temp/"video_no_overlay.mp4"; concat_segments(segs,no_overlay)
        video_for_audio=no_overlay
        if subscribe_overlay and Path(subscribe_overlay).exists():
            video_for_audio=temp/"video_overlay.mp4"; log("[LowMemoryLongV2] apply subscribe overlay")
            overlay_image(no_overlay,subscribe_overlay,video_for_audio)
        final=mux(video_for_audio,voice,out,music=music_path,sfx=first_audio(sfx_files),dur=vdur)
        try: out.with_suffix(".json").write_text(json.dumps({"engine":"low_memory_v2","clips":len(cps),"segments":len(segs),"duration":vdur,"intro":bool(intro_used),"outro":bool(outro_used),"subscribe":bool(subscribe_overlay),"final":str(final)},indent=2),encoding="utf-8")
        except Exception: pass
        log(f"[LowMemoryLongV2] done -> {final}"); return str(final)
    finally:
        if cleanup:
            try: shutil.rmtree(temp,ignore_errors=True)
            except Exception: pass
        gc.collect()
