import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from signalProcessor.EEGProcessor import *
from lslHandler.lslHandler import LslHandler
from signalProcessor.EEGProcessor import EEGProcessor
import visualizer.globals as g

class VisualizerTopoPlot(FigureCanvas):
    def __init__(self, parent=None):
        self.eegprocessor = g.eeg_processor
        self.window_size = g.DEFAULT_FFT_SAMPLES
        first_data = g.eeg_processor.get_specific_amount_of_eeg_samples_without_timestamps(self.window_size)
        self.data = first_data
        self.channel_names = g.eeg_processor.get_eeg_layout()
        self.set_montage(first_data)
        self.filter = Filter.NoNe
        self.fig, self.ax = plt.subplots()
        super(VisualizerTopoPlot, self).__init__(self.fig)
        self.setParent(parent)


        filtered_data = self.eegprocessor.filter_eeg_data(self.data, self.filter)
        mean_ch = np.mean(np.array(filtered_data), axis=0) 
        # mean_ch = np.mean(np.array(self.data), axis=0) 

        im, cn = mne.viz.plot_topomap(mean_ch, self.raw.info,axes=self.ax ,show=False, names = self.channel_names)
        self.cbar = self.fig.colorbar(im, ax=self.ax)
        self.cbar.set_label("µV")
                
        self.timer = self.fig.canvas.new_timer(interval=g.GRAPH_UPDATE_PAUSE_S)  # Update every 50 ms
        self.timer.add_callback(self.update_plot)
        self.timer.start()
    
    eegprocessor : EEGProcessor

    def update_plot(self):
        new_data = g.eeg_processor.get_available_eeg_data_without_timestamps(self.window_size)
        self.data = self.data[len(new_data):]
        self.data += new_data
        
        filtered_data = self.eegprocessor.filter_eeg_data(self.data, self.filter)
        mean_ch = np.mean(np.array(filtered_data), axis=0) 
        # mean_ch = np.mean(np.array(self.data), axis=0)

        self.ax.clear()
        im, cn = mne.viz.plot_topomap(mean_ch, self.raw.info,axes=self.ax ,show=False, names = self.channel_names)
        self.cbar.update_normal(im)
       
        self.ax.figure.canvas.draw()
        self.ax.figure.canvas.flush_events()

    def set_window_size(self, new_window_size):
        self.window_size = new_window_size
        self.data = g.eeg_processor.get_specific_amount_of_eeg_samples_without_timestamps(new_window_size)

    def set_filter(self, filter: Filter):
        self.filter = filter
        
    def set_montage(self, data):
        montage = mne.channels.make_standard_montage(g.USED_MNE_MONTAGE)  # set a montage, see mne document
        index_list = []  # correspond channel
        for ch_name in self.channel_names:
            found = False
            for index, biosemi_name in enumerate(montage.ch_names):
                if ch_name == biosemi_name:
                    index_list.append(index)
                    found=True

            assert(found)
        montage.ch_names = [montage.ch_names[i] for i in index_list]
        montage.dig = montage.dig[:3] + [montage.dig[i+3] for i in index_list]
        info = mne.create_info(ch_names=montage.ch_names, sfreq=g.eeg_processor.get_sampling_frequency(), ch_types='eeg')  # sample rate

        self.raw = mne.io.RawArray(np.array(data).T , info)
        # raw = mne.io.RawArray(mean_data.T, info)
        self.raw.set_montage(montage)

