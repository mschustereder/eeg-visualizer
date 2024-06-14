from  lslHandler.lslHandler import LslHandler
from signalProcessor.EEGProcessor import EEGProcessor
from signalProcessor.HRProcessor import HRProcessor
import threading

#CONSTANTS

# with how manny samples should the fft be calculated (has to be power of 2)
DEFAULT_FFT_SAMPLES = 1024
DEFAULT_SECONDS_SHOWN_IN_SPECTROGRAM = 5
FREQUENCY_MAX = 40
FREQUENCY_MIN = 1
GRAPH_UPDATE_PAUSE_S = 0.070
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
eeg_processor : EEGProcessor = None
hr_processor : HRProcessor = None

eeg_processor_lock = threading.Lock()
hr_processor_lock = threading.Lock()


MONTAGES = ["biosemi64", "standard_1020"]

USED_MNE_MONTAGE = MONTAGES[0]
GET_LAYOUT_FROM_JSON = True
