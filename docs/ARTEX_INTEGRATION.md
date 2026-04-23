# ARTEX Venue Integration

This document describes how Materialized Enhancements publishes generated sculptures
and jigsaws to the [ARTEX Platform API](https://github.com/CODAME/artex-open) and
pushes them to live venue displays in one click.

---

## Architecture Overview

```
Visitor browser          Reflex backend              Platform API :8787          Display :4173
───────────────          ──────────────              ──────────────────          ─────────────
?from=ARTEX   ──────►  apply_artex_params()
?token=abcd             seeds state vars
?display_id=test-wall
?redirect=<url>

[Send to Wall] ──────►  create_artex_project()  ──► POST /admin/dev-session ──► sessionToken
                        or publish_to_artex()    ──► PUT  /api/packages/:id  ──► upload zip
                                                 ──► POST /publish/apply     ──► slug
                                                 ──► POST /api/venue/
                                                         displays/:id/
                                                         load-slug            ──► SSE command
                                                                                  │
                                                                              Display fetches
                                                                              GET /public/
                                                                              projects/:slug/
                                                                              package (zip)
                                                                              and renders
```

---

## URL Query Parameters

The kiosk entrypoint is a URL that the room's QR code (or the wall display's own
redirect) sends visitors to. All parameters are optional with env-based defaults.

| Parameter | Example | Effect |
|-----------|---------|--------|
| `from` | `ARTEX` | Makes the "Send to Wall" button visible regardless of token/env config |
| `token` | `abcd` | Overrides `ARTEX_API_TOKEN` env var for this session |
| `display_id` | `test-wall` | Target display for venue push; overrides `ARTEX_DISPLAY_ID` env |
| `redirect` | `https://artex.live/` | If present and not `false`: enables the idle-inactivity timer, and redirects here both on idle expiry **and** after a successful publish. Supports `{slug}` substitution. |

**`redirect=false`** explicitly disables the timer and post-publish redirect even
when a default is configured in env.

### Example kiosk URLs

```
# Sculpture tab, full kiosk setup:
http://my-installation.example/materialize?from=ARTEX&token=abcd&display_id=north-wall&redirect=https://artex.live/

# Jigsaw tab, dev test with slug inspection after publish:
http://localhost:3000/jigsaw?from=ARTEX&redirect=http://127.0.0.1:8787/public/projects/{slug}

# No redirect, just show the button:
http://my-installation.example/materialize?from=ARTEX&token=abcd&display_id=entrance&redirect=false
```

---

## Publish Pipeline — Step by Step

All HTTP is synchronous Python (`urllib.request`) run in a thread-pool executor to
avoid blocking the Reflex event loop. Implementation in
[`src/materialized_enhancements/artex.py`](../src/materialized_enhancements/artex.py).

### 1. Generate STL (pre-existing, unchanged)

- **Sculpture**: `ComposeState.materialize()` calls `sculpture.generate_sculpture()` →
  writes STL to `data/output/sculptures/voronoi_shell_<timestamp>.stl`. Path stored in
  `ComposeState.stl_download_path`.
- **Jigsaw**: `JigsawState.generate_stl_background()` calls `jigsaw_stl.grid_to_stl()` →
  STL bytes held in-memory as `JigsawState._stl_bytes`.

### 2. Build artwork config (`build_sculpture_artwork` / `build_jigsaw_artwork`)

A **v2 ARTEX artwork config** (`config/artwork.json`) is constructed in memory:

```json
{
  "version": 2,
  "id": "me-sculpture-<uuid16>",
  "title": "Materialized Enhancement — Alice",
  "artistName": "Materialized Enhancements",
  "story": "...",
  "assets": [
    { "id": "preview", "kind": "image", "path": "preview/preview.png", "mimeType": "image/png" },
    { "id": "model",   "kind": "model", "path": "models/voronoi_shell_xxx.stl", "mimeType": "model/stl" }
  ],
  "layers": [
    { "id": "base", "kind": "image", "name": "Sculpture Preview", "zIndex": 0, "visible": true, "opacity": 1, "assetId": "preview" }
  ],
  "states": [{ "id": "default", "label": "Default", "initial": true }],
  "runtime": { "renderer": "webgl", "localFirst": true, ... },
  "mood": 0.6,
  "animation": { "baseSpeed": 0.5, "breathingEnabled": true, ... },
  ...
}
```

