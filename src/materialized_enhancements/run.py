from __future__ import annotations

import signal
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Start the Reflex development server."""
    root = Path(__file__).resolve().parents[2]
    proc = subprocess.Popen(["reflex", "run"], cwd=str(root))
    signal.signal(signal.SIGINT, lambda *_: (proc.terminate(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda *_: (proc.terminate(), sys.exit(0)))
    sys.exit(proc.wait())
