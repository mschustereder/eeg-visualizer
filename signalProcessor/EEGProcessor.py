from  lslHandler.lslHandler import LslHandler
from lslHandler.lslHandler import SAMPLE_COUNT_MAX_QUEUE
from pylsl import StreamInfo
from typing import Dict, Tuple, List
import numpy as np
import mne
import matplotlib.pyplot as plt
from dataclasses import dataclass


DELTA_BAND = (0.1,4)
THETA_BAND = (4,8)
ALPHA_BAND = (8,13)
BETA_BAND = (13,30)
GAMMA_BAND = (30,100)

@dataclass
class Filter:
    Delta : Tuple = DELTA_BAND
    Theta : Tuple = THETA_BAND
    Alpha : Tuple = ALPHA_BAND
    Beta : Tuple = BETA_BAND
    Gamma : Tuple = GAMMA_BAND
    NoNe: Tuple = (0,100)


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

    def get_eeg_layout(self):
        return self.eeg_layout

    def _correct_timestamps(self, list_to_change: List[Tuple[List[float], float]]) -> List[Tuple[List[float], float]]:
        data_with_corrected_timestamps = []
        for index,data_tuple in enumerate(list_to_change):
            timestamp = data_tuple[1]
            if self.first_timestamp == 0:
                self.first_timestamp = timestamp
            data_with_corrected_timestamps.append((list_to_change[index][0], timestamp-self.first_timestamp))
        return data_with_corrected_timestamps

    def get_available_eeg_data(self, max_samples = SAMPLE_COUNT_MAX_QUEUE)  -> List[Tuple[List[float], float]]:
        data = self.lslhandler.get_available_data(self.stream, max_samples)
        if data:
            return self._correct_timestamps(data)

    def get_available_eeg_data_without_timestamps(self, max_samples = SAMPLE_COUNT_MAX_QUEUE) -> List[List[float]]:
        return self.lslhandler.get_available_data_without_timestamps(self.stream, max_samples)
    
    def get_specific_amount_of_eeg_samples(self, required_sample_count) -> List[Tuple[List[float], float]]:
        data = self.lslhandler.get_specific_amount_of_samples(self.stream, required_sample_count)
        return self._correct_timestamps(data)
    
    def get_specific_amount_of_eeg_samples_without_timestamps(self, required_sample_count) -> List[List[float]]:
        return self.lslhandler.get_specific_amount_of_samples_without_timestamps(self.stream, required_sample_count)
    

    def filter_eeg_data(self, data : List[List[float]], filter: Filter) -> np.ndarray: 
        filtered_data = mne.filter.filter_data(np.array(data).T, self.sampling_frequency, l_freq=filter[0], h_freq=filter[1], verbose=False)
        
        return filtered_data.T
    

