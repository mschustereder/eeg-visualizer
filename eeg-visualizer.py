from dash import Dash, html, dash_table
import pandas as pd
import dash_bootstrap_components as dbc

external_stylesheets = [dbc.themes.BOOTSTRAP]
app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([], width=1),
        dbc.Col([
            html.Div(children=[
                html.H1("EEG Visualizer"),
                dbc.Row([
                    dbc.Col([html.Div('First Row, First Column')], width=3),
                    dbc.Col([html.Div('First Row, Second Column')], width=3)
                ]),
                dbc.Row([
                    dbc.Col([html.Div('Second Row, First Column')], width=3),
                    dbc.Col([html.Div('Second Row, Second Column')], width=3)
                ])
            ], className='outer-container')
        ])
    ])
], fluid=True)

if __name__ == '__main__':
    app.run(debug=True)
