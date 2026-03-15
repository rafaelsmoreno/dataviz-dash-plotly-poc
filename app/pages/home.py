"""
Home / landing page — links to all dashboard sections.
"""

import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(__name__, path="/", name="Home", order=0)


def _card(title: str, description: str, href: str, color: str) -> dbc.Col:
    return dbc.Col(
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4(title, className="card-title", style={"color": color}),
                        html.P(description, className="card-text text-muted"),
                        dbc.Button(
                            "Open Dashboard",
                            href=href,
                            color="primary",
                            outline=True,
                            size="sm",
                        ),
                    ]
                )
            ],
            className="shadow-sm h-100",
        ),
        md=4,
        className="mb-4",
    )


def layout() -> html.Div:
    return html.Div(
        [
            html.H1("Dash + Plotly POC", className="mb-1"),
            html.P(
                "Six dashboards powered by DuckDB + Parquet/CSV.",
                className="lead text-muted mb-5",
            ),
            dbc.Row(
                [
                    _card(
                        "NYC Yellow Taxi",
                        "January 2024 — 3 M+ trips. KPIs, daily trends, heatmap, payment breakdown, scatter.",
                        "/nyc-taxi",
                        "#3B82F6",
                    ),
                    _card(
                        "NYC Zone Map",
                        "Interactive scatter map of pickup volume by taxi zone, filterable by borough.",
                        "/nyc-zone-map",
                        "#14B8A6",
                    ),
                    _card(
                        "NYC Flows",
                        "Dropoff zone scatter map and top-30 origin→destination pairs, filterable by borough.",
                        "/nyc-flows",
                        "#8B5CF6",
                    ),
                    _card(
                        "World Energy",
                        "OWID energy dataset. Global mix trends 1990–present, top renewable countries, country comparison.",
                        "/world-energy",
                        "#22C55E",
                    ),
                    _card(
                        "Brazil Economy",
                        "World Bank macro indicators — GDP, inflation, unemployment, FX, trade balance.",
                        "/brazil-economy",
                        "#F59E0B",
                    ),
                ]
            ),
        ],
        className="px-4 py-5",
    )
