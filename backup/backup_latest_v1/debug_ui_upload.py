from pathlib import Path

for p in Path(".").rglob("*"):
    if p.is_file() and ("upload" in str(p).lower() or "temp" in str(p).lower() or "session" in str(p).lower()):
        print(p)