The `project_id` is a freshly generated `me-sculpture-<16 hex chars>` UUID, unique per publish.

### 3. Build package zip (`build_artex_package_zip`)

An in-memory zip (no temp files) containing:

```
config/artwork.json      ← v2 artwork config (JSON)
config/state.json        ← initial StateJsonV2 (ARTEX_V2_STATE_PATH constant)
preview/preview.png      ← matplotlib render of the STL — the image base layer
models/<stl_filename>    ← binary STL bytes (model asset, not a layer)
```

### 4. Upload package (`_upload_package`)

```
PUT http://127.0.0.1:8787/api/packages/me-pkg-<20hex>
Content-Type: application/zip
Body: <zip bytes>
```

No auth token required for loopback (127.0.0.1) requests — the API trusts the local
machine. Returns `{"ok": true, "packageId": "me-pkg-..."}`.

### 5. Acquire session token (`_get_session_token`)

```
POST http://127.0.0.1:8787/admin/dev-session
Content-Type: application/json
Body: {"adminToken": "abcd"}
```

`abcd` must match `ARTEX_PLATFORM_ADMIN_TOKEN` in the ARTEX server's `.env`.
Returns a short-lived session token used as the Bearer credential for publish.

> **Loopback-only**: this endpoint is intentionally restricted to `127.0.0.1`.
> The Python Reflex backend and the ARTEX Platform API must be on the same machine
> for the dev-session exchange to work.

### 6. Publish artwork (`_publish_artwork`)

```
POST http://127.0.0.1:8787/publish/apply
Authorization: Bearer <sessionToken>
Content-Type: application/json
Body: {
  "projectId": "me-sculpture-<uuid>",
  "packageBlobId": "me-pkg-<uuid>",
  "title": "Materialized Enhancement — Alice",
  "description": "...",
  "ownerUserId": "local-dev-admin"
}
```

The API creates/updates a `publishedArtwork` record and assigns a URL-safe slug derived
from the title (deduped with a numeric suffix if needed). Returns:

```json
{
  "artwork": { "slug": "materialized-enhancement-alice", "id": "art_xxx", ... },
  "project": { "id": "me-sculpture-...", "publishedSlug": "materialized-enhancement-alice", ... }
}
```

The slug is what the ARTEX runtime uses to fetch the package.

### 7. Push to display (`_push_to_display`)

```
POST http://127.0.0.1:8787/api/venue/displays/test-wall/load-slug
Content-Type: application/json
Body: {"slug": "materialized-enhancement-alice"}
```

No auth required. Returns `{"ok": true, "delivery": "sse"}` if the display has an
active SSE connection (command delivered instantly) or `{"delivery": "queued"}` if
the display is temporarily offline (command queued for next heartbeat check-in).

### 8. Display renders the artwork

The ARTEX runtime browser tab (at `:4173?mode=gallery&displayId=test-wall`) receives
the SSE `load-slug` command and fetches:

```
GET http://127.0.0.1:8787/public/projects/materialized-enhancement-alice/package
→ Returns the zip blob
```

It unpacks the zip and renders the artwork with the `webgl` renderer, displaying the `preview/preview.png` base layer.

### 9. Redirect (optional)

If `artex_redirect_url` is set (from `?redirect=<url>`) and is not `"false"`, the
Reflex backend yields `rx.redirect(url.format(slug=slug), is_external=True)`,
sending the visitor's browser to the destination URL.

---

## Inactivity Timer (Idle Band)

When `?redirect=<url>` is present in the page URL (and not `"false"`), a fixed
banner appears at the very top of the page:

- Shows "Next visitor in Xs — touch or move to continue"
- A progress bar depletes left-to-right over `IDLE_TIMEOUT_SECONDS` (default: 60)
- Any mouse/keyboard/touch/scroll event resets the counter
- Last `IDLE_WARNING_SECONDS` (default: 5) the band turns red
- At zero: `window.location.href = <redirect_url>` (same window)

