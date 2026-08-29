"""Fix Trim number_input max_value error"""
from pathlib import Path
import shutil, time

APP = Path(r"D:\My Creation Video Generator\backup\app.py")
ts = int(time.time())
shutil.copy2(APP, APP.parent / f"app.py.bak_trifix_{ts}")
text = APP.read_text(encoding="utf-8")
print("=" * 60)
print("FIX: Trim End max_value")
print("=" * 60)

# Fix 1: Session init — rus_trim_e default 0.0 instead of 60.0
old = '("rus_trim_e",60.0)'
new = '("rus_trim_e",0.0)'
if old in text:
    text = text.replace(old, new)
    print("[1] rus_trim_e default: 60.0 → 0.0")
else:
    print("[1] rus_trim_e default already fine or not found")

# Fix 2: Ensure End number_input uses safe max_value that includes current value
# Find the problematic line pattern
old2 = 'max(st.session_state.rus_trim_e,fd)'
new2 = 'max(st.session_state.rus_trim_e,fd,0.0)'
if old2 in text:
    text = text.replace(old2, new2)
    print("[2] max_value: added fallback 0.0")
else:
    print("[2] max_value pattern not found — checking alt...")

# Fix 3: Alternative — just set max_value=fd and use actual duration for default
old3 = 'max(st.session_state.rus_trim_e,fd)'
new3 = 'fd'
# Also ensure value doesn't exceed fd on first load
old4 = 'st.session_state.rus_trim_e=max(te_val,ts_val+0.1)'
new4 = 'st.session_state.rus_trim_e=min(max(te_val,ts_val+0.1),fd)'
if old4 in text:
    text = text.replace(old4, new4)
    print("[3] rus_trim_e clamped to fd")
else:
    print("[3] alt clamp not found")

# Fix 4: If rus_trim_e > fd on load, reset it
# Find the trim expander and add safety reset before number_input
old5 = 'with st.expander("✂️ Trim & Split",expanded=False):'
new5 = '''with st.expander("✂️ Trim & Split",expanded=False):
            try:
                rr=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",clips[0]["path"]],capture_output=True,text=True)
                fdur = float(rr.stdout.strip()) if rr.stdout.strip() else 60.0
            except: fdur=60.0
            if st.session_state.rus_trim_e <= 0 or st.session_state.rus_trim_e > fdur:
                st.session_state.rus_trim_e = fdur'''
if old5 in text:
    text = text.replace(old5, new5)
    print("[4] Added auto-reset for rus_trim_e")
else:
    print("[4] expander pattern not found")

# Fix 5: Replace number_input lines with safe versions
old6 = 'te_val=st.number_input("End (s)",0.0,fd,max(st.session_state.rus_trim_e,fd,0.0),0.1,key="rte")'
new6 = 'te_val=st.number_input("End (s)",0.0,fdur,min(st.session_state.rus_trim_e,fdur),0.1,key="rte")'
if 'fdur' in text:
    text = text.replace(old6, new6) if old6 in text else text
    # Also fix the Start line to use fdur
    old7 = 'st.number_input("Start (s)",0.0,fd,st.session_state.rus_trim_s,0.1,key="rts")'
    new7 = 'st.number_input("Start (s)",0.0,fdur,min(st.session_state.rus_trim_s,fdur),0.1,key="rts")'
    if old7 in text:
        text = text.replace(old7, new7)
        print("[5] Start/End number_inputs fixed with fdur")
else:
    print("[5] fdur not in text yet")

APP.write_text(text, encoding="utf-8")
print("[6] Written")

try:
    compile(text, "app.py", "exec")
    print("\n✅ SYNTAX OK!")
    print("Run: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ Line {e.lineno}: {e.msg}")