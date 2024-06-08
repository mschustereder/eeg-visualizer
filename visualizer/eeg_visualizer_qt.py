from PySide6.QtWidgets import QMainWindow, QGridLayout, QWidget, QVBoxLayout, QComboBox
from visualizer.Visualizer3D import Visualizer3D
from visualizer.VisualizerHR import VisualizerHR
from PySide6 import QtCore
import visualizer.globals as gl
import sys
from PySide6.QtWidgets import QApplication
from signalProcessor.EEGProcessor import EEGProcessor
from signalProcessor.HRProcessor import HRProcessor

def connect_to_streams():
    streams = gl.lsl_handler.get_all_lsl_streams()
    print([stream.name() for stream in streams])
    for stream in streams:
        gl.lsl_handler.connect_to_specific_lsl_stream(stream)
        gl.lsl_handler.start_data_recording_thread(stream)

    gl.eeg_processor = EEGProcessor(gl.lsl_handler, gl.lsl_handler.get_stream_by_name("BrainVision RDA"))
    gl.hr_processor = HRProcessor(gl.lsl_handler, gl.lsl_handler.get_stream_by_name("HR_Polar H10 CA549123"), gl.lsl_handler.get_stream_by_name("RR_Polar H10 CA549123"))

def execute_qt_app():
    app = QApplication(sys.argv)

    timer = QtCore.QTimer()
    window = EegVisualizerMainWindow(timer)

    window.show()

    sys.exit(app.exec())

class EegVisualizerMainWindow(QMainWindow):
    def __init__(self, timer):
        super().__init__()

        self.setWindowTitle("EEG Visualizer Main Window")

        visualizer_3d, visualizer_hr = EegVisualizerMainWindow.setup_timer_and_get_visualizers_3d_and_hr(timer)

        layout = QGridLayout()

        visualizer_3d.setFixedSize(QtCore.QSize(400, 300))
        visualizer_hr.setFixedSize(QtCore.QSize(400, 300))

        layout.addWidget(visualizer_3d, 0, 0)
        layout.addWidget(visualizer_hr, 1, 1)
        parameter_selection_container = EegVisualizerMainWindow.get_parameter_selection()
        layout.addWidget(parameter_selection_container, 0, 1)

        container_widget = QWidget()
        container_widget.setLayout(layout)

        self.setCentralWidget(container_widget)

        connect_to_streams()

    def setup_timer_and_get_visualizers_3d_and_hr(timer):
        visualizer_3d = Visualizer3D()
        visualizer_hr = VisualizerHR()

        timer = QtCore.QTimer(timer)
        timer.timeout.connect(visualizer_3d.update_spectrum)
        timer.timeout.connect(visualizer_hr.update_graph)
        timer.setInterval(gl.EEG_GRAPH_INTERVAL_MS)

        timer.start()

        return visualizer_3d, visualizer_hr
    
    def get_parameter_selection():
        parameter_selection_container = QWidget()
        vertical_layout = QVBoxLayout()
        dropdown = QComboBox()
        dropdown.addItem('Option 1')
        dropdown.addItem('Option 2')
        dropdown.addItem('Option 3')
        vertical_layout.addWidget(dropdown)
        parameter_selection_container.setLayout(vertical_layout)
        return parameter_selection_container
