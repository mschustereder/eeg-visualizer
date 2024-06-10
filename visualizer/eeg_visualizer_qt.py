from PySide6.QtWidgets import QMainWindow, QGridLayout, QWidget, QVBoxLayout, QComboBox, QSizePolicy, QLabel, QFrame, QFormLayout, QLineEdit
from PySide6.QtCore import Qt, QSize
from visualizer.Visualizer3D import Visualizer3D
from visualizer.VisualizerHR import VisualizerHR
from PySide6 import QtCore, QtGui
import visualizer.globals as gl
import sys
from PySide6.QtWidgets import QApplication
from signalProcessor.EEGProcessor import EEGProcessor
from signalProcessor.HRProcessor import HRProcessor

FONT_SIZE_H1 = 20
FONT_SIZE_H2 = 18
FONT_SIZE_P = 14

HORIZONTAL_ROW_SPACER = 150

class CardWidget(QFrame):
    def __init__(self, title, title_is_h1=False, text_description=None, content=None):
        super().__init__()

        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Raised)

        card_grid_layout = QGridLayout()

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        title_font_size = FONT_SIZE_H1 if title_is_h1 else FONT_SIZE_H2
        self.title_label.setStyleSheet(f"font-size: {title_font_size}px; font-weight: bold; border: none;")

        card_grid_layout.addWidget(self.title_label, 0, 0)

        layout = QVBoxLayout()

        if text_description != None:
            self.description_label = QLabel(text_description)
            self.description_label.setWordWrap(True)
            self.description_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            self.description_label.setStyleSheet(f"font-size: {FONT_SIZE_P}px")
            layout.addWidget(self.description_label)

        if content != None:
            layout.addWidget(content)

        content_container = QWidget()
        content_container.setLayout(layout)
        card_grid_layout.addWidget(content_container, 1, 0, 10, 1)
        self.setLayout(card_grid_layout)

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
        main_plot_configuration = EegVisualizerMainWindow.get_main_plot_configuration()
        sub_plot_configuration = EegVisualizerMainWindow.get_sub_plot_configuration()
        vertical_layout.addWidget(main_plot_configuration)
        vertical_layout.addWidget(sub_plot_configuration)
        parameter_selection_container.setLayout(vertical_layout)
        parameter_selection_card = CardWidget("Configuration", content=parameter_selection_container)
        return parameter_selection_card
       
    def get_main_plot_configuration():
        form_layout = QFormLayout()
        
        main_plot_dropdown = QComboBox()
        main_plot_dropdown.addItems(['Spectrogram', 'Topoplot'])
        main_plot_dropdown.setStyleSheet("margin-top: 10px;")
        plot_label = QLabel("Plot:")
        plot_label.setStyleSheet("border: none;")
        plot_label.setMinimumWidth(HORIZONTAL_ROW_SPACER)
        form_layout.addRow(plot_label, main_plot_dropdown)
        
        frequency_band_dropdown = QComboBox()
        frequency_band_dropdown.addItems(['Alpha', 'Beta', 'Theta', 'Delta'])
        frequency_band_dropdown.setStyleSheet("margin-top: 10px;")
        frequency_band_label = QLabel("Frequency Band:")
        frequency_band_label.setStyleSheet("border: none;")
        form_layout.addRow(frequency_band_label, frequency_band_dropdown)
        
        seconds_shown_input = QLineEdit()
        seconds_shown_input.setValidator(QtGui.QIntValidator())
        seconds_shown_input.setText("30")
        seconds_shown_input.setStyleSheet("margin-top: 10px;")
        seconds_shown_label = QLabel("Seconds Shown:")
        seconds_shown_label.setStyleSheet("border: none;")
        form_layout.addRow(seconds_shown_label, seconds_shown_input)

        form_container = QWidget()
        form_container.setLayout(form_layout)
        
        main_plot_configuration = CardWidget("Main Plot Configuration", content=form_container)
        return main_plot_configuration
    
    def get_sub_plot_configuration():
        form_layout = QFormLayout()
        
        sub_plot_dropdown = QComboBox()
        sub_plot_dropdown.addItems(['BPM', 'RMSSD', 'SDNN', 'Poin care ratio'])
        sub_plot_dropdown.setStyleSheet("margin-top: 10px;")
        plot_label = QLabel("Plot:")
        plot_label.setStyleSheet("border: none;")
        plot_label.setMinimumWidth(HORIZONTAL_ROW_SPACER)
        form_layout.addRow(plot_label, sub_plot_dropdown)

        form_container = QWidget()
        form_container.setLayout(form_layout)
        
        sub_plot_configuration = CardWidget("Sub Plot Configuration", content=form_container)
        return sub_plot_configuration

