from PySide6.QtWidgets import QMainWindow, QGridLayout, QWidget, QVBoxLayout, QComboBox, QSizePolicy, QLabel, QFrame, QFormLayout, QRadioButton, QPushButton, QHBoxLayout, QSpinBox, QScrollArea
from PySide6.QtCore import Qt, QSize
from PySide6 import QtCore, QtGui
import sys
from PySide6.QtWidgets import QApplication
from visualizer.Visualizer3D import Visualizer3DSurface, Visualizer3DLine
from visualizer.Visualizer3DColorBar import Visualizer3DColorBar
from visualizer.VisualizerTopoPlot import VisualizerTopoPlot
from visualizer.VisualizerHR import VisualizerHR, HR_BIO_VARIABLE
import visualizer.globals as gl
from signalProcessor.EEGProcessor import EEGProcessor, Filter
from signalProcessor.HRProcessor import HRProcessor
from enum import Enum
from visualizer.dark_stylesheet import dark_stylesheet

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

        self.content_container = QWidget()
        self.content_container.setLayout(layout)
        card_grid_layout.addWidget(self.content_container, 1, 0, 10, 1)
        self.setLayout(card_grid_layout)

                # border: 1px solid #d3d3d3;
        self.setStyleSheet("""
            QFrame {
                border: 2px solid black;
                border-radius: 2px;
                background-color: #2b2b2b;
                padding: 10px;
            }
        """)

    def replace_content(self, new_content):
        new_vbox_layout = QVBoxLayout()
        new_vbox_layout.addWidget(new_content)
        QWidget().setLayout(self.content_container.layout()) # 're-parent' the previous layout
        self.content_container.setLayout(new_vbox_layout)

def execute_qt_app():
    app = QApplication(sys.argv)

    app.setStyleSheet(dark_stylesheet)

    window = EegVisualizerMainWindow()

    window.showMaximized()

    sys.exit(app.exec())

