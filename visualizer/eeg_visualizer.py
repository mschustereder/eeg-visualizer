from dash import Dash, html, Input, Output, callback, dcc, State
import pandas as pd
import dash_bootstrap_components as dbc
import visualizer.globals as gl

import dash_draggable

external_stylesheets = [dbc.themes.LUX]
app = Dash(__name__, external_stylesheets=external_stylesheets)

header_bar = dbc.NavbarSimple(
    brand="EEG Visualizer",
    color="primary",
    dark=True,
)

main_plot = dcc.Graph(id='main-plot') # callback of dropdown will initialize graph

main_plot_container = dbc.Card(
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
    id='main-plot-container'
)

configuration_for_main_plot = [
    html.H5("Configure main plot", className="card-title"),
    html.Div([
        'Choose main plot',
        dcc.Dropdown(['Topoplot', 'Spectrogram'], 'Spectrogram', id='main-plot-selection', clearable=False)
    ]),
    html.Div(id='brainwave-selection'),
]

def get_configuration_for_sub_plot(index):
    return [
        html.H5(f"Configure sub plot {index + 1}", className="card-title"),
        html.Div([
            f'Choose sub plot {index + 1}',
            dcc.Dropdown(['ECG', 'Other'], 'ECG', id=f'sub-plot-selection-{index}', clearable=False)
        ])
    ]

configuration_list = dbc.ListGroup(id="configuration-list", children=[
    dbc.ListGroupItem(children=configuration_for_main_plot),
])

buttons_list_item = [
    dbc.Button("Add another sub plot", id="add-sub-plot-button", n_clicks=0, color="primary"),
    dbc.Button("Remove last sub plot", id="remove-sub-plot-button", n_clicks=0, color="danger")
]

buttons_for_plot_configuration = dbc.ListGroup(dbc.ListGroupItem(children=buttons_list_item, style={
    "display": "flex",
    "justifyContent": "space-evely"
}))

button_clicks_store = dcc.Store(id='button_clicks_store', data={'last_click_add_button': 0, 'last_click_remove_button': 0})

add_sub_plot_store = dcc.Store(id='add_sub_plot_store', data={'just_a_counter': 0, 'sub_plot_index': -17})

configuration_area = dbc.Card(
    [
        dbc.CardBody(
            [
                button_clicks_store,
                add_sub_plot_store,
                html.H4("Configuration", className="card-title"),
                configuration_list,
                buttons_for_plot_configuration
            ]
        )
    ],
    id='configuration-area'
)

def get_sub_plot(index):
    return html.Div(children=[
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(f"Sub Plot {index + 1}", className="card-title", id=f'sub-plot-title-{index}'),
                            html.P(
                                "Here there will be some form of line plot. ECG for example, or RR Plot.",
                                className="card-text",
                            )
                        ]
                    )
                ]
            )
        ],
        id=f'sub-plot-{index}-layout'
    )

def get_layout_for_sub_plot(index):
    return {
        "i": f"sub-plot-{index}-layout",
        "x": 0 if index % 2 == 0 else 8, "w": 8, "y": 12, "h": 8
    }

streams_list = dbc.ListGroup(id="lsl_streams_list")

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

draggable_layout = dash_draggable.GridLayout(
    id='draggable',
    gridCols=16,
    width=1800,
    layout=[
            {
                "i": "main-plot-container",
                "x": 0, "w": 11, "y": 0, "h": 12
            },
            {
                "i": "configuration-area",
                "x": 11, "w": 5, "y": 0, "h": 10
            },
            {
                "i": "modal",
                "x": 11, "w": 2, "y": 12, "h": 2
            },
        ],
    children=[
        main_plot_container,
        configuration_area,
        html.Div(children=[
                lsl_stream_selection_modal
            ],
            id='modal'
        ),
    ],
    style={
        "border":"2px solid blue",
    }
)

app.layout = dbc.Container([
    dbc.Row([header_bar]),
    dbc.Row([
        html.Div([
            draggable_layout
        ],
        style={
            "border":"2px solid red",
        })
    ])
], fluid=True)

@app.callback(
    Output("lsl_stream_selection_modal", "is_open"),
    Input("open_modal_button", "n_clicks")
)
def toggle_modal(open_modal_button_clicked):
    return open_modal_button_clicked

@callback(
    Output('main-plot-title', 'children'),
    Input('main-plot-selection', 'value')
)
def update_auxiliary_plot(value):
    return value

