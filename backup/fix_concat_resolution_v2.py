"""Fix concat_files_hard v2: scale+pad normalize then concat with correct labels"""
import os

target = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'batch_long_renderer.py')
with open(target, 'r', encoding='utf-8') as f:
    c = f.read()

with open(target + '.bak_concat_v2', 'w', encoding='utf-8') as f:
    f.write(c)

# v1 fix lines (to remove)
old_filter = '''    filter_parts = []
    for i, seg in enumerate(segments):
        cmd += ["-i", str(seg)]
        filter_parts.append(f"[{i}:v]scale=854:480:force_original_aspect_ratio=decrease,pad=854:480:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}];")'''

old_concat = '''    concat_filter = "".join(filter_parts) + \\
                    f"concat=n={len(segments)}:v=1:a=0[vout]"'''

# v2 fix: scale+pad each input, concat uses [scaled{i}] as inputs
new_filter = '''    filter_parts = []
    scale_parts = []
    for i, seg in enumerate(segments):
        cmd += ["-i", str(seg)]
        filter_parts.append(f"[{i}:v]scale=854:480:force_original_aspect_ratio=decrease,pad=854:480:(ow-iw)/2:(oh-ih)/2[scaled{i}];")
        scale_parts.append(f"[scaled{i}]")'''

new_concat = '''    concat_filter = "".join(filter_parts) + \\
                    "".join(scale_parts) + \\
                    f"concat=n={len(segments)}:v=1:a=0[vout]"'''

if old_filter in c and old_concat in c:
    c = c.replace(old_filter, new_filter)
    c = c.replace(old_concat, new_concat)
    compile(c, target, 'exec')
    with open(target, 'w', encoding='utf-8') as f:
        f.write(c)
    print('[OK] v2: scale+pad -> [scaled{i}] -> concat')
else:
    print('[FAIL] Patterns not found — showing current lines:')
    with open(target, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i in range(1863, 1874):
        print(f'  {i+1}: {lines[i].rstrip()}')