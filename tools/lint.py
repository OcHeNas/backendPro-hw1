import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for path in root.rglob("*.py"):
    if "reference" in path.parts:
        continue
    source = path.read_text()
    compile(source, str(path), "exec")
    assert source.endswith("\n") or not source, path
    for number, line in enumerate(source.splitlines(), 1):
        assert line == line.rstrip() and "\t" not in line, (path, number)
    if path.parent.name[:2].isdigit():
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                assert all(n.name in ("importlib",) for n in node.names), path
            elif isinstance(node, ast.ImportFrom):
                assert node.module in ("internal.futex", "importlib"), path
print("Python syntax, whitespace and primitive import restrictions: OK")
