from pathlib import Path

P = Path(r"D:\My Creation Video Generator\backup\app.py")
T = P.read_text(encoding="utf-8")

# Fix 1: v_stream always initialized before try block
old1 = '''        try:
            probe = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", vs],
                                    capture_output=True, text=True, timeout=15)
            info = _json_builtin.loads(probe.stdout) if probe.returncode == 0 else {}
            dur = float(info.get("format", {}).get("duration", 0))
            v_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
            vw = v_stream.get("width", 0)
            vh = v_stream.get("height", 0)
        except:
            dur, vw, vh = 0, 0, 0'''

new1 = '''        dur = 0.0
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
            pass'''

T = T.replace(old1, new1, 1)

# Fix 2: Remove Duration/Resolution/FPS/Size metrics, keep simple file info
old2 = '''    i1, i2, i3, i4 = st.columns(4)
    with i1:
        st.metric("\u23f1 Duration", f"{dur:.1f}s")
    with i2:
        st.metric("\U0001f4d0 Resolution", f"{vw}x{vh}" if vw and vh else "?")
    with i3:
        st.metric("\U0001f39e FPS", f"{eval(v_stream.get('r_frame_rate', '0/1')):.0f}" if v_stream.get('r_frame_rate') else "?")
    with i4:
        st.metric("\U0001f4e6 Size", f"{len(uploaded.getvalue())/1024/1024:.1f} MB")
    st.divider()'''

new2 = '''    fsize_mb = len(uploaded.getvalue()) / 1024 / 1024
    st.caption(f"\U0001f4e6 File: {uploaded.name}  \u2022  {fsize_mb:.1f} MB")
    st.divider()'''

T = T.replace(old2, new2, 1)

P.write_text(T, encoding="utf-8")
compile(T, str(P), "exec")
print("DONE - v_stream safe + metrics removed")