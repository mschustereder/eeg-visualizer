import visualizer.globals as gl
from visualizer.eeg_visualizer import *
from signalProcessor.EEGProcessor import EEGProcessor
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from visualizer.Visualizer3D import Visualizer3D
from PySide6 import QtCore


if __name__ == "__main__":
    streams = gl.lsl_handler.get_all_lsl_streams()
    gl.lsl_handler.connect_to_specific_lsl_stream(streams[0])
    gl.lsl_handler.start_data_recording_thread(streams[0])
    gl.eeg_processor = EEGProcessor(gl.lsl_handler, streams[0])
    app = QApplication(sys.argv)
    window = QMainWindow()
    vis = Visualizer3D()
    timer = QtCore.QTimer()
    timer.timeout.connect(vis.update_spectrum)
    timer.setInterval(gl.EEG_GRAPH_INTERVAL_MS)
    timer.start()
    window.setCentralWidget(vis)
    window.show()

    sys.exit(app.exec())
