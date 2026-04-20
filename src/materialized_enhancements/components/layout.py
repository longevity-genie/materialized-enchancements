from __future__ import annotations

import json

import reflex as rx

from materialized_enhancements.env import (
    DEV_MODE,
    IDLE_TIMEOUT_SECONDS,
    IDLE_WARNING_SECONDS,
    idle_redirect_url,
)


def fomantic_icon(
    name: str,
    size: int | str | None = None,
    color: str | None = None,
    style: dict | None = None,
) -> rx.Component:
    """Fomantic UI icon component."""
    mapping = {
        "circle-check": "check circle",
        "circle-x": "times circle",
        "circle-alert": "exclamation circle",
        "circle-play": "play circle",
        "cloud-upload": "cloud upload",
        "file-text": "file alternate",
        "refresh-cw": "sync",
        "external-link": "external alternate",
        "chart-bar": "chart bar",
        "heart-pulse": "heartbeat",
        "activity": "pulse",
        "zap": "bolt",
        "droplets": "tint",
        "pill": "pills",
        "book-open": "book open",
        "chevron-up": "chevron up",
        "chevron-down": "chevron down",
        "chevron-left": "chevron left",
        "chevron-right": "chevron right",
        "paw-print": "paw",
        "x": "times",
        "plus": "plus",
        "user": "user",
        "loader-circle": "spinner",
        "sparkles": "magic",
        "flask": "flask",
        "leaf": "leaf",
        "star": "star",
        "eye": "eye",
        "shield": "shield",
        "sun": "sun",
        "moon": "moon",
        "feather": "feather",
        "dna": "dna",
        "atom": "atom",
        "fire": "fire",
        "brain": "brain",
        "paint brush": "paint brush",
        "cube": "cube",
        "puzzle piece": "puzzle piece",
        "video": "video",
        "play": "play",
        "close": "close",
        "check": "check",
        "times": "times",
    }

    fomantic_name = mapping.get(name, name)

    icon_style: dict = {"margin": "0", **(style or {})}
    if size is not None:
        if isinstance(size, (int, float)) or (isinstance(size, str) and size.isdigit()):
            icon_style["fontSize"] = f"{size}px"
        else:
            icon_style["fontSize"] = size

    if color is not None:
        icon_style["color"] = color

    return rx.el.i(
        class_name=f"icon {fomantic_name}",
        style=icon_style,
    )


def fomantic_stylesheets() -> rx.Component:
    """Load Fomantic UI stylesheets and scripts inline."""
    return rx.fragment(
        rx.el.link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/fomantic-ui@2.9.4/dist/semantic.min.css",
        ),
        rx.script(src="https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js"),
        rx.script(src="https://cdn.jsdelivr.net/npm/fomantic-ui@2.9.4/dist/semantic.min.js"),
    )


