import pyqtgraph.opengl as gl
from OpenGL.GL import *
from PySide6 import QtGui
import numpy as np
from signalProcessor import fft
import visualizer.globals as g
from statistics import mean
from visualizer.EEGGraphFrame import EEGGraphFrame
import time


class CustomAxis(gl.GLAxisItem):

    def __init__(self, size=None, antialias=True, glOptions='translucent', parentItem=None, color=(0,0,0)):
        super().__init__(size, antialias, glOptions, parentItem)
        self.color = color
        self.grid_positions = []

    def add_grid_lines(self, positions):
        self.grid_positions.extend(positions)

    # reimplement paint method to change color (took original implementation and only changed colors)
    def paint(self):
        self.setupGLState()
        
        if self.antialias:
            glEnable(GL_LINE_SMOOTH)
            glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
            
        glBegin(GL_LINES)
        
        x,y,z = self.size()

        if len(self.color) ==4:
            glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])
        else:
            glColor4f(self.color[0], self.color[1], self.color[2], 1)

        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, z)

        glVertex3f(0, 0, 0)
        glVertex3f(0, y, 0)

        glVertex3f(0, 0, 0)
        glVertex3f(x, 0, 0)

        #draw gridlines
        for pos in self.grid_positions:
            glVertex3f(pos[0][0], pos[0][1], pos[0][2])
            glVertex3f(pos[1][0], pos[1][1], pos[1][2])

        glEnd()


class YAxis():

    def __init__(self, parent : gl.GLViewWidget, label) -> None:
        self.ticks_items = []
        self.parent = parent
        self.x_tick_offset = 1.5
        self.z_tick_offset = -1

        self.x_label_offset = 5
        self.z_label_offset = -1.5

        self.axe = CustomAxis()
        self.axe.setSize(0, 0, 0)
        self.parent.addItem(self.axe)

        self.label = gl.GLTextItem(text = label, color = (0, 0, 0), font = QtGui.QFont("Helvetica", 12))
        self.label.translate(self.x_label_offset, 0, self.z_label_offset)
        self.parent.addItem(self.label)

    def get_font_size_from_current_pixel_size(self, pixel_size):
        #linear function that turns pixel size relative to coordinate size into font size, the parameters k and d are gotten through experimentation
        k = -133
        d = 17.32
        return max(int(round(k*pixel_size + d)), 3)

    def add_ticks(self, ticks, scaling_factor, zero_pos, grid_len):
        positions = []
        #add ticks on their respective position
        for tick in ticks:
            tick_item = gl.GLTextItem(color = (0, 0, 0), font = QtGui.QFont("Helvetica", 12))
            tick_item.setData(text = str(tick))
            tick_item.translate(self.x_tick_offset, (tick+zero_pos)*scaling_factor, self.z_tick_offset)
            self.parent.addItem(tick_item)
            self.ticks_items.append((tick_item, tick))
            positions.append(((0, tick*scaling_factor, 0), (grid_len, tick*scaling_factor, 0)))

        #make axe fitting to size of ticks
        max = np.amax(np.array(self.ticks_items)[:, 1:])
        min = np.amin(np.array(self.ticks_items)[:, 1:])
        range = max-min
        self.axe.setSize(0, range*scaling_factor, 0)
        self.axe.translate(0, (zero_pos+min)*scaling_factor, 0)
        self.axe.add_grid_lines(positions)
        self.label.translate(0, range/2*scaling_factor*0.5, 0)


    def set_fontsizes_from_pixel_size(self, pixel_size):
        self.label.setData(font =  QtGui.QFont("Helvetica", self.get_font_size_from_current_pixel_size(pixel_size)))
        for tick in self.ticks_items:
            tick[0].setData(font =  QtGui.QFont("Helvetica", self.get_font_size_from_current_pixel_size(pixel_size)))


