"""
Fix style_id -> caption_style_id in safe_long_video_polished.py
"""
import os

SL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'safe_long_video_polished.py')

with open(SL, 'r', encoding='utf-8') as f:
    c = f.read()

bak = SL + '.bak_styleid'
with open(bak, 'w', encoding='utf-8') as f:
    f.write(c)

old = 'style_id=caption_profile.get("selected_style_id",style_id)'
new = 'caption_style_id=caption_profile.get("selected_style_id","auto")'

if old in c:
    c = c.replace(old, new)
    compile(c, SL, 'exec')
    with open(SL, 'w', encoding='utf-8') as f:
        f.write(c)
    print('[OK] style_id -> caption_style_id FIXED!')
else:
    print('[NOT FOUND] Searching...')
    idx = c.find('style_id')
    if idx >= 0:
        print('Found at', idx, ':', repr(c[idx:idx+120]))
    else:
        print('style_id not in file at all')