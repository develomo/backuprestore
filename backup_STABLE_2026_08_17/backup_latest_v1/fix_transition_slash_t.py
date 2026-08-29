"""Fix /t -> /1 in TRANSITION_TYPES (batch_long_renderer.py)"""
import os

target = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'batch_long_renderer.py')
with open(target, 'r', encoding='utf-8') as f:
    c = f.read()

# backup
with open(target + '.bak_t_fix', 'w', encoding='utf-8') as f:
    f.write(c)

pairs = [
    ('{dur}/t):ih:iw*{dur}/t:0', '{dur}/1):ih:iw*{dur}/1:0'),
    ('{dur}/t):ih:0:0',          '{dur}/1):ih:0:0'),
    ('{dur}/t:0,fade',           '{dur}/1:0,fade'),
    ('{dur}/t):0,',              '{dur}/1):0,'),
    ('{dur}/t,fade',             '{dur}/1,fade'),
    ('{dur}/t),',                '{dur}/1),'),
]

for old, new in pairs:
    if old in c:
        c = c.replace(old, new)
        print('[FIXED]', old[:40])
    else:
        print('[SKIP]', old[:40])

compile(c, target, 'exec')
with open(target, 'w', encoding='utf-8') as f:
    f.write(c)
print('[OK] All done. Syntax valid.')