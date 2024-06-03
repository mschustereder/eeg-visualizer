from dash import Dash, html, dcc, Input, Output  # pip install dash
import plotly.express as px
import dash_ag_grid as dag
import dash_bootstrap_components as dbc   # pip install dash-bootstrap-components
import pandas as pd     # pip install pandas

import matplotlib      # pip install matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import mne
from lslHandler.lslHandler import LslHandler
from signalProcessor.EEGProcessor import EEGProcessor
import numpy as np

df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/solar.csv")

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container([
    html.H1("Interactive Matplotlib with Dash", className='mb-2', style={'textAlign':'center'}),

    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='category',
                value='Number of Solar Plants',
                clearable=False,
                options=df.columns[1:])
        ], width=4)
    ]),

    dbc.Row([
        dbc.Col([
            html.Img(id='bar-graph-matplotlib')
        ], width=12)
    ]),
])

# Create interactivity between dropdown component and graph
@app.callback(
    Output(component_id='bar-graph-matplotlib', component_property='src'),
    # Output('bar-graph-plotly', 'figure'),
    # Output('grid', 'defaultColDef'),
    Input('category', 'value'),
)
def plot_data(selected_yaxis):

    # Build the matplotlib figure
    lslhandler = LslHandler()
    streams = lslhandler.get_all_lsl_streams()
    lslhandler.connect_to_specific_lsl_stream(streams[0])
    lslhandler.start_data_recording_thread(streams[0])
    eegprocessor = EEGProcessor(lslhandler, lslhandler.get_stream_by_name("BrainVision RDA"))
    fig = eegprocessor.return_topoplot_matplotlib_figure()

    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    fig_data = base64.b64encode(buf.getbuffer()).decode("ascii")
    fig_bar_matplotlib = f'data:image/png;base64,{fig_data}'

    # Build the Plotly figure
    fig_bar_plotly = px.bar(df, x='State', y=selected_yaxis).update_xaxes(tickangle=330)

    my_cellStyle = {
        "styleConditions": [
            {
                "condition": f"params.colDef.field == '{selected_yaxis}'",
                "style": {"backgroundColor": "#d3d3d3"},
            },
            {   "condition": f"params.colDef.field != '{selected_yaxis}'",
                "style": {"color": "black"}
            },
        ]
    }

    return fig_bar_matplotlib#, {'cellStyle': my_cellStyle}


if __name__ == '__main__':
    app.run_server(debug=False, port=8002)