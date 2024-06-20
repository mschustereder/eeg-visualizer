from pyqtgraph.colormap import get
import pyqtgraph.opengl as gl
import pyqtgraph as pg
from OpenGL.GL import *
from PySide6 import QtGui, QtCore
import numpy as np
from signalProcessor import fft
import visualizer.globals as g
from statistics import mean
from visualizer.EEGGraphFrame import EEGGraphFrame
from visualizer.Visualizer3DColorBar import Visualizer3DColorBar
import threading
import time
from signalProcessor.EEGProcessor import EEGProcessor, Filter

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

        self.axe = CustomAxis(color=(255, 255, 255))
        self.axe.setSize(0, 0, 0)
        self.parent.addItem(self.axe)

        self.label = gl.GLTextItem(text = label, color = (255, 255, 255), font = QtGui.QFont("Helvetica", 12))
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
            tick_item = gl.GLTextItem(color = (255, 255, 255), font = QtGui.QFont("Helvetica", 12))
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
    update_spectrum_signal = QtCore.Signal()
    loading_buffer_start_signal = QtCore.Signal()
    loading_buffer_end_signal = QtCore.Signal()
    # eeg_processor : EEGProcessor
    #the values for x, y and z than can be seen from the camera
    x_range = 48
    y_range = 40
    z_range = 10
    
    def __init__(self, color_bar : Visualizer3DColorBar= None, cm = pg.colormap.get('turbo')):
        super().__init__()     
        self.setBackgroundColor(0, 0, 0)
        self.cm = cm
        self.color_bar = color_bar
        if self.color_bar is not None:
            self.color_bar.set_color_map(cm)
        self.graph_parameter_lock = threading.Lock()
        self.eeg_processor = g.eeg_processor
        self.eeg_processor_lock = g.eeg_processor_lock
        self.initialize(g.DEFAULT_FFT_SAMPLES, g.DEFAULT_SECONDS_SHOWN_IN_SPECTROGRAM)
        self.setCameraPosition(pos=QtGui.QVector3D(0, 0, 5), distance=40, elevation=7, azimuth=0)
        self.scale_factor_y = 1
        self.scale_factor_z = 1
        self.z_was_scaled = False
        self.filter_type = Filter.NoNe

        self.resized.connect(self.on_resized)

        self.frequency_ticks = YAxis(self, "Frequency (Hz)")
        frequency_range = g.FREQUENCY_MAX - g.FREQUENCY_MIN
        self.frequency_ticks.add_ticks(list(range(0, g.FREQUENCY_MAX+5, 5)), self.scale_factor_y, (-frequency_range/2 - g.FREQUENCY_MIN), -500)

        self.thread_end_event = threading.Event()
        self.update_spectrum_signal.connect(self.update_spectrum_from_thread)
        self.plotting_done_cond = threading.Condition()
        self.plotting_done = False
        self.start_thread()


    def setup_plot_item(self, item):
        self.addItem(item)

        # we want that the spectrum is always good visible, x and y can be scaled at the beginning, since the paramters don´t change during execution
        frequency_range = g.FREQUENCY_MAX - g.FREQUENCY_MIN
        scale_y = self.y_range/frequency_range
        if scale_y != 1:
            if (self.scale_factor_y == 1): #only change once
                self.scale_factor_y = self.scale_factor_y*scale_y
            item.scale(1, scale_y, 1)

        #value gotten through experimenting
        scale_x = 9.5
        if scale_x != 1:
            item.scale(scale_x, 1, 1)
        
        self.plot_item.translate(0, (-frequency_range/2 - g.FREQUENCY_MIN)*self.scale_factor_y, 0)

        self.frequency_ticks = YAxis(self, "Frequency (Hz)")
        frequency_range = g.FREQUENCY_MAX - g.FREQUENCY_MIN
        self.frequency_ticks.add_ticks(list(range(0, g.FREQUENCY_MAX+5, 5)), self.scale_factor_y, (-frequency_range/2 - g.FREQUENCY_MIN), -500)

        self.thread_end_event = threading.Event()
        self.update_spectrum_signal.connect(self.update_spectrum_from_thread)
        self.plotting_done_cond = threading.Condition()
        self.plotting_done = False
        self.start_thread()


    def setup_plot_item(self, item):
        self.addItem(item)

        # we want that the spectrum is always good visible, x and y can be scaled at the beginning, since the paramters don´t change during execution
        frequency_range = g.FREQUENCY_MAX - g.FREQUENCY_MIN
        scale_y = self.y_range/frequency_range
        if scale_y != 1:
            if (self.scale_factor_y == 1): #only change once
                self.scale_factor_y = self.scale_factor_y*scale_y
            item.scale(1, scale_y, 1)

        #value gotten through experimenting
        scale_x = 9.5
        if scale_x != 1:
            item.scale(scale_x, 1, 1)
        
        item.translate(0, (-frequency_range/2 - g.FREQUENCY_MIN)*scale_y, 0)

    def init_frequencies(self):
        sampling_rate = self.eeg_processor.stream.nominal_srate()
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

    def processor_thread_func(self):
        
        loading = False

        while(not self.thread_end_event.is_set()):
            self.eeg_processor_lock.acquire()

            if self.eeg_processor is None:
                self.eeg_processor_lock.release()
                time.sleep(g.GRAPH_UPDATE_PAUSE_S)
                continue
            
            data = self.eeg_processor.get_available_eeg_data()
            
            self.eeg_processor_lock.release()

            if data == None:
                time.sleep(g.GRAPH_UPDATE_PAUSE_S)
                continue

            mean_ch = None

            self.graph_parameter_lock.acquire()

            self.data.filter_values_buffer.extend(data[0])
            
            #while the buffer is loading we can just don´t apply the filter
            if len(self.data.filter_values_buffer) >= self.fft_buffer_len and self.filter_type != Filter.NoNe:
                self.data.filter_values_buffer = self.data.filter_values_buffer[-self.fft_buffer_len:] 
                filtered_data = self.eeg_processor.filter_eeg_data(self.data.filter_values_buffer, self.filter_type)
                mean_ch = np.mean(np.array(filtered_data), axis=1) 
            else:
                mean_ch = np.mean(np.array(data[0]), axis=1)

            self.data.fft_values_buffer.extend(mean_ch)

            #only update graph if accumulated data is FFT_SAMPLES samples long
            if len(self.data.fft_values_buffer) >= self.fft_buffer_len:
                
                if loading:
                    print("loading end")
                    self.loading_buffer_end_signal.emit()
                loading = False

                #we want to get a spectrum every 100ms, so we will calulate overlapping fft windows, and thus use the fft_values_buffer as a FIFO buffer
                self.data.fft_values_buffer = self.data.fft_values_buffer[-self.fft_buffer_len:] 
                sample_time = data[1][-1] - data[1][0] #this is the time that has passed in the sample world
                fft_magnitude_normalized = fft.calculate_fft(self.data.fft_values_buffer)
                self.prepare_data_for_plotting(fft_magnitude_normalized, sample_time)
                self.scale_z()
                self.data.colors = self.cm.map(np.array(self.data.fft_vizualizer_values)/np.amax(self.data.fft_vizualizer_values), pg.ColorMap.FLOAT)
                self.update_spectrum_signal.emit()
                self.graph_parameter_lock.release()
                self.plotting_done_cond.acquire()
                while self.plotting_done == False:
                    self.plotting_done_cond.wait()
                self.plotting_done_cond.release()
            else:
                self.graph_parameter_lock.release()
                if loading == False:
                    self.loading_buffer_start_signal.emit()
                    print("loading start")
                loading = True

            time.sleep(g.GRAPH_UPDATE_PAUSE_S)

    def initialize(self, fft_buffer_len, seconds_shown):
        self.graph_parameter_lock.acquire()
        self.max_value = 0
        self.below_max_count = 0
        self.data = EEGGraphFrame()
        self.fft_buffer_len = fft_buffer_len
        self.seconds_shown = seconds_shown
        self.z_was_scaled = False #not doing this causes wrong scaling when initialize is called during operation
        self.init_frequencies()
        self.graph_parameter_lock.release()


    def set_eeg_processor(self, eeg_processor):
        print("setting eeg processor")
        self.eeg_processor_lock.acquire()
        self.eeg_processor = eeg_processor
        self.initialize(self.fft_buffer_len, self.seconds_shown)
        self.eeg_processor_lock.release()


    def set_filter_type(self, filter_type : Filter):
        print("setting eeg processor")
        self.eeg_processor_lock.acquire()
        self.filter_type = filter_type
        self.initialize(self.fft_buffer_len, self.seconds_shown)
        self.eeg_processor_lock.release()

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
    
    def scale_z(self):
        #scale z axis
        old_max = self.max_value
        max_val = np.amax(self.data.fft_vizualizer_values)

        if max_val >= self.max_value:
            self.below_max_count = 0
            self.max_value = max_val
        else:
            self.below_max_count +=1

        #only scale up after enough time has passed
        if (self.below_max_count > g.EEG_GRAPH_Z_UP_SCALE_THRESHOLD):
            self.max_value *= g.EEG_GRAPH_Z_UP_SCALE_FACTOR
            # print("scale up")

        if old_max == self.max_value:
            return
        

        self.scale_factor_z = self.z_range/self.max_value
        if self.scale_factor_z != 1:
            self.z_was_scaled = True


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

    def update_spectrum_from_thread(self):
        pass

    def on_resized(self, evt=None):
        self.frequency_ticks.set_fontsizes_from_pixel_size(self.pixelSize(QtGui.QVector3D(0, 0, 0)))

    def stop_and_wait_for_process_thread(self):
        if hasattr(self, "processor_thread") and not self.processor_thread.is_alive(): return
        self.thread_end_event.set()
        self.processor_thread.join()

    def start_thread(self):
        if hasattr(self, "processor_thread") and self.processor_thread.is_alive(): return
        print("starting thread")
        self.processor_thread = threading.Thread(target=self.processor_thread_func)
        self.thread_end_event.clear()
        self.processor_thread.start()




