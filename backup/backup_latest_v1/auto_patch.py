from pathlib import Path
import shutil
import re

FILE_NAME = "batch_long_renderer.py"

file = Path(FILE_NAME)

if not file.exists():
    print(f"\nERROR: {FILE_NAME} not found.")
    print("Copy auto_patch.py inside the same folder where batch_long_renderer.py exists.")
    input("\nPress Enter...")
    exit()

backup = file.with_suffix(".py.bak")

if not backup.exists():
    shutil.copy2(file, backup)
    print("Backup Created:")
    print(backup.name)

text = file.read_text(encoding="utf-8", errors="ignore")

old_position = 'pos = "main_w-overlay_w-24:main_h-overlay_h-96"'

new_position = '''# AUTO PATCH
    # Bottom Center (Below Captions)
    # Watermark remains bottom-right.
    # Overlay appears bottom-center with safe spacing.
    pos = "(main_w-overlay_w)/2:main_h-overlay_h-20"
'''

if old_position not in text:

    pattern = r'pos\s*=\s*"main_w-overlay_w-24:main_h-overlay_h-96"'

    if re.search(pattern, text):

        text = re.sub(pattern, new_position, text)

    else:
        print("\nPatch location not found.")
        print("Your renderer may already be modified.")
        input("\nPress Enter...")
        exit()

else:

    text = text.replace(old_position, new_position)

file.write_text(text, encoding="utf-8")

print()
print("="*50)
print("PATCH SUCCESSFUL")
print("="*50)
print()
print("Subscribe Overlay Position Changed")
print("Old : Bottom Right")
print("New : Bottom Center")
print()
print("Watermark : Bottom Right")
print("Captions  : Above Subscribe")
print("Subscribe : Bottom Center")
print()
print("Backup File:")
print(backup.name)
print()
input("Press Enter to Exit...")