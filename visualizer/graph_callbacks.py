from dash import Dash, html, Input, Output, callback, dcc, State, no_update
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import visualizer.globals as gl

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
    range_x=[0, 45]
    
    if len(gl.graph_frame["time"]) != 0:
        range_x = [gl.graph_frame["time"][0], gl.graph_frame["time"][0]+45]

    return range_x

def cut_buffer():
    time_diff = gl.graph_frame["time"][-1]  - gl.graph_frame["time"][0]
    if time_diff > 45:
        print("cut")
        cut_index = 0
        while((gl.graph_frame["time"][cut_index]  - gl.graph_frame["time"][0]) < 45 and cut_index < len(gl.graph_frame["time"])):
            cut_index +=1 
        print(cut_index)
        gl.graph_frame["time"] = gl.graph_frame["time"][cut_index:]
        gl.graph_frame["value"] = gl.graph_frame["value"][cut_index:]

def topoPlot():
    return go.Figure(data=go.Scatter(x=gl.graph_frame["time"], y=gl.graph_frame["value"], mode='lines', line_color="Blue", line_width=0.5) , layout_xaxis_range=get_x_range(), layout_yaxis_range=[-5400, -4900])

def spectrumPlot():
    return go.Figure(data=go.Scatter(x=gl.graph_frame["time"], y=gl.graph_frame["value"], mode='lines', line_color="Red", line_width=0.5) ,layout_xaxis_range=get_x_range(), layout_yaxis_range=[-5400, -4900])
    
@callback(
    Output('main-plot', 'figure'),
    Input('interval-graph', 'n_intervals'),
    State('main-plot-selection', 'value')
)
def update_main_plot(n_intervals, current_plot):
    data = gl.eeg_processor.get_eeg_data_as_chunk()

    if data == None:
        return no_update

    gl.buffer_frame = {"time" : [], "value" : []}
    
    for sample in data:
        gl.graph_frame["time"].append(sample[1])
        gl.graph_frame["value"].append(sample[0]["Fz"])

    cut_buffer()

    if (current_plot == "Topoplot"):
        return topoPlot()
    else:
        return spectrumPlot()
    
    # if current_plot == 'FrequencySignal':
    #     time = graph_frame["time"]
    #     values = graph_frame["value"]
    #     N = 1024
    #     if len(time) > N:
    #         time = time[N:]
    #         values = values[N:]

    #     sampling_rate = 500

    #     frequency, fft_magnitude_normalized = calculate_fft(values, sampling_rate)

    #     return go.Figure(data=go.Scatter(x=frequency, y=fft_magnitude_normalized, mode='lines', line_color=get_color(current_plot), line_width=1), layout=dict(
    #         xaxis=dict(range=[0, 5], title='Frequency in Hz')
    #     ))
    # else:
    #     return go.Figure(data=go.Scatter(x=graph_frame["time"], y=graph_frame["value"], mode='lines', line_color=get_color(current_plot), line_width=1), layout=dict(
    #         yaxis=dict(range=[-1, 1]),
    #         xaxis=dict(range=get_x_range(), title='Time in ms')
    #     ))


@callback(
    Output('auxiliary-plot-title', 'children'),
    Input('auxiliary-plot-selection', 'value')
)
def update_auxiliary_plot(value):
    return value
