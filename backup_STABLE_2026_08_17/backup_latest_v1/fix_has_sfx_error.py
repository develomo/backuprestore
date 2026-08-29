# fix_has_sfx_error.py
# Targeted fix for "NameError: name 'has_sfx' is not defined"
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent

def fix_has_sfx():
    filepath = BASE_DIR / "batch_long_renderer.py"
    if not filepath.exists():
        print("[ERROR] batch_long_renderer.py not found")
        return
    
    content = filepath.read_text(encoding="utf-8")
    lines = content.split('\n')
    new_lines = []
    
    fixed_count = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Look for "if has_sfx:"
        if stripped == "if has_sfx:":
            # Check if the previous few lines define has_sfx
            prev_defined = False
            for j in range(i-1, max(-1, i-5), -1):
                if "has_sfx =" in lines[j]:
                    prev_defined = True
                    break
                if lines[j].strip() and not lines[j].strip().startswith("#"):
                    break
            
            # If not defined, add it with correct indentation
            if not prev_defined:
                indent = len(line) - len(line.lstrip())
                indent_str = " " * indent
                new_lines.append(f"{indent_str}has_sfx = bool(sfx and Path(sfx).exists())")
                fixed_count += 1
                
        new_lines.append(line)
    
    if fixed_count > 0:
        filepath.write_text("\n".join(new_lines), encoding="utf-8")
        print(f"[OK] Fixed 'has_sfx' NameError ({fixed_count} instance(s) patched)")
    else:
        print("[INFO] 'has_sfx' definition already present.")

if __name__ == "__main__":
    print("🔧 Fixing 'has_sfx' NameError...")
    fix_has_sfx()
    print("✅ Fix complete. You can now run: streamlit run app.py")