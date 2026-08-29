"""SFX Engine - RAM Safe"""
import subprocess, tempfile, random, time
from pathlib import Path
BASE = Path(r"D:\My Creation Video Generator\backup")


def apply_sfx_burst_on_clip_change(video, mode="SHORT", niche="default",
                                   sfx_files=None, max_sfx=5):
    """RAM-safe SFX at uniform clip boundaries."""
    try:
        if video is None:
            return video

        td = Path(tempfile.gettempdir())

        # Get duration
        r = subprocess.run(
            ["ffprobe","-v","error","-show_entries",
             "format=duration","-of","csv=p=0", str(video)],
            capture_output=True, text=True
        )
        try:
            dur = float(r.stdout.strip() or 0)
        except:
            return video

        if dur <= 0:
            return video

        # Uniform boundaries
        clip_count = 8
        clip_dur = dur / clip_count
        times = [clip_dur * i for i in range(1, clip_count)]
        times = [t for t in times if 1.0 < t < dur - 1.0][:max_sfx]

        if not times:
            return video

        print(f"[SFX] {len(times)} boundaries")

        # Find SFX file
        sfx_dirs = [
            BASE / "assets" / "shorts" / "sfx",
            BASE / "assets" / "longs" / "sfx",
        ]
        sfx_path = None
        for d in sfx_dirs:
            if d.exists():
                files = list(d.glob("*.mp3")) + list(d.glob("*.wav"))
                if files:
                    sfx_path = files[0]
                    break

        if sfx_path is None:
            print("[SFX] No files, skip")
            return video

        # Build filter
        parts = []
        for i, ct in enumerate(times):
            ms = int(ct * 1000)
            parts.append(f"[1:a]adelay={ms}|{ms}[sfx{i}]")

        all_labels = "".join([f"[sfx{i}]" for i in range(len(times))])
        parts.append(
            f"[0:a]{all_labels}amix=inputs={len(times)+1}"
            f":duration=first[outa]"
        )

        out = td / f"sfx_{int(time.time())}.mp4"

        subprocess.run([
            "ffmpeg","-threads","1","-y",
            "-i", str(video),
            "-i", str(sfx_path),
            "-filter_complex", ";".join(parts),
            "-map","0:v","-map","[outa]",
            "-c:v","copy","-c:a","aac","-b:a","128k",
            str(out)
        ], capture_output=True, text=True)

        if out.exists() and out.stat().st_size > 1000:
            print(f"[SFX] {len(times)} bursts done")
            return str(out)

        return video
    except Exception as e:
        print(f"[SFX] skip: {e}")
        return video
