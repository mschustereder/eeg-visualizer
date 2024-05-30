from dash import Dash, html, Input, Output, callback, dcc
import pandas as pd
import dash_bootstrap_components as dbc


external_stylesheets = [dbc.themes.LUX]
app = Dash(__name__, external_stylesheets=external_stylesheets)

header_bar = dbc.NavbarSimple(
    brand="EEG Visualizer",
    color="primary",
    dark=True,
)

main_plot = dcc.Graph(id='main-plot', config={'staticPlot': True}) #callback of dropdown will initialize graph

main_plot_card = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(className="card-title", id='main-plot-title'),
                main_plot,
                dcc.Interval(
                    id='interval-graph',
                    interval=100, # in milliseconds
                    n_intervals=0
                ),
            ]
        ),
    ],
    className='main-plot'
)

selection_for_main_plot = dbc.Card([
    dbc.CardBody([
        html.H5("Main Plot Parameters", className="card-title"),
        html.Div([
            'Choose Main Plot',
            dcc.Dropdown(['TimeSignal', 'FrequencySignal', 'Topoplot', 'Spectrogram'], 'TimeSignal', id='main-plot-selection', clearable=False)
        ]),
        html.Div(id='brainwave-selection'),
    ])
])

selection_area = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4("Parameter Selection Area", className="card-title"),
                html.P(
                    "Here one will be able to choose parameters for the plots. Etc.",
                    className="card-text",
                ),
                selection_for_main_plot,
                html.Div([
                    'Choose Auxiliary Plot',
                    dcc.Dropdown(['ECG', 'Other'], 'ECG', id='auxiliary-plot-selection', clearable=False)
                ])
            ]
        )
    ],
    className='selection-area'
)

auxiliary_plot_card = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4("Auxiliary Plot Area", className="card-title", id='auxiliary-plot-title'),
                html.P(
                    "Here there will be some form of line plot. ECG for example, or RR Plot.",
                    className="card-text",
                )
            ]
        ),
    ],
    className='auxiliary-plot'
)

streams_list = dbc.ListGroup(
    [
        dbc.ListGroupItem("Stream 1"),
        dbc.ListGroupItem("Stream 2"),
        dbc.ListGroupItem("Stream 3"),
    ]
)

lsl_stream_selection_modal = html.Div(
    [
        dbc.Button("Open modal", id="open_modal_button", n_clicks=0),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Select an LSL Stream")),
                dbc.ModalBody(
                    streams_list
                )
            ],
            id="lsl_stream_selection_modal",
            is_open=False,
        ),
    ]
)

app.layout = dbc.Container([
    dbc.Row([header_bar]),
    html.Div(children=[
        dbc.Row([
            dbc.Col([main_plot_card], width=9),
            dbc.Col([selection_area])
        ]),
        dbc.Row([
            dbc.Col([auxiliary_plot_card])            
        ]),
        lsl_stream_selection_modal
    ], className='outer-container')
], fluid=True)

@app.callback(
    Output("lsl_stream_selection_modal", "is_open"),
    Input("open_modal_button", "n_clicks")
)
def toggle_modal(open_modal_button_clicked):
    # lslhandler = LslHandler()
    # all_streams = lslhandler.get_all_lsl_streams()
    # print(lslhandler.get_all_lsl_streams_as_infostring())
    return open_modal_button_clicked

@callback(
    Output('brainwave-selection', 'children'),
    Input('main-plot-selection', 'value')
)
def show_brainwave_selection(value):
    brainwave_selection = [
                    'Choose Brainwave',
                    dcc.Dropdown(['Alpha', 'Beta', 'Delta', 'Theta'], 'Alpha', id='brainwave-selection-dropdown', clearable=False)
                ]
    return brainwave_selection if value == 'Topoplot' else []

from visualizer.graph_callbacks import *
