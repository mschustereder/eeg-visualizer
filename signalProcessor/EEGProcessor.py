from  lslHandler.lslHandler import LslHandler
from pylsl import StreamInfo
from typing import Dict, Tuple, List
import numpy as np
import mne
import matplotlib.pyplot as plt

DELTA_BAND = (0.1,4)
THETA_BAND = (4,8)
ALPHA_BAND = (8,13)
BETA_BAND = (13,30)
GAMMA_BAND = (30,100)
#Source: https://de.wikipedia.org/wiki/Elektroenzephalografie#EEG-Frequenzb%C3%A4nder_und_Graphoelemente

class EEGProcessor:
    def __init__(self, lslhandler: LslHandler, stream : StreamInfo): #Must be called after connecting to EEG stream to get the layout
        self.lslhandler = lslhandler
        self.stream = stream
        self.sampling_frequency = stream.nominal_srate()
        inlet = lslhandler.get_inlet(stream)
        info = inlet.info()
        channels = info.desc().child('channels').child('channel')
        while channels.name() == 'channel':
            label = channels.child_value('label')
            if label:
                self.eeg_layout.append(label)
            channels = channels.next_sibling()
        
            
    lslhandler : LslHandler
    stream : StreamInfo
    eeg_layout = [] #store as list since the order matters
    first_timestamp = 0
    sampling_frequency = 0

    def get_eeg_data_dict(self):
        data_dict = {}

        data = self.lslhandler.get_data_sample(self.stream)
        if data != None:
            channel_data = data[0]
            timestamp = data[1]
            if self.first_timestamp == 0:
                self.first_timestamp = timestamp
            timestamp = (timestamp- self.first_timestamp) 
                
            assert len(channel_data) == len(self.eeg_layout)
            for i,channel in enumerate(self.eeg_layout):
                data_dict[channel] = channel_data[i]

            return data_dict, timestamp
        return None
    
    def get_eeg_data_as_chunk(self) -> List[Tuple[Dict,float]]:
        list_of_data_dicts = []

        data_list = self.lslhandler.get_available_data_as_chunk(self.stream)
        if data_list: # an empty list evaluates to False
            for data in data_list:
                data_dict = {}
                channel_data = data[0]
                timestamp = data[1]
                if self.first_timestamp == 0:
                    self.first_timestamp = timestamp
                timestamp = (timestamp- self.first_timestamp) 
                    
                assert len(channel_data) == len(self.eeg_layout)
                for i,channel in enumerate(self.eeg_layout):
                    data_dict[channel] = channel_data[i]

                list_of_data_dicts.append((data_dict, timestamp))
            return list_of_data_dicts
        return None
    
    def return_topoplot_matplotlib_figure(self):
        channel_names = []
        N_SAMPLES = 500
        S_FREQU = 500

        lslhandler = self.lslhandler
        all_streams = lslhandler.get_all_lsl_streams()
        print(lslhandler.get_all_lsl_streams_as_infostring())
        assert len(all_streams) != 0
        for stream_index in range(len(all_streams)):
            lslhandler.connect_to_specific_lsl_stream(all_streams[stream_index])
            lslhandler.start_data_recording_thread(all_streams[stream_index])

        eegprocessor = self
        data = []
        while len(data) < N_SAMPLES:
            if(data_sample := eegprocessor.get_eeg_data_dict()) != None:
                channel_names = list(data_sample[0].keys())[:-10]
                data.append(list(data_sample[0].values())[:-10])


        mean_data = (data - np.mean(data, axis=0)) / np.std(data, axis=0)
        mean_ch = np.mean(mean_data, axis=0)  # mean samples with channel dimension left

        # Draw topography
        biosemi_montage = mne.channels.make_standard_montage('biosemi64')  # set a montage, see mne document
        index_list = []  # correspond channel
        for ch_name in channel_names:
            found = False
            for index, biosemi_name in enumerate(biosemi_montage.ch_names):
                if ch_name == biosemi_name:
                    index_list.append(index)
                    found=True

            assert(found)
        biosemi_montage.ch_names = [biosemi_montage.ch_names[i] for i in index_list]
        biosemi_montage.dig = [biosemi_montage.dig[i+3] for i in index_list]
        info = mne.create_info(ch_names=biosemi_montage.ch_names, sfreq=500., ch_types='eeg')  # sample rate

        evoked = mne.EvokedArray(mean_data.T, info)
        evoked.set_montage(biosemi_montage)

        # raw = mne.io.RawArray(mean_data.T, info)
        # raw.set_montage(biosemi_montage)

        fig, ax = plt.subplots()
        # plt.ion()
        im, cn = mne.viz.plot_topomap(mean_ch, evoked.info, axes = ax, show=False)

        return fig
    


#The main function is just for testing purposes
def main():
    lslhandler = LslHandler()
    all_streams = lslhandler.get_all_lsl_streams()
    print(lslhandler.get_all_lsl_streams_as_infostring())
    assert len(all_streams) != 0
    for stream_index in range(len(all_streams)):
        lslhandler.connect_to_specific_lsl_stream(all_streams[stream_index])
        lslhandler.start_data_recording_thread(all_streams[stream_index])

    eegprocessor = EEGProcessor(lslhandler, lslhandler.get_stream_by_name("BrainVision RDA"))
    while True:
        if(data_list := eegprocessor.get_eeg_data_as_chunk()) != None:
            print(all(d[0] == data_list[0][0] for d in data_list))
            for data in data_list:
                print(f"Recieved data: {data[0]} with timestamp {data[1]}")


        