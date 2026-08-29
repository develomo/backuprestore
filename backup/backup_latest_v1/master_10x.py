import re, os, shutil, subprocess, random
from pathlib import Path

print("Starting 10/10 Master Patch...")

# ==========================================
# FILE 1: safe_long_video_polished.py (Fixing Caption Drop)
# ==========================================
fn1 = 'safe_long_video_polished.py'
if os.path.exists(fn1):
    c1 = open(fn1, encoding='utf-8', errors='ignore').read()
    o1 = c1
    
    # Regex: Match the block where transcription fails and replace it with forced captions
    pattern = r"elif ENABLE_CAPTIONS and not caption_segments:.*?else:"
    replacement = """elif ENABLE_CAPTIONS and not caption_segments:
        set_status(76, "Captions enabled but transcription failed. FORCING transcript text...")
        try:
            _text = locals().get("SCRIPT_TEXT") or locals().get("FULL_SCRIPT") or locals().get("transcript_text") or ""
            _words = _text.split()
            _step = VOICE_DURATION / max(1, len(_words))
            caption_segments = [{"start": i*_step, "end": (i+1)*_step, "text": w} for i, w in enumerate(_words)]
            print(f"FORCED {len(caption_segments)} segments from transcript text.")
            words = build_caption_words_from_segments(
                segments=caption_segments,
                voice_duration=VOICE_DURATION,
                hook_duration=HOOK_DURATION
            )
            video = apply_captions(
                video,
                words,
                mode="long",
                style_ids=SELECTED_CAPTION_STYLES
            )
            video = video.set_duration(FINAL_DURATION)
        except Exception as e:
            print("Failed to force captions from transcript:", e)
    else:"""
    
    c1_new = re.sub(pattern, replacement, c1, flags=re.DOTALL)
    if c1_new != c1:
        shutil.copy2(fn1, fn1 + '.bak_10x')
        open(fn1, 'w', encoding='utf-8').write(c1_new)
        print("SUCCESS 1: Caption Fallback Logic Injected into safe_long_video_polished.py!")
    else:
        print("SKIP 1: Caption block not found or already patched.")
else:
    print("SKIP 1: safe_long_video_polished.py not found.")

# ==========================================
# FILE 2: batch_long_renderer.py (10/10 Editing & Voice Engine)
# ==========================================
fn2 = 'batch_long_renderer.py'
if os.path.exists(fn2):
    c2 = open(fn2, encoding='utf-8', errors='ignore').read()
    o2 = c2
    
    # 1. B-Roll & Watermark Code Block
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
    if 'def apply_niche_watermark' not in c2:
        c2 = c2.replace('def render_long_batch_memory(', mc + '\ndef render_long_batch_memory(')
    if 'apply_broll_overlay(current, broll_out' not in c2:
        c2 = c2.replace('if add_captions:', "broll_out = temp / 'video_broll.mp4'\n        current = apply_broll_overlay(current, broll_out, total_duration)\n        if add_captions:")
    if 'apply_niche_watermark(current, wm_out' not in c2:
        c2 = c2.replace('final=mux_audio_timeline(current,voice', "wm_out = temp / 'video_watermarked.mp4'\n        current = apply_niche_watermark(current, wm_out, preset.get('niche', 'default'))\n        final=mux_audio_timeline(current,voice")

    # 2. Force Captions if Whisper fails
    c2 = re.sub(r'if not segments:\s*\n\s*log\("\[StableLong\] captions requested but no real words found; skipping captions"\); shutil\.copy2\(video,out\); return out', r'if not segments:\n        log("FORCING CAPTIONS")\n        if not transcript_text: shutil.copy2(video,out); return out\n        parts = str(transcript_text).split()\n        step = max(0.2, total/max(1,len(parts)))\n        segments = [{"start": i*step, "end": (i+1)*step, "text": p} for i,p in enumerate(parts)]', c2, flags=re.DOTALL)

    # 3. Cinematic Voice Mastering (Warmth & Authority)
    c2 = c2.replace('f"atrim=0:{intro_sec+voice_duration:.3f},"', 'f"highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=10:release=100,equalizer=f=4000:t=q:w=1:g=2,atrim=0:{intro_sec+voice_duration:.3f},"')

    # 4. Invisible Transitions (Luxury Pacing)
    c2 = c2.replace("dur=min(0.85,max(0.50,duration_base+0.20))", "dur=min(1.0,max(0.60,duration_base+0.25))")
    c2 = c2.replace("dur=min(0.70,max(0.45,duration_base+0.15))", "dur=min(0.85,max(0.55,duration_base+0.20))")
    c2 = c2.replace("dur=min(0.75,max(0.45,duration_base+0.15))", "dur=min(1.1,max(0.70,duration_base+0.25))")
    if 'fadewhite' not in c2:
        c2 = c2.replace("dur=min(1.1,max(0.70,duration_base+0.25))", "dur=min(1.1,max(0.70,duration_base+0.25)); kind='fadewhite' if index-int(index/3)*3==0 else 'crossfade'")

    # 5. Lock UI Caption Style
    c2 = c2.replace("st=caption_style(style_id,niche=niche)", "st=caption_style(style_id,niche=niche)\n    if style_id and not is_auto_caption_style(style_id): st['selected_style_id'] = style_id")

    if c2 != o2:
        shutil.copy2(fn2, fn2 + '.bak_10x')
        open(fn2, 'w', encoding='utf-8').write(c2)
        print("SUCCESS 2: 10/10 Master Patch Applied to batch_long_renderer.py!")
    else:
        print("SKIP 2: batch_long_renderer.py already patched or no match.")
else:
    print("SKIP 2: batch_long_renderer.py not found.")

# Create folders
os.makedirs('assets/brolls', exist_ok=True)
os.makedirs('assets/logos', exist_ok=True)
print("\nALL DONE! 10/10 Setup Complete. Ready to Render.")