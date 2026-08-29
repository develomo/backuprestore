import re, os, shutil
from pathlib import Path

fn = 'batch_long_renderer.py'
c = open(fn, encoding='utf-8', errors='ignore').read()
o = c

# 1. Fix Outro Length (Force trim to exactly 2 seconds and remove audio)
old_outro = """if outro:
            outro_out=batch_dir/f"batch_{len(outputs)+1:04d}_outro.mp4"; normalize_video_asset(outro,outro_out,size,fps,outro_sec,quality); outputs.append(outro_out)"""
new_outro = """if outro:
            outro_out=batch_dir/f"batch_{len(outputs)+1:04d}_outro.mp4"
            run_cmd([FFMPEG,"-y","-i",str(outro),"-t",f"{outro_sec:.3f}","-vf",f"scale={size[0]}:{size[1]}:force_original_aspect_ratio=decrease,pad={size[0]}:{size[1]}:(ow-iw)/2:(oh-ih)/2:black,fps={fps}","-c:v","libx264","-preset","ultrafast","-crf","30","-pix_fmt","yuv420p","-an",str(outro_out)])
            outputs.append(outro_out)"""
if old_outro in c:
    c = c.replace(old_outro, new_outro)
    print("SUCCESS 1: Outro forced to exactly 2 seconds and silent.")

# 2. Fix Clip Looping (Repeat clips from start instead of freezing last frame)
old_loop = """if visual_duration<total_duration-.5:
            extended=temp/"video_duration_fixed.mp4"; log(f"[StableLong] visual shorter ({visual_duration:.2f} < {total_duration:.2f}); extending")
            pad=max(0.1,total_duration-visual_duration)
            run_cmd([FFMPEG,"-y","-i",str(video_raw),"-vf",f"tpad=stop_mode=clone:stop_duration={pad:.3f},trim=0:{total_duration:.3f},setpts=PTS-STARTPTS","-c:v","libx264","-preset","ultrafast","-crf","30","-pix_fmt","yuv420p",str(extended)])"""
new_loop = """if visual_duration<total_duration-.5:
            extended=temp/"video_duration_fixed.mp4"; log(f"[StableLong] visual shorter ({visual_duration:.2f} < {total_duration:.2f}); LOOPING clips to match voice duration")
            run_cmd([FFMPEG,"-y","-stream_loop","-1","-i",str(video_raw),"-t",f"{total_duration:.3f}","-c:v","libx264","-preset","ultrafast","-crf","30","-pix_fmt","yuv420p",str(extended)])
        elif visual_duration>total_duration+.5:
            extended=temp/"video_duration_fixed.mp4"; log(f"[StableLong] visual longer ({visual_duration:.2f} > {total_duration:.2f}); trimming clips to match voice")
            run_cmd([FFMPEG,"-y","-i",str(video_raw),"-t",f"{total_duration:.3f}","-c:v","libx264","-preset","ultrafast","-crf","30","-pix_fmt","yuv420p",str(extended)])"""
if old_loop in c:
    c = c.replace(old_loop, new_loop)
    print("SUCCESS 2: Clips will now loop/repeat until voice ends.")

# 3. Fix Watermark (Use absolute path and print actual error if fails)
pattern_wm = r"def apply_niche_watermark\(v,o,n=\"default\"\):.*?return Path\(v\)"
replacement_wm = """def apply_niche_watermark(v,o,n="default"):
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
        return Path(v)"""
if re.search(pattern_wm, c, re.DOTALL):
    c = re.sub(pattern_wm, replacement_wm, c, flags=re.DOTALL)
    print("SUCCESS 3: Watermark engine upgraded (will show errors if any).")

if c != o:
    shutil.copy2(fn, fn + '.bak_outro_wm')
    open(fn, 'w', encoding='utf-8').write(c)
    print("\nALL DONE: Outro & Watermark bugs fixed! Ready to render.")
else:
    print("\nNO CHANGES SAVED. Texts might be slightly different.")