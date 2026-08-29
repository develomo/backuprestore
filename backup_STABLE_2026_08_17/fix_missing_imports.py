# fix_missing_imports.py
from pathlib import Path

file_path = Path("batch_long_renderer.py")
content = file_path.read_text(encoding="utf-8")

# Check and add missing imports at the top
imports_to_add = []

if "import re" not in content:
    imports_to_add.append("import re")
    
if "import random" not in content and "import random as _rand" not in content:
    imports_to_add.append("import random")

if imports_to_add:
    # Find the first import line and add before it
    lines = content.split('\n')
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            insert_idx = i
            break
    
    for imp in imports_to_add:
        lines.insert(insert_idx, imp)
        insert_idx += 1
    
    content = '\n'.join(lines)
    file_path.write_text(content, encoding="utf-8")
    print(f"✅ Added missing imports: {', '.join(imports_to_add)}")
else:
    print("ℹ️ All imports already present")

# Verify syntax
try:
    compile(content, str(file_path), "exec")
    print("✅ Syntax verification PASSED!")
    print("💡 NEXT: Run 'streamlit run app.py'")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")