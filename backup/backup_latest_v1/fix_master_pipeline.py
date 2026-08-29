"""
FIX 1/3: master_pipeline.py — Fix IndentationError on line 77-80
The 'except' block at line 76 has no body, causing IndentationError on line 80.
Surgical fix: Add 'pass' inside the except block.
"""
import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'master_pipeline.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# The problematic section — empty except block
old = """except Exception:
    # ============================================================
# PHASE 7: DNA-Driven Render Override
# ============================================================
def apply_content_dna_to_render"""

new = """except Exception:
    pass
# ============================================================
# PHASE 7: DNA-Driven Render Override
# ============================================================
def apply_content_dna_to_render"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ FIX 1 APPLIED: master_pipeline.py — except block fixed")
else:
    print("❌ FIX 1 SKIPPED: pattern not found. Checking alternative...")
    # Alternative: the except might already have pass or be different
    lines = content.split('\n')
    for i in range(73, 82):
        if i < len(lines):
            print(f"  L{i+1}: {lines[i]}")