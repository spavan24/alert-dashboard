# app.py
import dash
from dash import dcc, html, dash_table, Input, Output
import pandas as pd
import plotly.express as px

# -----------------------------
# Load your dataset
# -----------------------------
# Replace with your Excel/CSV file
df = pd.read_excel("your_data.xlsx")  # or pd.read_csv("your_data.csv")

# Normalize column names
df.columns = [c.strip().lower() for c in df.columns]

# Detect key columns dynamically
owner_col = next((c for c in df.columns if "owner" in c), None)
alert_col = next((c for c in df.columns if "alert" in c), None)
priority_col = next((c for c in df.columns if "priority" in c), None)
change_col = next((c for c in df.columns if "change" in c), None)
date_col = next((c for c in df.columns if "date" in c), None)

if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

# -----------------------------
# Initialize Dash app
# -----------------------------
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # For Render deployment

# -----------------------------
# Layout
# -----------------------------
app.layout = html.Div([
    html.H1("🚨 Alert Dashboard", style={"textAlign": "center"}),

    dcc.Tabs(id="tabs", value="analysis", children=[
        dcc.Tab(label="Analysis", value="analysis"),
        dcc.Tab(label="Specific Search", value="search"),
    ]),

    html.Div(id="tab-content"),

    # Auto-refresh every 12 hours
    dcc.Interval(id="interval-component", interval=12*60*60*1000, n_intervals=0)
])

# -----------------------------
# Render Tabs
# -----------------------------
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value")
)
def render_tab(tab):
    if tab == "analysis":
        return analysis_tab_layout()
    else:
        return search_tab_layout()

# -----------------------------
# Analysis Tab Layout
# -----------------------------
def analysis_tab_layout():
    filters = []

    if owner_col:
        filters.append(html.Div([
            html.Label("Select Owner:"),
            dcc.Dropdown(id="filter-owner",
                         options=[{"label": o, "value": o} for o in df[owner_col].dropna().unique()],
                         multi=True)
        ]))
    if alert_col:
        filters.append(html.Div([
            html.Label("Select Alert Name:"),
            dcc.Dropdown(id="filter-alert",
                         options=[{"label": a, "value": a} for a in df[alert_col].dropna().unique()],
                         multi=True)
        ]))
    if priority_col:
        filters.append(html.Div([
            html.Label("Select Priority:"),
            dcc.Dropdown(id="filter-priority",
                         options=[{"label": p, "value": p} for p in df[priority_col].dropna().unique()],
                         multi=True)
        ]))
    if change_col:
        filters.append(html.Div([
            html.Label("Select Change Number:"),
            dcc.Dropdown(id="filter-change",
                         options=[{"label": c, "value": c} for c in df[change_col].dropna().unique()],
                         multi=True)
        ]))
    if date_col:
        min_date = df[date_col].min().date()
        max_date = df[date_col].max().date()
        filters.append(html.Div([
            html.Label("Select Date Range:"),
            dcc.DatePickerRange(
                id="filter-date",
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                start_date=min_date,
                end_date=max_date
            )
        ]))
        months = df[date_col].dt.month_name().dropna().unique()
        quarters = df[date_col].dt.quarter.dropna().unique()
        filters.append(html.Div([
            html.Label("Select Month:"),
            dcc.Dropdown(id="filter-month", options=[{"label": m, "value": m} for m in months], multi=True)
        ]))
        filters.append(html.Div([
            html.Label("Select Quarter:"),
            dcc.Dropdown(id="filter-quarter", options=[{"label": f"Q{q}", "value": q} for q in quarters], multi=True)
        ]))

    layout = html.Div([
        html.Div(filters, style={"columnCount": 2, "marginBottom": "20px"}),

        html.Div(id="kpi-cards", style={"display": "flex", "justifyContent": "space-around"}),

        html.Div([
            html.Label("Select Chart Type:"),
            dcc.RadioItems(
                id="chart-type",
                options=[{"label": "Bar Chart", "value": "bar"},
                         {"label": "Pie Chart", "value": "pie"}],
                value="bar",
                labelStyle={"display": "inline-block", "margin-right": "10px"}
            )
        ], style={"marginBottom": "20px"}),

        dcc.Graph(id="owner-chart"),
        dcc.Graph(id="priority-chart"),

        html.H3("Filtered Data"),
        dash_table.DataTable(id="filtered-table",
                             page_size=50,
                             style_table={'overflowX': 'auto'},
                             export_format="csv")
    ])
    return layout

