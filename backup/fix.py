import re,os,shutil,subprocess
from pathlib import Path

# File 1 Patch
fn='batch_long_renderer.py'
c=open(fn,encoding='utf-8',errors='ignore').read()
o=c

mc = '''import random as _br
def get_broll_clip():
    d=Path("assets/brolls")
    if not d.exists(): return None
    f=[x for x in d.glob("*") if x.suffix.lower() in [".mp4",".mov",".jpg",".png",".jpeg",".webp"]]
    if not f: return None
    return _br.choice(f)

def apply_broll_overlay(v,o,t):
    b=get_broll_clip()
    if not b: return Path(v)
    try:
        s=max(0,t/2-1.5)
        cmd=[FFMPEG,"-y","-i",str(v),"-i",str(b),"-filter_complex",f"[1:v]scale=iw*0.3:ih*0.3,scale=iw:ih:force_original_aspect_ratio=decrease,pad=iw:ih:(ow-iw)/2:(oh-ih)/2:black@0,setsar=1,format=yuva420p,fade=t=in:st=0:d=0.5:alpha=1,fade=t=out:st=2.5:d=0.5:alpha=1[b];[0:v][b]overlay=x=(W-w)/2:y=(H-h)/2:enable=between(t,{s},{s}+3)","-c:a","copy","-c:v","libx264","-preset","ultrafast","-crf","28",str(o)]
        subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if o.exists() and o.stat().st_size > 1000: return Path(o)
    except: pass
    return Path(v)

def apply_niche_watermark(v,o,n="default"):
    d=Path("assets/logos")
    wp=None
    for e in [".png",".jpg",".jpeg",".webp"]:
        p=d/f"{n}{e}"
        if p.exists(): wp=p; break
    if not wp:
        for e in [".png",".jpg",".jpeg",".webp"]:
            p=d/f"default{e}"
            if p.exists(): wp=p; break
    if not wp: return Path(v)
    try:
        cmd=[FFMPEG,"-y","-i",str(v),"-i",str(wp),"-filter_complex","[1:v]scale=iw*0.12:-1,format=rgba,colorchannelmixer=aa=0.6[wm];[0:v][wm]overlay=W-w-25:25","-c:a","copy","-c:v","libx264","-preset","ultrafast","-crf","28",str(o)]
        subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if o.exists() and o.stat().st_size > 1000: return Path(o)
    except: pass
    return Path(v)
'''

if 'def apply_niche_watermark' not in c:
    c=c.replace('def render_long_batch_memory(', mc+'\ndef render_long_batch_memory(')
if 'apply_broll_overlay(current, broll_out' not in c:
    c=c.replace('if add_captions:', "broll_out = temp / 'video_broll.mp4'\n        current = apply_broll_overlay(current, broll_out, total_duration)\n        if add_captions:")
if 'apply_niche_watermark(current, wm_out' not in c:
    c=c.replace('final=mux_audio_timeline(current,voice', "wm_out = temp / 'video_watermarked.mp4'\n        current = apply_niche_watermark(current, wm_out, preset.get('niche', 'default'))\n        final=mux_audio_timeline(current,voice")

# Force Captions
c=re.sub(r'if not segments:\s*\n\s*log\("\[StableLong\] captions requested but no real words found; skipping captions"\); shutil\.copy2\(video,out\); return out', r'if not segments:\n        log("FORCING CAPTIONS")\n        if not transcript_text: shutil.copy2(video,out); return out\n        parts = str(transcript_text).split()\n        step = max(0.2, total/max(1,len(parts)))\n        segments = [{"start": i*step, "end": (i+1)*step, "text": p} for i,p in enumerate(parts)]', c, flags=re.DOTALL)

# Fix Hard Cuts (Smooth Transitions)
c=c.replace("dur=min(0.55,max(0.32,duration_base+0.08))", "dur=min(0.85,max(0.50,duration_base+0.20))")
c=c.replace("dur=min(0.48,max(0.25,duration_base+0.04))", "dur=min(0.70,max(0.45,duration_base+0.15))")
if 'fadewhite' not in c:
    c=c.replace("dur=min(0.75,max(0.45,duration_base+0.15))", "dur=min(0.75,max(0.45,duration_base+0.15)); kind='fadewhite' if index-int(index/3)*3==0 else 'crossfade'")

if c!=o:
    shutil.copy2(fn,fn+'.bak_master')
    open(fn,'w',encoding='utf-8').write(c)
    print('SUCCESS 1: batch_long_renderer.py patched!')

# File 2 Patch
fn2='safe_long_video_polished.py'
c2=open(fn2,encoding='utf-8',errors='ignore').read()
o2=c2
c2=re.sub(r'def caption_enabled\(add_captions,caption_mode,style_id=None\):\s*\n\s*if not bool\(add_captions\): return False\s*\n\s*if str\(caption_mode or ""\)\.lower\(\) in \{"none","off","false","0"\}: return False', r'def caption_enabled(add_captions,caption_mode,style_id=None):\n    return True', c2, flags=re.DOTALL)
if c2!=o2:
    shutil.copy2(fn2,fn2+'.bak_master')
    open(fn2,'w',encoding='utf-8').write(c2)
    print('SUCCESS 2: safe_long_video_polished.py patched!')

os.makedirs('assets/brolls',exist_ok=True)
os.makedirs('assets/logos',exist_ok=True)
print('ALL DONE! Ready to render 10/10 video.')