The timer is **pure client-side JavaScript** embedded via `rx.script()` in
`layout.py`'s `idle_band()` component, which is included in every page's template.
No Reflex state is involved — the JS reads the `?redirect=` param directly from
`window.location.search`.

---

## Environment Variables

All in [`.env.template`](../.env.template) / [`.env`](../.env).

| Variable | Default | Description |
|----------|---------|-------------|
| `ARTEX_API_URL` | `http://127.0.0.1:8787` | Platform API base URL (no trailing slash) |
| `ARTEX_API_TOKEN` | `abcd` | Admin token (`ARTEX_PLATFORM_ADMIN_TOKEN` on API server) |
| `ARTEX_DISPLAY_ID` | `test-wall` | Default venue display ID; overridden by `?display_id=` |
| `ARTEX_IDLE_URL` | `https://artex.live/` | Fallback idle-redirect in prod (JS uses `?redirect=` first) |
| `ARTEX_DEV_REDIRECT_URL` | `http://127.0.0.1:8787/public/projects/{slug}` | Dev-mode redirect with `{slug}` substitution |
| `IDLE_TIMEOUT_SECONDS` | `60` | Inactivity timeout in seconds |
| `IDLE_WARNING_SECONDS` | `5` | Seconds before expiry when the band turns red |

---

## Dev Mode (`--dev` / `MATERIALIZED_DEV_MODE=1`)

When `uv run start --dev` is used:

- The ARTEX section is always visible (no need for `?from=ARTEX` or a token)
- Three editable inputs appear above the "Send to Wall" button:
  - **ARTEX API URL** — override the platform API endpoint
  - **ARTEX Admin Token** — override the token (password input)
  - **Display ID** — override the target display
- Idle-redirect and post-publish redirect go to `ARTEX_DEV_REDIRECT_URL`

---

## Local Test Stand

### Start the ARTEX Platform API

```bash
cd /path/to/ARTEX
# Uses .services/artex-platform-api/.env which has:
#   ARTEX_PLATFORM_ADMIN_TOKEN=abcd
#   ARTEX_PLATFORM_STORE=json
npm run platform-api
# → http://127.0.0.1:8787
```

Verify:
```bash
curl http://127.0.0.1:8787/health
# → {"ok":true,"service":"artex-platform-api",...}
```

### Start the ARTEX Runtime (the display)

```bash
cd /path/to/ARTEX
VITE_PLATFORM_API_URL=http://127.0.0.1:8787 \
VITE_ARTEX_PLATFORM_DEV_TOKEN=abcd \
VITE_DISPLAY_ID=test-wall \
bun run dev:runtime
# → http://localhost:4173
```

Open `http://localhost:4173?mode=gallery&displayId=test-wall&apiBase=http://127.0.0.1:8787`
in a browser tab. It should show "Gallery mode — waiting for remote command" with
a `test-wall` badge in the corner.

Verify the display registered:
```bash
curl http://127.0.0.1:8787/api/venue/displays
# → {"displays":[{"id":"test-wall","status":"connected",...}],...}
```

### Send a sculpture to the display

Start the Reflex app:
```bash
cd /path/to/materialized-enchancements
uv run start
# → http://localhost:3000
```

Navigate to:
```
http://localhost:3000/materialize?from=ARTEX&display_id=test-wall&redirect=false
```

Select gene categories, generate the sculpture, click **Send to Wall**. The display
tab should immediately switch from "waiting" to rendering the sculpture.

---

## Running the Tests

### Unit tests (no server needed)

```bash
uv run pytest tests/test_artex.py -v
```

Covers: v2 config format, zip structure, `publish_and_push_sync` with mocked HTTP,
session-token parsing, delivery-mode return value.

### Integration tests (requires local test stand)

Auto-skipped if `http://127.0.0.1:8787/health` is unreachable.

```bash
uv run pytest tests/test_artex_integration.py -v -s
```