class EegVisualizerMainWindow(QMainWindow):
    class BioVariableOptions(Enum):
        BPM = "BPM"
        RMSSD = "RMSSD"
        SDNN = "SDNN"
        Poin_care_ratio = "Poin_care_ratio"

    class MainPlotOptions(Enum):
        Spectrogram = "Spectrogram"
        Topoplot = "Topoplot"

    class FilterOptions(Enum):
        Manual_filter = "Manual_filter"
        Delta = "Delta"
        Theta = "Theta"
        Alpha = "Alpha"
        Beta = "Beta"
        Gamma = "Gamma"
        All = "All"

    class StreamType(Enum):
        EEG = 1
        HR = 2
        RR = 3

    def __init__(self):
        super().__init__()

        self.count_times_searched_for_lsl_streams = 0
        self.all_lsl_streams = None

        self.setWindowTitle("EEG Visualizer")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)

        for i in range(3):
            self.search_for_lsl_streams_again()

        self.stream_selection_card = self.get_stream_selection_card()

        self.selected_eeg_stream = None
        self.selected_hr_stream = None
        self.selected_rr_stream = None

        self.show_stream_selection_view()

    def get_specific_lsl_stream(self, stream_name):
        all_lsl_streams = self.get_all_lsl_streams()
        first_match = next((stream for stream in all_lsl_streams if stream.name() == stream_name), None)

        if first_match is None:
            raise ValueError
        
        return first_match

    def connect_to_selected_streams(self, eeg_stream_name, hr_stream_name, rr_stream_name):
        stream_names = [eeg_stream_name, hr_stream_name, rr_stream_name]
        if any(stream_name is None for stream_name in stream_names): return

        streams = [self.get_specific_lsl_stream(stream_name) for stream_name in stream_names]
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
        self.connect_to_selected_streams(self.selected_eeg_stream, self.selected_hr_stream, self.selected_rr_stream)

        current_widget = self.central_layout.itemAt(0).widget()
        self.central_layout.removeWidget(current_widget)

        self.visualizer_3d, visualizer_3d_color_bar, self.visualizer_hr, self.visualizer_topo = EegVisualizerMainWindow.setup_visualizers_3d_and_hr()

        self.visualizer_3d_wrapper_widget = QWidget()
        visualizer_3d_layout = QGridLayout()
        visualizer_3d_layout.addWidget(self.visualizer_3d, 0, 0, 1, 10)
        visualizer_3d_layout.addWidget(visualizer_3d_color_bar, 0, 11, 1, 1)
        self.visualizer_3d_wrapper_widget.setLayout(visualizer_3d_layout)

        self.visualizer_3d.set_seconds_shown(DEFAULT_SECONDS_SHOWN)

        layout = QGridLayout()

        self.visualizer_3d.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.visualizer_hr.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_plot_container_widget = QWidget()
        self.main_plot_container_layout = QVBoxLayout()

        self.main_plot_container_layout.addWidget(self.visualizer_3d_wrapper_widget)
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

    def setup_visualizers_3d_and_hr():
        visualizer_3d_color_bar = Visualizer3DColorBar()
        visualizer_3d = Visualizer3DLine(visualizer_3d_color_bar)
        visualizer_hr = VisualizerHR()
        visualizer_topoplot = VisualizerTopoPlot()

        return visualizer_3d, visualizer_3d_color_bar, visualizer_hr, visualizer_topoplot
    
    def get_all_lsl_streams(self, search_again=False):
        if (not self.all_lsl_streams and self.count_times_searched_for_lsl_streams < 3) or search_again:
            self.all_lsl_streams = gl.lsl_handler.get_all_lsl_streams()        

        self.count_times_searched_for_lsl_streams += 1
        return self.all_lsl_streams

    def get_stream_selection_for(self, stream_type: StreamType):
        stream_selection_container = QWidget()
        stream_selection_layout = QVBoxLayout()
        selection_title = QLabel(f"Select {stream_type.name} Stream")
        selection_title.setStyleSheet(f"font-size: {FONT_SIZE_H2}px; font-weight: bold; border: none;")

        stream_selection_layout.addWidget(selection_title)

        lsl_streams = self.get_all_lsl_streams()

        callback_function = None
        if stream_type == EegVisualizerMainWindow.StreamType.EEG:
            callback_function = self.select_eeg_stream
        elif stream_type == EegVisualizerMainWindow.StreamType.HR:
            callback_function = self.select_hr_stream
        elif stream_type == EegVisualizerMainWindow.StreamType.RR:
            callback_function = self.select_rr_stream
        else:
            raise ValueError
        
        radio_button_area = QWidget()
        radio_button_vbox_layout = QVBoxLayout()
        
        for stream in lsl_streams:
            new_radio_button = QRadioButton(stream.name())
            radio_button_vbox_layout.addWidget(new_radio_button)
            new_radio_button.clicked.connect(callback_function)

        if len(lsl_streams) == 0:
            radio_button_vbox_layout.addWidget(QLabel("No streams found."))

        radio_button_area.setLayout(radio_button_vbox_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(radio_button_area)

        stream_selection_layout.addWidget(scroll_area)

        stream_selection_container.setLayout(stream_selection_layout)

        return stream_selection_container
    
    def search_for_lsl_streams_again(self):
        _ = self.get_all_lsl_streams(search_again=True)

    def search_again_and_update_stream_selection_view(self):
        self.search_for_lsl_streams_again()

        new_content = self.build_content_for_stream_selection_card()

        self.stream_selection_card.replace_content(new_content)

    def build_content_for_stream_selection_card(self):
        layout = QVBoxLayout()

        search_again_button = QPushButton("Search again")
        search_again_button.clicked.connect(self.search_again_and_update_stream_selection_view)

        layout.addWidget(search_again_button)

        start_button = QPushButton("Use selected streams")
        start_button.clicked.connect(self.show_main_layout)
    
        stream_types = [stream_type for stream_type in EegVisualizerMainWindow.StreamType]
        for stream_type in stream_types:
            layout.addWidget(self.get_stream_selection_for(stream_type))

        start_button.setEnabled(len(self.get_all_lsl_streams()) != 0)

        layout.addWidget(start_button)

        content = QWidget()
        content.setLayout(layout)

        return content
    
    def get_stream_selection_card(self):
        content = self.build_content_for_stream_selection_card()

        stream_selection_card = CardWidget("Select LSL Stream", content=content, title_is_h1=True)
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
        main_plot_dropdown.addItems([self.MainPlotOptions.Spectrogram.value,
                                     self.MainPlotOptions.Topoplot.value])
        main_plot_dropdown.setStyleSheet("margin-top: 10px;")
        plot_label = QLabel("Plot:")
        plot_label.setStyleSheet("border: none;")
        plot_label.setMinimumWidth(HORIZONTAL_ROW_SPACER)
        form_layout.addRow(plot_label, main_plot_dropdown)

        main_plot_dropdown.currentIndexChanged.connect(lambda index: self.update_main_plot(main_plot_dropdown.itemText(index)))
        
        frequency_band_dropdown = QComboBox()
        frequency_band_dropdown.addItems([self.FilterOptions.Manual_filter.value,
                                          self.FilterOptions.Delta.value,
                                          self.FilterOptions.Theta.value,
                                          self.FilterOptions.Alpha.value,
                                          self.FilterOptions.Beta.value,
                                          self.FilterOptions.Gamma.value,
                                          self.FilterOptions.All.value])
        frequency_band_dropdown.setStyleSheet("margin-top: 10px;")
        frequency_band_label = QLabel("Frequency Band:")
        frequency_band_label.setStyleSheet("border: none;")
        form_layout.addRow(frequency_band_label, frequency_band_dropdown)

        frequency_band_dropdown.currentIndexChanged.connect(lambda index: self.handle_filter_change(frequency_band_dropdown.itemText(index)))
        
        self.manual_filter_selection_container = QWidget()
        manual_filter_selection_container_layout = QFormLayout()

        lower_freq_input = QSpinBox()
        lower_freq_input.setRange(1, 100)
        lower_freq_input.setValue(Filter.Manual[0])
        lower_freq_input.setStyleSheet("margin-top: 10px;")
        lower_freq_label = QLabel("Lower Cutoff:")
        lower_freq_label.setStyleSheet("border: none;")
        manual_filter_selection_container_layout.addRow(lower_freq_label, lower_freq_input)

        lower_freq_input.valueChanged.connect(self.handle_manual_filter_low_freq_change)

        higher_freq_input = QSpinBox()
        higher_freq_input.setRange(1, 100)
        higher_freq_input.setValue(Filter.Manual[1])
        higher_freq_input.setStyleSheet("margin-top: 10px;")
        higher_freq_label = QLabel("Higher Cutoff:")
        higher_freq_label.setStyleSheet("border: none;")
        manual_filter_selection_container_layout.addRow(higher_freq_label, higher_freq_input)

        higher_freq_input.valueChanged.connect(self.handle_manual_filter_high_freq_change)

        self.manual_filter_selection_container.setLayout(manual_filter_selection_container_layout)

        self.manual_filter_label = QLabel("Manual filter: (ℹ️)")
        self.manual_filter_label.setToolTip("The filters will only be set, if the lower cutoff is smaller than the higher cutoff!")
        self.manual_filter_label.setStyleSheet("border: none;")
        form_layout.addRow(self.manual_filter_label, self.manual_filter_selection_container)

        self.handle_filter_change(self.FilterOptions.Manual_filter.value)

        self.seconds_shown_input = QSpinBox()
        self.seconds_shown_input.setRange(1, 60)
        self.seconds_shown_input.setValue(DEFAULT_SECONDS_SHOWN)
        self.seconds_shown_input.setStyleSheet("margin-top: 10px;")
        self.seconds_shown_label = QLabel("Seconds Shown:")
        self.seconds_shown_label.setStyleSheet("border: none;")
        form_layout.addRow(self.seconds_shown_label, self.seconds_shown_input)

        self.seconds_shown_input.valueChanged.connect(self.handle_seconds_shown_change)

        window_size_exponent_input = QSpinBox()
        window_size_exponent_input.setRange(6, 11)
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
        sub_plot_dropdown.addItems([self.BioVariableOptions.BPM.value,
                                    self.BioVariableOptions.RMSSD.value,
                                    self.BioVariableOptions.SDNN.value,
                                    self.BioVariableOptions.Poin_care_ratio.value])
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
        if plot_identifier == self.MainPlotOptions.Spectrogram.value:
            widget_to_use_as_main_plot = self.visualizer_3d_wrapper_widget
            self.visualizer_topo.stop_and_wait_for_process_thread()
            self.visualizer_3d.start_thread()
            self.seconds_shown_label.show()
            self.seconds_shown_input.show()
        else:
            widget_to_use_as_main_plot = self.visualizer_topo
            self.visualizer_3d.stop_and_wait_for_process_thread()
            self.visualizer_topo.start_thread()
            self.seconds_shown_label.hide()
            self.seconds_shown_input.hide()

        if self.main_plot_container_layout.count() > 0:
            current_widget = self.main_plot_container_layout.itemAt(0).widget()
            current_widget.hide()
            self.main_plot_container_layout.removeWidget(current_widget)
            self.main_plot_container_layout.addWidget(widget_to_use_as_main_plot)
            widget_to_use_as_main_plot.show()
    
    def update_sub_plot(self, plot_identifier):
        if plot_identifier == self.BioVariableOptions.BPM.value:
            self.visualizer_hr.set_bio_variable(HR_BIO_VARIABLE.BPM)
        elif plot_identifier == self.BioVariableOptions.RMSSD.value:
            self.visualizer_hr.set_bio_variable(HR_BIO_VARIABLE.RMSSD)
        elif plot_identifier == self.BioVariableOptions.SDNN.value:
            self.visualizer_hr.set_bio_variable(HR_BIO_VARIABLE.SDNN)
        elif plot_identifier == self.BioVariableOptions.Poin_care_ratio.value:
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
        except ValueError:
            pass

    def handle_filter_change(self, filter_identifier):
        if not filter_identifier == self.FilterOptions.Manual_filter.value:
            self.manual_filter_selection_container.hide()
            self.manual_filter_label.hide()

        if filter_identifier == self.FilterOptions.Delta.value:
            self.visualizer_topo.set_filter(Filter.Delta)
            self.visualizer_3d.set_filter_type(Filter.Delta)
        elif filter_identifier == self.FilterOptions.Theta.value:
            self.visualizer_topo.set_filter(Filter.Theta)
            self.visualizer_3d.set_filter_type(Filter.Theta)
        elif filter_identifier == self.FilterOptions.Alpha.value:
            self.visualizer_topo.set_filter(Filter.Alpha)
            self.visualizer_3d.set_filter_type(Filter.Alpha)
        elif filter_identifier == self.FilterOptions.Beta.value:
            self.visualizer_topo.set_filter(Filter.Beta)
            self.visualizer_3d.set_filter_type(Filter.Beta)
        elif filter_identifier == self.FilterOptions.Gamma.value:
            self.visualizer_topo.set_filter(Filter.Gamma)
            self.visualizer_3d.set_filter_type(Filter.Gamma)
        elif filter_identifier == self.FilterOptions.All.value:
            self.visualizer_topo.set_filter(Filter.NoNe)
            self.visualizer_3d.set_filter_type(Filter.NoNe)
        elif filter_identifier == self.FilterOptions.Manual_filter.value:
            self.visualizer_topo.set_filter(Filter.Manual)
            self.visualizer_3d.set_filter_type(Filter.Manual)
            self.manual_filter_selection_container.show()
            self.manual_filter_label.show()
        else: raise Exception()


    def handle_manual_filter_low_freq_change(self, lower_freq):
        if lower_freq >= Filter.Manual[1]: return

        Filter.Manual[0] = lower_freq

    def handle_manual_filter_high_freq_change(self, higher_freq):
        if higher_freq <= Filter.Manual[0]: return

        Filter.Manual[1] = higher_freq