import codecs 
with codecs.open('app.py', 'r', 'utf-8', 'replace') as f: 
    lines = f.readlines() 
new_lines = [] 
for i, line in enumerate(lines): 
    new_lines.append(line) 
        next_stripped = lines[i+1].strip() 
        if next_stripped and not next_stripped.startswith(')') and '=' not in next_stripped: 
            new_lines[-1] = line.rstrip() + ',' + line[len(line.rstrip()):] 
with codecs.open('app.py', 'w', 'utf-8') as f: 
    f.writelines(new_lines) 
print('Fixed positional/keyword argument order') 
