from pylsl import StreamInfo, StreamOutlet
import time
import pyxdf
import argparse
import os
from mne.datasets import misc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("xdf_file_path",  type = str, help = "Path to the cdf file that should be streamed")
    parser.add_argument('-c', '--continous', action='store_true', help ="Continous mode: file is streamed in a loop")               
    args = parser.parse_args()
    
    if not os.path.isfile(args.xdf_file_path):
        print("ERROR: path is not a file")
        exit()

    streams, file_header = pyxdf.load_xdf(args.xdf_file_path, select_streams=[{'type': 'EEG'}])
    print("loaded xdf")
    continous_mode = args.continous
    print("Coninous mode: " + str(continous_mode))
    #streams, file_header = pyxdf.load_xdf(misc.data_path()  / "xdf" / "sub-P001_ses-S004_task-Default_run-001_eeg_a2.xdf")

    outlets_streams = []
    active_streams = 0
    for stream in streams:
        info = StreamInfo(stream["info"]["name"][0], stream["info"]["type"][0], int(stream["info"]["channel_count"][0]), float(stream["info"]["nominal_srate"][0]), stream["info"]["channel_format"][0])
        channels_info = info.desc().append_child("channels")
        
        for channel in stream["info"]["desc"][0]["channels"][0]["channel"]:
            channel_info = channels_info.append_child("channel")
            channel_info.append_child_value("label", channel["label"][0])
            channel_info.append_child_value("unit", channel["unit"][0])
            channel_info.append_child_value("type", channel["type"][0])

        outlets_streams.append([StreamOutlet(info), stream, time.time(), 0, True])
        active_streams +=1

    print("Starting to stream data")

    while active_streams:
        for outlet_stream in outlets_streams:
            if not outlet_stream[4]:
                continue

            curr_time = time.time()
            if ((curr_time-outlet_stream[2]) >= 1/float(outlet_stream[1]["info"]["nominal_srate"][0])):
                data = outlet_stream[1]["time_series"]
                if (outlet_stream[3] >= data.shape[0]):
                    if (continous_mode):
                        outlet_stream[3] = 0
                    else:
                        active_streams -=1
                        outlet_stream[4] = False
                        continue
                outlet_stream[0].push_sample(data[outlet_stream[3]])
                outlet_stream[3] += 1
                outlet_stream[2] = time.time()
    print("Stopping to stream data")

if __name__ == "__main__":
    main()