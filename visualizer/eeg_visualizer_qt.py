from PySide6.QtWidgets import QMainWindow, QGridLayout, QWidget, QVBoxLayout, QComboBox, QSizePolicy, QLabel, QFrame, QFormLayout, QRadioButton, QPushButton, QHBoxLayout, QSpinBox
from PySide6.QtCore import Qt, QSize
from PySide6 import QtCore, QtGui
import sys
from PySide6.QtWidgets import QApplication
from visualizer.Visualizer3D import Visualizer3D
from visualizer.VisualizerTopoPlot import VisualizerTopoPlot
from visualizer.VisualizerHR import VisualizerHR, HR_BIO_VARIABLE
import visualizer.globals as gl
from signalProcessor.EEGProcessor import EEGProcessor, Filter
from signalProcessor.HRProcessor import HRProcessor
from enum import Enum


FONT_SIZE_H1 = 20
FONT_SIZE_H2 = 18
FONT_SIZE_P = 14

HORIZONTAL_ROW_SPACER = 200

DEFAULT_SECONDS_SHOWN = 5

DEFAULT_WINDOW_SIZE_EXPONENT = 9

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

        if text_description is not None:
            self.description_label = QLabel(text_description)
            self.description_label.setWordWrap(True)
            self.description_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            self.description_label.setStyleSheet(f"font-size: {FONT_SIZE_P}px")
            layout.addWidget(self.description_label)

        if content is not None:
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

def execute_qt_app():
    app = QApplication(sys.argv)

    window = EegVisualizerMainWindow()

    window.showMaximized()

    sys.exit(app.exec())

