import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from signalProcessor.EEGProcessor import *
from lslHandler.lslHandler import LslHandler
from signalProcessor.EEGProcessor import EEGProcessor
import visualizer.globals as g


N_SAMPLES = 1024
S_FREQU = 500
AMOUNT_OF_CHANNELS_TO_USE = 28

class VisualizerTopoPlot(FigureCanvas):
    def __init__(self, parent=None):
        self.eegprocessor = g.eeg_processor
        first_data = g.eeg_processor.get_specific_amount_of_eeg_samples_without_timestamps(N_SAMPLES)
        first_data = [liste[:AMOUNT_OF_CHANNELS_TO_USE] for liste in first_data] #THIS IS ONLY NECESSARY FOR THE TEST XDF FILE-REMOVE AFER TEST PHASE
        self.data = first_data
        self.channel_names = g.eeg_processor.get_eeg_layout()[:AMOUNT_OF_CHANNELS_TO_USE]
        self.set_montage(first_data)
        self.filter = Filter.NoNe
        
        self.fig, self.ax = plt.subplots()
        super(VisualizerTopoPlot, self).__init__(self.fig)
        self.setParent(parent)


        filtered_data = self.eegprocessor.filter_eeg_data(self.data, self.filter)
        mean_ch = np.mean(np.array(filtered_data), axis=0) 
        # mean_ch = np.mean(np.array(self.data), axis=0) 

        im, cn = mne.viz.plot_topomap(mean_ch, self.raw.info,axes=self.ax ,show=False)
        cbar = self.fig.colorbar(im, ax=self.ax)
        cbar.set_label("µV")
                
        self.timer = self.fig.canvas.new_timer(interval=g.EEG_GRAPH_INTERVAL_MS)  # Update every 50 ms
        self.timer.add_callback(self.update_plot)
        self.timer.start()
    
    eegprocessor : EEGProcessor

    def update_plot(self):
        new_data = g.eeg_processor.get_available_eeg_data_without_timestamps()
        new_data = [liste[:AMOUNT_OF_CHANNELS_TO_USE] for liste in new_data] #THIS IS ONLY NECESSARY FOR THE TEST XDF FILE-REMOVE AFER TEST PHASE
        self.data = self.data[len(new_data):]
        self.data += new_data
        
        filtered_data = self.eegprocessor.filter_eeg_data(self.data, self.filter)
        mean_ch = np.mean(np.array(filtered_data), axis=0) 
        # mean_ch = np.mean(np.array(self.data), axis=0)

        self.ax.clear()
        im, cn = mne.viz.plot_topomap(mean_ch, self.raw.info,axes=self.ax ,show=False)
       
        self.ax.figure.canvas.draw()
        self.ax.figure.canvas.flush_events()

   
        
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

