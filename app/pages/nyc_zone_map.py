"""
NYC Taxi Zone Map — January 2024.

Mirrors the Evidence-POC PointMap page.

Charts:
  • scatter_map (OpenStreetMap) — one bubble per taxi zone, sized by trip volume,
    coloured by average fare. Hover shows zone name, borough, trips, avg fare, avg tip %.
  • ag-grid table — zone-level pickup summary, sortable and filterable client-side.

Interactive filter: borough multi-select (All / Manhattan / Brooklyn / Queens / Bronx /
Staten Island / EWR). Both map and table react to the filter.

No Mapbox token required — uses open-street-map tile layer (Plotly >= 5.18).
"""

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from queries import nyc_zone_pickup_map

dash.register_page(__name__, path="/nyc-zone-map", name="NYC Zone Map", order=2)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BOROUGH_ORDER = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island", "EWR"]

_GRAPH_CONFIG = {"displayModeBar": True, "scrollZoom": True}

# Default map centre — NYC
_DEFAULT_CENTER = {"lat": 40.7128, "lon": -74.006}
_DEFAULT_ZOOM = 10

# ---------------------------------------------------------------------------
# ag-grid column definitions
# ---------------------------------------------------------------------------

_GRID_COL_DEFS = [
    {
        "field": "zone",
        "headerName": "Zone",
        "flex": 2,
        "filter": "agTextColumnFilter",
    },
    {
        "field": "borough",
        "headerName": "Borough",
        "flex": 1,
        "filter": "agTextColumnFilter",
    },
    {
        "field": "trips",
        "headerName": "Trips",
        "flex": 1,
        "type": "numericColumn",
        "valueFormatter": {"function": "d3.format(',')(params.value)"},
        "sort": "desc",
    },
    {
        "field": "avg_fare",
        "headerName": "Avg Fare ($)",
        "flex": 1,
        "type": "numericColumn",
        "valueFormatter": {"function": "d3.format('$.2f')(params.value)"},
    },
    {
        "field": "avg_tip_pct",
        "headerName": "Avg Tip %",
        "flex": 1,
        "type": "numericColumn",
        "valueFormatter": {"function": "d3.format('.1f')(params.value) + '%'"},
    },
]


# ---------------------------------------------------------------------------
# Figure / component builders
# ---------------------------------------------------------------------------


def _fig_map(selected_boroughs: list[str]) -> go.Figure:
    df = nyc_zone_pickup_map()
    if selected_boroughs:
        df = df[df["borough"].isin(selected_boroughs)]

    # Drop zones with zero trips (no activity — usually EWR / outliers)
    df = df[df["trips"] > 0].copy()

    # Dynamic zoom: expand viewport to fit selected boroughs
    if not df.empty:
        lat_center = df["lat"].mean()
        lon_center = df["lon"].mean()
        lat_range = df["lat"].max() - df["lat"].min()
        lon_range = df["lon"].max() - df["lon"].min()
        max_range = max(lat_range, lon_range)
        if max_range < 0.05:
            zoom = 13
        elif max_range < 0.1:
            zoom = 12
        elif max_range < 0.2:
            zoom = 11
        elif max_range < 0.5:
            zoom = 10
        else:
            zoom = 9
        center = {"lat": lat_center, "lon": lon_center}
    else:
        center = _DEFAULT_CENTER
        zoom = _DEFAULT_ZOOM

    fig = px.scatter_map(
        df,
        lat="lat",
        lon="lon",
        size="trips",
        color="avg_fare",
        color_continuous_scale="Viridis",
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
            "trips": "Trips",
            "avg_tip_pct": "Avg Tip %",
            "borough": "Borough",
        },
        title="NYC Taxi Pickup Volume by Zone — January 2024",
    )
    fig.update_layout(
        coloraxis_colorbar=dict(title="Avg Fare ($)"),
        margin=dict(l=0, r=0, t=50, b=0),
        height=600,
    )
    return fig


def _zone_grid(selected_boroughs: list[str]) -> dag.AgGrid:
    df = nyc_zone_pickup_map()
    if selected_boroughs:
        df = df[df["borough"].isin(selected_boroughs)]
    df = df[df["trips"] > 0][["zone", "borough", "trips", "avg_fare", "avg_tip_pct"]]
    return dag.AgGrid(
        id="zone-map-grid",
        rowData=df.to_dict("records"),
        columnDefs=_GRID_COL_DEFS,
        defaultColDef={"sortable": True, "resizable": True, "minWidth": 100},
        dashGridOptions={
            "pagination": True,
            "paginationPageSize": 20,
            "paginationPageSizeSelector": [10, 20, 50],
            "domLayout": "autoHeight",
        },
        className="ag-theme-alpine-dark",
    )


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def layout() -> html.Div:
    df = nyc_zone_pickup_map()
    total_trips = int(df["trips"].sum())
    active_zones = int((df["trips"] > 0).sum())

    filter_row = dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Label(
                            "Filter by borough",
                            className="small fw-semibold mb-2",
                        ),
                        dcc.Checklist(
                            id="zone-map-borough-filter",
                            options=[
                                {"label": f"  {b}", "value": b} for b in BOROUGH_ORDER
                            ],
                            value=BOROUGH_ORDER,
                            inline=True,
                            inputStyle={"marginRight": "4px"},
                            labelStyle={
                                "marginRight": "16px",
                                "fontSize": "0.85rem",
                            },
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
            html.H2("NYC Taxi Zone Map — January 2024", className="mb-1"),
            html.P(
                f"Source: NYC TLC  •  {active_zones} active zones  •  {total_trips:,} total pickups",
                className="text-muted mb-4",
            ),
            filter_row,
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        id="zone-map-graph",
                        figure=_fig_map(BOROUGH_ORDER),
                        config=_GRAPH_CONFIG,
                    ),
                    md=12,
                    className="mb-4",
                )
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H6(
                                    "Zone-level Pickup Summary",
                                    className="mb-3 fw-semibold",
                                ),
                                html.Div(
                                    _zone_grid(BOROUGH_ORDER),
                                    id="zone-map-grid-container",
                                ),
                            ]
                        ),
                        className="shadow-sm",
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
    Output("zone-map-graph", "figure"),
    Output("zone-map-grid-container", "children"),
    Input("zone-map-borough-filter", "value"),
)
def update_zone_page(selected_boroughs: list[str]) -> tuple:
    selected = selected_boroughs or BOROUGH_ORDER
    return _fig_map(selected), _zone_grid(selected)
