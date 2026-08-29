import os 
 
files = [ 
    'batch_long_renderer.py', 
    'render_worker.py', 
    'audio_mixer.py', 
    'render_orchestrator.py', 
    'task_manager.py', 
    'app_phase2.py', 
    'test_phase2.py', 
] 
 
bad = ['\u2014', '\u2013', '\u2018', '\u2019', '\u201c', '\u201d', '\u2026'] 
 
for f in files: 
    if not os.path.exists(f): print(f'MISSING: {f}'); continue 
    with open(f, 'r', encoding='utf-8') as fh: 
        for i, line in enumerate(fh, 1): 
            for ch in bad: 
                if ch in line: print(f'ERROR: {f} line {i}: {line.rstrip()[:100]}') 
