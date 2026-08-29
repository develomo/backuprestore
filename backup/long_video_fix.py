import re,shutil,glob,os;q=chr(39);Q=chr(34) 
P=[(r'captions\s*=\s*False','captions = True'),(r'enable_captions\s*=\s*False','enable_captions = True'),(r'caption_enabled\s*=\s*False','caption_enabled = True'),(r'skip_captions\s*=\s*True','skip_captions = False'),(r'no_captions\s*=\s*True','no_captions = False'),(r'disable_captions\s*=\s*True','disable_captions = False'),(r'transitions\s*=\s*False','transitions = True'),(r'enable_transitions\s*=\s*False','enable_transitions = True'),(r'skip_transitions\s*=\s*True','skip_transitions = False'),(r'disable_transitions\s*=\s*True','disable_transitions = False'),(r'\bzoom\s*=\s*False','zoom = True'),(r'enable_zoom\s*=\s*False','enable_zoom = True'),(r'ken_burns\s*=\s*False','ken_burns = True'),(r'skip_zoom\s*=\s*True','skip_zoom = False'),(r'disable_zoom\s*=\s*True','disable_zoom = False'),(r'captions\s*=\s*None','captions = True'),(r'transitions\s*=\s*None','transitions = True'),(r'zoom\s*=\s*None','zoom = True'),('transition_type\\s*=\\s*'+q+'cut'+q,'transition_type = '+q+'crossfade'+q),('transition_type\\s*=\\s*'+q+'none'+q,'transition_type = '+q+'crossfade'+q),('transition_type\\s*=\\s*'+q+'hard'+q,'transition_type = '+q+'crossfade'+q),('transition\\s*=\\s*'+q+'cut'+q,'transition = '+q+'crossfade'+q),('transition\\s*=\\s*'+q+'none'+q,'transition = '+q+'crossfade'+q),('transition_type\\s*=\\s*'+Q+'cut'+Q,'transition_type = '+q+'crossfade'+q),('transition_type\\s*=\\s*'+Q+'none'+Q,'transition_type = '+q+'crossfade'+q),('transition_type\\s*=\\s*'+Q+'hard'+Q,'transition_type = '+q+'crossfade'+q),('transition\\s*=\\s*'+Q+'cut'+Q,'transition = '+q+'crossfade'+q),('transition\\s*=\\s*'+Q+'none'+Q,'transition = '+q+'crossfade'+q)] 
t=0 
for fn in sorted(glob.glob('*.py')): 
 if fn.endswith('.bak_fix')or fn.startswith('long_video_fix'):continue 
 try:c=open(fn,encoding='utf-8').read() 
 except:continue 
 o=c;n=0 
 for p,r in P: 
  m=len(re.findall(p,c)) 
  if m:c=re.sub(p,r,c);n+=m 
 if c!=o: 
  shutil.copy2(fn,fn+'.bak_fix');open(fn,'w',encoding='utf-8').write(c);print('PATCHED: '+fn+' ('+str(n)+' changes)');t+=1 
 else:print('SKIP: '+fn) 
print('Total patched: '+str(t)) 
if t==0: 
 print('No patterns found. Showing relevant lines...') 
 for fn in ['batch_long_renderer.py','safe_long_video_polished.py','master_pipeline.py']: 
  if not os.path.exists(fn):continue 
  for i,l in enumerate(open(fn,encoding='utf-8').readlines()): 
   low=l.lower() 
   if any(k in low for k in ['caption','transition','zoom','ken_burns','clip_dur','cut_int']): 
    print(fn+' L'+str(i+1)+': '+l.rstrip()) 
