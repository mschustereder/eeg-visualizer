from lslHandler.lslHandler import LslHandler
from pylsl import StreamInfo
from hrvanalysis import get_time_domain_features, get_poincare_plot_features
from hrvanalysis.preprocessing import interpolate_nan_values, remove_ectopic_beats
import numpy as np
from collections import deque
from visualizer.VisualizerHR import HR_BIO_VARIABLE
from typing import Dict, Tuple, List

#Code with (ref) taken from https://github.com/abcsds/hrv/blob/main/src/09b_plot_hrv.py - Author: Luis Alberto Barradas Chacón

#(ref)
FEAT_WINDOW_SIZE = 30 # Number of points taken into account for the std 
MAX_DATA_POINTS = 200
average_hr = 60  # Average human hr
average_rr = 1000 * average_hr / 60  # Average human rr in ms
rr_data_buffer = deque([average_rr] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)


class HRProcessor:
    def __init__(self, lslhandler: LslHandler, hr_stream : StreamInfo, rr_stream : StreamInfo):
        self.lslhandler = lslhandler
        self.hr_stream = hr_stream
        self.rr_stream = rr_stream

    lslhandler : LslHandler
    hr_stream : StreamInfo
    rr_stream : StreamInfo

    def get_bpm(self) -> int:
        return self.lslhandler.get_specific_amount_of_samples_without_timestamps(self.hr_stream, 1)[0][0]
        
    def _get_rr_intervals(self):
        #(ref)
        global average_rr, rr_data_buffer
        rr_intervals = [rr_data_buffer[-i] for i in range(1, FEAT_WINDOW_SIZE+1)]
        sample = self.lslhandler.get_specific_amount_of_samples_without_timestamps(self.rr_stream, 1)
        if sample != None:
            this_rr = sample[0][0]  # RR peaks in ms
            rr_intervals = np.array(rr_intervals)
            rr_intervals = remove_ectopic_beats(rr_intervals)
            rr_intervals = interpolate_nan_values(rr_intervals)
            rr_data_buffer.append(this_rr)
            return rr_intervals
        return None
    
    def get_rmssd(self, rr_intervals) -> float:
       if not rr_intervals: return None
       time_feats = get_time_domain_features(nn_intervals=rr_intervals)
       return time_feats['rmssd']

    def get_sdnn(self, rr_intervals) -> float:
        if not rr_intervals: return None
        time_feats = get_time_domain_features(nn_intervals=rr_intervals)
        return time_feats['sdnn']
    
    def get_poincare(self, rr_intervals) -> float:
        if not rr_intervals: return None
        poincare_feats = get_poincare_plot_features(nn_intervals=rr_intervals)
        return poincare_feats['ratio_sd2_sd1']

    
    def get_all_bio_vars(self) -> Tuple[int,float,float,float]:
        rr_intervals = self._get_rr_intervals()
        return self.get_bpm(), self.get_rmssd(rr_intervals), self.get_sdnn(rr_intervals), self.get_poincare(rr_intervals)
    
