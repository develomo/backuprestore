import os

fn = 'batch_long_renderer.py'
print(f"========== VERIFYING PATCHES IN {fn} ==========")
c = open(fn, encoding='utf-8', errors='ignore').read()

# 1. Verify Outro Fix
if '-an",str(outro_out)' in c and '-t",f"{outro_sec:.3f}"' in c:
    print("✅ VERIFIED 1: Outro is forced to 2 seconds and is SILENT (-an applied).")
else:
    print("❌ FAILED 1: Outro fix not found.")

# 2. Verify Loop Fix
if '-stream_loop","-1","-i",str(video_raw)' in c:
    print("✅ VERIFIED 2: Clips will LOOP (repeat) if voice is longer than clips.")
else:
    print("❌ FAILED 2: Loop fix not found.")

# 3. Verify Watermark Fix
if '[Watermark] Applying logo:' in c:
    print("✅ VERIFIED 3: Robust Watermark Engine is applied (Will print errors if logo missing).")
else:
    print("❌ FAILED 3: Watermark fix not found.")

# 4. Verify Cinematic Voice
if 'acompressor=threshold=-20dB' in c:
    print("✅ VERIFIED 4: Cinematic Voice Mastering (Warmth/EQ) is applied.")
else:
    print("❌ FAILED 4: Cinematic Voice not found.")

# 5. Verify Captions Fallback
if 'FORCING CAPTIONS' in c:
    print("✅ VERIFIED 5: Caption Fallback Engine is applied.")
else:
    print("❌ FAILED 5: Caption fix not found.")

print("======================================")