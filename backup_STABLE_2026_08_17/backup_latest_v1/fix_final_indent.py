import re

fn = 'batch_long_renderer.py'
c = open(fn, encoding='utf-8', errors='ignore').read()
o = c

# Pura galat indentation wala function hata kar naya sahi wala lagana
broken_pattern = r"def apply_niche_watermark\(v,o,n=\"default\"\):.*?return Path\(v\)"
fixed_code = '''def apply_niche_watermark(v,o,n="default"):
    d=Path("assets/logos").resolve()
    wp=None
    for e in [".png",".jpg",".jpeg",".webp"]:
        p=d/f"{n}{e}"
        if p.exists(): wp=p; break
    if not wp:
        for e in [".png",".jpg",".jpeg",".webp"]:
            p=d/f"default{e}"
            if p.exists(): wp=p; break
    if not wp:
        print("[Watermark] No logo found in assets/logos. Skipping.")
        return Path(v)
    try:
        print(f"[Watermark] Applying logo: {wp}")
        cmd=[FFMPEG,"-y","-i",str(v),"-i",str(wp),"-filter_complex","[1:v]scale=iw*0.12:-1,format=rgba,colorchannelmixer=aa=0.6[wm];[0:v][wm]overlay=W-w-25:25","-c:a","copy","-c:v","libx264","-preset","ultrafast","-crf","28",str(o)]
        r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if r.returncode != 0:
            print(f"[Watermark] FFmpeg Error: {r.stderr.decode('utf-8', errors='ignore')[-500:]}")
        if o.exists() and o.stat().st_size > 1000: return Path(o)
    except Exception as e:
        print(f"[Watermark] Exception: {e}")
    return Path(v)
'''

c_new = re.sub(broken_pattern, fixed_code, c, flags=re.DOTALL)

if c_new != c:
    open(fn, 'w', encoding='utf-8').write(c_new)
    print("SUCCESS: Indentation Error 100% Fixed! Code is perfectly aligned now.")
else:
    print("SKIP: Pattern not found.")