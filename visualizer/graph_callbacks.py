from dash import Dash, html, Input, Output, callback, dcc, State, no_update
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import random
from globals import *

def get_next_lowest_power_of_two(num):
    return 2 ** (num - 1).bit_length()

def calculate_fft(signal, sampling_rate):
    window_length = get_next_lowest_power_of_two(len(signal))

    sampling_period = 1 / sampling_rate

    fft_result = np.fft.fft(signal, window_length)
    fft_magnitude = np.abs(fft_result)
    fft_magnitude_only_positive = fft_magnitude[:(window_length // 2)] # positive values are in first half
    fft_magnitude_normalized = fft_magnitude_only_positive / window_length
    frequency = np.fft.fftfreq(window_length, sampling_period)[:window_length // 2] # frequency vector
    return frequency, fft_magnitude_normalized

def get_x_range():
    range_x=[0, 10000]
    
    if len(graph_frame["time"]) != 0:
        range_x = [graph_frame["time"][0], graph_frame["time"][0]+10000]

    return range_x

def get_color(current_plot):
    if current_plot == "TimeSignal":
        return  "Blue"
    elif current_plot == "FrequencySignal":
        return  "Red"
    else:
        return "Green"
    
@callback(
    Output('main-plot', 'figure'),
    Input('interval-graph', 'n_intervals'),
    State('main-plot-selection', 'value')
)
def update_main_plot(n_intervals, current_plot):
    global graph_frame
    global buffer_frame
    graph_frame["time"].extend(buffer_frame["time"])
    graph_frame["value"].extend(buffer_frame["value"])
    buffer_frame = {"time" : [], "value" : []}

    if len(graph_frame["time"]) > 10000:
        print("cut")
        graph_frame["time"] = graph_frame["time"][10000:]
        graph_frame["value"] = graph_frame["value"][10000:]

    if current_plot == 'FrequencySignal':
        time = graph_frame["time"]
        values = graph_frame["value"]
        N = 1024
        if len(time) > N:
            time = time[N:]
            values = values[N:]

        sampling_rate = 500

        frequency, fft_magnitude_normalized = calculate_fft(values, sampling_rate)

        return go.Figure(data=go.Scatter(x=frequency, y=fft_magnitude_normalized, mode='lines', line_color=get_color(current_plot), line_width=1), layout=dict(
            xaxis=dict(range=[0, 5], title='Frequency in Hz')
        ))
    else:
        return go.Figure(data=go.Scatter(x=graph_frame["time"], y=graph_frame["value"], mode='lines', line_color=get_color(current_plot), line_width=1), layout=dict(
            yaxis=dict(range=[-1, 1]),
            xaxis=dict(range=get_x_range(), title='Time in ms')
        ))

@callback(
    Input('interval-data-gen', 'n_intervals'),
)
def add_data(n_intervals):
    global start_interval
    global buffer_frame
    buffer_frame["time"].append(start_interval)
    start_interval += 1
    frequency_of_sine = 1 / 250
    sine_value = np.sin(2 * np.pi * frequency_of_sine *start_interval)
    buffer_frame["value"].append(sine_value)
    # buffer_frame["value"].append(random.random())


@callback(
    Output('auxiliary-plot-title', 'children'),
    Input('auxiliary-plot-selection', 'value')
)
def update_auxiliary_plot(value):
    return value
