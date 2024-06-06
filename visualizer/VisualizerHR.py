import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import numpy as np
import visualizer.globals as g
from visualizer.HRGraphFrame import HRGraphFrame
import random



class VisualizerHR(pg.PlotWidget):

    def __init__(self, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(parent, background, plotItem, **kargs)
        self.showGrid(x = True, y = True)
        self.setBackground((255, 255, 255))
        self.line_plot = self.plot(np.zeros(10), np.zeros(10), pen = pg.mkPen(color = (0, 0, 255)))
        self.setYRange(0, 1)
        self.data = HRGraphFrame()


    def cut_hr_buffer(self):
        # we only need the last 45 seconds
        time_diff = self.data.timestamps[-1]  - self.data.timestamps[0]
        if time_diff > g.HR_GRAPH_TIME_RANGE_SEC:
            cut_index = 0
            while((self.data.timestamps[cut_index]-self.data.timestamps[0]) < g.HR_GRAPH_TIME_RANGE_SEC and cut_index < len(self.data.timestamps)):
                cut_index +=1 
            self.data.timestamps = self.data.timestamps[cut_index:]
            self.data.graph_values = self.data.graph_values[cut_index:]

    def get_x_time_range(self):
        range_x=[0, 45]
        
        if len(self.data.timestamps) != 0:
            range_x = [self.data.timestamps[0], self.data.timestamps[0]+45]

        return range_x


    def update_graph(self):
        # if g.hr_processor == None:
        #     return no_update

        # data = None

        # if data == None:
        #     return no_update
        
        # if aux_selection == "BPM":
        #     data = g.hr_processor.get_bpm_data()
        # elif aux_selection == "RMSSD":
        #     data = g.hr_processor.get_rmssd_data()
        # elif aux_selection == "SDNN":
        #     data =  g.hr_processor.get_sdnn_data()
        # else:
        #     data =  g.hr_processor.get_poincare_ratio()


        self.data.graph_values.append(random.random())
        if len(self.data.timestamps) != 0:
            self.data.timestamps.append(self.data.timestamps[len(self.data.timestamps)-1] + 0.1)
        else:
            self.data.timestamps.append(0)
        
        self.cut_hr_buffer()
        self.setXRange(*self.get_x_time_range())

        self.line_plot.setData(self.data.timestamps, self.data.graph_values)
