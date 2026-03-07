from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Start the Reflex development server."""
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["reflex", "run"],
        cwd=str(root),
    )
    sys.exit(result.returncode)
