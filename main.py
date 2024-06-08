import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from visualizer.eeg_visualizer_main_window import EegVisualizerMainWindow
import visualizer.globals as gl
from signalProcessor.EEGProcessor import EEGProcessor
from signalProcessor.HRProcessor import HRProcessor
from visualizer.Visualizer3D import Visualizer3D
from visualizer.VisualizerHR import VisualizerHR
from PySide6 import QtCore


def connect_to_streams():
    streams = gl.lsl_handler.get_all_lsl_streams()
    print([stream.name() for stream in streams])
    for stream in streams:
        gl.lsl_handler.connect_to_specific_lsl_stream(stream)
        gl.lsl_handler.start_data_recording_thread(stream)

    gl.eeg_processor = EEGProcessor(gl.lsl_handler, gl.lsl_handler.get_stream_by_name("BrainVision RDA"))
    gl.hr_processor = HRProcessor(gl.lsl_handler, gl.lsl_handler.get_stream_by_name("HR_Polar H10 CA549123"), gl.lsl_handler.get_stream_by_name("RR_Polar H10 CA549123"))

if __name__ == "__main__":
    connect_to_streams()

    app = QApplication(sys.argv)
    window = EegVisualizerMainWindow()
    visualizer_3d = Visualizer3D()
    visualizer_hr = VisualizerHR()
    timer = QtCore.QTimer()
    timer.timeout.connect(visualizer_3d.update_spectrum)
    timer.timeout.connect(visualizer_hr.update_graph)
    timer.setInterval(gl.EEG_GRAPH_INTERVAL_MS)
    timer.start()

    layout = QVBoxLayout()

    visualizer_3d.setFixedSize(QtCore.QSize(400, 300))
    visualizer_hr.setFixedSize(QtCore.QSize(400, 300))

    layout.addWidget(visualizer_3d)
    layout.addWidget(visualizer_hr)

    container_widget = QWidget()
    container_widget.setLayout(layout)

    window.setCentralWidget(container_widget)
    window.show()

    sys.exit(app.exec())
