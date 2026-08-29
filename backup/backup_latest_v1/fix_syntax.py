fn = 'batch_long_renderer.py'
c = open(fn, encoding='utf-8', errors='ignore').read()

# Galat ** ko sahi __ mein badalna
c = c.replace('from **future** import annotations', 'from __future__ import annotations')
c = c.replace('**init__', '__init__')
c = c.replace('**main__', '__main__')
c = c.replace('**name__', '__name__')

open(fn, 'w', encoding='utf-8').write(c)
print("SUCCESS: Syntax Error Fixed! (** replaced with __)")