_WS_WATCHDOG_JS = """
(function () {
  'use strict';
  var CONFIRM_MS    = 5000;
  var FORCE_MS      = 30000;
  var INIT_GRACE_MS = 8000;
  var startedAt       = Date.now();
  var everConnected   = false;
  var confirmedOutage = false;
  var confirmTimer    = null;
  var forceTimer      = null;
  var banner          = null;
  var sockets         = [];
  var _WS             = window.WebSocket;

  function PatchedWS(url, proto) {
    var ws = (proto !== undefined) ? new _WS(url, proto) : new _WS(url);
    sockets.push(ws);
    ws.addEventListener('open', function () {
      clearTimeout(confirmTimer); confirmTimer = null;
      if (confirmedOutage) { clearTimeout(forceTimer); window.location.reload(); return; }
      everConnected = true;
      clearTimeout(forceTimer); forceTimer = null;
      hideBanner();
    });
    ws.addEventListener('close', function () {
      sockets = sockets.filter(function (s) { return s !== ws; });
      if (!everConnected || confirmTimer || confirmedOutage) return;
      if (Date.now() - startedAt < INIT_GRACE_MS) return;
      var alive = sockets.some(function (s) { return s.readyState === 0 || s.readyState === 1; });
      if (alive) return;
      confirmTimer = setTimeout(function () {
        confirmTimer = null;
        var alive2 = sockets.some(function (s) { return s.readyState === 0 || s.readyState === 1; });
        if (alive2) return;
        confirmedOutage = true;
        showBanner();
        forceTimer = setTimeout(function () { window.location.reload(); }, FORCE_MS);
      }, CONFIRM_MS);
    });
    return ws;
  }
  PatchedWS.CONNECTING = 0; PatchedWS.OPEN = 1;
  PatchedWS.CLOSING   = 2; PatchedWS.CLOSED = 3;
  PatchedWS.prototype  = _WS.prototype;
  window.WebSocket     = PatchedWS;

  function showBanner() {
    if (banner) return;
    banner = document.createElement('div');
    banner.style.cssText =
      'position:fixed;top:0;left:0;right:0;z-index:99999;background:#7c3aed;' +
      'color:#fff;text-align:center;padding:0.65rem 1.1rem;font-size:0.95rem;' +
      'font-family:sans-serif;cursor:pointer;letter-spacing:.3px';
    banner.onclick = function () { window.location.reload(); };
    document.body && document.body.appendChild(banner);
    var secs = Math.ceil(FORCE_MS / 1000);
    function tick() {
      if (!banner) return;
      banner.textContent = 'Connection lost — reloading in ' + secs + 's, or click to reload now';
      secs--;
      if (secs >= 0) setTimeout(tick, 1000);
    }
    tick();
  }
  function hideBanner() {
    if (banner && banner.parentNode) banner.parentNode.removeChild(banner);
    banner = null;
  }
})();
"""


def ws_watchdog() -> rx.Component:
    """Client-side WebSocket watchdog: auto-reloads if the Reflex connection drops."""
    return rx.script(_WS_WATCHDOG_JS)


_MUI_THEME_SHIM_JS = """
(function () {
  'use strict';
  // reflex-mui-datagrid + the bundled MUI build expect theme.alpha() to exist on
  // the theme object passed through transformTheme(). In Reflex 0.8.28 the CSS-
  // variables theme path doesn't ship it, which throws
  //   TypeError: theme.alpha is not a function
  // crashing the Gene Library / Animal Library tabs. Install a no-op fallback
  // as a non-enumerable Object.prototype getter so it only fires when code
  // explicitly reads .alpha on an object, never showing up in iteration.
  if (!Object.prototype.hasOwnProperty('alpha')) {
    try {
      Object.defineProperty(Object.prototype, 'alpha', {
        configurable: true,
        enumerable: false,
        get: function () { return function (color, _value) { return color; }; },
      });
    } catch (_e) { /* sealed env — nothing we can do */ }
  }
})();
"""


def mui_theme_shim() -> rx.Component:
    """Patch missing theme.alpha() helper so reflex-mui-datagrid stops crashing."""
    return rx.script(_MUI_THEME_SHIM_JS)


def report_libs() -> rx.Component:
    """Load client-side libraries used by the Share & Report section.

    All three are vendored under ``assets/vendor/`` so the app works offline /
    on kiosk networks without CDN access:

    - html-to-image: DOM → PNG rasterization (modern html2canvas successor)
    - jsPDF: client-side A4 PDF generation
    - qrcode-generator: tiny standalone QR code generator for share links
    - me_report.js: our own helpers (buttons wire into window.__meDownloadPng etc.)
    """
    return rx.fragment(
        rx.script(src="/vendor/html-to-image.js"),
        rx.script(src="/vendor/jspdf.umd.min.js"),
        rx.script(src="/vendor/qrcode.min.js"),
        rx.script(src="/vendor/me_report.js"),
    )


IDLE_BAND_HEIGHT_PX = 34

