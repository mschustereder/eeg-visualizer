import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import numpy as np
import visualizer.globals as g
from visualizer.HRGraphFrame import HRGraphFrame
import time
from enum import Enum, auto


class HR_BIO_VARIABLE(Enum):
    BPM = auto()
    RMSSD = auto()
    SDNN = auto()
    POI_RAT = auto()


class VisualizerHR(pg.PlotWidget):

    def __init__(self, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(parent, background, plotItem, **kargs)
        self.showGrid(x = True, y = True)
        self.setBackground((255, 255, 255))
        self.line_plot = self.plot(np.zeros(10), np.zeros(10), pen = pg.mkPen(color = (0, 0, 255)))
        self.hideButtons()
        self.setMouseEnabled(False, False)
        self.data = HRGraphFrame()
        self.graph_start_time = time.time()
        self.set_bio_variable(HR_BIO_VARIABLE.BPM)
        #time axis label
        self.setLabel('bottom', 'Time', units ='s')


    def cut_hr_buffer(self):
        # we only need the last HR_GRAPH_TIME_RANGE_SEC seconds
        time_diff = self.data.timestamps[-1]  - self.data.timestamps[0]
        if time_diff > g.HR_GRAPH_TIME_RANGE_SEC:
            cut_index = 0
            while((self.data.timestamps[cut_index]-self.data.timestamps[0]) < g.HR_GRAPH_TIME_RANGE_SEC and cut_index < len(self.data.timestamps)):
                cut_index +=1 
            self.data.timestamps = self.data.timestamps[cut_index:]
            self.data.graph_values = self.data.graph_values[cut_index:]

    def get_x_time_range(self):
        range_x=[0, g.HR_GRAPH_TIME_RANGE_SEC]
        
        if len(self.data.timestamps) != 0:
            range_x = [self.data.timestamps[0], self.data.timestamps[0]+g.HR_GRAPH_TIME_RANGE_SEC]

        return range_x
    

    def set_bio_variable(self, bio_variable : HR_BIO_VARIABLE):
        self.bio_variable = bio_variable
        self.data = HRGraphFrame()
        self.max = None
        self.below_max_count = 0

        #set y label accordingly
        match self.bio_variable:

            case HR_BIO_VARIABLE.BPM:
                self.setLabel('left', 'BPM', units ='1')
            case HR_BIO_VARIABLE.RMSSD:
                self.setLabel('left', 'RMSSD', units ='1')
            case HR_BIO_VARIABLE.SDNN:
                self.setLabel('left', 'SDNN', units ='1')
            case HR_BIO_VARIABLE.POI_RAT:
                self.setLabel('left', 'Poincare ratio', units ='1')
            case _:
                raise ValueError("invalid bio variable")

    def get_y_range(self):
        curr_max = np.amax(self.data.graph_values)
        
        if (self.max is None or curr_max > self.max):
            self.max = curr_max*1.2
            self.below_max_count = 0
        elif curr_max < self.max*0.5:
            self.below_max_count += 1
            

        #only scale up after enough time has passed
        if (self.below_max_count > g.HR_GRAPH_Y_UP_SCALE_THRESHOLD):
            self.max *= g.HR_GRAPH_Y_UP_SCALE_FACTOR
            print("scale up y")

        return [0, self.max]

    def update_graph(self):
        if g.hr_processor == None:
            return

        data = None
        sample = None

        match self.bio_variable:

            case HR_BIO_VARIABLE.BPM:
                data = g.hr_processor.get_bpm_data() # tupple ([sample], timestamp)
                if data is not None:
                    sample = data[0]
            case HR_BIO_VARIABLE.RMSSD:
                data = g.hr_processor.get_rmssd_data() #float val
                if data is not None:
                    sample = [data]
            case HR_BIO_VARIABLE.SDNN:
                data =  g.hr_processor.get_sdnn_data() #float val
                if data is not None:
                    sample = [data]
            case HR_BIO_VARIABLE.POI_RAT:
                data =  g.hr_processor.get_poincare_ratio() #float val
                if data is not None:
                    sample = [data]
            case _:
                raise ValueError("invalid bio variable")


        if data is None:

            if (len(self.data.graph_values) != 0):
                sample = [self.data.graph_values[-1]]
            else:
                sample = [0]
        
        timestamp = time.time() - self.graph_start_time

        self.data.graph_values.extend(sample)
        self.data.timestamps.append(timestamp)
        
        self.cut_hr_buffer()
        self.setXRange(*self.get_x_time_range())
        self.setYRange(*self.get_y_range())


        self.line_plot.setData(self.data.timestamps, self.data.graph_values)
