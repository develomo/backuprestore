fn = 'safe_long_video_polished.py'
lines = open(fn, encoding='utf-8', errors='ignore').readlines()
print("========== LINES 190 TO 205 ==========")
for i in range(189, min(205, len(lines))):
    # Har line ke aage uska number likh ke print karega
    print(f"{i+1}: {lines[i].rstrip()}")
print("======================================")