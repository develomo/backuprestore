from pathlib import Path
p = Path("safe_long_video_polished.py")
c = p.read_text(encoding="utf-8")
Path("safe_long_video_polished.py.bak_p7").write_text(c, encoding="utf-8")

add = """
# PHASE 7: DNA Engine for Long Pipeline
DNA_ENGINE_LONG = False
try:
    from video_content_analyzer import ContentDNAAnalyzer, DNAtoCreativeMapping, ProjectDNAAggregator
    DNA_ENGINE_LONG = True
except Exception:
    pass
"""

mk = "PRESET_AVAILABLE_LONG = False"
if mk in c:
    c = c.replace(mk, mk + add)
    p.write_text(c, encoding="utf-8")
    print("PATCH OK: Engine 3 injected into safe_long_video_polished.py")
else:
    print("ERROR: marker not found")