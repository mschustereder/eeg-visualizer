#Use this file to avoid messy import errors and workarounds

import signalProcessor.HRProcessor as hr
import signalProcessor.EEGProcessor as eeg
import mne
import numpy as np
from mne.preprocessing import ICA
from lslHandler.lslHandler import LslHandler
from signalProcessor.EEGProcessor import EEGProcessor
# eeg.main()
import matplotlib.pyplot as plt

import numpy as np
import mne

channel_names = []
N_SAMPLES = 500
S_FREQU = 500

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


mean_data = (data - np.mean(data, axis=0)) / np.std(data, axis=0)
mean_ch = np.mean(mean_data, axis=0)  # mean samples with channel dimension left

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

raw = mne.io.RawArray(mean_data.T, info)
raw.set_montage(biosemi_montage)

fig, ax = plt.subplots()
plt.ion()
im, cn = mne.viz.plot_topomap(mean_ch, raw.info,axes=ax ,show=True)
plt.colorbar(im, ax=ax)

while True:
    new_data = []
    
    if(new_data := eegprocessor.get_eeg_data_as_chunk()) != None:
        channel_names = list(new_data[0][0].keys())[:-10]
        new_data = [list(arr[0].values())[:-10] for arr in new_data]
    else: continue

    data = data[len(new_data):]
    data += new_data

    mean_data = (data - np.mean(data, axis=0)) / np.std(data, axis=0)
    mean_ch = np.mean(mean_data, axis=0)  # mean samples with channel dimension left

    ax.clear()
    im, cn = mne.viz.plot_topomap(mean_ch, raw.info,axes=ax ,show=True)

    ax.figure.canvas.draw()
    ax.figure.canvas.flush_events()
