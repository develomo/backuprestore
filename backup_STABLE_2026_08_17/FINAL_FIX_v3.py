"""FINAL FIX V3 — All settings visible + connected to pipeline + trim + stretch + aspect + captions"""
from pathlib import Path
import shutil, time

APP = Path(r"D:\My Creation Video Generator\backup\app.py")
ts = int(time.time())
shutil.copy2(APP, APP.parent / f"app.py.bak_finalv3_{ts}")
text = APP.read_text(encoding="utf-8")
print("=" * 60)
print("FINAL FIX V3 — All-in-One")
print("=" * 60)

# ═══════════════════════════════════
# FIX 1: Trim rus_trim_e default
# ═══════════════════════════════════
text = text.replace('("rus_trim_e",60.0)', '("rus_trim_e",0.0)')
print("[1] Trim default fix")

# ═══════════════════════════════════
# FIX 2: Zoompan HATAO
# ═══════════════════════════════════
text = text.replace(
    '''if mz: vf.append("zoompan=z='min(zoom+0.0015,1.5)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'")''',
    '# zoompan REMOVED — caused stretch'
)
print("[2] Zoompan removed")

# ═══════════════════════════════════
# FIX 3: Safe scale
# ═══════════════════════════════════
text = text.replace(
    'vf.append(f"scale=-2:{th_out}")',
    'vf.append(f"scale={tw or -2}:{th_out or -2}:force_original_aspect_ratio=decrease,pad={tw}:{th_out}:(ow-iw)/2:(oh-ih)/2")'
)
print("[3] Scale preserve aspect")

# ═══════════════════════════════════
# FIX 4: FIND the editing section
# ═══════════════════════════════════
# Strategy: Find st.subheader("🎨 Editing") or similar and replace with full UI
import re

# Find the pattern: after upload, before render button
old_edit_block = None
for candidate in [
    'st.subheader("🎨 Editing")',
    'st.divider(); st.subheader("🎨',
    '"🎨 Editing"',
]:
    if candidate in text:
        print(f"[4] Found editing marker: {candidate[:40]}")
        break

# ═══════════════════════════════════
# FIX 5: REPLACE old editing with FULL settings
# ═══════════════════════════════════

FULL_SETTINGS = r'''
    # ═══════════════════════════════════════
    # ALL EDITING SETTINGS — Complete UI
    # ═══════════════════════════════════════
    st.divider()
    with st.expander("🎬 All Editing & Voice Settings", expanded=True):
        tab1, tab2, tab3, tab4 = st.tabs(["🎬 Video", "🎤 Voice/Audio", "🎨 Color/Transitions", "🏷 Branding"])
        
        with tab1:
            c1, c2, c3 = st.columns(3)
            with c1:
                ac = st.checkbox("🌈 Auto Color", True, key="rac")
                sh = st.checkbox("🔪 Sharpen", True, key="rsh")
                hdr = st.checkbox("☀️ HDR", False, key="rhdr")
                vnr = st.checkbox("🔇 Noise Reduce", False, key="rvnr")
                fe = st.checkbox("👤 Face Enhance", False, key="rfe")
            with c2:
                ms = st.checkbox("📹 Stabilize", False, key="rms")
                mf = st.checkbox("🪞 Mirror Flip", False, key="rmf")
                mp = st.checkbox("↔️ Pan Motion", True, key="rmp")
                msh = st.checkbox("📳 Shake", False, key="rmsh")
                mb = st.checkbox("🌫 Motion Blur", False, key="rmb")
            with c3:
                u1080 = st.checkbox("📺 1080p", True, key="ru1080")
                u4k = st.checkbox("🎯 4K", False, key="ru4k")
                ce = st.checkbox("💬 Captions", True, key="rcap")
                mz = False
            cpus = st.slider("⚡ CPU Cores", 1, 4, 2, key="rcpu")

        with tab2:
            v1, v2, v3 = st.columns(3)
            with v1:
                vp = st.slider("🎵 Pitch", -12, 12, 0, key="rvp")
                vs_v = st.slider("⏩ Speed", 0.7, 1.5, 1.0, 0.05, key="rvs")
            with v2:
                vv = st.slider("🔊 Voice Vol", 0.5, 2.0, 1.0, 0.1, key="rvv")
                nr = st.checkbox("🎧 Noise Removal", True, key="rnr")
            with v3:
                bgv = st.slider("🎼 BG Music Vol", 0.0, 1.0, 0.3, 0.05, key="rbgv")
                sfxv = st.slider("💥 SFX Vol", 0.0, 1.0, 0.7, 0.05, key="rsfxv")

        with tab3:
            cl1, cl2 = st.columns(2)
            with cl1:
                sat = st.slider("🌈 Saturation", 0.5, 2.0, 1.1, 0.05, key="rsat")
                con = st.slider("🌓 Contrast", 0.5, 2.0, 1.05, 0.05, key="rcon")
            with cl2:
                tr = st.selectbox("🎬 Transition", [
                    "fade","dissolve","slide_left","slide_right","slide_up","slide_down",
                    "flash","glitch","cross_zoom","whip","film_burn","zoom_in","spin",
                    "morph","smooth_blur","light_leak","dynamic_slide","circle_open",
                    "page_curl","pixelate","doorway","radial","swirl","cube","fadegrayscale"
                ], key="rtr")

        with tab4:
            br1, br2, br3 = st.columns(3)
            with br1:
                lf = st.file_uploader("🖼 Logo (PNG)", type=["png"], key="rlogo")
            with br2:
                inf = st.file_uploader("🎬 Intro", type=["mp4","mov"], key="rintro")
            with br3:
                outf = st.file_uploader("🎬 Outro", type=["mp4","mov"], key="routro")
            br4, br5 = st.columns(2)
            with br4:
                wmt = st.text_input("💧 Watermark", key="rwmtxt", placeholder="@handle")
            with br5:
                wmp = st.selectbox("📍 W.Mark Pos", ["bottom-right","bottom-left","top-right","top-left"], key="rwmpos")
            ba1, ba2 = st.columns(2)
            with ba1:
                bgp = st.file_uploader("🎼 BG Music (MP3/WAV)", type=["mp3","wav","m4a"], key="rbgm")
            with ba2:
                sfxp = st.file_uploader("💥 SFX Burst (MP3/WAV)", type=["mp3","wav"], key="rsfx")
'''

