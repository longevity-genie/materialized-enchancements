from __future__ import annotations

import argparse
import base64
import json
import multiprocessing
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv


def _terminal_hyperlink(url: str) -> str:
    """Return an OSC 8 hyperlink for terminals that support clickable links."""
    if not sys.stdout.isatty():
        return url
    return f"\033]8;;{url}\033\\{url}\033]8;;\033\\"


def _force_spawn_worker_processes() -> None:
    """Make ASGI worker processes ``spawn``, never ``fork``.

    Reflex imports/compiles the app in this process, and that import runs
    Polars, which builds its Rayon thread pool. Granian then creates its ASGI
    worker with ``multiprocessing.get_start_method()``. Under ``fork`` the
    child inherits that pool's state without its threads, so the first
    parallel Polars operation in a request (``unique()`` for filter value
    options, ``sort()``) blocks forever inside ``collect()`` — no traceback,
    port still listening. ``spawn`` gives the worker a fresh interpreter that
    builds its own pool.
    """
    if multiprocessing.get_start_method(allow_none=True) != "spawn":
        multiprocessing.set_start_method("spawn", force=True)


def _setup() -> None:
    """Load .env and ensure cwd is the project root (where rxconfig.py lives)."""
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")
    os.chdir(root)
    _force_spawn_worker_processes()


def _spawn_serve_liveness_watchdog(*, port: int, serve_pid: int, serve_pgid: int) -> subprocess.Popen[str]:
    """Watch ``/_health`` from a sibling process and hard-kill a wedged serve.

    Reflex fullstack + Granian can accept TCP while the ASGI worker is
    deadlocked (e.g. Polars parallel sort on the request thread). The parent
    still prints ``App running`` and looks alive. This watchdog treats a hung
    health probe as fatal and SIGKILLs the serve process group so the failure
    cannot stay silent in the terminal.
    """
    script = r"""
import os
import signal
import sys
import time
import urllib.error
import urllib.request

port = int(sys.argv[1])
serve_pid = int(sys.argv[2])
serve_pgid = int(sys.argv[3])
url = f"http://127.0.0.1:{port}/_health"
timeout = float(os.environ.get("SERVE_HEALTH_TIMEOUT", "5"))
interval = float(os.environ.get("SERVE_HEALTH_INTERVAL", "5"))
fail_limit = int(os.environ.get("SERVE_HEALTH_FAIL_LIMIT", "2"))
startup_grace = float(os.environ.get("SERVE_HEALTH_STARTUP_GRACE", "600"))


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _probe() -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= int(resp.status) < 500
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _kill_serve(reason: str) -> None:
    print("", flush=True)
    print("=" * 72, flush=True)
    print("FATAL: uv run serve became unresponsive.", flush=True)
    print(f"  health URL : {url}", flush=True)
    print(f"  reason     : {reason}", flush=True)
    print("  The process was still running but stopped answering HTTP.", flush=True)
    print("  Killing the serve process group so this cannot look healthy.", flush=True)
    print("=" * 72, flush=True)
    try:
        os.killpg(serve_pgid, signal.SIGKILL)
    except ProcessLookupError:
        try:
            os.kill(serve_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


print(
    f"[serve-watchdog] monitoring {url} "
    f"(timeout={timeout}s, interval={interval}s, fail_limit={fail_limit}, "
    f"startup_grace={startup_grace}s)",
    flush=True,
)

# Wait until the server becomes healthy once (compile/export can take a while).
startup_deadline = time.time() + startup_grace
while _pid_alive(serve_pid):
    if _probe():
        print(f"[serve-watchdog] health OK — {url}", flush=True)
        break
    if time.time() >= startup_deadline:
        _kill_serve(
            f"never became healthy within startup grace ({startup_grace}s)"
        )
        raise SystemExit(1)
    time.sleep(1.0)
else:
    raise SystemExit(0)

failures = 0
while _pid_alive(serve_pid):
    time.sleep(interval)
    if not _pid_alive(serve_pid):
        break
    if _probe():
        if failures:
            print("[serve-watchdog] health recovered", flush=True)
        failures = 0
        continue
    failures += 1
    print(
        f"[serve-watchdog] health FAILED ({failures}/{fail_limit}) — {url}",
        flush=True,
    )
    if failures >= fail_limit:
        _kill_serve(f"health timed out {fail_limit} times (timeout={timeout}s)")
        raise SystemExit(1)

raise SystemExit(0)
"""
    return subprocess.Popen(
        [
            sys.executable,
            "-c",
            script,
            str(port),
            str(serve_pid),
            str(serve_pgid),
        ],
        start_new_session=True,
        cwd=str(Path.cwd()),
    )


