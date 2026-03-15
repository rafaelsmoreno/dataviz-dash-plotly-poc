"""
NYC Taxi — January 2024 dashboard page.

Charts mirror the Evidence-POC nyc-taxi section:
  • KPI cards (total trips, revenue, avg fare, avg distance, avg duration, avg tip %)
  • Daily trips + revenue line chart
  • Hourly heatmap (day-of-week × hour)
  • Payment type donut
  • Vendor comparison bar
  • Distance distribution histogram
  • Fare vs. distance scatter (5 000-row sample)
"""

import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html

from queries import (
    nyc_daily_trips,
    nyc_distance_distribution,
    nyc_fare_vs_distance,
    nyc_hourly_patterns,
    nyc_overview_kpis,
    nyc_payment_breakdown,
    nyc_vendor_comparison,
)

dash.register_page(__name__, path="/nyc-taxi", name="NYC Taxi", order=1)

# ---------------------------------------------------------------------------
# Colour palette (consistent with Evidence POC blue tone)
# ---------------------------------------------------------------------------
BLUE = "#3B82F6"
GREEN = "#22C55E"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#8B5CF6"
TEAL = "#14B8A6"
SLATE = "#64748B"

PAYMENT_COLORS = {
    "Credit Card": BLUE,
    "Cash": GREEN,
    "No Charge": AMBER,
    "Dispute": RED,
    "Unknown": SLATE,
    "Voided Trip": PURPLE,
    "Other": TEAL,
}

VENDOR_COLORS = {
    "Creative Mobile Technologies": BLUE,
    "VeriFone Inc.": GREEN,
    "Unknown": SLATE,
}

DAY_ORDER = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


# ---------------------------------------------------------------------------
# Helper — KPI card
# ---------------------------------------------------------------------------


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
# Layout (data loaded at page render, cached by lru_cache in queries.py)
# ---------------------------------------------------------------------------


def layout() -> html.Div:
    kpis = nyc_overview_kpis().iloc[0]
    daily = nyc_daily_trips()
    hourly = nyc_hourly_patterns()
    payment = nyc_payment_breakdown()
    vendor = nyc_vendor_comparison()
    dist = nyc_distance_distribution()
    scatter = nyc_fare_vs_distance()

    # ── KPI cards ────────────────────────────────────────────────────────────
    kpi_row = dbc.Row(
        [
            kpi_card("Total Trips", f"{int(kpis.total_trips):,}", BLUE),
            kpi_card("Total Revenue", f"${kpis.total_revenue:,.0f}", GREEN),
            kpi_card("Avg Fare", f"${kpis.avg_fare:.2f}", AMBER),
            kpi_card("Avg Distance", f"{kpis.avg_distance_miles:.1f} mi", PURPLE),
            kpi_card("Avg Duration", f"{kpis.avg_duration_min:.0f} min", TEAL),
            kpi_card("Avg Tip %", f"{kpis.avg_tip_pct:.1f}%", RED),
        ],
        className="g-3 mb-4",
    )

    # ── Daily trips & revenue ─────────────────────────────────────────────────
    fig_daily = go.Figure()
    fig_daily.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["trips"],
            name="Trips",
            mode="lines+markers",
            line=dict(color=BLUE, width=2),
            marker=dict(size=4),
        )
    )
    fig_daily.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["revenue"],
            name="Revenue ($)",
            mode="lines",
            line=dict(color=GREEN, width=2, dash="dot"),
            yaxis="y2",
        )
    )
    fig_daily.update_layout(
        title="Daily Trips & Revenue — January 2024",
        xaxis_title="Date",
        yaxis=dict(title="Trips", showgrid=False),
        yaxis2=dict(title="Revenue ($)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.12),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
    )

    # ── Hourly heatmap ────────────────────────────────────────────────────────
    pivot = (
        hourly.assign(
            day_name=lambda d: (
                d["day_name"]
                .astype("category")
                .cat.set_categories(DAY_ORDER, ordered=True)
            )
        )
        .sort_values(["day_name", "hour_of_day"])
        .pivot(index="day_name", columns="hour_of_day", values="trips")
        .fillna(0)
    )
    fig_heatmap = px.imshow(
        pivot,
        color_continuous_scale="Blues",
        labels=dict(x="Hour of Day", y="Day of Week", color="Trips"),
        title="Trip Volume Heatmap — Hour × Day of Week",
        aspect="auto",
    )
    fig_heatmap.update_layout(
        template="plotly_white", margin=dict(l=40, r=40, t=60, b=40)
    )

    # ── Payment donut ──────────────────────────────────────────────────────────
    fig_payment = px.pie(
        payment,
        names="payment_type_name",
        values="trips",
        hole=0.45,
        color="payment_type_name",
        color_discrete_map=PAYMENT_COLORS,
        title="Payment Type Breakdown",
    )
    fig_payment.update_traces(textposition="inside", textinfo="percent+label")
    fig_payment.update_layout(
        showlegend=True,
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
    )

    # ── Vendor comparison ──────────────────────────────────────────────────────
    fig_vendor = px.bar(
        vendor,
        x="vendor_name",
        y=["trips", "avg_fare", "avg_distance"],
        barmode="group",
        color_discrete_sequence=[BLUE, GREEN, AMBER],
        title="Vendor Comparison",
        labels={"value": "Value", "variable": "Metric", "vendor_name": "Vendor"},
    )
    fig_vendor.update_layout(
        template="plotly_white", margin=dict(l=40, r=40, t=60, b=40)
    )

    # ── Distance distribution ─────────────────────────────────────────────────
    fig_dist = px.bar(
        dist,
        x="distance_bucket_miles",
        y="trips",
        color="avg_fare",
        color_continuous_scale="Blues",
        labels={
            "distance_bucket_miles": "Distance (miles)",
            "trips": "Trips",
            "avg_fare": "Avg Fare ($)",
        },
        title="Trip Distance Distribution",
    )
    fig_dist.update_layout(template="plotly_white", margin=dict(l=40, r=40, t=60, b=40))

    # ── Fare vs. distance scatter ──────────────────────────────────────────────
    fig_scatter = px.scatter(
        scatter,
        x="trip_distance",
        y="fare_amount",
        color="payment_type_name",
        color_discrete_map=PAYMENT_COLORS,
        opacity=0.5,
        size_max=6,
        labels={
            "trip_distance": "Distance (miles)",
            "fare_amount": "Fare ($)",
            "payment_type_name": "Payment",
        },
        title="Fare vs. Distance (5 000-row sample)",
        hover_data=["tip_amount", "total_amount", "trip_duration_min"],
    )
    fig_scatter.update_layout(
        template="plotly_white", margin=dict(l=40, r=40, t=60, b=40)
    )

    # ── Assemble page ──────────────────────────────────────────────────────────
    return html.Div(
        [
            html.H2("NYC Yellow Taxi — January 2024", className="mb-1"),
            html.P(
                f"Source: NYC TLC  •  {int(kpis.days_in_dataset)} days  •  {int(kpis.total_trips):,} trips",
                className="text-muted mb-4",
            ),
            kpi_row,
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_daily), md=12, className="mb-4"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_heatmap), md=12, className="mb-4"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_payment), md=5, className="mb-4"),
                    dbc.Col(dcc.Graph(figure=fig_vendor), md=7, className="mb-4"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_dist), md=6, className="mb-4"),
                    dbc.Col(dcc.Graph(figure=fig_scatter), md=6, className="mb-4"),
                ]
            ),
        ],
        className="px-4 py-3",
    )
