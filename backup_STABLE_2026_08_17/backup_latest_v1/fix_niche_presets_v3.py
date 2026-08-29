"""
FIX 3/3 v3: niche_editing_presets.py - Add missing get_preset_by_number()
Reads the file, finds the real get_preset lines, inserts new functions after.
"""
import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'niche_editing_presets.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# The real get_preset function in the file (L759-L763)
# We match just the start and end markers
old_marker = "def get_preset(niche: str, preset_number: int) -> EditingPreset:"

new_insertion = """def get_preset(niche: str, preset_number: int) -> EditingPreset:
    presets = get_presets_for_niche(niche)
    for p in presets:
        if p.preset_number == preset_number:
            return p
    return presets[0]  # fallback

def get_preset_by_number(preset_number: int, niche: str = "default"):
    # Return preset by number (1-8). Falls back to default niche.
    try:
        if niche == "auto":
            niche = "default"
        return get_preset(niche, preset_number)
    except Exception:
        presets = get_presets_for_niche("default")
        for p in presets:
            if p.preset_number == preset_number:
                return p
        return presets[0] if presets else None

def get_preset_labels(niche: str = "default"):
    # Return list of labels for given niche's 8 presets.
    presets = get_presets_for_niche(niche)
    return [p.label for p in presets[:8]]

def list_all_niches_with_presets():
    # Return {niche_name: [(1, label), (2, label), ...]}
    result = {}
    for niche_name, presets in _ALL_PRESETS.items():
        result[niche_name] = [(p.preset_number, p.label) for p in presets[:8]]
    return result"""

if old_marker in content:
    # Find the old get_preset and replace it + its body with new code
    # Strategy: find the next "def " after get_preset to know where it ends
    idx = content.index(old_marker)
    after = content[idx:]
    lines_after = after.split('\n')
    # Find where get_preset body ends (next blank line followed by def or ##)
    end_offset = len(old_marker)
    for i, line in enumerate(lines_after[1:], 1):
        stripped = line.strip()
        if stripped.startswith('def ') or stripped.startswith('# ='):
            end_offset += sum(len(l) + 1 for l in lines_after[1:i])
            break
    else:
        end_offset = len(after)
    
    old_block = content[idx:idx + end_offset]
    content = content.replace(old_block, new_insertion)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK FIX 3 v3 APPLIED: get_preset_by_number + get_preset_labels + list_all_niches_with_presets added")
else:
    print("SKIPPED: cannot find get_preset function. Showing context around L759:")
    lines = content.split('\n')
    for i in range(755, 768):
        if i < len(lines):
            print(f"  L{i+1}: {lines[i]}")