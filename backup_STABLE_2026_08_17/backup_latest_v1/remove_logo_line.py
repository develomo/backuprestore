with open("app.py", encoding="utf-8") as f:
    lines = f.readlines()

# Remove line containing '"logo": logo,'
lines = [line for line in lines if '"logo": logo' not in line]

with open("app.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("✅ Removed logo line. App should now run.")