class EegVisualizerMainWindow(QMainWindow):

    class StreamType(Enum):
        EEG = 1
        HR = 2
        RR = 3

    def __init__(self):
        super().__init__()

        self.setWindowTitle("EEG Visualizer")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)

        self.stream_selection_card = self.get_stream_selection_card()

        self.selected_eeg_stream = None
        self.selected_hr_stream = None
        self.selected_rr_stream = None

        self.show_stream_selection_view()

    def get_specific_lsl_stream(stream_name):
        all_lsl_streams = EegVisualizerMainWindow.get_all_lsl_streams()
        first_match = next((stream for stream in all_lsl_streams if stream.name() == stream_name), None)

        if first_match is None:
            raise ValueError
        
        return first_match

    def connect_to_selected_streams(eeg_stream_name, hr_stream_name, rr_stream_name):
        stream_names = [eeg_stream_name, hr_stream_name, rr_stream_name]
        if any(stream_name is None for stream_name in stream_names): return

        streams = [EegVisualizerMainWindow.get_specific_lsl_stream(stream_name) for stream_name in stream_names]
        if any(stream is None for stream in streams): return

        for stream in streams:
            gl.lsl_handler.connect_to_specific_lsl_stream(stream)
            # gl.lsl_handler.start_data_recording_thread(stream)

        eeg_stream = streams[0]
        hr_stream = streams[1]
        rr_stream = streams[2]

        gl.eeg_processor = EEGProcessor(gl.lsl_handler, gl.lsl_handler.get_stream_by_name(eeg_stream.name()))
        gl.hr_processor = HRProcessor(gl.lsl_handler, gl.lsl_handler.get_stream_by_name(hr_stream.name()), gl.lsl_handler.get_stream_by_name(rr_stream.name()))

    def resizeEvent(self, event):
        if self.stream_selection_card.isVisible():
            self.adjust_stream_selection_card_size()

        super().resizeEvent(event)

    def show_stream_selection_view(self):
        horizontal_container = QWidget()
        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.stream_selection_card)
        horizontal_container.setLayout(horizontal_layout)
        self.central_layout.addWidget(horizontal_container)
        self.adjust_stream_selection_card_size()

    def adjust_stream_selection_card_size(self):
        window_size = self.size()
        window_width, window_height = window_size.width(), window_size.height()
        self.stream_selection_card.setFixedSize(window_width * 0.4, window_height * 0.8)
        card_width, card_height = self.stream_selection_card.width(), self.stream_selection_card.height()
        self.stream_selection_card.move((window_width - card_width) // 2, (window_height - card_height) // 2)

    def show_main_layout(self):
        EegVisualizerMainWindow.connect_to_selected_streams(self.selected_eeg_stream, self.selected_hr_stream, self.selected_rr_stream)

        current_widget = self.central_layout.itemAt(0).widget()
        current_widget.hide()
        self.central_layout.removeWidget(current_widget)

        self.visualizer_3d, self.visualizer_hr, self.visualizer_topo = EegVisualizerMainWindow.setup_visualizers_3d_and_hr()

        self.visualizer_3d.set_seconds_shown(DEFAULT_SECONDS_SHOWN)

        layout = QGridLayout()

        self.visualizer_3d.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.visualizer_hr.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_plot_container_widget = QWidget()
        self.main_plot_container_layout = QVBoxLayout()

        self.main_plot_container_layout.addWidget(self.visualizer_3d)
        main_plot_container_widget.setLayout(self.main_plot_container_layout)

        layout.addWidget(main_plot_container_widget, 0, 0, 2, 2)
        layout.addWidget(self.visualizer_hr, 2, 0, 1, 2)
        parameter_selection_container = self.get_parameter_selection()
        layout.addWidget(parameter_selection_container, 0, 2, 3, 1)

        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)
        layout.setRowStretch(2, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)

        container_widget = QWidget()
        container_widget.setLayout(layout)

        self.central_layout.addWidget(container_widget)
        container_widget.show()

    def setup_visualizers_3d_and_hr():
        visualizer_3d = Visualizer3D(gl.eeg_processor)
        visualizer_hr = VisualizerHR(gl.hr_processor)
        visualizer_topoplot = VisualizerTopoPlot()

        return visualizer_3d, visualizer_hr, visualizer_topoplot
    
    def get_all_lsl_streams():
        streams = gl.lsl_handler.get_all_lsl_streams()
        return streams

    def get_stream_selection_for(self, stream_type: StreamType):
        stream_selection_container = QWidget()
        stream_selection_layout = QVBoxLayout()
        selection_title = QLabel(f"Select {stream_type.name} Stream")
        selection_title.setStyleSheet(f"font-size: {FONT_SIZE_H2}px; font-weight: bold; border: none;")

        stream_selection_layout.addWidget(selection_title)

        lsl_streams = EegVisualizerMainWindow.get_all_lsl_streams()

        callback_function = None
        if stream_type == EegVisualizerMainWindow.StreamType.EEG:
            callback_function = self.select_eeg_stream
        elif stream_type == EegVisualizerMainWindow.StreamType.HR:
            callback_function = self.select_hr_stream
        elif stream_type == EegVisualizerMainWindow.StreamType.RR:
            callback_function = self.select_rr_stream
        else:
            raise ValueError
        
        for stream in lsl_streams:
            new_radio_button = QRadioButton(stream.name())
            stream_selection_layout.addWidget(new_radio_button)
            new_radio_button.clicked.connect(callback_function)

        stream_selection_container.setLayout(stream_selection_layout)

        return stream_selection_container
    
    def get_stream_selection_card(self):

        layout = QVBoxLayout()

        start_button = QPushButton("Use selected streams")
        start_button.clicked.connect(self.show_main_layout)
    
        stream_types = [stream_type for stream_type in EegVisualizerMainWindow.StreamType]
        for stream_type in stream_types:
            layout.addWidget(self.get_stream_selection_for(stream_type))

        layout.addWidget(start_button)

        container = QWidget()
        container.setLayout(layout)

        stream_selection_card = CardWidget("Select LSL Stream", content=container, title_is_h1=True)
        return stream_selection_card
    
    def select_eeg_stream(self):
        sender = self.sender()
        self.selected_eeg_stream = sender.text()

    def select_hr_stream(self):
        sender = self.sender()
        self.selected_hr_stream = sender.text()

    def select_rr_stream(self):
        sender = self.sender()
        self.selected_rr_stream = sender.text()

    def get_parameter_selection(self):
        parameter_selection_container = QWidget()
        vertical_layout = QVBoxLayout()
        main_plot_configuration = self.get_main_plot_configuration()
        sub_plot_configuration = self.get_sub_plot_configuration()
        vertical_layout.addWidget(main_plot_configuration)
        vertical_layout.addWidget(sub_plot_configuration)
        parameter_selection_container.setLayout(vertical_layout)
        parameter_selection_card = CardWidget("Configuration", content=parameter_selection_container)
        return parameter_selection_card
       
    def get_main_plot_configuration(self):
        form_layout = QFormLayout()
        
        main_plot_dropdown = QComboBox()
        main_plot_dropdown.addItems(['Spectrogram', 'Topoplot'])
        main_plot_dropdown.setStyleSheet("margin-top: 10px;")
        plot_label = QLabel("Plot:")
        plot_label.setStyleSheet("border: none;")
        plot_label.setMinimumWidth(HORIZONTAL_ROW_SPACER)
        form_layout.addRow(plot_label, main_plot_dropdown)

        main_plot_dropdown.currentIndexChanged.connect(lambda index: self.update_main_plot(main_plot_dropdown.itemText(index)))
        
        frequency_band_dropdown = QComboBox()
        frequency_band_dropdown.addItems(['Delta','Theta' ,'Alpha', 'Beta', 'Gamma'])
        frequency_band_dropdown.setStyleSheet("margin-top: 10px;")
        frequency_band_label = QLabel("Frequency Band:")
        frequency_band_label.setStyleSheet("border: none;")
        form_layout.addRow(frequency_band_label, frequency_band_dropdown)

        frequency_band_dropdown.currentIndexChanged.connect(lambda index: self.handle_filter_change(frequency_band_dropdown.itemText(index)))
        
        seconds_shown_input = QSpinBox()
        seconds_shown_input.setRange(1, 100)
        seconds_shown_input.setValue(DEFAULT_SECONDS_SHOWN)
        seconds_shown_input.setStyleSheet("margin-top: 10px;")
        seconds_shown_label = QLabel("Seconds Shown:")
        seconds_shown_label.setStyleSheet("border: none;")
        form_layout.addRow(seconds_shown_label, seconds_shown_input)

        seconds_shown_input.valueChanged.connect(self.handle_seconds_shown_change)

        window_size_exponent_input = QSpinBox()
        window_size_exponent_input.setRange(1, 15)
        window_size_exponent_input.setValue(DEFAULT_WINDOW_SIZE_EXPONENT)
        window_size_exponent_input.setStyleSheet("margin-top: 10px;")
        window_size_exponent_label = QLabel("Window size exponent:")
        window_size_exponent_label.setStyleSheet("border: none;")
        form_layout.addRow(window_size_exponent_label, window_size_exponent_input)

        window_size_exponent_input.valueChanged.connect(self.handle_window_size_exponent_change)

        form_container = QWidget()
        form_container.setLayout(form_layout)
        
        main_plot_configuration = CardWidget("Main Plot Configuration", content=form_container)
        return main_plot_configuration
    
    def get_sub_plot_configuration(self):
        form_layout = QFormLayout()
        
        sub_plot_dropdown = QComboBox()
        sub_plot_dropdown.addItems(['BPM', 'RMSSD', 'SDNN', 'Poin care ratio'])
        sub_plot_dropdown.setStyleSheet("margin-top: 10px;")
        plot_label = QLabel("Plot:")
        plot_label.setStyleSheet("border: none;")
        plot_label.setMinimumWidth(HORIZONTAL_ROW_SPACER)
        form_layout.addRow(plot_label, sub_plot_dropdown)

        sub_plot_dropdown.currentIndexChanged.connect(lambda index: self.update_sub_plot(sub_plot_dropdown.itemText(index)))

        form_container = QWidget()
        form_container.setLayout(form_layout)
        
        sub_plot_configuration = CardWidget("Sub Plot Configuration", content=form_container)
        return sub_plot_configuration
    
    def update_main_plot(self, plot_identifier):
        widget_to_use_as_main_plot = self.visualizer_3d if plot_identifier == 'Spectrogram' else self.visualizer_topo

        if self.main_plot_container_layout.count() > 0:
            current_widget = self.main_plot_container_layout.itemAt(0).widget()
            current_widget.hide()
            self.main_plot_container_layout.removeWidget(current_widget)
            self.main_plot_container_layout.addWidget(widget_to_use_as_main_plot)
            widget_to_use_as_main_plot.show()
    
    def update_sub_plot(self, plot_identifier):
        if plot_identifier == 'BPM':
            self.visualizer_hr.set_bio_variable(HR_BIO_VARIABLE.BPM)
        elif plot_identifier == 'RMSSD':
            self.visualizer_hr.set_bio_variable(HR_BIO_VARIABLE.RMSSD)
        elif plot_identifier == 'SDNN':
            self.visualizer_hr.set_bio_variable(HR_BIO_VARIABLE.SDNN)
        elif plot_identifier == 'Poin care ratio':
            self.visualizer_hr.set_bio_variable(HR_BIO_VARIABLE.POI_RAT)

    def handle_seconds_shown_change(self):
        new_value = self.sender().text()
        try:
            seconds = int(new_value)
            self.visualizer_3d.set_seconds_shown(seconds)
        except ValueError:
            pass

    def handle_window_size_exponent_change(self):
        new_value = self.sender().text()
        try:
            exponent = int(new_value)
            new_window_size = 2 ** exponent

            self.visualizer_3d.set_fft_buffer_len(new_window_size)
            self.visualizer_topo.set_window_size(new_window_size)
            # @todo: change window size for spectrogram and topoplot
        except ValueError:
            pass

    def handle_filter_change(self, filter_identifier):
        if filter_identifier == "Delta":
            self.visualizer_topo.set_filter(Filter.Delta)
        elif filter_identifier == "Theta":
            self.visualizer_topo.set_filter(Filter.Theta)
        elif filter_identifier == "Alpha":
            self.visualizer_topo.set_filter(Filter.Alpha)
        elif filter_identifier == "Beta":
            self.visualizer_topo.set_filter(Filter.Beta)
        elif filter_identifier == "Gamma":
            self.visualizer_topo.set_filter(Filter.Gamma)
        else: raise Exception()
