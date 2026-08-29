"""Fix concat_files_hard: normalize all segments to 854x480 before concat"""
import os

target = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'batch_long_renderer.py')
with open(target, 'r', encoding='utf-8') as f:
    c = f.read()

# backup
with open(target + '.bak_concat', 'w', encoding='utf-8') as f:
    f.write(c)

old = '''    filter_parts = []
    for i, seg in enumerate(segments):
        cmd += ["-i", str(seg)]
        filter_parts.append(f"[{i}:v]")'''

new = '''    filter_parts = []
    for i, seg in enumerate(segments):
        cmd += ["-i", str(seg)]
        filter_parts.append(f"[{i}:v]scale=854:480:force_original_aspect_ratio=decrease,pad=854:480:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}];")'''

if old in c:
    c = c.replace(old, new)
    compile(c, target, 'exec')
    with open(target, 'w', encoding='utf-8') as f:
        f.write(c)
    print('[OK] concat_files_hard: scale+pad normalization added!')
else:
    print('[FAIL] Pattern not found')