_IDLE_BAND_JS_TEMPLATE = """
(function () {
  'use strict';
  var TIMEOUT = %(timeout)d;
  var WARNING = %(warning)d;
  var BAND_H  = %(band_height)d;
  var IDLE_URL = %(url)s;
  var ACTIVATE_VALUE = 'artex';

  // Activate only when URL has ?interaction=artex (kiosk mode).
  var params = new URLSearchParams(window.location.search);
  if (params.get('interaction') !== ACTIVATE_VALUE) return;

  // Optional ?redirect=<url> overrides the default idle-redirect destination.
  var override = params.get('redirect');
  if (override) IDLE_URL = override;

  var band = document.getElementById('idle-band');
  var text = document.getElementById('idle-band-text');
  var fill = document.getElementById('idle-band-fill');
  var content = document.getElementById('me-app-content');
  if (!band || !text || !fill) return;

  // Unhide the band and shift the rest of the layout down to make room.
  band.style.display = 'flex';
  if (content) {
    content.style.marginTop = BAND_H + 'px';
    content.style.minHeight = 'calc(100vh - ' + BAND_H + 'px)';
  }

  var remaining = TIMEOUT;

  function render() {
    text.textContent = 'Next visitor in ' + remaining + 's \u2014 touch or move to continue';
    fill.style.width = ((remaining / TIMEOUT) * 100) + '%%';
    var warn = remaining <= WARNING;
    band.style.backgroundColor = warn ? '#dc2626' : '#1a1a2e';
    fill.style.backgroundColor = warn ? '#fca5a5' : '#7c3aed';
    text.style.color = warn ? '#ffffff' : '#e5e7eb';
  }

  function tick() {
    remaining -= 1;
    if (remaining <= 0) {
      window.location.href = IDLE_URL;
      return;
    }
    render();
  }

  function reset() {
    remaining = TIMEOUT;
    render();
  }

  ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'].forEach(function (evt) {
    document.addEventListener(evt, reset, { passive: true, capture: true });
  });

  render();
  setInterval(tick, 1000);
})();
"""


def idle_band() -> rx.Component:
    """Kiosk inactivity timer band at the very top.

    Activated by ``?interaction=artex`` in the URL (dev or prod). When active,
    starts at IDLE_TIMEOUT_SECONDS, resets on any user activity, turns red in
    the last IDLE_WARNING_SECONDS, and redirects to ``ARTEX_IDLE_URL`` at 0.
    Markup is always rendered but kept ``display: none`` until the JS sees the
    query param.
    """
    script = _IDLE_BAND_JS_TEMPLATE % {
        "timeout": IDLE_TIMEOUT_SECONDS,
        "warning": IDLE_WARNING_SECONDS,
        "band_height": IDLE_BAND_HEIGHT_PX,
        "url": json.dumps(idle_redirect_url()),
    }

    return rx.fragment(
        rx.el.div(
            rx.el.div(
                id="idle-band-fill",
                style={
                    "position": "absolute",
                    "top": "0",
                    "left": "0",
                    "bottom": "0",
                    "width": "100%",
                    "backgroundColor": "#7c3aed",
                    "opacity": "0.35",
                    "transition": "width 1s linear, background-color 0.3s ease",
                    "zIndex": "0",
                },
            ),
            rx.el.span(
                f"Next visitor in {IDLE_TIMEOUT_SECONDS}s",
                id="idle-band-text",
                style={
                    "position": "relative",
                    "zIndex": "1",
                    "fontSize": "0.88rem",
                    "fontWeight": "600",
                    "letterSpacing": "0.04em",
                    "color": "#e5e7eb",
                },
            ),
            id="idle-band",
            style={
                "position": "fixed",
                "top": "0",
                "left": "0",
                "right": "0",
                "height": f"{IDLE_BAND_HEIGHT_PX}px",
                "backgroundColor": "#1a1a2e",
                "display": "none",
                "alignItems": "center",
                "justifyContent": "center",
                "overflow": "hidden",
                "zIndex": "1100",
                "transition": "background-color 0.3s ease",
            },
        ),
        rx.script(script),
    )


