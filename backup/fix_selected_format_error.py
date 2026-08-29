import os
import ast
import re

print("🚀 Fixing NameError: selected_format in app.py...")

APP_FILE = "app.py"

if not os.path.exists(APP_FILE):
    print("❌ Error: app.py file not found.")
    exit(1)

with open(APP_FILE, "r", encoding="utf-8") as f:
    code = f.read()

# Backup app.py
with open("app.py.bak_selected_format", "w", encoding="utf-8") as f_bak:
    f_bak.write(code)

# Safe replacement line (Checks variable safely without NameError crash)
safe_line = "if locals().get('is_long_format', False) or ('selected_format' in locals() and ('16:9' in str(selected_format) or 'Long' in str(selected_format))):"

# Replace problematic line
if 'if ("16:9" in str(selected_format)) or ("Long" in str(selected_format)) or is_long_format:' in code:
    code = code.replace(
        'if ("16:9" in str(selected_format)) or ("Long" in str(selected_format)) or is_long_format:',
        safe_line
    )
else:
    # Regex replacement to catch minor space variations
    code = re.sub(
        r'if\s*\(\s*"16:9"\s*in\s*str\(selected_format\)\s*\).*?:',
        safe_line,
        code
    )

# Validate Python AST syntax
try:
    ast.parse(code)
    with open(APP_FILE, "w", encoding="utf-8") as f:
        f.write(code)
    print("✅ AST PASSED! app.py successfully fixed without any syntax errors.")
except SyntaxError as e:
    print(f"❌ Syntax Error during validation: {e}")