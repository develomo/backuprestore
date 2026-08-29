import os

fn = 'batch_long_renderer.py'
print(f"========== SCANNING {fn} FOR OUTRO & WATERMARK BUGS ==========")
try:
    c = open(fn, encoding='utf-8', errors='ignore').readlines()
    for i, l in enumerate(c):
        low = l.lower()
        # Dhoondh rahe hain jahan outro, total_duration, ya watermark ka logic ho
        if any(k in low for k in ['outro', 'total_duration', 'voice_duration', 'apply_niche_watermark', 'concat_files', 'tpad', 'loop']):
            print(f'{fn} L{i+1}: {l.rstrip()}')
except Exception as e:
    print(f"Error: {e}")

print("\nDONE: Copy this output and send it.")