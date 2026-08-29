import ast
import os

files = ["voice_duration.py", "duration_guard.py", "audio_engine.py"]

for file_name in files:
    print(f"\n================ {file_name} ================")
    if os.path.exists(file_name):
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
                functions = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        args = [a.arg for a in node.args.args]
                        functions.append(f"{node.name}({', '.join(args)})")
                
                if functions:
                    print("Functions found:")
                    for fn in functions:
                        print(f" - {fn}")
                else:
                    print("No functions found in this file.")
        except Exception as e:
            print(f"Error parsing file: {e}")
    else:
        print(f"File '{file_name}' nahi mili.")