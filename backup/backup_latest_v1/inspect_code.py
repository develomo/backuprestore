import ast
import os

files = ["app.py", "master_pipeline.py", "safe_long_video_polished.py"]

for file_name in files:
    print(f"\n================ {file_name} ================")
    if os.path.exists(file_name):
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        args = [a.arg for a in node.args.args]
                        print(f"Function: {node.name}({', '.join(args)})")
        except Exception as e:
            print(f"Error reading file: {e}")
    else:
        print(f"File '{file_name}' nahi mili.")