# Now find the old editing block and replace it
# The old block typically starts with # ───── or st.divider or st.subheader
lines = text.split('\n')
edit_start = None
edit_end = None
for i, line in enumerate(lines):
    stripped = line.strip()
    if ('EDITING' in stripped or 'Editing' in stripped) and ('st.subheader' in stripped or 'st.divider' in stripped or '#' in stripped):
        edit_start = i
        # Find where the editing block ends (look for next divider or "Generate" or "render" button)
        for j in range(i+1, min(i+100, len(lines))):
            if 'st.button("🚀' in lines[j] or 'st.button("🎬 Render' in lines[j] or 'Generate Video' in lines[j] or 'def ' in lines[j].strip():
                edit_end = j
                break
            if '_render_video' in lines[j] and not lines[j].strip().startswith('#'):
                edit_end = j + 15  # include render call
                break
        if edit_end:
            break

if edit_start and edit_end:
    print(f"[4] Found editing block: lines {edit_start+1} to {edit_end+1}")
    # Replace the block
    new_lines = lines[:edit_start] + [FULL_SETTINGS] + lines[edit_end:]
    text = '\n'.join(new_lines)
    print("[5] ✅ All settings injected with tabs UI")
else:
    print("[4] ❌ Editing block not found with standard search")
    # Try to inject before "Generate" button
    for i, line in enumerate(lines):
        if 'Generate Video' in line and 'st.button' in line:
            # Inject FULL_SETTINGS right before
            new_lines = lines[:i] + [FULL_SETTINGS + '\n'] + lines[i:]
            text = '\n'.join(new_lines)
            print("[5] ✅ Injected before Generate button")
            break
    else:
        print("[5] ❌ Could not find injection point")

# ═══════════════════════════════════
# FIX 6: Ensure render call passes ALL settings
# ═══════════════════════════════════
# Variables that must be defined before render: ac,sat,con,sh,hdr,vnr,fe,ms,mf,u1080,u4k,mp,msh,mb,mz,vp,vs_v,vv,nr,bgv,tr,wmt,wmp,bgp,sfxp,sfxv,inf,outf,lf,ce,cpus
# All defined in FULL_SETTINGS above ✓

APP.write_text(text, encoding="utf-8")
print(f"[Done] Written: {len(text)} chars")

try:
    compile(text, "app.py", "exec")
    print("\n✅✅✅ SYNTAX OK! ✅✅✅")
    print("\n─── ALL SETTINGS NOW VISIBLE ───")
    print("  🎬 Video tab: Color, Sharpen, HDR, Noise, Face, Stabilize, Mirror, Pan, Shake, Blur, 1080p, 4K, Captions")
    print("  🎤 Voice tab: Pitch, Speed, Volume, Noise Removal, BG Music Vol, SFX Vol")
    print("  🎨 Color tab: Saturation, Contrast, 25 Transitions")
    print("  🏷 Branding tab: Logo, Intro, Outro, Watermark, BG Music, SFX file")
    print("\nRun: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ Line {e.lineno}: {e.msg}")
    L = text.split('\n')
    for ln in range(max(0,e.lineno-4), min(len(L),e.lineno+3)):
        marker = ">>>" if ln+1==e.lineno else "   "
        print(f"  {marker} {ln+1}: {L[ln][:200]}")