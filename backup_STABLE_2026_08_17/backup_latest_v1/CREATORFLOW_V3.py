"""
CREATORFLOW_V3.py — Backup se restore + actual file structure se match
"""
from pathlib import Path
import shutil

P = Path(r"D:\My Creation Video Generator\backup\app.py")
orig = P.read_text(encoding="utf-8")

# Step 0: Restore from clean backup
backups = sorted(Path(r"D:\My Creation Video Generator\backup").glob("app.py.bak*"), reverse=True)
if backups:
    shutil.copy(backups[0], P)
    print(f"[0] Restored from: {backups[0].name}")

T = P.read_text(encoding="utf-8")
lines = T.splitlines()

# 1. Page config
for i, line in enumerate(lines):
    if "st.set_page_config" in line and "page_title" in line:
        T = T.replace(line, 'st.set_page_config(page_title="CreatorFlow AI", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")', 1)
        print(f"[1] Page config updated (line {i+1})")
        break
else:
    print("[1] No set_page_config found — will add inline")

# 2. words=None
T = T.replace('words=[]', 'words=None')
T = T.replace('"words": []', '"words": None')
print("[2] words=None")

# 3 & 4. Find exact st.tabs line
TAB_MARKER = None
for i, line in enumerate(T.splitlines()):
    if 'st.tabs(' in line and ('Video Generator' in line or 'Reels' in line or 't1' in line or 't2' in line):
        TAB_MARKER = line
        TAB_IDX = i
        print(f"[3] Found tabs at line {i+1}: {line.strip()[:100]}")
        break

if not TAB_MARKER:
    print("[3] ⚠️ st.tabs NOT FOUND — showing grep:")
    for i, line in enumerate(T.splitlines()):
        if 'st.tabs' in line.lower() or 'tabs(' in line.lower():
            print(f"    {i+1}: {line[:120]}")
    raise SystemExit(1)

# 5. Inject navbar
indent = TAB_MARKER[:len(TAB_MARKER) - len(TAB_MARKER.lstrip())]

navbar = f'''
{indent}# ═══════════ CreatorFlow AI Navbar ═══════════
{indent}st.markdown(\"\"\"
{indent}<style>
{indent}[data-testid="stAppViewContainer"] > .main {{ background: linear-gradient(135deg, #0B1220, #111827); }}
{indent}header[data-testid="stHeader"] {{ background: transparent !important; }}
{indent}.cf-navbar {{
{indent}    display: flex; align-items: center; justify-content: space-between;
{indent}    padding: 10px 28px; margin: 8px 12px 0 12px; border-radius: 16px;
{indent}    background: rgba(17,24,39,0.7); backdrop-filter: blur(20px);
{indent}    -webkit-backdrop-filter: blur(20px);
{indent}    border: 1px solid rgba(108,92,231,0.25);
{indent}    box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 60px rgba(108,92,231,0.08);
{indent}}}
{indent}.cf-left {{ display: flex; align-items: center; gap: 14px; }}
{indent}.cf-logo {{
{indent}    width: 44px; height: 44px; border-radius: 12px;
{indent}    background: linear-gradient(135deg, #6C5CE7, #A855F7, #00D4FF);
{indent}    display: flex; align-items: center; justify-content: center;
{indent}    font-size: 22px; box-shadow: 0 0 20px rgba(108,92,231,0.5);
{indent}}}
{indent}.cf-brand-text {{ display: flex; flex-direction: column; }}
{indent}.cf-brand-name {{
{indent}    font-size: 18px; font-weight: 700;
{indent}    background: linear-gradient(90deg, #A855F7, #00D4FF);
{indent}    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
{indent}}}
{indent}.cf-brand-sub {{ font-size: 10px; color: rgba(255,255,255,0.45); }}
{indent}.cf-center {{ display: flex; align-items: center; gap: 6px; }}
{indent}.cf-nav-btn {{
{indent}    padding: 9px 20px; border-radius: 10px; font-size: 13px; font-weight: 600;
{indent}    color: rgba(255,255,255,0.6); background: transparent; border: 1px solid transparent;
{indent}    cursor: pointer; transition: all 0.3s; white-space: nowrap;
{indent}}}
{indent}.cf-nav-btn:hover {{
{indent}    color: #fff; background: rgba(108,92,231,0.15);
{indent}    border-color: rgba(108,92,231,0.4); box-shadow: 0 0 16px rgba(108,92,231,0.2);
{indent}}}
{indent}.cf-nav-btn.active {{
{indent}    color: #fff; background: linear-gradient(135deg, rgba(108,92,231,0.25), rgba(0,212,255,0.1));
{indent}    border-color: rgba(108,92,231,0.6); box-shadow: 0 0 20px rgba(108,92,231,0.3);
{indent}}}
{indent}.cf-right {{ display: flex; align-items: center; gap: 10px; }}
{indent}.cf-icon-btn {{
{indent}    width: 36px; height: 36px; border-radius: 10px;
{indent}    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
{indent}    display: flex; align-items: center; justify-content: center; cursor: pointer;
{indent}    transition: all 0.25s; font-size: 16px;
{indent}}}
{indent}.cf-icon-btn:hover {{ background: rgba(108,92,231,0.2); border-color: rgba(108,92,231,0.5); }}
{indent}.cf-theme-select {{
{indent}    padding: 6px 10px; border-radius: 8px; font-size: 12px;
{indent}    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12);
{indent}    color: rgba(255,255,255,0.7); cursor: pointer;
{indent}}}
{indent}#MainMenu {{ visibility: hidden; }}
{indent}footer {{ visibility: hidden; }}
{indent}[data-testid="stToolbar"] {{ display: none; }}
{indent}[data-testid="stDecoration"] {{ display: none; }}
{indent}</style>
{indent}<div class="cf-navbar">
{indent}    <div class="cf-left"><div class="cf-logo">🎬</div><div class="cf-brand-text"><span class="cf-brand-name">CreatorFlow AI</span><span class="cf-brand-sub">Create • Transform • Automate</span></div></div>
{indent}    <div class="cf-center"><button class="cf-nav-btn active">🎬 Video Generator</button><button class="cf-nav-btn">🚀 Reels Upload Studio</button></div>
{indent}    <div class="cf-right"><select class="cf-theme-select"><option>🌙 Dark</option></select><div class="cf-icon-btn">🔔</div><div class="cf-icon-btn">⚙️</div><div class="cf-icon-btn">❓</div><div class="cf-icon-btn">ℹ️</div></div>
{indent}</div>
{indent}\"\"\", unsafe_allow_html=True)
{indent}# ═══════════════════════════════════════════════════
'''

T = T.replace(TAB_MARKER + '\n', navbar + '\n' + TAB_MARKER + '\n', 1)
print("[5] Navbar injected")

# VALIDATE
P.write_text(T, encoding="utf-8")
try:
    compile(T, str(P), "exec")
    print("\n✅ DONE — 0 errors! Run: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ {e}")
    P.write_text(orig, encoding="utf-8")
    print("↩️ Rolled back")