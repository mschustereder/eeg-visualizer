from dash import Dash, html, Input, Output, callback, dcc, State, no_update
import plotly.express as px
import pandas as pd
import random
from globals import *


# @callback(
#     Output('main-plot', 'figure'),
#     Input('main-plot-selection', 'value')
# )
# def change_main_plot(value):
#     print(value)

#     fig = None
    
#     if value == "Topoplot":
#         fig = px.line()
#     else:
#         fig = px.line()

#     return fig

def get_x_range():
    range_x=[0, 10000]
    
    if len(graph_frame["time"]) != 0:
        range_x = [graph_frame["time"][0], graph_frame["time"][0]+10000]

    return range_x

@callback(
    Output('main-plot', 'figure'),
    Input('interval-graph', 'n_intervals'),
)
def update_main_plot(n_intervals):
    global buffer_frame
    global graph_frame 
    graph_frame["time"].extend(buffer_frame["time"])
    graph_frame["value"].extend(buffer_frame["value"])
    if len(graph_frame["time"]) > 10000:
        print("cut")
        graph_frame["time"] = graph_frame["time"][10000:]
        graph_frame["value"] = graph_frame["value"][10000:]
    buffer_frame = {"time" : [], "value" : []}

    return px.line(pd.DataFrame(graph_frame), x = "time", y = "value", range_x = get_x_range(), range_y=[0, 1])


@callback(
    Input('interval-data-gen', 'n_intervals'),
)
def add_data(n_intervals):
    global start_interval
    global buffer_frame
    buffer_frame["time"].append(start_interval)
    start_interval += 1
    buffer_frame["value"].append(random.random())


@callback(
    Output('auxiliary-plot-title', 'children'),
    Input('auxiliary-plot-selection', 'value')
)
def update_auxiliary_plot(value):
    return value
