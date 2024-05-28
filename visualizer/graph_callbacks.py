from dash import Dash, html, Input, Output, callback, dcc
import plotly.graph_objects as go
import pandas as pd


@callback(
    Output('main-plot', 'figure'),
    Input('main-plot-selection', 'value')
)
def change_main_plot(value):
    print(value)

    fig = None
    
    if value == "Topoplot":
        fig = go.Figure(go.Scatter(line_color="crimson"))
    else:
        fig = go.Figure(go.Scatter(line_color="green"))

    return fig

@callback(
    Output('auxiliary-plot-title', 'children'),
    Input('auxiliary-plot-selection', 'value')
)
def update_auxiliary_plot(value):
    return value
