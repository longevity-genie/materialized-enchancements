from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _setup() -> None:
    """Load .env and ensure cwd is the project root (where rxconfig.py lives)."""
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")
    os.chdir(root)


def main() -> None:
    """Start the Reflex development server.

    Accepts ``--dev`` which exposes developer-only UI (ARTEX API config, etc.).
    All other arguments pass through to ``reflex run``.
    """
    args = sys.argv[1:]
    if "--dev" in args:
        os.environ["MATERIALIZED_DEV_MODE"] = "1"
        args = [a for a in args if a != "--dev"]

    _setup()

    from reflex import constants
    from reflex.reflex import _run
    from reflex_base.config import environment

    environment.REFLEX_COMPILE_CONTEXT.set(constants.CompileContext.RUN)
    _run(env=constants.Env.DEV)


def serve() -> None:
    """Start the single-port production server (Reflex 0.9+ unified mode)."""
    _setup()

    from reflex import constants
    from reflex.constants.base import RunningMode
    from reflex.reflex import _run
    from reflex_base.config import environment

    environment.REFLEX_COMPILE_CONTEXT.set(constants.CompileContext.RUN)
    _run(env=constants.Env.PROD, running_mode=RunningMode.FULLSTACK)