| Test | What it verifies |
|------|-----------------|
| `test_sculpture_publish_and_push` | Sculpture config → zip → upload → publish → push to `test-wall`; package fetchable |
| `test_jigsaw_publish_and_push` | Jigsaw config → same pipeline |
| `test_display_list_reachable` | `GET /api/venue/displays` responds; `test-wall` listed |
| `test_real_sculpture_stl_publish_and_push` | Uses smallest real STL from `data/output/sculptures/`; verifies binary round-trip (face count intact) |

---

## Open Issue — `model3d` layer kind not implemented in v2 runtime

**Expected behaviour**: a package with `kind: "model3d"` layers should render the
3D mesh live on the display (as it does in ARTEX Studio v1).

**Current status**: the v2 runtime (`packages/artex-runtime-web`) is a 2D WebGL
compositor and silently drops `model3d` layers, causing the warning
*"No visible image or video layer is available for the runtime stage."*

### Root cause (for ARTEX dev — all line refs are in `ARTEX/`)

| # | File | Line(s) | Issue |
|---|------|---------|-------|
| 1 | `packages/artex-contract/src/v2/types.ts` | 110 | `LayerKind` union is `"image"\|"video"\|"shader"\|"audio"\|"mask"\|"text"` — `"model3d"` is absent |
| 2 | `packages/artex-contract/src/v2/types.ts` | 332–337 | `runtime.renderer` is typed as the literal `"webgl"` only — no `"three-experimental"` or `"three"` variant |
| 3 | `packages/artex-runtime-web/src/runtimePlan.ts` | 62–63 | `mediaLayers` filter accepts only `kind==="image"\|\|kind==="video"` — a `model3d` layer is silently discarded |
| 4 | `packages/artex-runtime-web/src/runtimePlan.ts` | 71–73 | `unsupportedLayers` only catches `"shader"` and `"audio"` — `model3d` is not even surfaced as a warning |
| 5 | `packages/artex-runtime-web/src/runtimePlan.ts` | 81–83 | With 0 media layers, fires: *"No visible image or video layer…"* |
| 6 | `packages/artex-contract/src/v2/packageContract.ts` | 241–247 | `readArtexV2PackageArchive` loads every `asset.path` into `files` regardless of kind — STL blob reaches `files` but the stage ignores it |
| 7 | `packages/artex-contract/src/v2/packageContract.ts` | 99–127 | `validateArtworkConfigV2` never validates asset/layer kind values — invalid configs pass silently |

**Suggested fix for ARTEX dev**: add `"model3d"` to `LayerKind` (point 1), add a
`"three"` / `"three-experimental"` renderer variant (point 2), and handle the new
layer kind in `buildRuntimeStagePlan` (points 3–5) and `ArtexRuntimeStage`
(analogous to the `image`/`video` branches in
`packages/artex-runtime-web/src/runtimeStage.tsx:203-230`), porting the Three.js
mesh loader that already exists in ARTEX Studio v1.

### Current workaround (this repo)

While `model3d` is not supported in the v2 runtime, `publish_and_push_sync` in
`artex.py` renders a perspective PNG of the STL via `render_stl_preview_png`
(trimesh + matplotlib, headless Agg backend) and uses it as the `image` base layer.
The STL is still included in the package under `models/` as a `model` asset so it
survives the round-trip and can be loaded once the runtime gains 3D support.

The package also fixed a secondary path bug: `state.json` was written to the zip
root but `readArtexV2PackageArchive` reads `config/state.json`
(`ARTEX_V2_STATE_PATH`, `packages/artex-contract/src/v2/packageContract.ts:15`).

When the ARTEX v2 runtime gains `model3d` support the workaround can be removed by:
1. Restoring `kind: "model3d"` layers and `renderer: "three-experimental"` in the
   artwork builders.
2. Dropping the `render_stl_preview_png` call from `publish_and_push_sync`.
3. Keeping the `preview/preview.png` asset as an optional poster fallback.

### Dev-session is loopback-only

`POST /admin/dev-session` rejects non-loopback callers. For a setup where the Reflex
backend runs on a different machine from the ARTEX Platform API (e.g. a kiosk device
on LAN), an alternative auth path (Firebase ID token or a pre-issued session secret)
would be needed. For all current use-cases the same machine runs both processes.
