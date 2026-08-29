"""FIX v_stream + Remove Duration/Resolution/etc metrics — clean fix"""
from pathlib import Path

P = Path(r"D:\My Creation Video Generator\backup\app.py")
T = P.read_text(encoding="utf-8")

# 1. Fix v_stream init (pichla fix properly apply hua check karo, agar nahi toh force karo)
OLD = """        # ───── VIDEO INFO ─────
        try:
            probe = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", vs],
                                    capture_output=True, text=True, timeout=15)
            info = _json_builtin.loads(probe.stdout) if probe.returncode == 0 else {}
            dur = float(info.get("format", {}).get("duration", 0))
            v_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
            vw = v_stream.get("width", 0)
            vh = v_stream.get("height", 0)
        except:
            dur, vw, vh = 0, 0, 0"""

NEW = """        # ───── VIDEO INFO ─────
        dur = 0.0
        vw = 0
        vh = 0
        v_stream = {}
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", vs],
                capture_output=True, text=True, timeout=15
            )
            if probe.returncode == 0 and probe.stdout.strip():
                info = _json_builtin.loads(probe.stdout)
                dur = float(info.get("format", {}).get("duration", 0))
                v_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
                vw = v_stream.get("width", 0)
                vh = v_stream.get("height", 0)
        except Exception:
            pass"""

T = T.replace(OLD, NEW, 1)

# 2. Remove the 4-metric info row (Duration/Resolution/FPS/Size) — replace with simple file info only
OLD2 = """    # ═══════════════════════════════════════
    # INFO ROW (4 metric boxes)
    # ═══════════════════════════════════════
    i1, i2, i3, i4 = st.columns(4)
    with i1:
        st.metric("⏱ Duration", f"{dur:.1f}s")
    with i2:
        st.metric("📐 Resolution", f"{vw}x{vh}" if vw and vh else "?")
    with i3:
        st.metric("🎞 FPS", f"{eval(v_stream.get('r_frame_rate', '0/1')):.0f}" if v_stream.get('r_frame_rate') else "?")
    with i4:
        st.metric("📦 Size", f"{len(uploaded.getvalue())/1024/1024:.1f} MB")
    st.divider()"""

NEW2 = """    # ═══════════════════════════════════════
    # INFO — simple file details
    # ═══════════════════════════════════════
    fsize_mb = len(uploaded.getvalue()) / 1024 / 1024
    st.caption(f"📦 File: {uploaded.name}  •  {fsize_mb:.1f} MB")
    st.divider()"""

T = T.replace(OLD2, NEW2, 1)

P.write_text(T, encoding="utf-8")
compile(T, str(P), "exec")
print("✅ FIXED — v_stream safe init + Duration/Resolution/FPS/Size metrics removed")