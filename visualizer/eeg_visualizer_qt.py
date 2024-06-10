from PySide6.QtWidgets import QMainWindow, QGridLayout, QWidget, QVBoxLayout, QComboBox, QSizePolicy, QLabel, QFrame
from PySide6.QtCore import Qt
from visualizer.Visualizer3D import Visualizer3D
from visualizer.VisualizerHR import VisualizerHR
from PySide6 import QtCore
import visualizer.globals as gl
import sys
from PySide6.QtWidgets import QApplication
from signalProcessor.EEGProcessor import EEGProcessor
from signalProcessor.HRProcessor import HRProcessor

FONT_SIZE_H1 = 20
FONT_SIZE_H2 = 18
FONT_SIZE_P = 14

class CardWidget(QFrame):
    def __init__(self, title, text_description=None, content=None):
        super().__init__()

        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Raised)

        layout = QVBoxLayout()

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"font-size: {FONT_SIZE_H2}px; font-weight: bold; border: none;")

        layout.addWidget(self.title_label)

        if text_description != None:
            self.description_label = QLabel(text_description)
            self.description_label.setWordWrap(True)
            self.description_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            self.description_label.setStyleSheet(f"font-size: {FONT_SIZE_P}px")
            layout.addWidget(self.description_label)

        if content != None:
            layout.addWidget(content)

        self.setLayout(layout)

        self.setStyleSheet("""
            QFrame {
                border: 1px solid #d3d3d3;
                border-radius: 2px;
                background-color: white;
                padding: 10px;
            }
        """)

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

        visualizer_3d.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        visualizer_hr.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(visualizer_3d, 0, 0, 2, 2)
        layout.addWidget(visualizer_hr, 2, 0, 1, 2)
        parameter_selection_container = EegVisualizerMainWindow.get_parameter_selection()
        layout.addWidget(parameter_selection_container, 0, 2, 3, 1)

        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)
        layout.setRowStretch(2, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)

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
        title = QLabel("Parameter Selection")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: {FONT_SIZE_H1}px; font-weight: bold;")
        dropdown = QComboBox()
        dropdown.addItem('Option 1')
        dropdown.addItem('Option 2')
        dropdown.addItem('Option 3')
        main_plot_configuration = CardWidget("Main Plot Configuration", text_description="This is a description for card 1.", content=dropdown)
        sub__plot_configuration = CardWidget("Sub Plot Configuration", text_description="This is a description for card 2.")
        vertical_layout.addWidget(title)
        vertical_layout.addWidget(main_plot_configuration)
        vertical_layout.addWidget(sub__plot_configuration)
        parameter_selection_container.setLayout(vertical_layout)
        return parameter_selection_container
