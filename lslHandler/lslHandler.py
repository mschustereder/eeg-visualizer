import pylsl
from pylsl import StreamInfo
from pylsl import StreamInlet
from typing import List
import threading
import queue
from dataclasses import dataclass, field
from typing import Dict, Tuple
from datetime import datetime
import time


SAMPLE_COUNT_MAX_QUEUE = 100

@dataclass
class DataQueue:
    data_queue : queue.Queue = queue.Queue()
    data_queue_lock : threading.Lock = threading.Lock()
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
                    queue.data_queue.put(self.active_streams[stream][0].pull_sample(timeout = 0.0))
                    queue.queue_length += 1
                    if queue.queue_length > SAMPLE_COUNT_MAX_QUEUE:
                        while not queue.data_queue.empty(): #this mechanism is probably not really efficient and should be overthought
                            queue.data_queue.get()
                        queue.queue_length = 0
                time.sleep(0.0001)

    def connect_to_specific_lsl_stream(self, stream : StreamInfo):
        new_inlet = pylsl.StreamInlet(stream)
        self.active_streams[stream] = (new_inlet, DataQueue())
    
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
    


def main():
    lslhandler = LslHandler()
    all_streams = lslhandler.get_all_lsl_streams()
    print(lslhandler.get_all_lsl_streams_as_infostring())
    assert len(all_streams) != 0
    for stream_index in range(len(all_streams)):
        lslhandler.connect_to_specific_lsl_stream(all_streams[stream_index])
        lslhandler.start_data_recording_thread(all_streams[stream_index])

    while True:
        for stream_index in range(len(all_streams)):
            data = lslhandler.get_data_sample(all_streams[stream_index])
            if data != None and data != (None,None):
                print(data)



if __name__ == '__main__':
    main()