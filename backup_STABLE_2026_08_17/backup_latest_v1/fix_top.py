fn = 'batch_long_renderer.py'
lines = open(fn, encoding='utf-8', errors='ignore').readlines()
fixed = False

# File ke shuru ke 15 lines check karenge
for i in range(min(15, len(lines))):
    stripped = lines[i].lstrip()
    # Agar koi bhi line top level par extra spaces se shuru ho rahi hai
    if lines[i].startswith('    ') or lines[i].startswith('\t'):
        lines[i] = stripped  # 0 spaces par set kar do
        fixed = True

if fixed:
    open(fn, 'w', encoding='utf-8').writelines(lines)
    print("SUCCESS: Top lines indentation fixed to 0 spaces!")
else:
    print("SKIP: No top-level indentation found.")