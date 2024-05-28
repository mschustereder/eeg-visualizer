from lslHandler.lslHandler import LslHandler
from pylsl import StreamInfo
from hrvanalysis import get_time_domain_features, get_poincare_plot_features
from hrvanalysis.preprocessing import interpolate_nan_values, remove_ectopic_beats
import numpy as np
from collections import deque

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

    def get_bpm_data(self):
        return self.lslhandler.get_data_sample(self.hr_stream)
        
    def _get_rr_intervals(self):
        #(ref)
        global average_rr, rr_data_buffer
        rr_intervals = [rr_data_buffer[-i] for i in range(1, FEAT_WINDOW_SIZE+1)]
        sample = self.lslhandler.get_data_sample(self.rr_stream)
        if sample != None:
            this_rr = sample[0][0]  # RR peaks in ms
            rr_intervals = np.array(rr_intervals)
            rr_intervals = remove_ectopic_beats(rr_intervals)
            rr_intervals = interpolate_nan_values(rr_intervals)
            rr_data_buffer.append(this_rr)
            return rr_intervals
        return None
    
    def get_rmssd_data(self):
        rr_intervals = self._get_rr_intervals()
        if rr_intervals != None:
            time_feats = get_time_domain_features(nn_intervals=rr_intervals)
            return time_feats['rmssd']
        return None

    def get_sdnn_data(self):
        rr_intervals = self._get_rr_intervals()
        if rr_intervals != None:
            time_feats = get_time_domain_features(nn_intervals=rr_intervals)
            return time_feats['sdnn']
        return None
    
    def get_poincare_ratio(self):
        rr_intervals = self._get_rr_intervals()
        if rr_intervals != None:
            poincare_feats = get_poincare_plot_features(nn_intervals=rr_intervals)
            return poincare_feats['ratio_sd2_sd1']
        return None
    


#The main function is just for testing purposes
def main():
    lslhandler = LslHandler()
    all_streams = lslhandler.get_all_lsl_streams()
    print(lslhandler.get_all_lsl_streams_as_infostring())
    assert len(all_streams) != 0
    for stream_index in range(len(all_streams)):
        lslhandler.connect_to_specific_lsl_stream(all_streams[stream_index])
        lslhandler.start_data_recording_thread(all_streams[stream_index])

    hr_stream = lslhandler.get_stream_by_name("HR_Polar H10 CA549123")
    hrprocessor = HRProcessor(lslhandler,hr_stream,lslhandler.get_stream_by_name("RR_Polar H10 CA549123"))
    while True:
        data = hrprocessor.get_poincare_ratio()
        if data != None:
            print(data)

        
