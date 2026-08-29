import os

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'merged_settings = {**settings, **assets}' in line:
        # Correct indentation measure
        indent = ' ' * (len(line) - len(line.lstrip()))
        fixed_lines.append(line)
        fixed_lines.append(f"{indent}rendered_path = process_multi_clip_render(clips, voice, str(output_file), settings=merged_settings)\n")
        # Skip the broken line next to it if present
        if i + 1 < len(lines) and 'rendered_path = process_multi_clip_render' in lines[i + 1]:
            i += 1
    elif 'rendered_path = process_multi_clip_render' in line and 'merged_settings' not in (lines[i-1] if i > 0 else ''):
        # Fallback if line is orphan
        indent = ' ' * (len(line) - len(line.lstrip()))
        fixed_lines.append(f"{indent}rendered_path = process_multi_clip_render(clips, voice, str(output_file), settings=settings)\n")
    else:
        fixed_lines.append(line)
    i += 1

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("✅ Indentation Error in app.py successfully fixed!")