class Visualizer3DSurface(Visualizer3D):


    def __init__(self, eeg_processor, color_bar: Visualizer3DColorBar = None, cm=pg.colormap.get('turbo')):

        self.plot_item = gl.GLSurfacePlotItem(np.zeros(10), np.zeros(10), np.zeros((10, 10)))
        super().__init__(eeg_processor, color_bar, cm)
        self.setup_plot_item(self.plot_item)

    def update_spectrum_from_thread(self):
        self.graph_parameter_lock.acquire()
        x = np.array(self.data.fft_timestamps)
        y = np.array(self.data.frequencies)
        z = np.array(self.data.fft_vizualizer_values)*self.scale_factor_z

        if len(self.data.fft_vizualizer_values) != 0:
            if self.z_was_scaled:
                if self.color_bar is not None:
                    self.color_bar.update_values([0, self.max_value])
                self.z_was_scaled = False

            self.plot_item.setData(x, y, z, self.data.colors)
            self.graph_parameter_lock.release()

        else:
            print("buffer empty, update spectrum was called right after change of parameters")
            self.graph_parameter_lock.release()

        self.plotting_done_cond.acquire()
        self.plotting_done = True
        self.plotting_done_cond.notify()
        self.plotting_done_cond.release()



class Visualizer3DLine(Visualizer3D):


    def __init__(self, color_bar: Visualizer3DColorBar = None, cm=pg.colormap.get('turbo')):

        self.traces = []
        super().__init__(color_bar, cm)
        self.setBackgroundColor(0, 0, 0)


    def update_spectrum_from_thread(self):
        self.graph_parameter_lock.acquire()

        if len(self.traces) < len(self.data.fft_vizualizer_values):
            diff = len(self.data.fft_vizualizer_values)-len(self.traces)
            for _ in range(len(self.traces), len(self.data.fft_vizualizer_values)):
                plt = gl.GLLinePlotItem(width=2, antialias=True)
                plt.setGLOptions("opaque")
                self.traces.append(plt)
                self.setup_plot_item(self.traces[-1])
            # print(f"added {diff} traces")

        elif len(self.traces) > len(self.data.fft_vizualizer_values):
            diff = len(self.traces)-len(self.data.fft_vizualizer_values)
            items_to_remove = self.traces[len(self.data.fft_vizualizer_values) :]
            for item in items_to_remove:
                self.removeItem(item)
            self.traces = self.traces[0: len(self.data.fft_vizualizer_values)]
            # print(f"removed {diff} traces")

        x = np.array(self.data.fft_timestamps)
        y = np.array(self.data.frequencies)
        z = np.array(self.data.fft_vizualizer_values)*self.scale_factor_z

        if len(self.data.fft_vizualizer_values) != 0:
            if self.z_was_scaled:
                if self.color_bar is not None:
                    self.color_bar.update_values([0, self.max_value])
                self.z_was_scaled = False

            
            for index, spec in enumerate(z):
                points = np.vstack([np.full((len(y)), x[index]), y, spec]).transpose()
                self.traces[index].setData(pos = points, color = self.data.colors[index])
            
            self.graph_parameter_lock.release()

        else:
            print("buffer empty, update spectrum was called right after change of parameters")
            self.graph_parameter_lock.release()

        self.plotting_done_cond.acquire()
        self.plotting_done = True
        self.plotting_done_cond.notify()
        self.plotting_done_cond.release()    
        


