import re
import os

APP_PATH = "app.py" # agar backup folder mai ho to yahi rehne do

with open(APP_PATH, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

# --- PART 1: IndentationError Fix for line 1624 around with t2: ---
print("Fixing indentation around t2...")
fixed_lines = []
for i, line in enumerate(lines):
    # line number 1624 ke aas paas check karo (index 1623)
    if 1615 <= i <= 1635 and "with t2:" in line:
        # pichli tab ka indent lo
        prev_indent = ""
        for j in range(i-1, -1, -1):
            if "with t1:" in lines[j] or "with gr.Tab" in lines[j]:
                prev_indent = re.match(r'^(\s*)', lines[j]).group(1)
                break
        # t2 ko same indent pe set karo
        fixed_lines.append(prev_indent + "with t2:\n")
        print(f"Fixed line {i+1}: {repr(fixed_lines[-1])}")
    else:
        fixed_lines.append(line)

lines = fixed_lines

# --- PART 2: Navbar Inject ---
# Check agar navbar pehle se nahi hai
content = "".join(lines)
if "my-navbar" not in content:
    print("Injecting Navbar...")

    navbar_code = '''
# --- AUTO INJECTED NAVBAR START ---
navbar_html = """
<style>
#my-navbar { display:flex; gap:12px; padding:12px 20px; background: linear-gradient(135deg,#8E2DE2,#4A00E0); border-radius:12px; margin-bottom:15px; align-items:center; }
#my-navbar button { background:white; color:#4A00E0; border:none; padding:8px 16px; border-radius:20px; font-weight:600; cursor:pointer; }
#my-navbar button.active { background:#FF2D55; color:white; }
</style>
<div id="my-navbar">
    <span style="color:white; font-weight:800; margin-right:20px;">My Creation Video Generator</span>
    <button onclick="document.querySelector('[data-testid=tab] button:nth-child(1)')?.click()" class="active">Video Generator</button>
    <button onclick="document.querySelector('[data-testid=tab] button:nth-child(2)')?.click()">Editing Style</button>
    <button onclick="document.querySelector('[data-testid=tab] button:nth-child(3)')?.click()">Auto-Detect Mode</button>
    <button onclick="document.querySelector('[data-testid=tab] button:nth-child(4)')?.click()">Export Studio</button>
</div>
"""
# --- AUTO INJECTED NAVBAR END ---
'''

    # Gradio Blocks ke andar sab se upar inject karo
    new_lines = []
    injected = False
    for line in lines:
        new_lines.append(line)
        if not injected and "gr.Blocks" in line and "as demo" in line:
            new_lines.append(navbar_code)
            new_lines.append(" gr.HTML(navbar_html)\n")
            injected = True

    # Agar gr.Blocks wala pattern na mile to import ke baad daal do
    if not injected:
        for idx, l in enumerate(new_lines):
            if "import gradio" in l:
                new_lines.insert(idx+1, navbar_code)
                break

    lines = new_lines
else:
    print("Navbar already exists, skipping inject.")

with open(APP_PATH, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("DONE! app.py fixed successfully.")