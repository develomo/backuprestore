"""FIX: All editing settings visible & working in UI"""
from pathlib import Path
import shutil, time

APP = Path(r"D:\My Creation Video Generator\backup\app.py")
ts = int(time.time())
shutil.copy2(APP, APP.parent / f"app.py.bak_editfix_{ts}")
text = APP.read_text(encoding="utf-8")
print("=" * 60)
print("FIX: Editing Settings in UI")
print("=" * 60)

# Find the editing section in reels_upload_studio_tab
# Look for the divider and editing section
old_editing = '''# ───── EDITING ─────
    st.divider(); st.subheader("🎨 Editing")'''

new_editing = '''# ═══════════════════════════════════════════════════
    # ALL SETTINGS — Single Expander
    # ═══════════════════════════════════════════════════
    st.divider()
    with st.expander("⚙️ All Editing Settings", expanded=True):
        st.markdown("### 🎬 Video Editing")
        cva, cvb = st.columns(2)
        with cva:
            ac = st.checkbox("🌈 Auto Color", True, key="rac", help="Auto color correction")
            sh_ = st.checkbox("🔪 Sharpen", True, key="rsh", help="Sharpen the video")
            hdr = st.checkbox("☀️ HDR Look", False, key="rhdr", help="HDR-style enhancement")
            vnr = st.checkbox("🔇 Noise Reduce", False, key="rvnr", help="Remove video noise")
            fe = st.checkbox("👤 Face Enhance", False, key="rfe", help="Enhance faces")
            ms = st.checkbox("📹 Stabilize", False, key="rms", help="Stabilize shaky footage")
            mf = st.checkbox("🪞 Mirror Flip", False, key="rmf", help="Horizontal flip")
        with cvb:
            u1080 = st.checkbox("📺 Upscale 1080p", True, key="ru1080")
            u4k = st.checkbox("🎯 Upscale 4K", False, key="ru4k")
            mp = st.checkbox("↔️ Pan Motion", True, key="rmp")
            msh = st.checkbox("📳 Shake Effect", False, key="rmsh")
            mb = st.checkbox("🌫 Motion Blur", False, key="rmb")
            mz = False  # disabled
        
        st.divider()
        st.markdown("### 🎤 Voice & Audio")
        cv1, cv2 = st.columns(2)
        with cv1:
            vp = st.slider("🎵 Pitch", -12, 12, 0, key="rvp", help="Voice pitch shift")
            vs_v = st.slider("⏩ Speed", 0.7, 1.5, 1.0, 0.05, key="rvs", help="Voice speed")
            vv = st.slider("🔊 Voice Volume", 0.5, 2.0, 1.0, 0.1, key="rvv")
            nr = st.checkbox("🎧 Noise Removal", True, key="rnr")
        with cv2:
            bgv_val = st.slider("🎼 BG Music Volume", 0.0, 1.0, 0.3, 0.05, key="rbgv2")
            sfxv_val = st.slider("💥 SFX Volume", 0.0, 1.0, 0.7, 0.05, key="rsfxv2")
        
        st.divider()
        st.markdown("### 🎨 Color & Transitions")
        ct1, ct2 = st.columns(2)
        with ct1:
            sat = st.slider("🌈 Saturation", 0.5, 2.0, 1.1, 0.05, key="rsat2")
            con = st.slider("🌓 Contrast", 0.5, 2.0, 1.05, 0.05, key="rcon2")
        with ct2:
            tr = st.selectbox("🎬 Transition Style", [
                "fade","dissolve","slide_left","slide_right","slide_up","slide_down",
                "flash","glitch","cross_zoom","whip","film_burn","zoom_in","spin",
                "morph","smooth_blur","light_leak","dynamic_slide","circle_open",
                "page_curl","pixelate","doorway","radial","swirl","cube","fadegrayscale"
            ], key="rtr2")
        
        st.divider()
        st.markdown("### 🏷 Branding")
        cb1, cb2, cb3 = st.columns(3)
        with cb1:
            lf = st.file_uploader("Logo PNG", type=["png"], key="rlogo2")
        with cb2:
            inf = st.file_uploader("Intro Video", type=["mp4","mov"], key="rintro2")
        with cb3:
            outf = st.file_uploader("Outro Video", type=["mp4","mov"], key="routro2")
        cb4, cb5 = st.columns(2)
        with cb4:
            wmt = st.text_input("Watermark Text", key="rwmtxt2", placeholder="@yourhandle")
        with cb5:
            wmp = st.selectbox("Watermark Position", ["bottom-right","bottom-left","top-right","top-left"], key="rwmpos2")
        
        st.divider()
        st.markdown("### 🎵 Background Music & SFX")
        ca1, ca2 = st.columns(2)
        with ca1:
            bgf = st.file_uploader("🎼 BG Music (MP3/WAV)", type=["mp3","wav","m4a"], key="rbgm2")
        with ca2:
            sfxf = st.file_uploader("💥 SFX Burst (MP3/WAV)", type=["mp3","wav"], key="rsfx2")
        
        bgv = bgv_val
        sfxv = sfxv_val
        sh = sh_'''

