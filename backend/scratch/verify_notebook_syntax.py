import json
from pathlib import Path

nb_path = Path("backend/notebooks/SchemaSense_AI_GenAI_AAT1.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")
errors = []
for idx, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"])
        # Filter out IPython magic lines like !pip or %matplotlib before compiling
        py_lines = []
        for line in source.splitlines():
            if line.strip().startswith("!") or line.strip().startswith("%"):
                py_lines.append("# " + line)
            else:
                py_lines.append(line)
        py_source = "\n".join(py_lines)
        try:
            compile(py_source, f"cell_{idx}", "exec")
        except SyntaxError as e:
            errors.append((idx, str(e), source[:200]))

if errors:
    print(f"Found {len(errors)} syntax errors:")
    for idx, err, src in errors:
        print(f"Cell {idx}: {err}\nSnippet:\n{src}\n---")
else:
    print("ALL CODE CELLS COMPILED CLEANLY WITH VALID PYTHON SYNTAX!")
