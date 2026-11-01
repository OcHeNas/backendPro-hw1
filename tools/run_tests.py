import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
parser = argparse.ArgumentParser()
parser.add_argument("--only", default="")
parser.add_argument("--repeat", type=int, default=1)
parser.add_argument("--race", action="store_true")
parser.add_argument("--child", action="store_true")
args = parser.parse_args()
name = args.only.split("_", 1)[-1] if args.only else ""
if args.child:
    import faulthandler
    import unittest

    faulthandler.enable()
    faulthandler.dump_traceback_later(45, exit=True)
    if args.race:
        sys.setswitchinterval(0.00001)
    suite = unittest.defaultTestLoader.discover(
        "tests", pattern=f"test_{name}.py" if name else "test_*.py", top_level_dir="."
    )
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    faulthandler.cancel_dump_traceback_later()
    sys.exit(0 if result.wasSuccessful() and result.testsRun else 1)
if args.repeat < 1:
    parser.error("repeat must be positive")
if args.race:
    print("Concurrency checks with frequent thread switches; NOT a race detector.", flush=True)
for index in range(args.repeat):
    command = [sys.executable, "-X", "dev", __file__, "--child", "--only", args.only]
    if args.race:
        command.append("--race")
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    if result.returncode:
        print(result.stdout + result.stderr)
        sys.exit(result.returncode)
    if args.repeat == 1 or index == args.repeat - 1:
        print(result.stderr.strip())
    if (index + 1) % 10 == 0:
        print(f"{index + 1}/{args.repeat} repeats passed", flush=True)
