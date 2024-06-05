import pyqtgraph.opengl as gl
from PySide6 import QtGui
import numpy as np
from signalProcessor import fft
import visualizer.globals as g
from statistics import mean

#todo: retrive x and z scale from data


class Visualizer3D(gl.GLViewWidget):
    grid_size = 200
    grid_space = 5

    #the values for x and z than can be seen from the camera
    x_range = 48
    z_range = 0
    
    def __init__(self):
        super(Visualizer3D, self).__init__()     
        self.setBackgroundColor(255, 255, 255)
        self.grid_item = gl.GLGridItem()
        self.grid_item.setColor((0, 0, 0, 80))
        self.grid_item.setSize(self.grid_size, self.grid_size)
        self.grid_item.setSpacing(self.grid_space, self.grid_space)
        self.addItem(self.grid_item)
        self.plot_item = gl.GLSurfacePlotItem(np.zeros(10), np.zeros(10), np.zeros((10, 10)))
        self.addItem(self.plot_item)
        frequency_range = g.FREQUENCY_MIN_MAX_BOUND[1] - g.FREQUENCY_MIN_MAX_BOUND[0]
        self.plot_item.translate(0, frequency_range/2-1, 0)
        self.setCameraPosition(elevation=5, azimuth=-1, distance=80)
        self.accumulated_scale_factor = 1

    def wheelEvent(self, ev):
        pass

    def keyPressEvent(self, ev):
        pass

    def keyReleaseEvent(self, ev):
        pass
    
    def mouseReleaseEvent(self, ev):
        pass

    def mousePressEvent(self, ev):
        pass

    def mouseMoveEvent(self, ev):
        pass

    def __get_colors(self, values, max_val):
        colors=[]
        gradient_red_max = g.SPECTRUM_GRAPH_GRADIENT_TOP_COLOR[0]
        gradient_red_min = g.SPECTRUM_GRAPH_GRADIENT_BOTTOM_COLOR[0]
        gradient_green_max = g.SPECTRUM_GRAPH_GRADIENT_TOP_COLOR[1]
        gradient_green_min = g.SPECTRUM_GRAPH_GRADIENT_BOTTOM_COLOR[1]
        gradient_blue_max = g.SPECTRUM_GRAPH_GRADIENT_TOP_COLOR[2]
        gradient_blue_min = g.SPECTRUM_GRAPH_GRADIENT_BOTTOM_COLOR[2]
        for row in values:
            color_row = []
            for value in row:
                percentage = value/max_val
                red = gradient_red_min +  percentage * (gradient_red_max-gradient_red_min)
                green = gradient_green_min + percentage * (gradient_green_max-gradient_green_min)
                blue = gradient_blue_min + percentage * (gradient_blue_max-gradient_blue_min)
                color_row.append([red/255, green/255, blue/255])
            colors.append(color_row)
        return colors


    def update_spectrum(self):
        data = g.eeg_processor.get_eeg_data_as_chunk()

        if data == None:
            return
        
        for sample in data:
            g.main_graph_frame.fft_values_buffer.append(mean(list(sample[0].values())))

        #only update graph if accumulated data is FFT_SAMPLES samples long
        if len(g.main_graph_frame.fft_values_buffer) >= g.FFT_SAMPLES:

            #we want to get a spectrum every 100ms, so we will calulate overlapping fft windows, and thus use the fft_values_buffer as a FIFO buffer
            g.main_graph_frame.fft_values_buffer = g.main_graph_frame.fft_values_buffer[-g.FFT_SAMPLES:] 
            sampling_rate = g.eeg_processor.stream.nominal_srate()
            sample_time = data[-1][1] - data[0][1] #this is the time that has passed in the sample world
            frequency, fft_magnitude_normalized = fft.calculate_fft(g.main_graph_frame.fft_values_buffer, sampling_rate)

            # we want that the spectrum is always good visible, theoretically we always show g.EEG_GRAPH_INTERVAL_MS*0.001* g.SAMPLES_SHOWN_IN_SPECTROGRAM seconds so we will use this to scale the graph
            shown = (g.EEG_GRAPH_INTERVAL_MS*0.001* g.SAMPLES_SHOWN_IN_SPECTROGRAM)*self.accumulated_scale_factor
            scale = self.x_range/shown
            if scale != 1:
                self.accumulated_scale_factor = self.accumulated_scale_factor*scale
                self.plot_item.scale(scale, 1, 1) # scale is relative i.e if it was scaled before it will scale the already scaled values

            #we dont want the offset a 0 Hz included, so we will cut off every frequency below 1 Hz
            cut_index = 0
            while(frequency[cut_index] < 1):
                cut_index += 1

            #we can also cut anything above FREQUENCY_CUT_OFF
                
            cut_index_top = 0
            while(frequency[cut_index_top] < g.FREQUENCY_CUT_OFF):
                cut_index_top += 1

            g.main_graph_frame.frequencies = frequency[cut_index:cut_index_top]
            g.main_graph_frame.fft_vizualizer_values.append(fft_magnitude_normalized[cut_index:cut_index_top])

            #we are using relative times from the first sample to the last sample in the fft_visualizer_values
            if len(g.main_graph_frame.fft_timestamps)==0:
                g.main_graph_frame.fft_timestamps.append(sample_time)
            else:
                g.main_graph_frame.fft_timestamps.append(g.main_graph_frame.fft_timestamps[-1] + sample_time)

            
            #only show the last SAMPLES_SHOWN_IN_SPECTROGRAM samples
            if len(g.main_graph_frame.fft_vizualizer_values) > g.SAMPLES_SHOWN_IN_SPECTROGRAM:
                g.main_graph_frame.fft_vizualizer_values = g.main_graph_frame.fft_vizualizer_values[-g.SAMPLES_SHOWN_IN_SPECTROGRAM:]
                time_shift_start = g.main_graph_frame.fft_timestamps[0]
                g.main_graph_frame.fft_timestamps = g.main_graph_frame.fft_timestamps[-g.SAMPLES_SHOWN_IN_SPECTROGRAM:]
                    
                #move graph so that is stays in the center
                time_shift = g.main_graph_frame.fft_timestamps[0]-time_shift_start
                #since .scale() got called at the beginning all values are multiplied by self.accumulated_scale_factor so we have to consider this, when shifting the graph
                self.plot_item.translate(-time_shift*self.accumulated_scale_factor, 0, 0)

                x = np.array(g.main_graph_frame.fft_timestamps)
                y = np.array(g.main_graph_frame.frequencies)
                z = np.array(g.main_graph_frame.fft_vizualizer_values)
                max_val = np.amax(g.main_graph_frame.fft_vizualizer_values)
                colors = np.array(self.__get_colors(z, max_val))
                self.plot_item.setData(x, y, z, colors = colors)
            
            