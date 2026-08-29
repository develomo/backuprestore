from pathlib import Path

for file in ["master_pipeline.py", "format_by_duration.py", "smart_clip_engine.py"]:
    p = Path(file)
    print("\n---", file, "exists:", p.exists(), "---")
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8", errors="ignore")
    for term in ["chunk_size=8", "chunk_size = 8", "8.0", "subclip", "prepare_clip_sequence_for_duration", "target_duration"]:
        print(term, "=>", text.find(term))