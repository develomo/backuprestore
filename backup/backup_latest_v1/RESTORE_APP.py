"""RESTORE_FRESH.py — backup se restore karo"""
from pathlib import Path
import shutil

P = Path(r"D:\My Creation Video Generator\backup\app.py")
backups = sorted(Path(r"D:\My Creation Video Generator\backup").glob("app.py.bak*"), reverse=True)

if backups:
    bak = backups[0]
    shutil.copy(bak, P)
    print(f"✅ Restored from: {bak.name}")
else:
    print("❌ No backup found! Manually restore karo.")