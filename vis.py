import visualizer.globals as gl
from visualizer.eeg_visualizer import *
from signalProcessor.EEGProcessor import EEGProcessor
from signalProcessor.HRProcessor import HRProcessor
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from visualizer.Visualizer3D import Visualizer3D
from visualizer.VisualizerHR import VisualizerHR
from PySide6 import QtCore


if __name__ == "__main__":
    streams = gl.lsl_handler.get_all_lsl_streams()
    gl.lsl_handler.connect_to_specific_lsl_stream(streams[0])
    gl.lsl_handler.start_data_recording_thread(streams[0])
    gl.eeg_processor = EEGProcessor(gl.lsl_handler, streams[0])

    gl.lsl_handler.connect_to_specific_lsl_stream(streams[1])
    gl.lsl_handler.start_data_recording_thread(streams[1])

    gl.lsl_handler.connect_to_specific_lsl_stream(streams[2])
    gl.lsl_handler.start_data_recording_thread(streams[2])

    gl.hr_processor = HRProcessor(gl.lsl_handler, streams[1], streams[2])

    app = QApplication(sys.argv)
    window = QMainWindow()
    window2 = QMainWindow()
    vis = Visualizer3D()
    vis2 = VisualizerHR()
    timer = QtCore.QTimer()
    timer.timeout.connect(vis.update_spectrum)
    timer.timeout.connect(vis2.update_graph)
    timer.setInterval(gl.EEG_GRAPH_INTERVAL_MS)
    timer.start()
    window.setCentralWidget(vis)
    window.show()
    window2.setCentralWidget(vis2)
    window2.show()

    sys.exit(app.exec())
