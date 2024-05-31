import visualizer.globals as gl
from visualizer.eeg_visualizer import *
from signalProcessor.EEGProcessor import EEGProcessor


if __name__ == '__main__':
    streams = gl.lsl_handler.get_all_lsl_streams()
    gl.lsl_handler.connect_to_specific_lsl_stream(streams[0])
    gl.lsl_handler.start_data_recording_thread(streams[0])
    gl.eeg_processor = EEGProcessor(gl.lsl_handler, streams[0])
    gl.main_graph_frame.eeg_values["Fz"] = []
    app.run(debug=True)
