import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import numpy as np
import visualizer.globals as g
from visualizer.HRGraphFrame import HRGraphFrame, BioVariableGraphSettings
import time
from enum import Enum, auto
import threading


class HR_BIO_VARIABLE(Enum):
    BPM = auto()
    RMSSD = auto()
    SDNN = auto()
    POI_RAT = auto()


class VisualizerHR(pg.PlotWidget):

    update_graph_signal = QtCore.Signal()

    def __init__(self, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(parent, background, plotItem, **kargs)
        self.showGrid(x = True, y = True)
        self.setBackground((255, 255, 255))
        self.line_plot = self.plot(np.zeros(10), np.zeros(10), pen = pg.mkPen(color = (0, 0, 255), width = 2))
        self.hideButtons()
        self.setMouseEnabled(False, False)
        self.data = HRGraphFrame()
        self.graph_start_time = time.time()
        self.set_bio_variable(HR_BIO_VARIABLE.BPM)
        #time axis label
        self.setLabel('bottom', 'Time', units ='s')
        self.hr_processor_lock = g.hr_processor_lock
        self.hr_processor = g.hr_processor

        self.graph_parameter_lock = threading.Lock()
        self.thread_end_event = threading.Event()
        self.update_graph_signal.connect(self.update_graph_from_thread)
        self.processor_thread = threading.Thread(target=self.processor_thread_func)
        self.plotting_done_cond = threading.Condition()
        self.plotting_done = False
        self.processor_thread.start()

    
    def processor_thread_func(self):
        while(not self.thread_end_event.is_set()):
            
            self.hr_processor_lock.acquire()

            if g.hr_processor == None:
                time.sleep(g.GRAPH_UPDATE_PAUSE_S)
                return
            bpm, rmssd, sdnn, poi_rat = g.hr_processor.get_all_bio_vars()
            self.hr_processor_lock.release()

            self.graph_parameter_lock.acquire()

            timestamp = time.time() - self.graph_start_time
            # if bpm is not None:
            #     bpm = bpm[0][0]

            self._add_data(timestamp, self.data.timestamps_bpm, bpm, self.data.bpm_values)
            self._add_data(timestamp, self.data.timestamps_rmssd, rmssd, self.data.rmssd_values)
            self._add_data(timestamp, self.data.timestamps_sdnn, sdnn, self.data.sdnn_values)
            self._add_data(timestamp, self.data.timestamps_poi_rat, poi_rat, self.data.poi_rat_values)

            self.data.timestamps_bpm, self.data.bpm_values = self._cut_hr_buffer(self.data.timestamps_bpm, self.data.bpm_values)
            self.data.timestamps_rmssd, self.data.rmssd_values = self._cut_hr_buffer(self.data.timestamps_rmssd, self.data.rmssd_values)
            self.data.timestamps_sdnn, self.data.sdnn_values = self._cut_hr_buffer(self.data.timestamps_sdnn, self.data.sdnn_values)
            self.data.timestamps_poi_rat, self.data.poi_rat_values = self._cut_hr_buffer(self.data.timestamps_poi_rat, self.data.poi_rat_values)

            self._set_y_range(self.data.bpm_values, self.data.bpm_settings)
            self._set_y_range(self.data.rmssd_values, self.data.rmssd_settings)
            self._set_y_range(self.data.sdnn_values, self.data.sdnn_settings)
            self._set_y_range(self.data.poi_rat_values, self.data.poi_rat_settings)

            self.graph_parameter_lock.release()
            self.update_graph_signal.emit()

            self.plotting_done_cond.acquire()
            while self.plotting_done == False:
                self.plotting_done_cond.wait()
            self.plotting_done_cond.release()

            time.sleep(g.GRAPH_UPDATE_PAUSE_S)

    def _cut_hr_buffer(self, timestamps, values):
        # we only need the last HR_GRAPH_TIME_RANGE_SEC seconds
        if len(timestamps) != 0:
            time_diff = timestamps[-1]  - timestamps[0]
            if time_diff > g.HR_GRAPH_TIME_RANGE_SEC:
                cut_index = 0
                while((timestamps[cut_index]-timestamps[0]) < g.HR_GRAPH_TIME_RANGE_SEC and cut_index < len(timestamps)):
                    cut_index +=1 
                return timestamps[cut_index:], values[cut_index:]
            
        return timestamps, values

    def get_x_time_range(self, timestamps):
        range_x=[0, g.HR_GRAPH_TIME_RANGE_SEC]
        
        if len(timestamps) != 0:
            range_x = [timestamps[0], timestamps[0]+g.HR_GRAPH_TIME_RANGE_SEC]

        return range_x
    
    def set_hr_processor(self, hr_processor):
        print("setting hr processor")
        self.hr_processor_lock.acquire()
        self.hr_processor = hr_processor
        self.data = HRGraphFrame()
        self.graph_start_time = time.time()
        self.hr_processor_lock.release()

    def set_bio_variable(self, bio_variable : HR_BIO_VARIABLE):
        self.bio_variable = bio_variable

        #set y label accordingly
        if self.bio_variable == HR_BIO_VARIABLE.BPM:
            self.setLabel('left', 'BPM', units ='1')
        elif self.bio_variable == HR_BIO_VARIABLE.RMSSD:
            self.setLabel('left', 'RMSSD', units ='1')
        elif self.bio_variable == HR_BIO_VARIABLE.SDNN:
            self.setLabel('left', 'SDNN', units ='1')
        elif self.bio_variable == HR_BIO_VARIABLE.POI_RAT:
            self.setLabel('left', 'Poincare ratio', units ='1')
        else:
            raise ValueError("invalid bio variable")
        

    def _set_y_range(self, values, settings: BioVariableGraphSettings):

        if len(values)==0:
            return

        curr_max = np.amax(values)
        if (settings.max is None or curr_max > settings.max):
            settings.max = curr_max*1.2
            settings.below_max_count = 0
        elif curr_max < settings.max*0.5:
            settings.below_max_count += 1
            

        #only scale up after enough time has passed
        if (settings.below_max_count > g.HR_GRAPH_Y_UP_SCALE_THRESHOLD):
            settings.max *= g.HR_GRAPH_Y_UP_SCALE_FACTOR
            print("scale up y")
        

    def _add_data(self, new_timestamp, timestamps, new_value, values):
        if new_value is None or np.isnan(new_value):

            if (len(values) != 0):
                values.append(values[-1])
                timestamps.append(new_timestamp)
        else:
            values.append(new_value)
            timestamps.append(new_timestamp)


    def update_graph_from_thread(self):
        #these variables act like a pointer
        value_buffer = None
        timestamp_buffer = None
        settings = None

        self.graph_parameter_lock.acquire()
            
        if self.bio_variable == HR_BIO_VARIABLE.BPM:
            value_buffer = self.data.bpm_values
            timestamp_buffer = self.data.timestamps_bpm
            settings = self.data.bpm_settings
        elif self.bio_variable == HR_BIO_VARIABLE.RMSSD:
            value_buffer = self.data.rmssd_values
            timestamp_buffer = self.data.timestamps_rmssd
            settings = self.data.rmssd_settings
        elif self.bio_variable == HR_BIO_VARIABLE.SDNN:
            value_buffer = self.data.sdnn_values
            timestamp_buffer = self.data.timestamps_sdnn
            settings = self.data.sdnn_settings
        elif self.bio_variable == HR_BIO_VARIABLE.POI_RAT:
            value_buffer = self.data.poi_rat_values
            timestamp_buffer = self.data.timestamps_poi_rat
            settings = self.data.poi_rat_settings
        else:
            raise ValueError("invalid bio variable")

        self.setXRange(*self.get_x_time_range(timestamp_buffer))
        self.setYRange(0, settings.max)
        self.line_plot.setData(timestamp_buffer, value_buffer)

        self.graph_parameter_lock.release()

        self.plotting_done_cond.acquire()
        self.plotting_done = True
        self.plotting_done_cond.notify()
        self.plotting_done_cond.release()

    def stop_and_wait_for_process_thread(self):
        self.thread_end_event.is_set()
        self.processor_thread.join()