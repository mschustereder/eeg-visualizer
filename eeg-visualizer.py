from dash import Dash, html, dash_table
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
                html.H4("Main Plot Area", className="card-title"),
                html.P(
                    "Here there will be a 'topoplot' or a spectrogram. Possibly others.",
                    className="card-text",
                )
            ]
        ),
    ],
    className='main-plot'
)

selection_area = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4("Parameter Selection Area", className="card-title"),
                html.P(
                    "Here one will be able to choose parameters for the plots. Etc.",
                    className="card-text",
                )
            ]
        ),
    ],
    className='selection-area'
)

auxiliary_plot_card = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4("Auxiliary Plot Area", className="card-title"),
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

if __name__ == '__main__':
    app.run(debug=True)
