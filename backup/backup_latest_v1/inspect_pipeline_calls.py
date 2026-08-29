import re

APP_FILE = "app.py"

print("==================================================")
print("INSPECTING APP.PY FOR RENDERING CALLS")
print("==================================================")

try:
    with open(APP_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Total lines in {APP_FILE}: {len(lines)}\n")

    print("--- 1. IMPORTED PIPELINE MODULES ---")
    for idx, line in enumerate(lines, 1):
        if "import" in line and any(k in line.lower() for k in ["pipeline", "master", "batch", "render", "short", "long"]):
            print(f"Line {idx}: {line.strip()}")

    print("\n--- 2. GENERATE BUTTONS & PIPELINE TRIGGERS ---")
    for idx, line in enumerate(lines, 1):
        if any(k in line for k in ["st.button", "button", "render_", "process_", "execute_"]):
            if any(k in line.lower() for k in ["video", "short", "long", "generate", "pipeline"]):
                print(f"Line {idx}: {line.strip()[:100]}")

    print("\n--- 3. FUNCTIONS DEFINED IN APP.PY RELATED TO PIPELINES ---")
    for idx, line in enumerate(lines, 1):
        if line.strip().startswith("def ") and any(k in line.lower() for k in ["render", "pipeline", "short", "long", "process", "generate"]):
            print(f"Line {idx}: {line.strip()}")

except Exception as e:
    print(f"Error reading app.py: {e}")