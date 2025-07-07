import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import requests
import pandas as pd

API = "https://v13-quant.onrender.com"

def fetch_top_stocks():
    try:
        r = requests.get(f"{API}/recommendations/top")
        if r.ok and isinstance(r.json(), list):
            return pd.DataFrame(r.json())
    except Exception:
        pass
    return pd.DataFrame()

top_df = fetch_top_stocks()
tickers = top_df['ticker'].tolist() if not top_df.empty else []

app = dash.Dash(__name__)
app.title = "Oracle Black AI Dashboard"

app.layout = html.Div(
    style={"background": "#181818", "color": "#fafafa", "minHeight": "100vh", "padding": "2rem", "fontFamily": "Arial"},
    children=[
        html.H1("Oracle Black AI Dashboard", style={"textAlign": "center", "fontWeight": "bold"}),
        html.Div([
            html.H3("Buy These Now!"),
            html.P("These stocks are going to be a win.", style={"color": "#03DAC6", "fontWeight": "bold"}),
            html.Ul(
                [
                    html.Li(
                        f"{row['ticker']} — Score: {row['combined_score']:.2f}",
                        style={"fontSize": "1.1rem", "margin": "6px 0"}
                    ) for _, row in top_df.iterrows()
                ]
            ) if not top_df.empty else html.Div("No recommendations found. Please check the backend.", style={"color": "red"})
        ],
        style={"background": "#23272b", "borderRadius": "12px", "padding": "1.3rem", "boxShadow": "0 2px 10px #0003", "marginBottom": "2rem"}
        ),
        html.Div([
            html.Label("Explore Stock Details:", style={"fontWeight": "bold", "marginRight": "12px"}),
            dcc.Dropdown(
                id="ticker-dropdown",
                options=[{"label": t, "value": t} for t in tickers],
                value=tickers[0] if tickers else None,
                style={"width": "300px", "color": "#181818"}
            )
        ]),
        dcc.Tabs(
            id="info-tabs",
            value="options",
            children=[
                dcc.Tab(label="Options Chain", value="options"),
                dcc.Tab(label="Earnings", value="earnings"),
            ],
            style={"marginTop": "1rem"}
        ),
        html.Div(id="tab-content", style={"marginTop": "1.5rem"}),
        html.Div([
            html.P("Powered by Oracle Black ULTRA — The Quant God Mode.", style={"color": "#888", "textAlign": "center", "marginTop": "3rem"})
        ])
    ]
)

@app.callback(
    Output("tab-content", "children"),
    [Input("ticker-dropdown", "value"), Input("info-tabs", "value")]
)
def render_tab(ticker, tab):
    if not ticker:
        return html.Div("Select a ticker from the dropdown.")
    if tab == "options":
        try:
            r = requests.get(f"{API}/options/{ticker}", timeout=8)
            if not r.ok or not r.json():
                return html.Div("No options data available.")
            df = pd.DataFrame(r.json())
            if df.empty or "strike" not in df.columns or "impliedVolatility" not in df.columns:
                return html.Div("Options data is incomplete.")
            fig = go.Figure()
            for opt_type in ["call", "put"]:
                sub = df[df['type'] == opt_type]
                if not sub.empty:
                    fig.add_trace(go.Scatter(
                        x=sub['strike'][:30],
                        y=sub['impliedVolatility'][:30],
                        mode='markers+lines',
                        name=opt_type.capitalize(),
                        marker={'size': 8}
                    ))
            fig.update_layout(
                title=f"{ticker} Option IV vs Strike",
                xaxis_title="Strike",
                yaxis_title="Implied Volatility",
                plot_bgcolor="#23272b",
                paper_bgcolor="#23272b",
                font=dict(color="#fafafa"),
                legend=dict(x=0.7, y=1.15, orientation="h")
            )
            return dcc.Graph(figure=fig)
        except Exception as e:
            return html.Div(f"Error fetching options: {e}")
    elif tab == "earnings":
        try:
            r = requests.get(f"{API}/earnings/{ticker}", timeout=8)
            if r.ok and isinstance(r.json(), dict):
                ne = r.json().get("next_earnings")
                return html.Div([
                    html.H4("Next Earnings Date", style={"marginBottom": "8px"}),
                    html.Div(str(ne) if ne else "No upcoming earnings found.", style={"fontSize": "1.1rem"})
                ])
            return html.Div("No earnings info.")
        except Exception as e:
            return html.Div(f"Error fetching earnings: {e}")
    return html.Div("Select a tab.")

if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
