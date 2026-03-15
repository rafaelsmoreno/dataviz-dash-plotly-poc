"""
app.py — Dash multi-page application entrypoint.

Layout:
  - Left sidebar navigation with dark mode toggle
  - Main content area (dash.page_container)

Run:
  python app.py          (local dev, debug=True)
  gunicorn app:server    (production / Docker)

Dark mode:
  A Bootstrap theme swap is implemented via a clientside callback that rewrites
  the href of the Bootstrap CSS <link> element between FLATLY (light) and DARKLY
  (dark). No extra packages required. Plotly figures keep plotly_white template;
  the Bootstrap dark theme styles the page chrome, cards, and sidebar.
"""

import sys
from pathlib import Path

# Ensure the app/ directory is on sys.path so pages can import queries.py
sys.path.insert(0, str(Path(__file__).parent))

import dash
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, clientside_callback, dcc, html

# Theme URLs referenced by the dark-mode clientside callback
_THEME_LIGHT = dbc.themes.FLATLY
_THEME_DARK = dbc.themes.DARKLY

app = Dash(
    __name__,
    use_pages=True,
    pages_folder="pages",
    external_stylesheets=[_THEME_LIGHT, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Dash + Plotly POC",
)

server = app.server  # expose for gunicorn

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

NAV_LINKS = [
    {"label": "Home", "href": "/", "icon": "bi-house"},
    {"label": "NYC Taxi", "href": "/nyc-taxi", "icon": "bi-taxi-front"},
    {"label": "NYC Zone Map", "href": "/nyc-zone-map", "icon": "bi-map"},
    {"label": "NYC Flows", "href": "/nyc-flows", "icon": "bi-arrow-left-right"},
    {"label": "World Energy", "href": "/world-energy", "icon": "bi-lightning-charge"},
    {"label": "Brazil Economy", "href": "/brazil-economy", "icon": "bi-graph-up"},
]


def sidebar() -> html.Div:
    links = []
    for item in NAV_LINKS:
        links.append(
            dbc.NavLink(
                [html.I(className=f"{item['icon']} me-2"), item["label"]],
                href=item["href"],
                active="exact",
                className="py-2 px-3",
            )
        )
    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        "Dash", style={"fontWeight": "800", "fontSize": "1.25rem"}
                    ),
                    html.Span(" POC", className="text-muted"),
                ],
                className="px-3 pt-4 pb-2 border-bottom",
            ),
            dbc.Nav(links, vertical=True, pills=True, className="px-2 pt-2"),
            # Dark mode toggle at the bottom of the sidebar
            html.Div(
                [
                    html.I(className="bi-sun me-2", style={"fontSize": "0.85rem"}),
                    dbc.Switch(
                        id="dark-mode-switch",
                        value=False,
                        className="d-inline-block",
                        style={"transform": "scale(0.85)"},
                    ),
                    html.I(className="bi-moon ms-1", style={"fontSize": "0.85rem"}),
                ],
                className="px-3 py-3 border-top d-flex align-items-center",
                style={"position": "absolute", "bottom": 0, "width": "220px"},
            ),
        ],
        id="sidebar",
        style={
            "width": "220px",
            "minHeight": "100vh",
            "backgroundColor": "#f8fafc",
            "borderRight": "1px solid #e2e8f0",
            "position": "fixed",
            "top": 0,
            "left": 0,
            "overflowY": "auto",
        },
    )


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------

app.layout = html.Div(
    [
        # dcc.Store persists the theme preference across page navigation
        dcc.Store(id="theme-store", storage_type="local", data="light"),
        sidebar(),
        html.Div(
            dash.page_container,
            style={"marginLeft": "220px", "padding": "0"},
        ),
    ],
    style={"display": "flex"},
)

# ---------------------------------------------------------------------------
# Dark mode — clientside callback (no Python round-trip)
# ---------------------------------------------------------------------------

clientside_callback(
    """
    function(dark_mode) {
        // Find the Bootstrap theme <link> element (first external stylesheet)
        var links = document.querySelectorAll('link[rel="stylesheet"]');
        var themeLight = '"""
    + _THEME_LIGHT
    + """';
        var themeDark  = '"""
    + _THEME_DARK
    + """';
        for (var i = 0; i < links.length; i++) {
            if (links[i].href.indexOf('bootstrap') !== -1 ||
                links[i].href === themeLight || links[i].href === themeDark) {
                links[i].href = dark_mode ? themeDark : themeLight;
                break;
            }
        }
        // Sync sidebar background
        var sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.style.backgroundColor = dark_mode ? '#1a1a2e' : '#f8fafc';
            sidebar.style.borderRight = dark_mode
                ? '1px solid #2d2d44' : '1px solid #e2e8f0';
        }
        return dark_mode ? 'dark' : 'light';
    }
    """,
    Output("theme-store", "data"),
    Input("dark-mode-switch", "value"),
)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
