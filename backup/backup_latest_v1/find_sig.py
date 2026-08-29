"""
Find full signature of render_long_batch_memory in batch_long_renderer.py
Run on user's PC: python find_sig.py
"""
with open('batch_long_renderer.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('def render_long_batch_memory')
if idx >= 0:
    # Find the full signature (until the first line of function body)
    # Look for the pattern: def func(...):\n    (first indented line)
    rest = content[idx:]
    # Print first 2000 chars to see full signature + params
    print(rest[:2000])
    print("\n---END---")
else:
    print("NOT FOUND")