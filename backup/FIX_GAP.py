"""Fix indent gap after function replacement"""
from pathlib import Path
import shutil, time

APP = Path(r"D:\My Creation Video Generator\backup\app.py")
ts = int(time.time())
shutil.copy2(APP, APP.parent / f"app.py.bak_gap_{ts}")
text = APP.read_text(encoding="utf-8")
print("=" * 60)
print("FIX: Indent gap after function body")
print("=" * 60)

# Fix 1: Remove blank section between NEW_FUNCTION_BODY end and next def
old = """        st.caption("No videos in queue — upload a video above")
    

def main()"""
new = """        st.caption("No videos in queue — upload a video above")

def main()"""

if old in text:
    text = text.replace(old, new)
    print("[1] Gap fixed")
else:
    # Try broader
    for gap in ['\n\n\ndef ', '\n\n\n\ndef ']:
        if gap in text:
            text = text.replace(gap, '\n\ndef ')
            print(f"[1] Gap fixed: {repr(gap)}")
            break

APP.write_text(text, encoding="utf-8")
print(f"[Done] Written: {len(text)} chars")

try:
    compile(text, "app.py", "exec")
    print("\n✅✅✅ SYNTAX OK! ✅✅✅")
    print("Run: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ Line {e.lineno}: {e.msg}")
    L = text.split('\n')
    for ln in range(max(0, e.lineno - 3), min(len(L), e.lineno + 2)):
        marker = ">>>" if ln + 1 == e.lineno else "   "
        print(f"  {marker} {ln+1}: {L[ln][:200]}")