from __future__ import annotations

import reflex as rx


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
      'position:fixed;top:56px;left:0;right:0;z-index:99999;background:#7c3aed;' +
      'color:#fff;text-align:center;padding:10px 16px;font-size:14px;' +
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


def topbar() -> rx.Component:
    """Top navigation bar — logo only, tabs live in page content."""
    return rx.el.div(
        rx.el.a(
            rx.el.span(
                "Materialized Enhancements",
                style={
                    "fontSize": "1.2rem",
                    "fontWeight": "700",
                    "color": "#7c3aed",
                    "letterSpacing": "0.03em",
                },
            ),
            href="/",
            style={"display": "flex", "alignItems": "center", "textDecoration": "none"},
        ),
        style={
            "position": "fixed",
            "top": "0",
            "left": "0",
            "right": "0",
            "height": "56px",
            "backgroundColor": "#ffffff",
            "borderBottom": "1px solid #e5e7eb",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.06)",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "flex-start",
            "padding": "0 24px",
            "zIndex": "1000",
        },
        id="topbar",
    )


def template(*children: rx.Component) -> rx.Component:
    """Main page template — White Mirror light theme."""
    global_css = rx.el.style(
        """
        body { background-color: #f8f9fa !important; color: #1a1a2e !important; }
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
    return rx.el.div(
        fomantic_stylesheets(),
        ws_watchdog(),
        global_css,
        topbar(),
        rx.el.div(
            rx.el.div(
                *children,
                class_name="ui fluid container",
            ),
            style={
                "marginTop": "56px",
                "padding": "20px",
                "minHeight": "calc(100vh - 56px)",
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
    column_height = "calc(100vh - 96px)"
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
