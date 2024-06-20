import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from signalProcessor.EEGProcessor import *
from signalProcessor.EEGProcessor import EEGProcessor
import visualizer.globals as g
import threading
from pyqtgraph.Qt import QtCore
import time
from datetime import datetime
class VisualizerTopoPlot(FigureCanvas):

    update_graph_signal = QtCore.Signal()

    def __init__(self, parent=None):
        self.eeg_processor = g.eeg_processor
        self.eeg_processor_lock = g.eeg_processor_lock
        self.window_size = g.DEFAULT_FFT_SAMPLES
        with self.eeg_processor_lock:
            self.channel_names = self.eeg_processor.get_eeg_layout()
            self.sampling_frequency = self.eeg_processor.get_sampling_frequency()
        self.filter = Filter.NoNe
        self.initial_plot(parent)

        self.graph_parameter_lock = threading.Lock()
        self.thread_end_event = threading.Event()
        self.update_graph_signal.connect(self.update_plot)
        self.plotting_done_cond = threading.Condition()
        self.plotting_done = False


    def initial_plot(self, parent):
        self.fig, self.ax = plt.subplots()
        super(VisualizerTopoPlot, self).__init__(self.fig)
        self.setParent(parent)

        with self.eeg_processor_lock:
            first_data = self.eeg_processor.get_specific_amount_of_eeg_samples_without_timestamps(self.window_size)
            self.data = first_data
            self.set_montage(first_data)

            filtered_data = self.eeg_processor.filter_eeg_data(self.data, self.filter)
        mean_ch = np.mean(np.array(filtered_data), axis=0) 

        im, cn = mne.viz.plot_topomap(mean_ch, self.raw.info,axes=self.ax ,show=False, names = self.channel_names)
        self.cbar = self.fig.colorbar(im, ax=self.ax)
        self.cbar.set_label("µV")
                

    def data_processing_thread(self):
        while not self.thread_end_event.is_set():
            # print(f"thread: {datetime.now().time()}")
            with self.eeg_processor_lock:
                new_data = self.eeg_processor.get_specific_amount_of_eeg_samples_without_timestamps(self.window_size //4)
                if not new_data: continue
            
                with self.graph_parameter_lock:
                    self.data = self.data[len(new_data):]
                    self.data += new_data
                    # print(len(self.data))
                    
                    filtered_data = self.eeg_processor.filter_eeg_data(self.data, self.filter)
                    self.mean_ch = np.mean(np.array(filtered_data), axis=0) 

            self.update_graph_signal.emit()

            self.plotting_done_cond.acquire()
            while self.plotting_done == False:
                self.plotting_done_cond.wait()
            self.plotting_done_cond.release()

            time.sleep(g.GRAPH_UPDATE_PAUSE_S)

    def update_plot(self):
        assert not self.graph_parameter_lock.locked()
        with self.graph_parameter_lock:
            self.ax.clear()
            im, cn = mne.viz.plot_topomap(self.mean_ch, self.raw.info,axes=self.ax ,show=False, names = self.channel_names)
            self.cbar.update_normal(im)
        
            self.ax.figure.canvas.draw()
        
        self.plotting_done_cond.acquire()
        self.plotting_done = True
        self.plotting_done_cond.notify()
        self.plotting_done_cond.release()

    def set_window_size(self, new_window_size):
        with self.graph_parameter_lock:
            if new_window_size < self.window_size: #if window gets smaller just cut len of data_array
                self.data = self.data[:new_window_size]
            else:
                size_to_additionally_append = new_window_size - self.window_size
                with self.eeg_processor_lock:
                    self.data += self.eeg_processor.get_specific_amount_of_eeg_samples_without_timestamps(size_to_additionally_append)
            self.window_size = new_window_size

    def set_filter(self, filter: Filter):
        with self.graph_parameter_lock:
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
        info = mne.create_info(ch_names=montage.ch_names, sfreq=self.sampling_frequency, ch_types='eeg')  # sample rate

        self.raw = mne.io.RawArray(np.array(data).T , info)
        # raw = mne.io.RawArray(mean_data.T, info)
        self.raw.set_montage(montage)

    def stop_and_wait_for_process_thread(self):
        if hasattr(self, "processor_thread") and not self.processor_thread.is_alive(): return
        self.thread_end_event.set()
        self.processor_thread.join()

    def start_thread(self):
        if hasattr(self, "processor_thread") and self.processor_thread.is_alive(): return
        self.processor_thread = threading.Thread(target=self.data_processing_thread)
        self.thread_end_event.clear()
        self.processor_thread.start()
