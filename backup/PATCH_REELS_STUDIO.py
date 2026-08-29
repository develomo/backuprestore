"""PATCH — Sirf Reels Upload Studio ke andar fix + new settings.
Fixes: NameError 'time', inline imports cleanup
Adds: CPU Safe Mode checkbox, Render Quality Target slider
"""
import sys
from pathlib import Path

P = Path(r"D:\My Creation Video Generator\backup\app.py")
T = P.read_text(encoding="utf-8")

# ──────────────────────────────────────────────────────
#  1. Function top me import time, tempfile, subprocess, json add karo
# ──────────────────────────────────────────────────────
OLD1 = '''    """Reels Upload Studio — Complete AI Video Editor"""

    PRESETS = {'''
NEW1 = '''    """Reels Upload Studio — Complete AI Video Editor"""

    import time, tempfile, subprocess, json as _json_builtin

    PRESETS = {'''
T = T.replace(OLD1, NEW1, 1)

# ──────────────────────────────────────────────────────
#  2. Caption Style ke baad CPU Safe Mode + Quality Target add karo
# ──────────────────────────────────────────────────────
SPOT = 'st.selectbox("💬 Caption Style", ["kinetic", "classic", "neon", "minimal", "bold", "typewriter"], key="rus_capstyle")'
INSERT = SPOT + '''

    q1, q2 = st.columns(2)
    with q1:
        cpu_safe = st.checkbox("🧊 CPU Safe Mode", True, key="rus_cpu_safe", help="Slower but prevents laptop overheating on 8GB RAM")
    with q2:
        quality_target = st.slider("🎯 Render Quality Target", 5, 10, 9, key="rus_quality", help="Voice score target (9+ recommended)")'''
T = T.replace(SPOT, INSERT, 1)

# ──────────────────────────────────────────────────────
#  3. has_vid block se inline import tempfile hatao
# ──────────────────────────────────────────────────────
OLD2 = '''    if has_vid:
        import tempfile, os as _os
        tdir = tempfile.gettempdir()'''
NEW2 = '''    if has_vid:
        tdir = tempfile.gettempdir()'''
T = T.replace(OLD2, NEW2, 1)

# ──────────────────────────────────────────────────────
#  4. VIDEO INFO section se inline import subprocess, json hatao
# ──────────────────────────────────────────────────────
OLD3 = '''        # ───── VIDEO INFO ─────
        import subprocess, json as _json
        try:'''
NEW3 = '''        # ───── VIDEO INFO ─────
        try:'''
T = T.replace(OLD3, NEW3, 1)

# ──────────────────────────────────────────────────────
#  5. _json.loads → _json_builtin.loads
# ──────────────────────────────────────────────────────
T = T.replace("_json.loads", "_json_builtin.loads")

# ──────────────────────────────────────────────────────
#  WRITE + VERIFY
# ──────────────────────────────────────────────────────
P.write_text(T, encoding="utf-8")
compile(T, str(P), "exec")
print("✅ PATCH APPLIED — SYNTAX OK")
print("   • import time, tempfile, subprocess, json — function top pe add")
print("   • CPU Safe Mode checkbox + Render Quality Target slider — add")
print("   • inline imports — cleanup")
print(f"   File: {P}")