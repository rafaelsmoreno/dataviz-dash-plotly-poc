"""
Brazil Economy dashboard page.

Charts:
  • GDP (billion USD) bar chart with line for GDP per capita (dual axis)
  • Inflation & unemployment dual-axis line chart
  • USD/BRL exchange rate line chart
  • Trade balance (exports, imports, balance) stacked/grouped bar
"""

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html

from queries import brazil_macro

dash.register_page(__name__, path="/brazil-economy", name="Brazil Economy", order=3)

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
BLUE = "#3B82F6"
GREEN = "#22C55E"
RED = "#EF4444"
AMBER = "#F59E0B"
PURPLE = "#8B5CF6"
TEAL = "#14B8A6"


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


def layout() -> html.Div:
    df = brazil_macro()
    latest = df.iloc[-1]

    # ── KPI cards ─────────────────────────────────────────────────────────────
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

    # ── GDP chart ──────────────────────────────────────────────────────────────
    fig_gdp = go.Figure()
    fig_gdp.add_trace(
        go.Bar(
            x=df["year"],
            y=df["gdp_billion_usd"],
            name="GDP (B USD)",
            marker_color=BLUE,
            opacity=0.75,
        )
    )
    fig_gdp.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["gdp_per_capita_usd"],
            name="GDP per Capita (USD)",
            mode="lines+markers",
            line=dict(color=GREEN, width=2),
            yaxis="y2",
        )
    )
    fig_gdp.update_layout(
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

    # ── Inflation & unemployment ───────────────────────────────────────────────
    fig_inf = go.Figure()
    fig_inf.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["inflation_pct"],
            name="Inflation (%)",
            mode="lines+markers",
            line=dict(color=RED, width=2),
        )
    )
    fig_inf.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["unemployment_pct"],
            name="Unemployment (%)",
            mode="lines+markers",
            line=dict(color=AMBER, width=2, dash="dot"),
            yaxis="y2",
        )
    )
    fig_inf.update_layout(
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

    # ── USD/BRL rate ──────────────────────────────────────────────────────────
    fig_fx = go.Figure()
    fig_fx.add_trace(
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
    fig_fx.update_layout(
        title="USD / BRL Exchange Rate",
        xaxis_title="Year",
        yaxis_title="BRL per 1 USD",
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
    )

    # ── Trade balance ──────────────────────────────────────────────────────────
    fig_trade = go.Figure()
    fig_trade.add_trace(
        go.Bar(
            x=df["year"],
            y=df["exports_billion_usd"],
            name="Exports",
            marker_color=GREEN,
            opacity=0.85,
        )
    )
    fig_trade.add_trace(
        go.Bar(
            x=df["year"],
            y=df["imports_billion_usd"],
            name="Imports",
            marker_color=RED,
            opacity=0.85,
        )
    )
    fig_trade.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["trade_balance_billion_usd"],
            name="Trade Balance",
            mode="lines+markers",
            line=dict(color=BLUE, width=2),
            yaxis="y",
        )
    )
    fig_trade.update_layout(
        barmode="group",
        title="Brazil Trade: Exports, Imports & Balance (B USD)",
        xaxis_title="Year",
        yaxis_title="Billion USD",
        legend=dict(orientation="h", y=1.12),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return html.Div(
        [
            html.H2("Brazil Economy — Macro Indicators", className="mb-1"),
            html.P("Source: World Bank Open Data API", className="text-muted mb-4"),
            kpi_row,
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_gdp), md=12, className="mb-4"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_inf), md=6, className="mb-4"),
                    dbc.Col(dcc.Graph(figure=fig_fx), md=6, className="mb-4"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_trade), md=12, className="mb-4"),
                ]
            ),
        ],
        className="px-4 py-3",
    )
