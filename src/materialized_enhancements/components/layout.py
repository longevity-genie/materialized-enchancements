from __future__ import annotations

import reflex as rx


def fomantic_icon(
    name: str,
    size: int | str | None = None,
    color: str | None = None,
    style: dict | None = None,
) -> rx.Component:
    """
    Fomantic UI icon component.
    Replaces rx.icon because Lucide icons often fail to load or give warnings.
    """
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


def _nav_tab(
    label: str,
    icon_name: str,
    href: str,
    is_active: rx.Var,
) -> rx.Component:
    """Navigation tab for the topbar with reactive active state."""
    base_style = {
        "display": "flex",
        "alignItems": "center",
        "padding": "6px 16px",
        "borderRadius": "4px",
        "fontSize": "0.95rem",
        "textDecoration": "none",
        "transition": "all 0.15s ease",
        "cursor": "pointer",
    }
    return rx.el.a(
        fomantic_icon(icon_name, size=16),
        rx.el.span(label, style={"marginLeft": "6px"}),
        href=href,
        style=base_style,
        class_name=rx.cond(
            is_active,
            "nav-tab nav-tab-active",
            "nav-tab",
        ),
    )


def topbar() -> rx.Component:
    """Top navigation bar with page tabs."""
    current_path = rx.State.router.page.path
    nav_tab_css = rx.el.style(
        """
        .nav-tab { color: #555; font-weight: 500; }
        .nav-tab:hover { background-color: #1a0a2e; color: #c084fc; }
        .nav-tab-active { background-color: #2d1b69 !important; color: #e879f9 !important; font-weight: 600 !important; }
        """
    )
    return rx.el.div(
        nav_tab_css,
        # Left: Logo / title
        rx.el.div(
            rx.el.a(
                rx.el.span(
                    "Materialized Enhancements",
                    style={
                        "fontSize": "1.2rem",
                        "fontWeight": "700",
                        "color": "#e879f9",
                        "letterSpacing": "0.03em",
                    },
                ),
                href="/",
                style={"display": "flex", "alignItems": "center", "textDecoration": "none"},
            ),
            style={"display": "flex", "alignItems": "center", "flex": "0 0 auto"},
        ),
        # Center: Navigation tabs
        rx.el.div(
            _nav_tab("Gene Library", "dna", "/", current_path == "/"),
            _nav_tab("Compose", "sparkles", "/compose", current_path == "/compose"),
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "8px",
                "flex": "1 1 auto",
                "justifyContent": "center",
            },
        ),
        # Right: spacer
        rx.el.div(style={"width": "80px", "flex": "0 0 80px"}),
        style={
            "position": "fixed",
            "top": "0",
            "left": "0",
            "right": "0",
            "height": "56px",
            "backgroundColor": "#0d0221",
            "borderBottom": "1px solid #3b1a6e",
            "boxShadow": "0 1px 6px rgba(200,100,255,0.15)",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "padding": "0 24px",
            "zIndex": "1000",
        },
        id="topbar",
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


def template(*children: rx.Component) -> rx.Component:
    """Main page template with dark biopunk styling."""
    global_css = rx.el.style(
        """
        body { background-color: #0d0221 !important; color: #e2d9f3 !important; }
        .ui.segment { background-color: #150535 !important; border-color: #3b1a6e !important; color: #e2d9f3 !important; }
        .ui.raised.segment { box-shadow: 0 2px 8px rgba(200,100,255,0.15) !important; }
        .ui.button { background-color: #2d1b69 !important; color: #e879f9 !important; border: 1px solid #7c3aed !important; }
        .ui.primary.button { background-color: #7c3aed !important; color: #fff !important; }
        .ui.top.attached.tabular.menu { background-color: #0d0221 !important; border-color: #3b1a6e !important; }
        .ui.top.attached.tabular.menu .item { color: #a78bfa !important; }
        .ui.top.attached.tabular.menu .active.item { background-color: #150535 !important; color: #e879f9 !important; border-color: #7c3aed !important; }
        .ui.bottom.attached.segment { background-color: #150535 !important; border-color: #3b1a6e !important; }
        .ui.label { background-color: #2d1b69 !important; color: #c084fc !important; }
        .ui.green.label { background-color: #065f46 !important; color: #6ee7b7 !important; }
        .ui.violet.label { background-color: #4c1d95 !important; color: #ddd6fe !important; }
        .ui.teal.label { background-color: #134e4a !important; color: #5eead4 !important; }
        .ui.orange.label { background-color: #7c2d12 !important; color: #fdba74 !important; }
        .ui.blue.label { background-color: #1e3a5f !important; color: #93c5fd !important; }
        .ui.red.label { background-color: #7f1d1d !important; color: #fca5a5 !important; }
        .ui.pink.label { background-color: #831843 !important; color: #f9a8d4 !important; }
        a { color: #a78bfa !important; }
        a:hover { color: #e879f9 !important; }
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
                "backgroundColor": "#0d0221",
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
        "backgroundColor": "#150535",
        "borderRadius": "6px",
        "boxShadow": "0 1px 4px rgba(200,100,255,0.12)",
        "border": "1px solid #3b1a6e",
    }
    divider_style = {
        "width": "1px",
        "backgroundColor": "#3b1a6e",
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
