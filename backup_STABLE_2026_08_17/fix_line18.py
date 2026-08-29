import re

fn = 'batch_long_renderer.py'
lines = open(fn, encoding='utf-8', errors='ignore').readlines()
fixed = False

# Agar line 18 par unexpected indent hai, toh usko 0 spacing par set karo
for i in range(len(lines)):
    stripped = lines[i].lstrip()
    if stripped.startswith('if not logo_path or not Path(logo_path).exists():'):
        lines[i] = stripped  # Remove all leading spaces
        fixed = True
        print(f"SUCCESS: Fixed line {i+1} indentation to 0 spaces.")
        break

if fixed:
    open(fn, 'w', encoding='utf-8').writelines(lines)
else:
    print("SKIP: Line not found.")