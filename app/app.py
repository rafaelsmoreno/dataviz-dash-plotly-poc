"""
app.py — Dash multi-page application entrypoint.

Layout:
  - Left sidebar navigation with collapsible NYC group and dark mode toggle
  - Main content area (dash.page_container)

Run:
  python app.py          (local dev, debug=True)
  gunicorn app:server    (production / Docker)

Dark mode:
  Dark mode is the default. A Bootstrap theme swap is implemented via a
  clientside callback that rewrites the href of the Bootstrap CSS <link> element
  between DARKLY (dark, default) and FLATLY (light). A second clientside callback
  calls Plotly.relayout on all rendered charts to swap the Plotly template.
  Preference is persisted in localStorage via dcc.Store.

NYC group:
  The three NYC pages (NYC Taxi, NYC Zone Map, NYC Flows) are grouped under a
  collapsible "NYC" parent entry in the sidebar. State is toggled by a callback
  and defaults to expanded.
"""

import sys
from pathlib import Path

# Ensure the app/ directory is on sys.path so pages can import queries.py
sys.path.insert(0, str(Path(__file__).parent))

import dash
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, State, clientside_callback, dcc, html

# Dark is the default theme; FLATLY is the light alternative
_THEME_DARK = dbc.themes.DARKLY
_THEME_LIGHT = dbc.themes.FLATLY

_SIDEBAR_BG_DARK = "#1a1a2e"
_SIDEBAR_BG_LIGHT = "#f8fafc"
_SIDEBAR_BR_DARK = "1px solid #2d2d44"
_SIDEBAR_BR_LIGHT = "1px solid #e2e8f0"

app = Dash(
    __name__,
    use_pages=True,
    pages_folder="pages",
    # Start with DARKLY so the page renders dark before any JS runs (no flash)
    external_stylesheets=[_THEME_DARK, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Dash + Plotly POC",
)

server = app.server  # expose for gunicorn

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

_NYC_CHILDREN = [
    {"label": "NYC Taxi", "href": "/nyc-taxi", "icon": "bi-taxi-front"},
    {"label": "NYC Zone Map", "href": "/nyc-zone-map", "icon": "bi-map"},
    {"label": "NYC Flows", "href": "/nyc-flows", "icon": "bi-arrow-left-right"},
]

_OTHER_LINKS = [
    {"label": "World Energy", "href": "/world-energy", "icon": "bi-lightning-charge"},
    {"label": "Brazil Economy", "href": "/brazil-economy", "icon": "bi-graph-up"},
]


def sidebar() -> html.Div:
    # NYC collapsible group
    nyc_children_nav = dbc.Nav(
        [
            dbc.NavLink(
                [html.I(className=f"{item['icon']} me-2"), item["label"]],
                href=item["href"],
                active="exact",
                className="py-2 px-3 ps-4",  # extra left-indent for children
            )
            for item in _NYC_CHILDREN
        ],
        vertical=True,
        pills=True,
    )

    nyc_group = html.Div(
        [
            # Parent row — clicking toggles the collapse
            html.Div(
                [
                    html.I(className="bi-geo-alt me-2"),
                    html.Span("NYC", style={"flex": "1"}),
                    html.I(
                        className="bi-chevron-down",
                        id="nyc-chevron",
                        style={"fontSize": "0.75rem", "transition": "transform 0.2s"},
                    ),
                ],
                id="nyc-group-toggle",
                className="d-flex align-items-center py-2 px-3 rounded",
                style={"cursor": "pointer", "userSelect": "none", "fontSize": "0.9rem"},
                n_clicks=0,
            ),
            dbc.Collapse(
                nyc_children_nav,
                id="nyc-collapse",
                is_open=True,  # expanded by default
            ),
        ]
    )

    other_links = dbc.Nav(
        [
            dbc.NavLink(
                [html.I(className=f"{item['icon']} me-2"), item["label"]],
                href=item["href"],
                active="exact",
                className="py-2 px-3",
            )
            for item in _OTHER_LINKS
        ],
        vertical=True,
        pills=True,
    )

    home_link = dbc.Nav(
        [
            dbc.NavLink(
                [html.I(className="bi-house me-2"), "Home"],
                href="/",
                active="exact",
                className="py-2 px-3",
            )
        ],
        vertical=True,
        pills=True,
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
            html.Div(
                [home_link, nyc_group, other_links],
                className="px-2 pt-2",
            ),
            # Dark mode toggle at the bottom of the sidebar
            html.Div(
                [
                    html.I(className="bi-sun me-2", style={"fontSize": "0.85rem"}),
                    dbc.Switch(
                        id="dark-mode-switch",
                        value=True,  # dark by default
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
            "backgroundColor": _SIDEBAR_BG_DARK,  # dark by default
            "borderRight": _SIDEBAR_BR_DARK,
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
        # theme-store persists Bootstrap theme preference (localStorage)
        dcc.Store(id="theme-store", storage_type="local", data="dark"),
        # plotly-theme-store is a dummy output for the Plotly relayout callback
        dcc.Store(id="plotly-theme-store", data="dark"),
        sidebar(),
        html.Div(
            dash.page_container,
            style={"marginLeft": "220px", "padding": "0"},
        ),
    ],
    style={"display": "flex"},
)

# ---------------------------------------------------------------------------
# NYC collapse toggle
# ---------------------------------------------------------------------------


@app.callback(
    Output("nyc-collapse", "is_open"),
    Output("nyc-chevron", "style"),
    Input("nyc-group-toggle", "n_clicks"),
    State("nyc-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_nyc_group(n_clicks, is_open):
    new_open = not is_open
    chevron_style = {
        "fontSize": "0.75rem",
        "transition": "transform 0.2s",
        "transform": "rotate(0deg)" if new_open else "rotate(-90deg)",
    }
    return new_open, chevron_style


# ---------------------------------------------------------------------------
# Dark mode — two clientside callbacks (no Python round-trip)
# ---------------------------------------------------------------------------

# Callback 1: swap Bootstrap CSS link + sync sidebar styling
clientside_callback(
    """
    function(dark_mode) {
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
        var sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.style.backgroundColor = dark_mode
                ? '"""
    + _SIDEBAR_BG_DARK
    + """'
                : '"""
    + _SIDEBAR_BG_LIGHT
    + """';
            sidebar.style.borderRight = dark_mode
                ? '"""
    + _SIDEBAR_BR_DARK
    + """'
                : '"""
    + _SIDEBAR_BR_LIGHT
    + """';
        }
        return dark_mode ? 'dark' : 'light';
    }
    """,
    Output("theme-store", "data"),
    Input("dark-mode-switch", "value"),
)

# Callback 2: update Plotly chart templates to match the Bootstrap theme
clientside_callback(
    """
    function(dark_mode) {
        var template = dark_mode ? 'plotly_dark' : 'plotly_white';
        setTimeout(function() {
            var graphs = document.querySelectorAll('.js-plotly-plot');
            graphs.forEach(function(g) {
                try { Plotly.relayout(g, {'template': template}); } catch(e) {}
            });
        }, 50);
        return dark_mode ? 'dark' : 'light';
    }
    """,
    Output("plotly-theme-store", "data"),
    Input("dark-mode-switch", "value"),
)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
