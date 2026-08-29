with open("app.py", encoding="utf-8") as f:
    lines = f.readlines()
    for i in range(519, 541):  # 0-index, so 519 = line 520
        print(f"{i+1:4d}: {lines[i].rstrip()}")