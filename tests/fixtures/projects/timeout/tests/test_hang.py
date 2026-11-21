import subprocess
import sys
import time
from pathlib import Path

PID_FILE = Path(__file__).with_name("child.pid")


def test_hangs_until_terminated() -> None:
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    PID_FILE.write_text(str(child.pid), encoding="utf-8")
    time.sleep(60)