class Visualizer3D(gl.GLViewWidget):
    grid_size = 200
    grid_space = 5

    #the values for x, y and z than can be seen from the camera
    x_range = 48
    y_range = 40
    z_range = 10
    
    def __init__(self):
        super().__init__()     
        self.setBackgroundColor(255, 255, 255)

        self.plot_item = gl.GLSurfacePlotItem(np.zeros(10), np.zeros(10), np.zeros((10, 10)))
        self.addItem(self.plot_item)
        self.initialize(g.DEFAULT_FFT_SAMPLES, g.DEFAULT_SECONDS_SHOWN_IN_SPECTROGRAM)
        self.setCameraPosition(pos=QtGui.QVector3D(0, 0, 5), distance=40, elevation=7, azimuth=0)
        self.scale_factor_x = 1
        self.scale_factor_y = 1
        self.scale_factor_z = 1

        self.resized.connect(self.on_resized)

        # we want that the spectrum is always good visible, x and y can be scaled at the beginning, since the paramters don´t change during execution
        frequency_range = g.FREQUENCY_MAX - g.FREQUENCY_MIN
        scale_y = self.y_range/frequency_range
        if scale_y != 1:
            self.scale_factor_y = self.scale_factor_y*scale_y
            self.plot_item.scale(1, scale_y, 1)

        #value gotten through experimenting
        scale_x = 9.5
        if scale_x != 1:
            self.scale_factor_x = self.scale_factor_x*scale_x
            print(self.scale_factor_x)
            self.plot_item.scale(scale_x, 1, 1)
        
        self.plot_item.translate(0, (-frequency_range/2 - g.FREQUENCY_MIN)*self.scale_factor_y, 0)

        self.frequency_ticks = YAxis(self, "Frequency (Hz)")
        self.frequency_ticks.add_ticks(list(range(0, g.FREQUENCY_MAX+5, 5)), self.scale_factor_y, (-frequency_range/2 - g.FREQUENCY_MIN), -500)


    def init_frequencies(self):
        sampling_rate = g.eeg_processor.stream.nominal_srate()
        frequencies = fft.calculate_frequencies(self.fft_buffer_len, sampling_rate)

        #we dont want the offset a 0 Hz included, so we will cut off every frequency below 1 Hz
        cut_index_bottom = 0
        while(frequencies[cut_index_bottom] < g.FREQUENCY_MIN):
            cut_index_bottom += 1

        #we can also cut anything above FREQUENCY_CUT_OFF
            
        cut_index_top = 0
        while(frequencies[cut_index_top] < g.FREQUENCY_MAX):
            cut_index_top += 1

        self.frequency_cut_index_bottom = cut_index_bottom
        self.frequency_cut_index_top = cut_index_top

        self.data.frequencies = frequencies[self.frequency_cut_index_bottom:self.frequency_cut_index_top]


    def initialize(self, fft_buffer_len, seconds_shown):
        self.max = 0
        self.below_max_count = 0
        self.data = EEGGraphFrame()
        self.fft_buffer_len = fft_buffer_len
        self.seconds_shown = seconds_shown
        self.init_frequencies()

    #disable all interaction mechanisms by overriding the corresponding functions
        
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

    def set_fft_buffer_len(self, len):
        print("set fft buffer len shown")
        assert len%2==0
        self.initialize(len, self.seconds_shown)

    def set_seconds_shown(self, seconds_shown):
        print("set seconds shown")
        self.initialize(self.fft_buffer_len, seconds_shown)

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
    
    def scale_z(self):
        #scale z axis
        max_val = np.amax(self.data.fft_vizualizer_values)

        if max_val >= self.max:
            self.below_max_count = 0
            self.max = max_val
        else:
            self.below_max_count +=1

        #only scale up after enough time has passed
        if (self.below_max_count > g.EEG_GRAPH_Z_UP_SCALE_THRESHOLD):
            self.max *= g.EEG_GRAPH_Z_UP_SCALE_FACTOR
            print("scale up")

        shown_max = self.max*self.scale_factor_z
        scale_z = self.z_range/shown_max
        if scale_z != 1:
            self.scale_factor_z = self.scale_factor_z*scale_z
            self.plot_item.scale(1, 1, scale_z)

    def prepare_data_for_plotting(self, fft_magnitude_normalized, sample_time):
            #cut away frequencies we don´t need
            self.data.fft_vizualizer_values.append(fft_magnitude_normalized[self.frequency_cut_index_bottom:self.frequency_cut_index_top])

            #we want to the past to go into -x direction, so we will set the new value as time 0
            arr = np.array(self.data.fft_timestamps)
            self.data.fft_timestamps = list(arr-sample_time)
            self.data.fft_timestamps.append(0)


            if abs(self.data.fft_timestamps[0]) > self.seconds_shown:
                cut_time_index = 0
                while(abs(self.data.fft_timestamps[cut_time_index]) > self.seconds_shown):
                    cut_time_index += 1

                self.data.fft_vizualizer_values = self.data.fft_vizualizer_values[cut_time_index:]
                self.data.fft_timestamps = self.data.fft_timestamps[cut_time_index:]

    def update_spectrum(self):
        data = g.eeg_processor.get_eeg_data_as_chunk()

        if data == None:
            return
        
        for sample in data:
            self.data.fft_values_buffer.append(mean(list(sample[0].values())))

        #only update graph if accumulated data is FFT_SAMPLES samples long
        if len(self.data.fft_values_buffer) >= self.fft_buffer_len:

            #we want to get a spectrum every 100ms, so we will calulate overlapping fft windows, and thus use the fft_values_buffer as a FIFO buffer
            self.data.fft_values_buffer = self.data.fft_values_buffer[-self.fft_buffer_len:] 
            sample_time = data[-1][1] - data[0][1] #this is the time that has passed in the sample world
            fft_magnitude_normalized = fft.calculate_fft(self.data.fft_values_buffer)
            self.prepare_data_for_plotting(fft_magnitude_normalized, sample_time)
            self.scale_z()
            x = np.array(self.data.fft_timestamps)
            y = np.array(self.data.frequencies)
            z = np.array(self.data.fft_vizualizer_values)
            colors = np.array(self.__get_colors(z, self.max))
            self.plot_item.setData(x, y, z, colors = colors)

    def on_resized(self, evt=None):
        self.frequency_ticks.set_fontsizes_from_pixel_size(self.pixelSize(QtGui.QVector3D(0, 0, 0)))