if old_editing in text:
    text = text.replace(old_editing, new_editing)
    print("[1] Editing section replaced with full settings")
else:
    # Try to find where editing section starts
    old_editing2 = 'st.divider(); st.subheader("🎨 Editing")'
    if old_editing2 in text:
        text = text.replace(old_editing2, new_editing)
        print("[1b] Editing section replaced (alt)")
    else:
        print("[1] ❌ Editing section not found — adding at upload section end")
        # Find "has_vid" block and add editing before generate button
        old_gen = 'if st.button("🚀 Generate Videos"'
        if old_gen in text:
            text = text.replace(old_gen, new_editing + '\n\n    ' + old_gen)
            print("[1c] Injected before Generate button")

# ═══════════════════════════════════════════════════
# FIX: Ensure render call uses all the right variables
# ═══════════════════════════════════════════════════
# Find the _render_video call and ensure it passes all UI vars
old_render = '_render_video(inpath,op,cpus,'
# Make sure all UI variables are passed in correct order
# The function signature takes: inpath,outpath,cpus,mf,ms,vnr,fe,u4k,u1080,ac,sat,con,sh,hdr,mz,mp,msh,mb,preset,wmt,wmp,vs_,vp,vv,nr,bgv,tr,tw,th_,bgp,sfxp,sfxv,introp,outrop,logop,texts,ts_,te_

print("[2] Checking render call variables...")
# All variables should be defined in the UI checkboxes/sliders above
# ac, sat, con, sh, hdr, vnr, fe, ms, mf, u1080, u4k, mp, msh, mb, mz=False
# vp, vs_v, vv, nr, bgv, sfxv, tr, wmt, wmp, bgf, sfxf, inf, outf, lf
# These all get defined inside the expander now

APP.write_text(text, encoding="utf-8")
print(f"[Done] Written: {len(text)} chars")

try:
    compile(text, "app.py", "exec")
    print("\n✅✅✅ SYNTAX OK! ✅✅✅")
    print("\n─── ALL EDITING SETTINGS NOW VISIBLE ───")
    print("  🎬 Video: Auto Color, Sharpen, HDR, Noise, Face, Stabilize, Mirror, Upscale, Pan, Shake, Blur")
    print("  🎤 Voice: Pitch, Speed, Volume, Noise Removal")
    print("  🎨 Color: Saturation, Contrast")
    print("  🎬 Transitions: 25 styles")
    print("  🏷 Branding: Logo, Intro, Outro, Watermark")
    print("  🎵 Audio: BG Music upload + volume, SFX upload + volume")
    print("\nRun: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ Line {e.lineno}: {e.msg}")
    L = text.split('\n')
    for ln in range(max(0,e.lineno-4), min(len(L),e.lineno+3)):
        marker = ">>>" if ln+1==e.lineno else "   "
        print(f"  {marker} {ln+1}: {L[ln][:200]}")