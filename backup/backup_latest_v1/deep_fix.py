import re,os,shutil 
def patch(fn, patterns): 
 if not os.path.exists(fn): print('MISSING: '+fn); return 
 c=open(fn,encoding='utf-8',errors='ignore').read(); o=c 
 for p,r in patterns: c=re.sub(p,r,c,flags=re.DOTALL) 
 if c!=o: shutil.copy2(fn,fn+'.bak2'); open(fn,'w',encoding='utf-8').write(c); print('DEEP PATCHED: '+fn) 
 else: print('NO CHANGE: '+fn) 
patch('batch_long_renderer.py', [ 
 (r'if not segments:\s*\n\s*log\("\[StableLong\] captions requested but no real words found; skipping captions"\); shutil\.copy2\(video,out\); return out', r'if not segments:\n        log("[StableLong] captions requested but no words found! FORCING basic transcript captions")\n        if not transcript_text: shutil.copy2(video,out); return out\n        parts = str(transcript_text).split()\n        step = max(0.2, total/max(1,len(parts)))\n        segments = [{"start": i*step, "end": (i+1)*step, "text": p} for i,p in enumerate(parts)]'), 
 (r'dur=min\(0\.55,max\(0\.32,duration_base\+0\.08\)\)', r'dur=min(0.75,max(0.45,duration_base+0.15))'), 
 (r'dur=min\(0\.48,max\(0\.25,duration_base\+0\.04\)\)', r'dur=min(0.65,max(0.40,duration_base+0.10))'), 
]) 
patch('safe_long_video_polished.py', [ 
 (r'def caption_enabled\(add_captions,caption_mode,style_id=None\):\s*\n\s*if not bool\(add_captions\): return False\s*\n\s*if str\(caption_mode or ""\)\.lower\(\) in \{"none","off","false","0"\}: return False', r'def caption_enabled(add_captions,caption_mode,style_id=None):\n    return True # FORCED CAPTIONS ON'), 
 (r'caption_mode\s*=\s*"none"', r'caption_mode = "phrase"'), 
]) 
print("Deep patch complete! Ready to render.") 
