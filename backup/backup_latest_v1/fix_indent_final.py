from pathlib import Path

file_path = Path("app.py")
content = file_path.read_text(encoding="utf-8")

lines = content.splitlines()

# Line 534 fix karo (0-index -> 533)
target_line_index = 533  # kyunki error line 534 dikha raha hai

if len(lines) > target_line_index:
    # Check karo ke line mein "logo" hai
    if '"logo": logo' in lines[target_line_index]:
        # Pehle line (533) ka indent nikaalo (jo "outro" wali line hai)
        prev_line = lines[target_line_index - 1]
        # Indent spaces count karo
        indent = len(prev_line) - len(prev_line.lstrip())
        indent_str = " " * indent
        
        # Line ko sahi indent ke saath replace karo
        lines[target_line_index] = indent_str + '"logo": logo,'
        
        # File ko dubara likho
        file_path.write_text("\n".join(lines), encoding="utf-8")
        print("✅ Indentation fixed at line 534.")
    else:
        print("⚠️ Line 534 doesn't contain 'logo'. Trying fallback search...")
        # Fallback: poori file mein "logo" dhundho aur uski indent fix karo
        for i, line in enumerate(lines):
            if '"logo": logo' in line:
                prev_line = lines[i - 1]
                indent = len(prev_line) - len(prev_line.lstrip())
                indent_str = " " * indent
                lines[i] = indent_str + '"logo": logo,'
                file_path.write_text("\n".join(lines), encoding="utf-8")
                print(f"✅ Fixed indentation at line {i+1}.")
                break
else:
    print("❌ File mein 534 lines nahi hain?")