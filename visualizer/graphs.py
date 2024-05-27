from dash import Dash, html, Input, Output, callback, dcc


@callback(
    Output('main-plot-title', 'children'),
    Input('main-plot-selection', 'value')
)
def update_main_plot(value):
    return value

@callback(
    Output('auxiliary-plot-title', 'children'),
    Input('auxiliary-plot-selection', 'value')
)
def update_auxiliary_plot(value):
    return value
