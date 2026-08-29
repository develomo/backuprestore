with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("==================================================")
print("INSPECTING EXECUTE_RENDERING_PIPELINE (LINES 420 TO 560)")
print("==================================================")

for idx in range(420, min(560, len(lines))):
    print(f"Line {idx+1}: {lines[idx]}", end="")