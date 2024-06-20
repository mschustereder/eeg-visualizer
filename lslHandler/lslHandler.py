import pylsl
from pylsl import StreamInfo
from pylsl import StreamInlet
import threading
import queue
from dataclasses import dataclass, field
from typing import Dict, Tuple, List
from datetime import datetime
import time
import numpy as np

SAMPLE_COUNT_MAX_QUEUE = 500 #for 250Hz this would be 2 seconds worth of data

class LslHandler:
    def __init__(self):
        self._stop_event = threading.Event()

    active_streams = {}

    def get_all_lsl_streams(self):
        return pylsl.resolve_streams()
    
    def get_all_lsl_streams_as_infostring(self) -> List[str] :
        info_string_list = []
        for stream in self.get_all_lsl_streams():
            string_of_list = f"{stream.name()}, {stream.type()}, {stream.source_id()}, {stream.channel_count()}, {stream.nominal_srate()}"
            info_string_list.append(string_of_list)

        return info_string_list
    
    def connect_to_specific_lsl_stream(self, stream : StreamInfo):
        new_inlet = pylsl.StreamInlet(stream)
        self.active_streams[stream] = new_inlet
        
    def get_available_data(self, stream: StreamInfo, max_samples = SAMPLE_COUNT_MAX_QUEUE) -> Tuple[List[List[float]], List[float]]:
        inlet = self.active_streams[stream]
        samples, timestamps = inlet.pull_chunk(timeout = 0.0, max_samples = max_samples)
        if not samples: return None,None
        # data_with_timestamps = self._zip_samples_and_timestamps(samples, timestamps)
        if inlet.samples_available() > SAMPLE_COUNT_MAX_QUEUE:
            nr_of_flushed_samples = inlet.flush()
            print(f"Warning: Throwing away {nr_of_flushed_samples} samples")
        return samples, timestamps
    
    def get_available_data_without_timestamps(self, stream: StreamInfo, max_samples = SAMPLE_COUNT_MAX_QUEUE) -> List[List[float]]:
        samples, _ = self.get_available_data(stream, max_samples)
        if not list: return None
        return samples
    
    def get_specific_amount_of_samples(self, stream: StreamInfo, required_sample_count) -> Tuple[List[List[float]], List[float]]:
        data = []
        timestamps = []
        while (length := len(data)) < required_sample_count:
            data_temp, samples_temp = self.get_available_data(stream, required_sample_count - length)
            if data_temp:
                data += data_temp
                timestamps += samples_temp
            missing_samples = required_sample_count - len(data)
            # print(f"Going to sleep for {missing_samples / stream.nominal_srate()} seconds")
            time.sleep(missing_samples / stream.nominal_srate())
        assert len(data) == required_sample_count
        return data, timestamps

    def get_specific_amount_of_samples_without_timestamps(self, stream: StreamInfo, required_sample_count) -> List[List[float]]:
        samples, _ = self.get_specific_amount_of_samples(stream, required_sample_count)
        return samples

    # def _zip_samples_and_timestamps(self, samples : List[List[float]], timestamps : List[float])  -> List[Tuple[List[float], float]]:
    #     data_with_timestamps = []
    #     data_with_timestamps.extend(zip(samples, timestamps))
    #     return data_with_timestamps
   
    def get_stream_by_name(self, name):
        for stream in self.active_streams:
            if stream.name() == name:
                return stream
            
        return None
    
    def get_inlet(self,stream : StreamInfo) -> StreamInlet:
        return self.active_streams[stream]
    
    def disconnect(self, stream : StreamInfo):
        self.get_inlet(stream).close_stream()
        del self.active_streams[stream]
    