# -----------------------------
# Search Tab Layout
# -----------------------------
def search_tab_layout():
    return html.Div([
        html.Label("Search Keyword (any column):"),
        dcc.Input(id="search-keyword", type="text"),
        html.Br(), html.Br(),
        dash_table.DataTable(id="search-table",
                             page_size=50,
                             style_table={'overflowX': 'auto'},
                             export_format="csv")
    ])

# -----------------------------
# Update Analysis Filters
# -----------------------------
@app.callback(
    Output("kpi-cards", "children"),
    Output("owner-chart", "figure"),
    Output("priority-chart", "figure"),
    Output("filtered-table", "data"),
    Output("filtered-table", "columns"),
    Input("filter-owner", "value"),
    Input("filter-alert", "value"),
    Input("filter-priority", "value"),
    Input("filter-change", "value"),
    Input("filter-date", "start_date"),
    Input("filter-date", "end_date"),
    Input("filter-month", "value"),
    Input("filter-quarter", "value"),
    Input("chart-type", "value")
)
def update_analysis(owner, alert, priority, change, start_date, end_date, months, quarters, chart_type):
    dff = df.copy()
    if owner_col and owner: dff = dff[dff[owner_col].isin(owner)]
    if alert_col and alert: dff = dff[dff[alert_col].isin(alert)]
    if priority_col and priority: dff = dff[dff[priority_col].isin(priority)]
    if change_col and change: dff = dff[dff[change_col].isin(change)]
    if date_col and start_date and end_date:
        dff = dff[(dff[date_col] >= start_date) & (dff[date_col] <= end_date)]
    if date_col and months: dff = dff[dff[date_col].dt.month_name().isin(months)]
    if date_col and quarters: dff = dff[dff[date_col].dt.quarter.isin(quarters)]

    # KPI cards
    kpis = []
    kpis.append(html.Div([html.H4("Total Alerts"), html.P(len(dff))], style={"padding": "10px", "border": "1px solid black"}))
    if owner_col: kpis.append(html.Div([html.H4("Unique Owners"), html.P(dff[owner_col].nunique())], style={"padding": "10px", "border": "1px solid black"}))
    if priority_col: kpis.append(html.Div([html.H4("Unique Priorities"), html.P(dff[priority_col].nunique())], style={"padding": "10px", "border": "1px solid black"}))
    if alert_col: kpis.append(html.Div([html.H4("Unique Alerts"), html.P(dff[alert_col].nunique())], style={"padding": "10px", "border": "1px solid black"}))
    if change_col: kpis.append(html.Div([html.H4("Unique Change Numbers"), html.P(dff[change_col].nunique())], style={"padding": "10px", "border": "1px solid black"}))

    # Charts
    owner_fig = px.bar(dff.groupby(owner_col).size().reset_index(name="Count"), x=owner_col, y="Count") if owner_col else px.scatter()
    priority_fig = px.bar(dff.groupby(priority_col).size().reset_index(name="Count"), x=priority_col, y="Count") if priority_col else px.scatter()
    if chart_type == "pie":
        if owner_col: owner_fig = px.pie(dff.groupby(owner_col).size().reset_index(name="Count"), names=owner_col, values="Count")
        if priority_col: priority_fig = px.pie(dff.groupby(priority_col).size().reset_index(name="Count"), names=priority_col, values="Count")

    # DataTable
    data = dff.to_dict("records")
    columns = [{"name": i, "id": i} for i in dff.columns]

    return kpis, owner_fig, priority_fig, data, columns

# -----------------------------
# Update Search Tab
# -----------------------------
@app.callback(
    Output("search-table", "data"),
    Output("search-table", "columns"),
    Input("search-keyword", "value")
)
def update_search(keyword):
    dff = df.copy()
    if keyword:
        dff = dff[dff.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]
    data = dff.to_dict("records")
    columns = [{"name": i, "id": i} for i in dff.columns]
    return data, columns

# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":
    app.run_server(debug=True)
