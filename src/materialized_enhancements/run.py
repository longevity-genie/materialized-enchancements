from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Start the Reflex development server.

    Accepts ``--dev`` which exposes developer-only UI (ARTEX API config, etc.).
    All other arguments pass through to ``reflex run``.
    """
    args = sys.argv[1:]
    env = os.environ.copy()
    if "--dev" in args:
        env["MATERIALIZED_DEV_MODE"] = "1"
        args = [a for a in args if a != "--dev"]

    root = Path(__file__).resolve().parents[2]
    proc = subprocess.Popen(["reflex", "run", *args], cwd=str(root), env=env)
    signal.signal(signal.SIGINT, lambda *_: (proc.terminate(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda *_: (proc.terminate(), sys.exit(0)))
    sys.exit(proc.wait())
