import re

fn = 'safe_long_video_polished.py'
c = open(fn, encoding='utf-8', errors='ignore').read()

# Line 197 ko exactly 4 spaces par set karna
c = re.sub(r"^[ \t]*out=Path\(output_path\) if output_path else OUTPUT_DIR.*?exist_ok=True\)", "    out=Path(output_path) if output_path else OUTPUT_DIR/f\"final_long_stable_{int(time.time())}.mp4\"; out.parent.mkdir(parents=True,exist_ok=True)", c, flags=re.MULTILINE)

# Line 198 ko exactly 4 spaces par set karna
c = re.sub(r"^[ \t]*safe_print\(f\"\[SafeLongStable\] render.*?subscribe_mid=\{bool\(subscribe\)\}\"\)", "    safe_print(f\"[SafeLongStable] render | clips={len(clip_list)} | quality={q} | captions={cap_on} | intro={bool(intro)} | outro={bool(outro)} | subscribe_mid={bool(subscribe)}\")", c, flags=re.MULTILINE)

open(fn, 'w', encoding='utf-8').write(c)
print("SUCCESS: Both lines (197 & 198) fixed to exactly 4 spaces indentation!")