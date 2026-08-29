"""FIX — v_stream UnboundLocalError + proper fallback for all video info fields"""
from pathlib import Path

P = Path(r"D:\My Creation Video Generator\backup\app.py")
T = P.read_text(encoding="utf-8")

# ── FIX: replace the entire VIDEO INFO block ──
OLD = '''        # ───── VIDEO INFO ─────
        try:
            probe = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", vs],
                                    capture_output=True, text=True, timeout=15)
            info = _json.loads(probe.stdout) if probe.returncode == 0 else {}
            dur = float(info.get("format", {}).get("duration", 0))
            v_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
            vw = v_stream.get("width", 0)
            vh = v_stream.get("height", 0)
        except:
            dur, vw, vh = 0, 0, 0'''

NEW = '''        # ───── VIDEO INFO ─────
        info = {}
        v_stream = {}
        dur = 0.0
        vw = 0
        vh = 0
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", vs],
                capture_output=True, text=True, timeout=15
            )
            if probe.returncode == 0:
                info = _json_builtin.loads(probe.stdout)
                dur = float(info.get("format", {}).get("duration", 0))
                v_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
                vw = v_stream.get("width", 0)
                vh = v_stream.get("height", 0)
        except Exception:
            pass'''

T = T.replace(OLD, NEW, 1)

P.write_text(T, encoding="utf-8")
compile(T, str(P), "exec")
print("✅ FIX APPLIED — v_stream always defined, all video info fields have safe fallbacks")