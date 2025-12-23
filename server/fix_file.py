with open('app/core/raganything_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with rag_engine = DocumentEngine()
idx = next(i for i, line in enumerate(lines) if 'rag_engine = DocumentEngine()' in line)

# Keep everything up to and including that line
with open('app/core/raganything_engine.py', 'w', encoding='utf-8') as f:
    f.writelines(lines[:idx+1])

print(f"Fixed! Kept {idx+1} lines, removed {len(lines) - idx - 1} lines")
