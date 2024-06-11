import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from signalProcessor.EEGProcessor import *
from lslHandler.lslHandler import LslHandler
from signalProcessor.EEGProcessor import EEGProcessor
import visualizer.globals as g


N_SAMPLES = 1024
S_FREQU = 500


class VisualizerTopoPlot(FigureCanvas):
    def __init__(self, parent=None):
        self.eegprocessor = g.eeg_processor
        first_data = self.get_initial_data()
        self.data = first_data
        self.set_montage(first_data)
        mean_ch = np.mean(np.array(first_data), axis=0) 
        self.filter = Filter.NoNe
        

        self.fig, self.ax = plt.subplots()
        super(VisualizerTopoPlot, self).__init__(self.fig)
        self.setParent(parent)
        self.ax.set_title('Dynamic Plot')

        im, cn = mne.viz.plot_topomap(mean_ch, self.raw.info,axes=self.ax ,show=False)
        plt.colorbar(im, ax=self.ax)
                
        self.timer = self.fig.canvas.new_timer(interval=g.GRAPH_UPDATE_PAUSE_S)  # Update every 50 ms
        self.timer.add_callback(self.update_plot)
        self.timer.start()
    
    def update_plot(self):
        # self.line.set_ydata(np.sin(self.x + np.random.randn() * 0.1))  # Update data with some noise
        new_data = self.get_data()
        self.data = self.data[len(new_data):]
        self.data += new_data
        
        filtered_data = self.eegprocessor.filter_eeg_data(self.data, self.filter)
        # filtered_data = self.data
        mean_ch = np.mean(np.array(filtered_data), axis=0) 

        self.ax.clear()
        im, cn = mne.viz.plot_topomap(mean_ch, self.raw.info,axes=self.ax ,show=False)

        self.ax.figure.canvas.draw()
        self.ax.figure.canvas.flush_events()

    def get_initial_data(self):
        data = []
        while len(data) < N_SAMPLES:
            if(data_sample := self.eegprocessor.get_eeg_data_dict()) != None:
                self.channel_names = list(data_sample[0].keys())[:-10]
                data.append(list(data_sample[0].values())[:-10])
        return data
    
    def get_data(self):
        new_data = []

        if(new_chunk := self.eegprocessor.get_eeg_data_as_chunk(N_SAMPLES)) != None:
            new_data = [list(arr[0].values())[:-10] for arr in new_chunk]
        else: return None

        return new_data
    
        
    def set_montage(self, data):
        biosemi_montage = mne.channels.make_standard_montage('biosemi64')  # set a montage, see mne document
        index_list = []  # correspond channel
        for ch_name in self.channel_names:
            found = False
            for index, biosemi_name in enumerate(biosemi_montage.ch_names):
                if ch_name == biosemi_name:
                    index_list.append(index)
                    found=True

            assert(found)
        biosemi_montage.ch_names = [biosemi_montage.ch_names[i] for i in index_list]
        biosemi_montage.dig = [biosemi_montage.dig[i+3] for i in index_list]
        info = mne.create_info(ch_names=biosemi_montage.ch_names, sfreq=500., ch_types='eeg')  # sample rate

        self.raw = mne.io.RawArray(np.array(data).T , info)
        # raw = mne.io.RawArray(mean_data.T, info)
        self.raw.set_montage(biosemi_montage)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Dynamic Plot in Qt')
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        self.plot_canvas = VisualizerTopoPlot(central_widget)
        layout.addWidget(self.plot_canvas)
        
        self.show()

if __name__ == '__main__':
    streams = g.lsl_handler.get_all_lsl_streams()
    print([stream.name() for stream in streams])
    for stream in streams:
        g.lsl_handler.connect_to_specific_lsl_stream(stream)
        g.lsl_handler.start_data_recording_thread(stream)

    g.eeg_processor = EEGProcessor(g.lsl_handler, g.lsl_handler.get_stream_by_name("BrainVision RDA"))
    app = QApplication(sys.argv)
    main_app = App()
    sys.exit(app.exec_())