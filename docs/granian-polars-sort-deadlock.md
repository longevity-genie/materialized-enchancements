# Granian + Polars: fork-after-threads deadlock (not “slow Polars”)

## Symptom

Under production fullstack:

```bash
uv run serve
```

any **parallel** Polars operation triggered by a Knowledgebase DataGrid — a
column sort, or the `unique()` that computes filter value options when you click
a filter icon — could **silently wedge** the server:

- process alive, TCP still accepting, console still says `App running at`
- HTTP / WebSocket stop answering — **no traceback, no exit**
- browser shows a websocket-error toast, then the `/_health` watchdog SIGKILLs

Dev (`uv run start`) never reproduced it.

## Root cause

Not thread-safety, not slowness — **fork after Rayon**.

1. `reflex run --env prod` imports and compiles the app **in the parent process**.
   That import path touches Polars, which builds its Rayon worker pool.
2. Granian then creates its ASGI worker with `multiprocessing`, which on Linux
   defaults to **`fork`**.
3. The child inherits the Rayon pool’s *state* (locks, queues) but **not its
   threads**. The first parallel Polars call in a request blocks forever inside
   `collect()`.

Reproduced minimally: warm Polars in a parent, `os.fork()`, run `unique()` in the
child → child hangs. Skip the parent warm-up → child runs fine.

Thread dump of a wedged worker (`kill -ABRT` with `PYTHONFAULTHANDLER=1`) shows
the main ASGI thread parked on `future.result()` in `_run_grid_query`, and the
query worker thread parked inside `polars.lazyframe.frame.collect`.

## The fix

`src/materialized_enhancements/run.py` → `_force_spawn_worker_processes()`:

```python
multiprocessing.set_start_method("spawn", force=True)
```

called from `_setup()`, before Reflex/Granian start. Granian’s
`server/mp.py` respects `multiprocessing.get_start_method()`, so the worker
becomes a **fresh interpreter** that builds its own Rayon pool.

Do not remove this. Without it the wedge returns for *any* parallel Polars call
on the request path, not just sorting.

## What is / is not the fix

| Approach | Verdict |
|----------|---------|
| `multiprocessing` start method `spawn` for ASGI workers | **The fix** |
| Cap `POLARS_MAX_THREADS=1` | **Not a fix** — cripples huge LazyFrame hosts |
| Full `collect()` + Python `sort_dataframe_model` | **Not a fix** — OOM / crawl on big frames |
| Cache the entire sorted DataFrame in the grid | **Not a fix** for huge frames |
| Lazy `filter → sort → slice → collect` with **full Rayon**, off the ASGI thread | Correct, and needed independently (keeps the event loop free) |
| `/_health` liveness watchdog on `uv run serve` | Safety net if anything else wedges |

## Library behavior (`reflex-mui-datagrid` ≥ 0.3.13)

`LazyFrameGridMixin._refresh_lf_grid_page`:

1. apply filter lazily
2. apply sort via `apply_sort_model` (Polars `lf.sort`, no collect)
3. `select(len)` / `slice(offset, page_size).collect()` only
4. that materialize runs in `_run_grid_query` on a **shared, never-shut-down**
   `ThreadPoolExecutor`, so the Granian request thread never holds Rayon and a
   timeout can actually return (a `with`-scoped pool would `shutdown(wait=True)`
   and wait out the very query it was abandoning)

Filter/sort/scroll handlers clear `lf_grid_loading` and report into
`lf_grid_stats` on failure, so one grid cannot stall the page.

Optional hard ceiling: `REFLEX_MUIGRID_QUERY_TIMEOUT` (seconds). Unset / `0` =
no timeout (default — correct for large sorts).

## How to verify

```bash
uv run serve
curl -s http://127.0.0.1:3000/_health   # {"status":"ok"}
```

Then on `/knowledgebase/`: open the Organizations tab, click the **Name** filter
icon (operator must stay `Contains` with a text input), type `Adair`, Apply →
one row, `Adair Lab (Fred Hutchinson Cancer Center)`. Sort a column both
directions. `/_health` must keep answering throughout.

Cross-tab check: filter Genes on `Gene contains a` (59 rows), switch to
Organizations and back — the filter must survive. `load_grid()` returns early
when `lf_grid_loaded` is set, because `set_lazyframe()` resets
filter/sort/pagination and `set_surface()` calls `load_grid()` on every tab
switch; without the guard the visitor's filter silently disappears.

## Reading the shutdown log

A clean Ctrl+C ends with `Reflex app stopped.` and exit code 0. Two lines are
easy to misread as a wedge:

- **`FATAL: liveness watchdog aborted the server (exit=-15)`** on a healthy
  shutdown was a reporting bug (`serve()` tested the watchdog's `returncode`
  *after* terminating it, so its own `SIGTERM` looked like a watchdog verdict).
  Fixed by reading `poll()` before `terminate()`. If you see this banner now, it
  is real.
- **A `websocket error` toast in the browser** means the backend went away —
  check whether the process is still listening before blaming grid code. Clicks
  after that point are silent no-ops, which can look exactly like a filter bug.
