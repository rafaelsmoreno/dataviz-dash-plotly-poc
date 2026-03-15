"""
app.py — Dash multi-page application entrypoint.

Layout:
  - Left sidebar navigation (NYC Taxi / World Energy / Brazil Economy)
  - Main content area (dash.page_container)

Run:
  python app.py          (local dev, debug=True)
  gunicorn app:server    (production / Docker)
"""

import sys
from pathlib import Path

# Ensure the app/ directory is on sys.path so pages can import queries.py
sys.path.insert(0, str(Path(__file__).parent))

import dash
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html

app = Dash(
    __name__,
    use_pages=True,
    pages_folder="pages",
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
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
                className="px-3 pt-4 pb-3 border-bottom",
            ),
            dbc.Nav(links, vertical=True, pills=True, className="px-2 pt-2"),
        ],
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
        sidebar(),
        html.Div(
            dash.page_container,
            style={"marginLeft": "220px", "padding": "0"},
        ),
    ],
    style={"display": "flex"},
)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
