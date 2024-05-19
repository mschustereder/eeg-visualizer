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

main_plot_card = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(className="card-title", id='main-plot-title'),
                html.P(
                    "Here there will be a 'topoplot' or a spectrogram. Possibly others.",
                    className="card-text",
                )
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
            dcc.Dropdown(['Topoplot', 'Spectrogram'], 'Topoplot', id='main-plot-selection', clearable=False)
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

app.layout = dbc.Container([
    dbc.Row([header_bar]),
    html.Div(children=[
        dbc.Row([
            dbc.Col([main_plot_card], width=9),
            dbc.Col([selection_area])
        ]),
        dbc.Row([
            dbc.Col([auxiliary_plot_card])            
        ])
    ], className='outer-container')
], fluid=True)

@callback(
    Output('main-plot-title', 'children'),
    Input('main-plot-selection', 'value')
)
def update_main_plot(value):
    return value

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

@callback(
    Output('auxiliary-plot-title', 'children'),
    Input('auxiliary-plot-selection', 'value')
)
def update_auxiliary_plot(value):
    return value

if __name__ == '__main__':
    app.run(debug=True)
