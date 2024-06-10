#Use this file to avoid messy import errors and workarounds

import signalProcessor.HRProcessor as hr
from signalProcessor.EEGProcessor import *
import mne
import numpy as np
from mne.preprocessing import ICA
from lslHandler.lslHandler import LslHandler
from signalProcessor.EEGProcessor import EEGProcessor
# eeg.main()
import matplotlib.pyplot as plt

import numpy as np
import mne

import pickle


channel_names = []
N_SAMPLES = 250
S_FREQU = 500

#USE THIS TO USE LSLSTEAM
lslhandler = LslHandler()
all_streams = lslhandler.get_all_lsl_streams()
print(lslhandler.get_all_lsl_streams_as_infostring())
assert len(all_streams) != 0
for stream_index in range(len(all_streams)):
    lslhandler.connect_to_specific_lsl_stream(all_streams[stream_index])
    lslhandler.start_data_recording_thread(all_streams[stream_index])

eegprocessor = EEGProcessor(lslhandler, lslhandler.get_stream_by_name("BrainVision RDA"))
data = []
while len(data) < N_SAMPLES:
    if(data_sample := eegprocessor.get_eeg_data_dict()) != None:
        channel_names = list(data_sample[0].keys())[:-10]
        data.append(list(data_sample[0].values())[:-10])
######################################

#USE THIS TO TEST THE APPLICATION TO THE SAME TEST DATA, ONCE RECORDED
# with open("data_test.pkl" , "rb") as file:
#     data = pickle.load(file)

# with open("channel_names.pkl" , "rb") as file:
#     channel_names = pickle.load(file)
###########################################

# mean_data = (data - np.mean(data, axis=0)) / np.std(data, axis=0)
mean_ch = np.mean(np.array(data), axis=0)  
# mean_ch = np.mean(mean_data, axis=0)  


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

# evoked1 = mne.EvokedArray(mean_data.T, info)
# evoked1.set_montage(biosemi_montage)

raw = mne.io.RawArray(np.array(data).T , info)
# raw = mne.io.RawArray(mean_data.T, info)
raw.set_montage(biosemi_montage)


fig, ax = plt.subplots()
plt.ion()
im, cn = mne.viz.plot_topomap(mean_ch, raw.info,axes=ax ,show=False)
plt.colorbar(im, ax=ax)
plt.show(block=False)

while True:
    new_data = []
    
    if(new_chunk := eegprocessor.get_eeg_data_as_chunk(N_SAMPLES)) != None:
        channel_names = list(new_chunk[0][0].keys())[:-10]
        new_data = [list(arr[0].values())[:-10] for arr in new_chunk]
    else: continue

    data = data[len(new_data):]
    data += new_data

    filtered_data = eegprocessor.filter_eeg_data(data, Filter.Alpha)
    # filtered_data = data
    # mean_data = (data - np.mean(data, axis=0)) / np.std(data, axis=0)
    mean_ch = np.mean(np.array(filtered_data), axis=0)  
    # mean_ch = np.mean(mean_data, axis=0)  


    # alpha_data = mne.filter.filter_data(np.array(data).T, S_FREQU, l_freq=ALPHA_BAND[0], h_freq=ALPHA_BAND[1], verbose=False)
    # alpha_mean = np.mean(alpha_data, axis=1)

    ax.clear()
    im, cn = mne.viz.plot_topomap(mean_ch, raw.info,axes=ax ,show=False)
    # im, cn = mne.viz.plot_topomap(alpha_mean, raw.info,axes=ax ,show=False)

    ax.figure.canvas.draw()
    ax.figure.canvas.flush_events()
