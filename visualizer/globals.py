from  lslHandler.lslHandler import LslHandler



#CONSTANTS

# with how manny samples should the fft be calculated (has to be power of 2)
FFT_SAMPLES = 512
SAMPLES_SHOWN_IN_SPECTROGRAM = 100
FREQUENCY_MAX = 40
FREQUENCY_MIN = 1
SPECTRUM_GRAPH_GRADIENT_BOTTOM_COLOR = [65, 23, 105]
SPECTRUM_GRAPH_GRADIENT_TOP_COLOR = [255, 213, 3]
EEG_GRAPH_INTERVAL_MS = 50
EEG_GRAPH_Z_UP_SCALE_THRESHOLD = 100
EEG_GRAPH_Z_UP_SCALE_FACTOR = 0.95
HR_GRAPH_TIME_RANGE_SEC = 45

HR_GRAPH_Y_UP_SCALE_THRESHOLD = 60
HR_GRAPH_Y_UP_SCALE_FACTOR = 0.95

MAX_HR_DATA_SAMPLES =100

# NOTE: usually it is forbidden to use global variables with Dash, 
# but due to the simple fact that dcc.storage is way too slow we will use it anyways
# the requirements for it to work is that dash is run with only 1 woker and 1 user at a time

#global lsl hanlder object
lsl_handler = LslHandler()

#global eeg processor object
eeg_processor = None
hr_processor = None

 