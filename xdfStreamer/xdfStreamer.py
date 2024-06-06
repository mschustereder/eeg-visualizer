from pylsl import StreamInfo, StreamOutlet
import time
import pyxdf
import argparse
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("xdf_file_path",  type = str, help = "Path to the cdf file that should be streamed")
    parser.add_argument('-c', '--continous', action='store_true', help ="Continous mode: file is streamed in a loop")               
    parser.add_argument('-hr', '--heart', action='store_true', help ="The stream we are looking for is a HR stream")               

    args = parser.parse_args()
    
    if not os.path.isfile(args.xdf_file_path):
        print("ERROR: path is not a file")
        exit()

    type = "Markers" if args.heart else "EEG"

    #load xdf file
    streams, file_header = pyxdf.load_xdf(args.xdf_file_path, select_streams=[{'type': type}])
    print("loaded xdf")
    continous_mode = args.continous
    print("Coninous mode: " + str(continous_mode))

    
    streams_data = []
    active_streams = 0
    for stream in streams:
        info = StreamInfo(stream["info"]["name"][0], stream["info"]["type"][0], int(stream["info"]["channel_count"][0]), float(stream["info"]["nominal_srate"][0]), stream["info"]["channel_format"][0])
        
        if stream["info"]["type"][0] == "EEG":
            channels_info = info.desc().append_child("channels")
            
            for channel in stream["info"]["desc"][0]["channels"][0]["channel"]:
                channel_info = channels_info.append_child("channel")
                channel_info.append_child_value("label", channel["label"][0])
                channel_info.append_child_value("unit", channel["unit"][0])
                channel_info.append_child_value("type", channel["type"][0])

        #for each stream store realated data into a dict
        streams_data.append({"outlet" : StreamOutlet(info), 
                             "stream" : stream, 
                             "time_since_last_sent_sample" : time.time(), 
                             "data_index" : 0, 
                             "is_active" : True,
                             "period" : 0 if float(stream["info"]["nominal_srate"][0]) == 0 else  1/float(stream["info"]["nominal_srate"][0])}) 
        active_streams +=1

    print("Starting to stream data")

    while active_streams:
        for stream_index, current_stream in enumerate(streams_data):
            if not current_stream["is_active"]:
                continue

            curr_time = time.time()
            if current_stream["stream"]["info"]["type"][0] == "Markers": #here the samples need to be sent according to their timestamps
                current_data_index = current_stream["data_index"]
                previous_data_index = current_stream["data_index"] - 1
                if not previous_data_index < 0:
                    if curr_time-current_stream["time_since_last_sent_sample"] < current_stream["stream"]["time_stamps"][current_data_index] - current_stream["stream"]["time_stamps"][previous_data_index] :continue

            elif ((curr_time-current_stream["time_since_last_sent_sample"]) < current_stream["period"]): continue
            data = current_stream["stream"]["time_series"]
            data_count = data.shape[0]

            current_stream["outlet"].push_sample(data[current_stream["data_index"]])

            #only log every 1000th sample to not overwhelm the console
            if current_stream["stream"]["info"]["type"][0] == "Markers" or (current_stream["stream"]["info"]["type"][0] == "EEG" and (not current_stream['data_index'] % 1000)): #prints every sample for Markers and every 1000 for EEG
                print(f"Stream {stream_index} sent sample {current_stream['data_index']+1} / {data_count}")

            current_stream["time_since_last_sent_sample"] = time.time()
            current_stream["data_index"] += 1

            if (current_stream["data_index"] >= data_count):
                if (continous_mode):
                    current_stream["data_index"] = 0 #just reset index in continuos mode
                else:
                    active_streams -=1
                    current_stream["is_active"] = False
                    continue

    print("Stopping to stream data")

if __name__ == "__main__":
    main()