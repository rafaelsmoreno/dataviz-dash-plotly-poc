"""
World Energy dashboard page.

Charts:
  • Stacked area — global electricity mix share over time (1990–present)
  • Line chart    — absolute generation by source (TWh)
  • Bar chart     — top 20 countries by renewable share (latest year)
  • Grouped bar   — energy mix breakdown for top-10 countries by generation

Interactive filter: year range slider.
  - Affects: stacked area (share %) and TWh line chart.
  - Not affected: top-20 bar and country mix (already fixed to latest year).
"""

import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from queries import (
    energy_country_mix,
    energy_global_trends,
    energy_top_renewable_countries,
)

dash.register_page(__name__, path="/world-energy", name="World Energy", order=3)

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
COAL = "#6B7280"  # grey
GAS = "#F59E0B"  # amber
NUCLEAR = "#8B5CF6"  # purple
HYDRO = "#3B82F6"  # blue
SOLAR = "#FDE047"  # yellow
WIND = "#22C55E"  # green
OTHER = "#14B8A6"  # teal

_GRAPH_CONFIG = {"displayModeBar": False}

_SHARE_SOURCES = [
    ("fossil_pct", "Fossil", COAL),
    ("nuclear_pct", "Nuclear", NUCLEAR),
    ("hydro_pct", "Hydro", HYDRO),
    ("wind_pct", "Wind", WIND),
    ("solar_pct", "Solar", SOLAR),
]

_TWH_SOURCES = [
    ("coal_twh", "Coal", COAL),
    ("nuclear_twh", "Nuclear", NUCLEAR),
    ("hydro_twh", "Hydro", HYDRO),
    ("wind_twh", "Wind", WIND),
    ("solar_twh", "Solar", SOLAR),
]

_MIX_COLS = [
    "coal_pct",
    "gas_pct",
    "nuclear_pct",
    "hydro_pct",
    "solar_pct",
    "wind_pct",
    "other_renewables_pct",
]
_MIX_LABELS = ["Coal", "Gas", "Nuclear", "Hydro", "Solar", "Wind", "Other Renew."]
_MIX_COLORS = [COAL, GAS, NUCLEAR, HYDRO, SOLAR, WIND, OTHER]


# ---------------------------------------------------------------------------
# Figure builders
# ---------------------------------------------------------------------------


def _fig_share(year_min: int, year_max: int) -> go.Figure:
    trends = energy_global_trends()
    subset = trends[(trends["year"] >= year_min) & (trends["year"] <= year_max)]
    fig = go.Figure()
    for col, label, color in _SHARE_SOURCES:
        fig.add_trace(
            go.Scatter(
                x=subset["year"],
                y=subset[col],
                name=label,
                mode="lines",
                line=dict(color=color, width=0),
                fill="tonexty" if col != "fossil_pct" else "tozeroy",
                stackgroup="one",
            )
        )
    fig.update_layout(
        title="Global Electricity Mix — Share of Generation (%)",
        xaxis_title="Year",
        yaxis_title="Share (%)",
        template="plotly_white",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=40, r=40, t=60, b=60),
    )
    return fig


def _fig_twh(year_min: int, year_max: int) -> go.Figure:
    trends = energy_global_trends()
    subset = trends[(trends["year"] >= year_min) & (trends["year"] <= year_max)]
    fig = go.Figure()
    for col, label, color in _TWH_SOURCES:
        fig.add_trace(
            go.Scatter(
                x=subset["year"],
                y=subset[col],
                name=label,
                mode="lines",
                line=dict(color=color, width=2),
            )
        )
    fig.update_layout(
        title="Global Electricity Generation by Source (TWh)",
        xaxis_title="Year",
        yaxis_title="TWh",
        template="plotly_white",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=40, r=40, t=60, b=60),
    )
    return fig


def _fig_top20() -> go.Figure:
    top20 = energy_top_renewable_countries()
    fig = px.bar(
        top20.sort_values("renewables_pct"),
        x="renewables_pct",
        y="country",
        orientation="h",
        color="renewables_pct",
        color_continuous_scale="Greens",
        labels={"renewables_pct": "Renewables %", "country": "Country"},
        title=f"Top 20 Countries by Renewable Share — {int(top20['year'].iloc[0])}",
        text="renewables_pct",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        margin=dict(l=120, r=60, t=60, b=40),
        height=520,
    )
    return fig


def _fig_mix() -> go.Figure:
    mix = energy_country_mix()
    top10 = mix.head(10)
    fig = go.Figure()
    for col, label, color in zip(_MIX_COLS, _MIX_LABELS, _MIX_COLORS):
        fig.add_trace(
            go.Bar(
                x=top10["country"],
                y=top10[col],
                name=label,
                marker_color=color,
            )
        )
    fig.update_layout(
        barmode="stack",
        title="Energy Mix — Top 10 Countries by Generation (latest year)",
        xaxis_title="Country",
        yaxis_title="Share (%)",
        template="plotly_white",
        legend=dict(orientation="h", y=-0.25),
        margin=dict(l=40, r=40, t=60, b=80),
    )
    return fig


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

_YEAR_MIN = 1990
_YEAR_MAX = 2023  # conservative ceiling; actual max determined at runtime


def _year_range() -> tuple[int, int]:
    trends = energy_global_trends()
    return int(trends["year"].min()), int(trends["year"].max())


def layout() -> html.Div:
    try:
        yr_min, yr_max = _year_range()
    except Exception:
        yr_min, yr_max = _YEAR_MIN, _YEAR_MAX

    slider_marks = {y: str(y) for y in range(yr_min, yr_max + 1, 5)}

    filter_row = dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Label(
                            "Filter year range",
                            className="small fw-semibold mb-3",
                        ),
                        dcc.RangeSlider(
                            id="energy-year-slider",
                            min=yr_min,
                            max=yr_max,
                            step=1,
                            value=[yr_min, yr_max],
                            marks=slider_marks,
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ]
                ),
                className="shadow-sm mb-4",
            ),
            md=12,
        )
    )

    return html.Div(
        [
            html.H2("World Energy — Global Electricity Mix", className="mb-1"),
            html.P(
                "Source: Our World in Data (OWID Energy Dataset)",
                className="text-muted mb-4",
            ),
            filter_row,
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        id="energy-graph-share",
                        figure=_fig_share(yr_min, yr_max),
                        config=_GRAPH_CONFIG,
                    ),
                    md=12,
                    className="mb-4",
                )
            ),
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        id="energy-graph-twh",
                        figure=_fig_twh(yr_min, yr_max),
                        config=_GRAPH_CONFIG,
                    ),
                    md=12,
                    className="mb-4",
                )
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            id="energy-graph-top20",
                            figure=_fig_top20(),
                            config=_GRAPH_CONFIG,
                        ),
                        md=6,
                        className="mb-4",
                    ),
                    dbc.Col(
                        dcc.Graph(
                            id="energy-graph-mix",
                            figure=_fig_mix(),
                            config=_GRAPH_CONFIG,
                        ),
                        md=6,
                        className="mb-4",
                    ),
                ]
            ),
        ],
        className="px-4 py-3",
    )


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


@callback(
    Output("energy-graph-share", "figure"),
    Output("energy-graph-twh", "figure"),
    Input("energy-year-slider", "value"),
)
def update_energy_charts(year_range: list[int]) -> tuple:
    yr_min, yr_max = year_range
    return _fig_share(yr_min, yr_max), _fig_twh(yr_min, yr_max)