def main() -> None:
    """Start the Reflex development server.

    Accepts ``--dev`` which exposes developer-only UI (ARTEX API config, etc.).
    All other arguments pass through to ``reflex run``.
    """
    args = sys.argv[1:]
    if "--dev" in args:
        os.environ["MATERIALIZED_DEV_MODE"] = "1"
        args = [a for a in args if a != "--dev"]

    if "--clean" in args:
        os.environ["CLEAN_BROWSER_STORAGE"] = "1"
        args = [a for a in args if a != "--clean"]
    if "--clean-storage" in args:
        os.environ["CLEAN_BROWSER_STORAGE"] = "1"
        args = [a for a in args if a != "--clean-storage"]

    _setup()

    from reflex import constants
    from reflex.reflex import _run
    from reflex_base.config import environment

    environment.REFLEX_COMPILE_CONTEXT.set(constants.CompileContext.RUN)
    _run(env=constants.Env.DEV)


def _resolve_serve_asgi_server(cli_server: str | None) -> str:
    """Pick ASGI server for ``uv run serve``: granian (default) or uvicorn.

    Priority: ``--server`` CLI flag → ``SERVE_ASGI_SERVER`` env → granian.
    Sets ``REFLEX_USE_GRANIAN`` so Reflex's ``should_use_granian()`` follows.
    """
    raw = (cli_server or os.getenv("SERVE_ASGI_SERVER", "") or "granian").strip().lower()
    if raw in {"granian", "gr"}:
        server = "granian"
    elif raw in {"uvicorn", "uv", "gunicorn"}:
        server = "uvicorn"
    else:
        print(
            f"[serve] FATAL: unknown ASGI server {raw!r}. "
            "Use --server granian|uvicorn (or SERVE_ASGI_SERVER).",
            flush=True,
        )
        raise SystemExit(2)

    if server == "granian":
        os.environ["REFLEX_USE_GRANIAN"] = "1"
        return server

    import importlib.util

    missing = [
        name
        for name in ("uvicorn", "gunicorn")
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        print(
            "[serve] FATAL: --server uvicorn requires "
            + " and ".join(missing)
            + ". Install with: uv add uvicorn gunicorn",
            flush=True,
        )
        raise SystemExit(2)

    os.environ["REFLEX_USE_GRANIAN"] = "0"
    return server


def serve() -> None:
    """Start the single-port production server (Reflex 0.9+ unified mode).

    Starts an external liveness watchdog that SIGKILLs the serve process group
    if ``/_health`` stops responding — wedged workers must not look healthy.

    ASGI server selection (default Granian)::

        uv run serve --server granian
        uv run serve --server uvicorn
        SERVE_ASGI_SERVER=uvicorn uv run serve
    """
    parser = argparse.ArgumentParser(
        description="Production fullstack serve (single port).",
    )
    parser.add_argument(
        "--server",
        choices=("granian", "uvicorn"),
        default=None,
        help=(
            "ASGI server for the Reflex fullstack worker "
            "(default: SERVE_ASGI_SERVER or granian). "
            "uvicorn uses gunicorn+UvicornH11Worker on Linux."
        ),
    )
    args = parser.parse_args()

    _setup()
    asgi_server = _resolve_serve_asgi_server(args.server)

    # Own process group so the watchdog can hard-kill ASGI workers too.
    try:
        os.setpgrp()
    except OSError:
        pass

    web_dir = Path(".web")
    if web_dir.exists():
        shutil.rmtree(web_dir)
        print("Removed stale .web build directory before production serve.", flush=True)

    from materialized_enhancements.crawler_assets import generate_crawler_assets
    from materialized_enhancements.state import regenerate_stale_report_landing_pages

    generate_crawler_assets()
    regenerate_stale_report_landing_pages()

    from reflex import constants
    from reflex.config import get_config
    from reflex.constants.base import RunningMode
    from reflex.reflex import _run
    from reflex_base.config import environment

    port_str = os.getenv("APP_PORT", "").strip()
    if port_str:
        port = int(port_str)
    else:
        port = int(get_config().frontend_port or 3000)

    # Keep env knobs readable for operators / the watchdog child.
    os.environ.setdefault("SERVE_HEALTH_TIMEOUT", "5")
    os.environ.setdefault("SERVE_HEALTH_INTERVAL", "5")
    os.environ.setdefault("SERVE_HEALTH_FAIL_LIMIT", "2")
    os.environ.setdefault("SERVE_HEALTH_STARTUP_GRACE", "600")

    print(
        f"[serve] ASGI server={asgi_server} "
        f"(REFLEX_USE_GRANIAN={os.environ.get('REFLEX_USE_GRANIAN')})",
        flush=True,
    )

    watchdog: subprocess.Popen[str] | None = None
    if os.getenv("SERVE_HEALTH_WATCHDOG", "1").strip() not in {"0", "false", "False", "no", "NO"}:
        watchdog = _spawn_serve_liveness_watchdog(
            port=port,
            serve_pid=os.getpid(),
            serve_pgid=os.getpgrp(),
        )
        print(
            f"[serve] liveness watchdog pid={watchdog.pid} "
            f"→ http://127.0.0.1:{port}/_health",
            flush=True,
        )
    else:
        print("[serve] liveness watchdog DISABLED (SERVE_HEALTH_WATCHDOG=0)", flush=True)

    environment.REFLEX_COMPILE_CONTEXT.set(constants.CompileContext.RUN)
    try:
        _run(
            env=constants.Env.PROD,
            running_mode=RunningMode.FULLSTACK,
            frontend_port=port,
            backend_port=port,
        )
    finally:
        if watchdog is not None:
            # Read the exit status BEFORE our own terminate(), which would
            # itself set returncode=-15 and make every clean Ctrl+C shutdown
            # look like the watchdog had aborted a wedged server.
            watchdog_exit = watchdog.poll()
            if watchdog_exit is None:
                watchdog.terminate()
                try:
                    watchdog.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    watchdog.kill()
                    watchdog.wait(timeout=3)
            # If the watchdog already killed us, we never get here. If _run
            # returned while the watchdog reported a hang, surface that loudly.
            if watchdog_exit not in (None, 0):
                print(
                    "[serve] FATAL: liveness watchdog aborted the server "
                    f"(exit={watchdog_exit}).",
                    flush=True,
                )
                raise SystemExit(1)


def _build_preselect_url(
    name: str,
    categories: int,
    genes_per_category: int,
    host: str,
    port: int,
) -> str:
    """Build a materialization URL with pre-selected genes within budget."""
    from materialized_enhancements.gene_data import (
        DEFAULT_BUDGET,
        GENE_LIBRARY,
        GENE_PRICES,
        UNIQUE_CATEGORIES,
    )

    cats_to_use = UNIQUE_CATEGORIES[: min(categories, len(UNIQUE_CATEGORIES))]

    budget = DEFAULT_BUDGET
    selected_cats: list[str] = []
    selected_genes: list[str] = []

    for cat in cats_to_use:
        genes = sorted(
            ((g["gene"], GENE_PRICES.get(g["gene"], 0)) for g in GENE_LIBRARY if g["category"] == cat),
            key=lambda t: t[1],
        )
        for gene_name, price in genes[: genes_per_category]:
            if budget - price >= 0:
                if cat not in selected_cats:
                    selected_cats.append(cat)
                selected_genes.append(gene_name)
                budget -= price

    bitmask = 0
    for cat in selected_cats:
        idx = UNIQUE_CATEGORIES.index(cat) + 1
        bitmask |= 1 << (idx - 1)

    name_b64 = base64.urlsafe_b64encode(name.encode("utf-8")).decode("ascii").rstrip("=")
    genes_json = json.dumps(selected_genes, separators=(",", ":"))
    genes_b64 = base64.urlsafe_b64encode(genes_json.encode("utf-8")).decode("ascii").rstrip("=")
    path = f"/materialization?report=1&name={quote(name_b64)}&cats={bitmask}&genes={quote(genes_b64)}"
    url = f"http://{host}:{port}{path}"

    print(f"Pre-selected {len(selected_genes)} genes across {len(selected_cats)} categories")
    print(f"Budget: {DEFAULT_BUDGET - budget}/{DEFAULT_BUDGET} cr spent")
    print(f"Genes: {', '.join(selected_genes)}")
    print(f"URL: {_terminal_hyperlink(url)}")
    return url


def _spawn_open_when_ready(
    name: str,
    categories: int,
    genes_per_category: int,
    frontend_port: int,
) -> None:
    """Open the preselected URL from a side process after the frontend is ready."""
    opener_script = """
import sys
import time
import webbrowser
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from materialized_enhancements.run import _build_preselect_url

name = sys.argv[1]
categories = int(sys.argv[2])
genes_per_category = int(sys.argv[3])
frontend_port = int(sys.argv[4])
url = _build_preselect_url(
    name=name,
    categories=categories,
    genes_per_category=genes_per_category,
    host="localhost",
    port=frontend_port,
)

for _ in range(120):
    time.sleep(3)
    try:
        resp = urlopen(f"http://localhost:{frontend_port}/materialization", timeout=2)
        body = resp.read(4096).decode("utf-8", errors="replace").lower()
    except (HTTPError, URLError, TimeoutError):
        continue
    if resp.status == 200 and "404: page not found" not in body:
        print(f"\\n>>> Server ready on :{frontend_port}; opening browser\\n", flush=True)
        webbrowser.open(url)
        raise SystemExit(0)

print("\\n>>> Timed out waiting for server.\\n", flush=True)
"""
    subprocess.Popen(
        [
            sys.executable,
            "-c",
            opener_script,
            name,
            str(categories),
            str(genes_per_category),
            str(frontend_port),
        ],
        cwd=Path.cwd(),
    )


def preselect() -> None:
    """Start the Reflex dev server and open the materialization page with pre-selected genes.

    Identical to ``uv run start`` but auto-opens the materialization page with
    genes pre-selected via URL parameters once the server is ready.

    Usage::

        uv run preselect                     # all categories, 2 cheapest genes each
        uv run preselect --categories 3      # first 3 categories only
        uv run preselect --name "TestBot"    # custom personal tag
        uv run preselect --url-only          # print URL only, don't start server
    """
    args_raw = sys.argv[1:]
    dev_mode = "--dev" in args_raw
    if dev_mode:
        os.environ["MATERIALIZED_DEV_MODE"] = "1"
        args_raw = [a for a in args_raw if a != "--dev"]

    _setup()

    parser = argparse.ArgumentParser(description="Start server with pre-selected genes on materialization page")
    parser.add_argument("--name", default="TestUser", help="Personal tag / character name")
    parser.add_argument("--categories", type=int, default=999,
                        help="Number of categories to include")
    parser.add_argument("--genes-per-category", type=int, default=2,
                        help="Max cheapest genes to pick per category")
    parser.add_argument("--frontend-port", type=int, default=None,
                        help="Frontend port to use and open (default: auto)")
    parser.add_argument("--backend-port", type=int, default=None,
                        help="Backend port to use (default: auto)")
    parser.add_argument("--backend-host", default=None,
                        help="Backend bind host, defaults to Reflex config / .env")
    parser.add_argument("--url-only", action="store_true", help="Print URL and exit without starting server")
    parser.add_argument("--clean", "--clean-storage", action="store_true", help="Clear client-side LocalStorage on launch")
    parsed = parser.parse_args(args_raw)

    if parsed.clean:
        os.environ["CLEAN_BROWSER_STORAGE"] = "1"

    if parsed.url_only:
        _build_preselect_url(
            name=parsed.name,
            categories=parsed.categories,
            genes_per_category=parsed.genes_per_category,
            host="localhost",
            port=parsed.frontend_port or 3000,
        )
        return

    from reflex import constants
    from reflex.config import get_config
    from reflex.reflex import _run
    from reflex.utils import processes
    from reflex_base.config import environment

    config = get_config()
    explicit_frontend = parsed.frontend_port is not None
    explicit_backend = parsed.backend_port is not None
    frontend_port = processes.handle_port(
        "frontend",
        parsed.frontend_port or config.frontend_port or constants.DefaultPorts.FRONTEND_PORT,
        auto_increment=not explicit_frontend,
    )
    backend_port = processes.handle_port(
        "backend",
        parsed.backend_port or config.backend_port or constants.DefaultPorts.BACKEND_PORT,
        auto_increment=not explicit_backend,
    )

    _spawn_open_when_ready(
        name=parsed.name,
        categories=parsed.categories,
        genes_per_category=parsed.genes_per_category,
        frontend_port=frontend_port,
    )

    environment.REFLEX_COMPILE_CONTEXT.set(constants.CompileContext.RUN)
    _run(
        env=constants.Env.DEV,
        frontend_port=frontend_port,
        backend_port=backend_port,
        backend_host=parsed.backend_host,
    )


def kill_ports() -> None:
    """Show and kill processes on ports 3000 and 8000.

    Usage::

        uv run kill-ports            # show and kill both
        uv run kill-ports 3000       # only port 3000
        uv run kill-ports 3000 8000  # explicit list
    """
    ports = [int(p) for p in sys.argv[1:]] if len(sys.argv) > 1 else [3000, 8000]
    killed_any = False
    for port in ports:
        try:
            out = subprocess.check_output(
                ["lsof", "-ti", f":{port}"], text=True, stderr=subprocess.DEVNULL,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            out = ""
        if not out:
            print(f"Port {port}: free")
            continue
        pids = [int(p) for p in out.split()]
        for pid in pids:
            try:
                cmd = subprocess.check_output(
                    ["ps", "-p", str(pid), "-o", "comm="], text=True, stderr=subprocess.DEVNULL,
                ).strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                cmd = "?"
            print(f"Port {port}: killing PID {pid} ({cmd})")
            try:
                os.kill(pid, signal.SIGKILL)
                killed_any = True
            except OSError as exc:
                print(f"  failed: {exc}")
    if not killed_any:
        print("Nothing to kill — ports are free.")
