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
    print([stream.name() for stream in streams])
    for stream in streams:
        gl.lsl_handler.connect_to_specific_lsl_stream(stream)
        gl.lsl_handler.start_data_recording_thread(stream)

    gl.eeg_processor = EEGProcessor(gl.lsl_handler, gl.lsl_handler.get_stream_by_name("BrainVision RDA"))
    gl.hr_processor = HRProcessor(gl.lsl_handler, gl.lsl_handler.get_stream_by_name("HR_Polar H10 CA549123"), gl.lsl_handler.get_stream_by_name("RR_Polar H10 CA549123"))

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
