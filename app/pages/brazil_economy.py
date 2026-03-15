"""
Brazil Economy dashboard page.

Charts:
  • GDP (billion USD) bar chart with line for GDP per capita (dual axis)
  • Inflation & unemployment dual-axis line chart
  • USD/BRL exchange rate line chart
  • Trade balance (exports, imports, balance) stacked/grouped bar

Interactive filter: year range slider.
  - Affects: all four charts.
"""

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from queries import brazil_macro

dash.register_page(__name__, path="/brazil-economy", name="Brazil Economy", order=5)

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
BLUE = "#3B82F6"
GREEN = "#22C55E"
RED = "#EF4444"
AMBER = "#F59E0B"
PURPLE = "#8B5CF6"
TEAL = "#14B8A6"

_GRAPH_CONFIG = {"displayModeBar": False}


def kpi_card(label: str, value: str, color: str = BLUE) -> dbc.Col:
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.P(label, className="text-muted small mb-1"),
                    html.H4(value, style={"color": color, "fontWeight": "700"}),
                ]
            ),
            className="shadow-sm h-100",
        ),
        xs=6,
        sm=4,
        md=2,
    )


# ---------------------------------------------------------------------------
# Figure builders
# ---------------------------------------------------------------------------


def _fig_gdp(df) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["year"],
            y=df["gdp_billion_usd"],
            name="GDP (B USD)",
            marker_color=BLUE,
            opacity=0.75,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["gdp_per_capita_usd"],
            name="GDP per Capita (USD)",
            mode="lines+markers",
            line=dict(color=GREEN, width=2),
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="Brazil GDP — Billion USD & Per Capita",
        xaxis_title="Year",
        yaxis=dict(title="GDP (B USD)", showgrid=False),
        yaxis2=dict(
            title="GDP per Capita (USD)", overlaying="y", side="right", showgrid=False
        ),
        legend=dict(orientation="h", y=1.12),
        template="plotly_white",
        margin=dict(l=40, r=60, t=60, b=40),
    )
    return fig


def _fig_inf(df) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["inflation_pct"],
            name="Inflation (%)",
            mode="lines+markers",
            line=dict(color=RED, width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["unemployment_pct"],
            name="Unemployment (%)",
            mode="lines+markers",
            line=dict(color=AMBER, width=2, dash="dot"),
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="Brazil Inflation & Unemployment",
        xaxis_title="Year",
        yaxis=dict(title="Inflation (%)", showgrid=False),
        yaxis2=dict(
            title="Unemployment (%)", overlaying="y", side="right", showgrid=False
        ),
        legend=dict(orientation="h", y=1.12),
        template="plotly_white",
        margin=dict(l=40, r=60, t=60, b=40),
    )
    return fig


def _fig_fx(df) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["usd_brl_rate"],
            name="USD/BRL",
            mode="lines+markers",
            fill="tozeroy",
            line=dict(color=PURPLE, width=2),
            fillcolor="rgba(139,92,246,0.15)",
        )
    )
    fig.update_layout(
        title="USD / BRL Exchange Rate",
        xaxis_title="Year",
        yaxis_title="BRL per 1 USD",
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def _fig_trade(df) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["year"],
            y=df["exports_billion_usd"],
            name="Exports",
            marker_color=GREEN,
            opacity=0.85,
        )
    )
    fig.add_trace(
        go.Bar(
            x=df["year"],
            y=df["imports_billion_usd"],
            name="Imports",
            marker_color=RED,
            opacity=0.85,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["trade_balance_billion_usd"],
            name="Trade Balance",
            mode="lines+markers",
            line=dict(color=BLUE, width=2),
            yaxis="y",
        )
    )
    fig.update_layout(
        barmode="group",
        title="Brazil Trade: Exports, Imports & Balance (B USD)",
        xaxis_title="Year",
        yaxis_title="Billion USD",
        legend=dict(orientation="h", y=1.12),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def layout() -> html.Div:
    df = brazil_macro()
    latest = df.iloc[-1]
    yr_min = int(df["year"].min())
    yr_max = int(df["year"].max())

    kpi_row = dbc.Row(
        [
            kpi_card("GDP (latest)", f"${latest.gdp_billion_usd:.0f}B", BLUE),
            kpi_card("GDP per capita", f"${latest.gdp_per_capita_usd:,.0f}", GREEN),
            kpi_card("Inflation", f"{latest.inflation_pct:.1f}%", RED),
            kpi_card("Unemployment", f"{latest.unemployment_pct:.1f}%", AMBER),
            kpi_card("USD/BRL", f"{latest.usd_brl_rate:.2f}", PURPLE),
            kpi_card(
                "Trade Balance", f"${latest.trade_balance_billion_usd:.1f}B", TEAL
            ),
        ],
        className="g-3 mb-4",
    )

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
                            id="brazil-year-slider",
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
            html.H2("Brazil Economy — Macro Indicators", className="mb-1"),
            html.P("Source: World Bank Open Data API", className="text-muted mb-4"),
            kpi_row,
            filter_row,
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        id="brazil-graph-gdp",
                        figure=_fig_gdp(df),
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
                            id="brazil-graph-inf",
                            figure=_fig_inf(df),
                            config=_GRAPH_CONFIG,
                        ),
                        md=6,
                        className="mb-4",
                    ),
                    dbc.Col(
                        dcc.Graph(
                            id="brazil-graph-fx",
                            figure=_fig_fx(df),
                            config=_GRAPH_CONFIG,
                        ),
                        md=6,
                        className="mb-4",
                    ),
                ]
            ),
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        id="brazil-graph-trade",
                        figure=_fig_trade(df),
                        config=_GRAPH_CONFIG,
                    ),
                    md=12,
                    className="mb-4",
                )
            ),
        ],
        className="px-4 py-3",
    )


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


@callback(
    Output("brazil-graph-gdp", "figure"),
    Output("brazil-graph-inf", "figure"),
    Output("brazil-graph-fx", "figure"),
    Output("brazil-graph-trade", "figure"),
    Input("brazil-year-slider", "value"),
)
def update_brazil_charts(year_range: list[int]) -> tuple:
    yr_min, yr_max = year_range
    df = brazil_macro()
    subset = df[(df["year"] >= yr_min) & (df["year"] <= yr_max)]
    return (
        _fig_gdp(subset),
        _fig_inf(subset),
        _fig_fx(subset),
        _fig_trade(subset),
    )
