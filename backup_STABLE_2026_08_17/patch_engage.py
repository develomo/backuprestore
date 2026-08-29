import re, shutil, os, subprocess 
fn = 'batch_long_renderer.py' 
c = open(fn, encoding='utf-8', errors='ignore').read() 
o = c 
broll_code = "import random as _broll_random\nfrom pathlib import Path\ndef get_broll_clip():\n    broll_dir = Path('assets/brolls')\n    if not broll_dir.exists(): return None\n    files = [f for f in broll_dir.glob('*') if f.suffix.lower() in ['.mp4', '.mov', '.jpg', '.png']]\n    if not files: return None\n    return _broll_random.choice(files)\ndef apply_broll_overlay(video, out, total_duration):\n    broll = get_broll_clip()\n    if not broll:\n        shutil.copy2(video, out); return out\n    try:\n        mid = total_duration / 2\n        start = max(0, mid - 1.5)\n        cmd = [FFMPEG, '-y', '-i', str(video), '-i', str(broll), '-filter_complex', f'[1:v]scale=iw*0.3:ih*0.3,scale=iw:ih:force_original_aspect_ratio=decrease,pad=iw:ih:(ow-iw)/2:(oh-ih)/2:black@0,setsar=1,format=yuva420p,fade=t=in:st=0:d=0.5:alpha=1,fade=t=out:st=2.5:d=0.5:alpha=1[b];[0:v][b]overlay=x=(W-w)/2:y=(H-h)/2:enable=between(t,{start},{start}+3)', '-c:a', 'copy', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28', str(out)]\n        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)\n        if out.exists() and out.stat().st_size > 1000: return out\n    except Exception as e:\n        pass\n    shutil.copy2(video, out); return out\n" 
c = c.replace('def render_long_batch_memory(', broll_code + '\ndef render_long_batch_memory(') 
c = c.replace('if add_captions:', "broll_out = temp / 'video_broll.mp4'\n        current = apply_broll_overlay(current, broll_out, total_duration)\n        if add_captions:") 
c = c.replace("st=caption_style(style_id,niche=niche)", "st=caption_style(style_id,niche=niche)\n    if style_id and not is_auto_caption_style(style_id): st['selected_style_id'] = style_id") 
c = c.replace('zoompan=z=\'min({z:.4f},zoom+{step:.6f})\'', 'zoompan=z=\'if(lte(on,2),min({z*1.05:.4f},{z:.4f}),min({z:.4f},zoom+{step:.6f}))\'') 
if c != o: 
    shutil.copy2(fn, fn + '.bak_engage') 
    open(fn, 'w', encoding='utf-8').write(c) 
    print('SUCCESS: B-roll, UI Captions, aur Zoom Punch code add ho gaya hai!') 
else: 
    print('ERROR: Code add nahi hua, text match nahi hua.') 
if not os.path.exists('assets/brolls'): 
    os.makedirs('assets/brolls') 
    print('Created assets/brolls folder. Put 1-2 broll videos inside it.') 
