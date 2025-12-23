with open('app/core/raganything_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

class_started = False
for i, line in enumerate(lines, 1):
    stripped = line.lstrip()
    if stripped.startswith('class DocumentEngine'):
        class_started = True
        print(f'{i}: CLASS START')
    elif class_started and stripped and not line.startswith(' ') and not line.startswith('\t'):
        print(f'{i}: CLASS END - {repr(line[:60])}')
        break