def template(*children: rx.Component) -> rx.Component:
    """Main page template — White Mirror light theme."""
    global_css = rx.el.style(
        """
        /* Slightly larger type for projection / kiosk; between default (100%) and the prior 125% pass */
        html { font-size: 112.5%; }
        body { background-color: #f8f9fa !important; color: #1a1a2e !important; line-height: 1.5; }
        .ui.button { font-size: 1rem !important; padding: 0.6em 1em !important; }
        .ui.primary.button { font-size: 1.02rem !important; }
        .ui.top.attached.tabular.menu .item { font-size: 1.03rem !important; padding: 0.72em 1em !important; }
        .ui.segment { background-color: #ffffff !important; border-color: #e5e7eb !important; color: #1a1a2e !important; }
        .ui.raised.segment { box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important; }
        .ui.button { background-color: #f3f0ff !important; color: #7c3aed !important; border: 1px solid #d4c5f9 !important; }
        .ui.button:hover { background-color: #ede9fe !important; }
        .ui.primary.button { background-color: #7c3aed !important; color: #fff !important; border: none !important; }
        .ui.primary.button:hover { background-color: #6d28d9 !important; }
        .ui.top.attached.tabular.menu { background-color: #ffffff !important; border-color: #e5e7eb !important; }
        .ui.top.attached.tabular.menu .item { color: #6b7280 !important; }
        .ui.top.attached.tabular.menu .active.item { background-color: #ffffff !important; color: #7c3aed !important; border-color: #7c3aed !important; font-weight: 600 !important; }
        .ui.bottom.attached.segment { background-color: #ffffff !important; border-color: #e5e7eb !important; }
        .ui.label { background-color: #f3f0ff !important; color: #7c3aed !important; }
        .ui.green.label { background-color: #ecfdf5 !important; color: #059669 !important; }
        .ui.violet.label { background-color: #f3f0ff !important; color: #7c3aed !important; }
        .ui.teal.label { background-color: #f0fdfa !important; color: #0d9488 !important; }
        .ui.orange.label { background-color: #fff7ed !important; color: #ea580c !important; }
        .ui.blue.label { background-color: #eff6ff !important; color: #2563eb !important; }
        .ui.red.label { background-color: #fef2f2 !important; color: #dc2626 !important; }
        .ui.pink.label { background-color: #fdf2f8 !important; color: #db2777 !important; }
        .ui.yellow.label { background-color: #fffbeb !important; color: #d97706 !important; }
        .ui.message { background-color: #f9fafb !important; color: #374151 !important; border: 1px solid #e5e7eb !important; }
        .ui.divider { border-color: #e5e7eb !important; }
        a { color: #7c3aed !important; }
        a:hover { color: #6d28d9 !important; }
        """
    )
    # Default layout has no band. The idle_band() JS shifts content down at runtime
    # when ?interaction=artex activates the kiosk.
    return rx.el.div(
        fomantic_stylesheets(),
        mui_theme_shim(),
        ws_watchdog(),
        report_libs(),
        global_css,
        idle_band(),
        rx.el.div(
            rx.el.div(
                *children,
                class_name="ui fluid container",
            ),
            id="me-app-content",
            style={
                "marginTop": "0",
                "padding": "1.25rem",
                "minHeight": "100vh",
                "boxSizing": "border-box",
                "backgroundColor": "#f8f9fa",
            },
        ),
        style={"fontFamily": "'Lato', 'Helvetica Neue', Arial, Helvetica, sans-serif"},
    )


def two_column_layout(
    left: rx.Component,
    right: rx.Component,
) -> rx.Component:
    """Two-column layout using flexbox. Left narrow, right wide."""
    column_height = "calc(100vh - 3rem)"
    column_base = {
        "height": column_height,
        "overflowY": "auto",
        "overflowX": "hidden",
        "padding": "16px",
        "backgroundColor": "#ffffff",
        "borderRadius": "6px",
        "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
        "border": "1px solid #e5e7eb",
    }
    divider_style = {
        "width": "1px",
        "backgroundColor": "#e5e7eb",
        "margin": "0 12px",
        "flexShrink": "0",
    }
    return rx.el.div(
        rx.el.div(
            left,
            style={**column_base, "flex": "0 0 30%", "minWidth": "320px", "maxWidth": "420px"},
            id="layout-left-column",
        ),
        rx.el.div(style=divider_style),
        rx.el.div(
            right,
            style={**column_base, "flex": "1 1 70%", "minWidth": "500px"},
            id="layout-right-column",
        ),
        style={
            "display": "flex",
            "flexDirection": "row",
            "gap": "0",
            "width": "100%",
            "alignItems": "stretch",
        },
        id="two-column-layout",
    )
