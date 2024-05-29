import pylsl
from pylsl import StreamInfo
from pylsl import StreamInlet
import threading
import queue
from dataclasses import dataclass, field
from typing import Dict, Tuple, List
from datetime import datetime
import time

SAMPLE_COUNT_MAX_QUEUE = 20

@dataclass
class DataQueueStruct:
    data_queue : queue.Queue = field(default_factory=queue.Queue)
    data_queue_lock : threading.Lock = field(default_factory=threading.Lock)
    queue_length : int = 0


class LslHandler:
    def __init__(self):
        pass

    active_streams = {}

    def get_all_lsl_streams(self):
        return pylsl.resolve_streams()
    
    def get_all_lsl_streams_as_infostring(self) -> List[str] :
        info_string_list = []
        for stream in self.get_all_lsl_streams():
            string_of_list = f"{stream.name()}, {stream.type()}, {stream.source_id()}, {stream.channel_count()}, {stream.nominal_srate()}"
            info_string_list.append(string_of_list)

        return info_string_list

    def data_recording_thread(self, stream : StreamInfo):
        queue = self.active_streams[stream][1]
        while True: 
                with queue.data_queue_lock:
                    data = self.active_streams[stream][0].pull_sample(timeout = 0.0)
                    if data != (None,None):
                        queue.data_queue.put(data)
                        # print(f"added {data} to queue of stream {self.get_stream_name(stream)}")
                        queue.queue_length += 1
                    if queue.queue_length > SAMPLE_COUNT_MAX_QUEUE:
                        while not queue.data_queue.empty(): #this mechanism is probably not really efficient and should be overthought
                            queue.data_queue.get(block= False)
                        queue.queue_length = 0
                time.sleep(0.0001)

    def connect_to_specific_lsl_stream(self, stream : StreamInfo):
        new_inlet = pylsl.StreamInlet(stream)
        self.active_streams[stream] = (new_inlet, DataQueueStruct())
    
    def start_data_recording_thread(self, stream: StreamInfo):
        assert stream in self.active_streams
        threading.Thread(target=self.data_recording_thread, args=(stream,)).start()

    def get_data_sample(self, stream: StreamInfo):
        queue = self.active_streams[stream][1]
        data_sample = None
        with queue.data_queue_lock:
            try:
                data_sample = queue.data_queue.get(block = False) #.get() normally blocks which leads to a deadlock, therfore we set block to false and accept the exception if the queue is empty
                queue.data_queue.task_done()
                queue.queue_length -= 1
            except: 
                pass
        return data_sample #if the queue was empty it returns None
    
    def get_available_data_as_chunk(self, stream : StreamInfo):
        chunk_to_return = []
        queue_struct = self.active_streams[stream][1]
        with queue_struct.data_queue_lock: 
            while not queue_struct.data_queue.empty(): 
                chunk_to_return.append(queue_struct.data_queue.get(block = False))
                queue_struct.data_queue.task_done()
            queue_struct.queue_length = 0
        return chunk_to_return #returns empty list if queue is empty
    
    def get_stream_by_name(self, name):
        for stream in self.active_streams:
            if stream.name() == name:
                return stream
            
        return None
    
    def get_inlet(self,stream : StreamInfo):
        return self.active_streams[stream][0]
    
