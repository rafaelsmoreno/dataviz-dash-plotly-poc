"""
World Energy dashboard page.

Charts:
  • Stacked area — global electricity mix share over time (1990–present)
  • Line chart    — absolute generation by source (TWh)
  • Bar chart     — top 20 countries by renewable share (latest year)
  • Grouped bar   — energy mix breakdown for top-10 countries by generation
"""

import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html

from queries import (
    energy_country_mix,
    energy_global_trends,
    energy_top_renewable_countries,
)

dash.register_page(__name__, path="/world-energy", name="World Energy", order=2)

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


def layout() -> html.Div:
    trends = energy_global_trends()
    top20 = energy_top_renewable_countries()
    mix = energy_country_mix()

    # ── Stacked area — share % ────────────────────────────────────────────────
    fig_share = go.Figure()
    source_map = [
        ("fossil_pct", "Fossil", COAL),
        ("nuclear_pct", "Nuclear", NUCLEAR),
        ("hydro_pct", "Hydro", HYDRO),
        ("wind_pct", "Wind", WIND),
        ("solar_pct", "Solar", SOLAR),
        ("renewables_pct", None, None),  # skip — composite
        ("low_carbon_pct", None, None),  # skip — composite
    ]
    for col, label, color in source_map:
        if label is None:
            continue
        fig_share.add_trace(
            go.Scatter(
                x=trends["year"],
                y=trends[col],
                name=label,
                mode="lines",
                line=dict(width=0),
                fill="tonexty" if col != "fossil_pct" else "tozeroy",
                fillcolor=color,
                stackgroup="one",
            )
        )
    fig_share.update_layout(
        title="Global Electricity Mix — Share of Generation (%)",
        xaxis_title="Year",
        yaxis_title="Share (%)",
        template="plotly_white",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=40, r=40, t=60, b=60),
    )

    # ── Line chart — TWh ──────────────────────────────────────────────────────
    fig_twh = go.Figure()
    twh_map = [
        ("coal_twh", "Coal", COAL),
        ("nuclear_twh", "Nuclear", NUCLEAR),
        ("hydro_twh", "Hydro", HYDRO),
        ("wind_twh", "Wind", WIND),
        ("solar_twh", "Solar", SOLAR),
    ]
    for col, label, color in twh_map:
        fig_twh.add_trace(
            go.Scatter(
                x=trends["year"],
                y=trends[col],
                name=label,
                mode="lines",
                line=dict(color=color, width=2),
            )
        )
    fig_twh.update_layout(
        title="Global Electricity Generation by Source (TWh)",
        xaxis_title="Year",
        yaxis_title="TWh",
        template="plotly_white",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=40, r=40, t=60, b=60),
    )

    # ── Top 20 renewable countries ────────────────────────────────────────────
    fig_top20 = px.bar(
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
    fig_top20.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_top20.update_layout(
        template="plotly_white",
        showlegend=False,
        margin=dict(l=120, r=60, t=60, b=40),
        height=520,
    )

    # ── Energy mix — top 10 countries by generation ───────────────────────────
    top10 = mix.head(10)
    mix_cols = [
        "coal_pct",
        "gas_pct",
        "nuclear_pct",
        "hydro_pct",
        "solar_pct",
        "wind_pct",
        "other_renewables_pct",
    ]
    mix_labels = ["Coal", "Gas", "Nuclear", "Hydro", "Solar", "Wind", "Other Renew."]
    mix_colors = [COAL, GAS, NUCLEAR, HYDRO, SOLAR, WIND, OTHER]

    fig_mix = go.Figure()
    for col, label, color in zip(mix_cols, mix_labels, mix_colors):
        fig_mix.add_trace(
            go.Bar(
                x=top10["country"],
                y=top10[col],
                name=label,
                marker_color=color,
            )
        )
    fig_mix.update_layout(
        barmode="stack",
        title="Energy Mix — Top 10 Countries by Generation (latest year)",
        xaxis_title="Country",
        yaxis_title="Share (%)",
        template="plotly_white",
        legend=dict(orientation="h", y=-0.25),
        margin=dict(l=40, r=40, t=60, b=80),
    )

    return html.Div(
        [
            html.H2("World Energy — Global Electricity Mix", className="mb-1"),
            html.P(
                "Source: Our World in Data (OWID Energy Dataset)",
                className="text-muted mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_share), md=12, className="mb-4"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_twh), md=12, className="mb-4"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_top20), md=6, className="mb-4"),
                    dbc.Col(dcc.Graph(figure=fig_mix), md=6, className="mb-4"),
                ]
            ),
        ],
        className="px-4 py-3",
    )
