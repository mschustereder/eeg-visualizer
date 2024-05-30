from  lslHandler.lslHandler import LslHandler
from visualizer.EEGGraphFrame import EEGGraphFrame

#CONSTANTS

# with how manny samples should the fft be calculated (has to be power of 2)
FFT_SAMPLES = 512
SAMPLES_SHOWN_IN_SPECTROGRAM = 40
FREQUENCY_CUT_OFF = 40
FREQUENCY_MIN_MAX_BOUND = [FREQUENCY_CUT_OFF, 1]

# NOTE: usually it is forbidden to use global variables with Dash, 
# but due to the simple fact that dcc.storage is way too slow we will use it anyways
# the requirements for it to work is that dash is run with only 1 woker and 1 user at a time

#global lsl hanlder object
lsl_handler = LslHandler()

#global eeg processor object
eeg_processor = None

#holds the data that the graph is displaying
graph_frame = EEGGraphFrame()

 