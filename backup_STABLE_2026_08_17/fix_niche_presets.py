"""
FIX 3/3: niche_editing_presets.py - Add missing get_preset_by_number() function
The function 'get_preset_by_number' does not exist. Only 'get_preset(niche, preset_number)' exists at L759.
Surgical fix: Add get_preset_by_number() right after get_preset().
"""
import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'niche_editing_presets.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the get_preset function and add get_preset_by_number after it
old = """def get_preset(niche: str, preset_number: int) -> EditingPreset:
    presets = get_presets_for_niche(niche)
    for p in presets:
        if p.preset_number == preset_number:
            return p
    return presets[0]  # fallback"""

new = """def get_preset(niche: str, preset_number: int) -> EditingPreset:
    presets = get_presets_for_niche(niche)
    for p in presets:
        if p.preset_number == preset_number:
            return p
    return presets[0]  # fallback

def get_preset_by_number(preset_number: int, niche: str = "default") -> EditingPreset:
    # Return preset by number (1-8) for given niche. Auto-detects niche if auto.
    if niche == "auto":
        niche = "default"
    return get_preset(niche, preset_number)

def get_preset_labels(niche: str = "default") -> list:
    # Return list of (number, label) tuples for given niche.
    presets = get_presets_for_niche(niche)
    return [(p.preset_number, p.label) for p in presets]

def list_all_niches_with_presets() -> dict:
    # Return dict of niche -> list of preset labels.
    return {niche: [(p.preset_number, p.label) for p in get_presets_for_niche(niche)]
            for niche in _ALL_PRESETS.keys()}"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK FIX 3 APPLIED: niche_editing_presets.py - get_preset_by_number added")
    print("   Also added: get_preset_labels() + list_all_niches_with_presets()")
else:
    print("SKIPPED: get_preset function not found exactly. Searching...")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'def get_preset' in line and 'by_number' not in line and 'by_id' not in line and 'summary' not in line and 'labels' not in line:
            print(f"  L{i+1}: {line.strip()}")
