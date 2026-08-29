import re
c = open('batch_long_renderer.py', 'r', encoding='utf-8').read()
c = c.replace('~150s', 'about 150 seconds')
c = c.replace('360p/480p/720p', '360p, 480p, or 720p')
c = re.sub(r'~(\d+)s', r'about \1 seconds', c)
open('batch_long_renderer.py', 'w', encoding='utf-8').write(c)
print('DONE')
