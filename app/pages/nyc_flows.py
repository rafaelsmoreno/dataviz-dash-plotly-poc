"""
NYC Taxi Trip Flows — January 2024.

Sections:
  • Dropoff zone scatter map — one bubble per zone, sized by dropoff volume.
  • Top-30 origin→destination pairs — horizontal bar chart.

Interactive filter: borough multi-select (same as zone map pickup page).
  - Affects the dropoff map (zooms and filters bubbles).
  - O/D chart always shows the top-30 across all boroughs (no meaningful per-borough slice).
"""

import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from queries import nyc_top_od_pairs, nyc_zone_dropoff_map

dash.register_page(__name__, path="/nyc-flows", name="NYC Flows", order=3)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BOROUGH_ORDER = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island", "EWR"]

_GRAPH_CONFIG = {"displayModeBar": True, "scrollZoom": True}
_DEFAULT_CENTER = {"lat": 40.7128, "lon": -74.006}
_DEFAULT_ZOOM = 10

# Colour palette consistent with other NYC pages
BLUE = "#3B82F6"
GREEN = "#22C55E"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#8B5CF6"
TEAL = "#14B8A6"
SLATE = "#64748B"

_BOROUGH_COLORS = {
    "Manhattan": BLUE,
    "Brooklyn": GREEN,
    "Queens": AMBER,
    "Bronx": RED,
    "Staten Island": PURPLE,
    "EWR": SLATE,
}


# ---------------------------------------------------------------------------
# Figure builders
# ---------------------------------------------------------------------------


def _fig_dropoff_map(selected_boroughs: list[str]) -> go.Figure:
    df = nyc_zone_dropoff_map()
    if selected_boroughs:
        df = df[df["borough"].isin(selected_boroughs)]
    df = df[df["trips"] > 0].copy()

    if not df.empty:
        lat_center = df["lat"].mean()
        lon_center = df["lon"].mean()
        max_range = max(
            df["lat"].max() - df["lat"].min(), df["lon"].max() - df["lon"].min()
        )
        zoom = (
            13
            if max_range < 0.05
            else 12
            if max_range < 0.1
            else 11
            if max_range < 0.2
            else 10
            if max_range < 0.5
            else 9
        )
        center = {"lat": lat_center, "lon": lon_center}
    else:
        center, zoom = _DEFAULT_CENTER, _DEFAULT_ZOOM

    fig = px.scatter_map(
        df,
        lat="lat",
        lon="lon",
        size="trips",
        color="avg_fare",
        color_continuous_scale="Plasma",
        size_max=40,
        zoom=zoom,
        center=center,
        map_style="open-street-map",
        hover_name="zone",
        hover_data={
            "borough": True,
            "trips": ":,",
            "avg_fare": ":.2f",
            "avg_tip_pct": ":.1f",
            "lat": False,
            "lon": False,
        },
        labels={
            "avg_fare": "Avg Fare ($)",
            "trips": "Dropoffs",
            "avg_tip_pct": "Avg Tip %",
            "borough": "Borough",
        },
        title="NYC Taxi Dropoff Volume by Zone — January 2024",
    )
    fig.update_layout(
        coloraxis_colorbar=dict(title="Avg Fare ($)"),
        margin=dict(l=0, r=0, t=50, b=0),
        height=600,
    )
    return fig


def _fig_od_pairs() -> go.Figure:
    od = nyc_top_od_pairs()
    od["pair"] = od["pu_zone"] + " → " + od["do_zone"]
    od = od.sort_values("trips")

    fig = px.bar(
        od,
        x="trips",
        y="pair",
        orientation="h",
        color="avg_fare",
        color_continuous_scale="Blues",
        hover_data={"avg_fare": ":.2f", "avg_distance": ":.1f"},
        labels={
            "trips": "Trips",
            "pair": "Origin → Destination",
            "avg_fare": "Avg Fare ($)",
            "avg_distance": "Avg Distance (mi)",
        },
        title="Top 30 Origin → Destination Pairs",
    )
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        margin=dict(l=260, r=60, t=60, b=40),
        height=700,
        coloraxis_colorbar=dict(title="Avg Fare ($)"),
    )
    return fig


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def layout() -> html.Div:
    df = nyc_zone_dropoff_map()
    total_dropoffs = int(df["trips"].sum())
    active_zones = int((df["trips"] > 0).sum())

    filter_row = dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Label(
                            "Filter dropoff map by borough",
                            className="small fw-semibold mb-2",
                        ),
                        dcc.Checklist(
                            id="flows-borough-filter",
                            options=[
                                {"label": f"  {b}", "value": b} for b in BOROUGH_ORDER
                            ],
                            value=BOROUGH_ORDER,
                            inline=True,
                            inputStyle={"marginRight": "4px"},
                            labelStyle={"marginRight": "16px", "fontSize": "0.85rem"},
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
            html.H2("NYC Taxi Trip Flows — January 2024", className="mb-1"),
            html.P(
                f"Source: NYC TLC  •  {active_zones} active dropoff zones  •  {total_dropoffs:,} total dropoffs",
                className="text-muted mb-4",
            ),
            filter_row,
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        id="flows-dropoff-map",
                        figure=_fig_dropoff_map(BOROUGH_ORDER),
                        config=_GRAPH_CONFIG,
                    ),
                    md=12,
                    className="mb-4",
                )
            ),
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        id="flows-od-chart",
                        figure=_fig_od_pairs(),
                        config={"displayModeBar": False},
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
    Output("flows-dropoff-map", "figure"),
    Input("flows-borough-filter", "value"),
)
def update_flows_map(selected_boroughs: list[str]) -> go.Figure:
    return _fig_dropoff_map(selected_boroughs or BOROUGH_ORDER)
