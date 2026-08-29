import re

fn = 'safe_long_video_polished.py'
lines = open(fn, encoding='utf-8', errors='ignore').readlines()
fixed = False

for i, line in enumerate(lines):
    if 'out=Path(output_path) if output_path else OUTPUT_DIR' in line:
        # Pehli ki line ka indentation check karenge
        j = i - 1
        while j >= 0 and lines[j].strip() == '':
            j -= 1
        if j >= 0:
            prev_line = lines[j]
            match = re.match(r'^(\s*)', prev_line)
            indent = match.group(1) if match else '    '
            if prev_line.strip().endswith(':'):
                indent += '    '
            lines[i] = indent + line.lstrip()
            print(f"SUCCESS: Fixed line {i+1} indentation to {len(indent)} spaces.")
            fixed = True
            break

if fixed:
    open(fn, 'w', encoding='utf-8').writelines(lines)
else:
    print("SKIP: Line not found.")