@app.callback(
    Output("configuration-list", "children"),
    Output('button_clicks_store', 'data'),
    Output('add_sub_plot_store', 'data'),
    # Output('add-sub-plot-button', 'disabled'),
    # Output('remove-sub-plot-button', 'disabled'),
    [Input("add-sub-plot-button", "n_clicks"), Input("remove-sub-plot-button", "n_clicks")],
    State('button_clicks_store', 'data'),
    State('configuration-list', 'children'),
    State('add_sub_plot_store', 'data')
    # State('draggable', 'children'),
    # State('draggable', 'layout'),
)
def update_plot_configuration(num_clicks_add_button, num_clicks_remove_button, stored_clicks_data, children_configuration_list, add_sub_plot_store_data):
    def was_button_clicked(num_clicks, last_click): return num_clicks > last_click

    add_button_clicked = was_button_clicked(num_clicks_add_button, stored_clicks_data['last_click_add_button'])
    remove_button_clicked = was_button_clicked(num_clicks_remove_button, stored_clicks_data['last_click_remove_button'])
    
    update_value_for_store = {'last_click_add_button': num_clicks_add_button, 'last_click_remove_button': num_clicks_remove_button}

    # if add_button_clicked is True and remove_button_clicked is True:
    #     return no_update, update_value_for_store, no_update, no_update, no_update, no_update

    if add_button_clicked:
        sub_plot_index = len(children_configuration_list) - 1
        new_children_for_configuration_list = children_configuration_list + [dbc.ListGroupItem(children=get_configuration_for_sub_plot(sub_plot_index))]
        # new_children_for_draggable = children_draggable + [get_sub_plot(sub_plot_index)]
        # new_layout_for_draggable = layout_draggable + [get_layout_for_sub_plot(sub_plot_index)]
        # should_disable_add_button = True if len(new_children_for_configuration_list) >= gl.MAX_NUM_OF_PLOTS else False
        # return new_children_for_configuration_list, update_value_for_store, should_disable_add_button, no_update, new_children_for_draggable, new_layout_for_draggable
        update_value_for_add_sub_plot_store = {'just_a_counter': add_sub_plot_store_data['just_a_counter'], 'sub_plot_index': sub_plot_index}
        return new_children_for_configuration_list, update_value_for_store, update_value_for_add_sub_plot_store
        # return new_children_for_configuration_list, update_value_for_store, new_children_for_draggable, new_layout_for_draggable
    elif remove_button_clicked:
        new_children_for_configuration_list = children_configuration_list[:-1]
        # new_children_for_draggable = children_draggable[:-1]
        # new_layout_for_draggable = layout_draggable[:-1]
        # should_disable_remove_button = True if len(new_children_for_configuration_list) <= 1 else False
        # return new_children_for_configuration_list, update_value_for_store, no_update, should_disable_remove_button, new_children_for_draggable, new_layout_for_draggable
        return new_children_for_configuration_list, update_value_for_store, no_update
        # return new_children_for_configuration_list, update_value_for_store, new_children_for_draggable, new_layout_for_draggable
    else:
        return no_update, update_value_for_store, no_update
    
@app.callback(
    Output('draggable', 'children'),
    Output('draggable', 'layout'),
    Input('add_sub_plot_store', 'data'),
    State('draggable', 'children'),
    State('draggable', 'layout'),
)
def add_plots_and_layouts(data_in_add_sub_plot_store, children_draggable, layout_draggable):
    print(f"The data in the add_sub_plot_store changed! It is now: {data_in_add_sub_plot_store}")
    sub_plot_index = data_in_add_sub_plot_store['sub_plot_index']
    new_children_for_draggable = children_draggable + [get_sub_plot(sub_plot_index)]
    new_layout_for_draggable = layout_draggable + [get_layout_for_sub_plot(sub_plot_index)]
    return new_children_for_draggable, new_layout_for_draggable

@app.callback(
    Output("lsl_streams_list", "children"),
    Input("open_modal_button", "n_clicks")
)
def toggle_modal(open_modal_button_clicked):
    lsl_streams_as_infostrings = gl.lsl_handler.get_all_lsl_streams_as_infostring()
    def create_list_item(infostr, idx): return dbc.ListGroupItem(dbc.Button(infostr, color="primary", id=f"button_id_{idx}", n_clicks=0, className="lsl_stream_button"), className="lsl_stream_item")

    lsl_streams_list_as_group_items = [create_list_item(infostring, index) for index, infostring in enumerate(lsl_streams_as_infostrings)]
    return lsl_streams_list_as_group_items

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
