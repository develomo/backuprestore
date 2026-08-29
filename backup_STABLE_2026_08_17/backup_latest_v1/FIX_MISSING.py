"""Fix missing mp_b, mb_ variables in _render_video call"""
from pathlib import Path
import shutil, time

APP = Path(r"D:\My Creation Video Generator\backup\app.py")
ts = int(time.time())
shutil.copy2(APP, APP.parent / f"app.py.bak_missing_{ts}")
text = APP.read_text(encoding="utf-8")
print("=" * 60)
print("FIX: mp_b, mb_ undefined")
print("=" * 60)

# Fix 1: Replace all mp_b → mp, mb_ → mb in render calls (these are the checkbox vars)
count = 0
# mp_b → mp_bool (rename to match actual variable)
for old, new in [('mp_b', 'mp'), ('mb_', 'mb'), ('ms_', 'ms')]:
    if old in text and old not in ['_mp_','_mb_']:
        text = text.replace(old, new)
        count += 1
        print(f"[{count}] {old} → {new}")

# Also check if variables are defined in UI
if 'mp=st.checkbox' not in text and 'mp_b=st.checkbox' not in text:
    print("[!] mp checkbox not found — adding")
    text = text.replace(
        'msh=st.checkbox("Shake",False,key="rmsh")',
        'msh=st.checkbox("Shake",False,key="rmsh"); mp=st.checkbox("Pan",True,key="rmp")'
    )

if 'mb=st.checkbox' not in text and 'mb_=st.checkbox' not in text:
    print("[!] mb checkbox not found — adding")
    text = text.replace(
        'msh=st.checkbox("Shake",False,key="rmsh"); mp=st.checkbox("Pan",True,key="rmp")',
        'msh=st.checkbox("Shake",False,key="rmsh"); mp=st.checkbox("Pan",True,key="rmp"); mb=st.checkbox("Blur",False,key="rmb")'
    )

APP.write_text(text, encoding="utf-8")
print(f"[Done] Written: {len(text)} chars")

try:
    compile(text, "app.py", "exec")
    print("\n✅✅✅ SYNTAX OK! ✅✅✅")
    print("Run: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ Line {e.lineno}: {e.msg}")