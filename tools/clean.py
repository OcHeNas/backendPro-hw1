from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
for path in root.rglob("__pycache__"):
    shutil.rmtree(path)
for path in (root / "internal/futex/_native.so", root / "build"):
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()
