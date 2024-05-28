from  lslHandler.lslHandler import LslHandler
from pylsl import StreamInfo


class EEGProcessor:
    def __init__(self, lslhandler: LslHandler, stream : StreamInfo): #Must be called after connecting to EEG stream to get the layout
        self.lslhandler = lslhandler
        self.stream = stream
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
        if(data := eegprocessor.get_eeg_data_dict()) != None:
            print(data[1])

        