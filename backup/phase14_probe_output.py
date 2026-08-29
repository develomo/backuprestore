import sys
import json
from pathlib import Path
from engine.validation import Phase14Validator

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python phase14_probe_output.py outputs\\your_video.mp4")
        raise SystemExit(1)

    result = Phase14Validator(".").ffprobe_video(sys.argv[1])
    out = Path("outputs/phase14_output_probe.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("PHASE 14 OUTPUT PROBE")
    print("ok:", result.get("ok"))
    print("width:", result.get("width"))
    print("height:", result.get("height"))
    print("dar:", result.get("display_aspect_ratio"))
    print("report:", out)
