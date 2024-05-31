from dash import Dash, html, Input, Output, callback, dcc, State, no_update
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import visualizer.globals as gl
import time

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
    
    if len(gl.graph_frame.timestamps) != 0:
        range_x = [gl.graph_frame.timestamps[0], gl.graph_frame.timestamps[0]+45]

    return range_x

def cut_buffer():
    time_diff = gl.graph_frame.timestamps[-1]  - gl.graph_frame.timestamps[0]
    if time_diff > 45:
        print("cut")
        cut_index = 0
        while((gl.graph_frame.timestamps[cut_index]  -gl.graph_frame.timestamps[0]) < 45 and cut_index < len(gl.graph_frame.timestamps)):
            cut_index +=1 
        print(cut_index)
        gl.graph_frame.timestamps = gl.graph_frame.timestamps[cut_index:]
        gl.graph_frame.eeg_values["Fz"] = gl.graph_frame.eeg_values["Fz"][cut_index:]

def topoPlot():
    data = gl.eeg_processor.get_eeg_data_as_chunk()

    if data == None:
        return no_update
    
    for sample in data:
        gl.graph_frame.timestamps.append(sample[1])
        gl.graph_frame.eeg_values["Fz"].append(sample[0]["Fz"])

    cut_buffer()

    return go.Figure(data=go.Scatter(x=gl.graph_frame.timestamps, y=gl.graph_frame.eeg_values["Fz"], mode='lines', line_color="Blue", line_width=0.5) , layout_xaxis_range=get_x_range())#, layout_yaxis_range=[-5400, -4900])

def spectrumPlot():

    data = gl.eeg_processor.get_eeg_data_as_chunk()

    if data == None:
        return no_update
    
    for sample in data:
        gl.graph_frame.fft_values_buffer.append(sample[0]["Fz"])

    #only update graph if accumulated data is FFT_SAMPLES samples long
    if len(gl.graph_frame.fft_values_buffer) >= gl.FFT_SAMPLES:

        #we want to get a spectrum every 100ms, so we will calulate overlapping fft windows, and thus use the fft_values_buffer as a FIFO buffer
        gl.graph_frame.fft_values_buffer = gl.graph_frame.fft_values_buffer[-gl.FFT_SAMPLES:] 
        sampling_rate = gl.eeg_processor.stream.nominal_srate()
        sample_time = data[-1][1] - data[0][1] #this is the time that has passed in the sample world
        frequency, fft_magnitude_normalized = calculate_fft(gl.graph_frame.fft_values_buffer, sampling_rate)

        #we dont want the offset a 0 Hz included, so we will cut off every frequency below 1 Hz
        cut_index = 0
        while(frequency[cut_index] < 1):
            cut_index += 1

        #we can also cut anything above FREQUENCY_CUT_OFF
            
        cut_index_top = 0
        while(frequency[cut_index_top] < gl.FREQUENCY_CUT_OFF):
            cut_index_top += 1

        gl.graph_frame.frequencies = frequency[cut_index:cut_index_top]
        gl.graph_frame.fft_vizualizer_values.append(fft_magnitude_normalized[cut_index:cut_index_top])

        #we are using relative times from the first sample to the last sample in the fft_visualizer_values
        if len(gl.graph_frame.fft_timestamps)==0:
            gl.graph_frame.fft_timestamps.append(sample_time)
        else:
            gl.graph_frame.fft_timestamps.append(gl.graph_frame.fft_timestamps[-1] + sample_time)

        
        #only show the last SAMPLES_SHOWN_IN_SPECTROGRAM samples
        if len(gl.graph_frame.fft_vizualizer_values) > gl.SAMPLES_SHOWN_IN_SPECTROGRAM:
            gl.graph_frame.fft_vizualizer_values = gl.graph_frame.fft_vizualizer_values[-gl.SAMPLES_SHOWN_IN_SPECTROGRAM:]
            gl.graph_frame.fft_timestamps = gl.graph_frame.fft_timestamps[-gl.SAMPLES_SHOWN_IN_SPECTROGRAM:]
        fig = go.Figure(data=go.Surface(z=gl.graph_frame.fft_vizualizer_values, x = gl.graph_frame.frequencies, y = gl.graph_frame.fft_timestamps))
        fig.update_layout(
            scene=dict(
                xaxis = dict(range=gl.FREQUENCY_MIN_MAX_BOUND, showgrid=True, title="Frequency", showbackground=True, backgroundcolor="rgba(0, 0, 0,0)"),
                yaxis = dict(title="", showgrid=False, showbackground=True, backgroundcolor="rgba(0, 0, 0,0)",showticklabels=False),
                zaxis = dict(showgrid=True, title="", showticklabels=False),
                aspectmode = "manual",
                aspectratio = dict(x=7, y=4, z=1)),

            scene_camera = dict(
                eye=dict(x=-0.2, y=4.5, z=0.5)),
            
            )
        return fig
    print(len(gl.graph_frame.fft_values_buffer))
    return no_update

@callback(
    Output('main-plot', 'figure'),
    Input('interval-graph', 'n_intervals'),
    State('main-plot-selection', 'value')
)
def update_main_plot(n_intervals, current_plot):
    if gl.eeg_processor == None:
        return no_update

    if current_plot == 'Topoplot':
        return topoPlot()
    elif current_plot == 'Spectrogram':
        return spectrumPlot()
    else:
        return no_update

# @callback(
#     Output('auxiliary-plot-title', 'children'),
#     Input('auxiliary-plot-selection', 'value')
# )
# def update_auxiliary_plot(value):
#     return value
