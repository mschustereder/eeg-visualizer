import visualizer.globals as gl
from visualizer.eeg_visualizer import *
from signalProcessor.EEGProcessor import EEGProcessor, Filter
from signalProcessor.HRProcessor import HRProcessor
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from visualizer.Visualizer3D import Visualizer3D
from visualizer.VisualizerHR import VisualizerHR
from visualizer.VisualizerTopoPlot import VisualizerTopoPlot
from PySide6 import QtCore


if __name__ == "__main__":
    streams = gl.lsl_handler.get_all_lsl_streams()
    print([stream.name() for stream in streams])
    for stream in streams:
        gl.lsl_handler.connect_to_specific_lsl_stream(stream)
        gl.lsl_handler.start_data_recording_thread(stream)

    gl.eeg_processor = EEGProcessor(gl.lsl_handler, gl.lsl_handler.get_stream_by_name("BrainVision RDA"))
    gl.hr_processor = HRProcessor(gl.lsl_handler, gl.lsl_handler.get_stream_by_name("HR_Polar H10 CA549123"), gl.lsl_handler.get_stream_by_name("RR_Polar H10 CA549123"), gl.MAX_HR_DATA_SAMPLES)

    app = QApplication(sys.argv)
    window = QMainWindow()
    vis = Visualizer3D()
    timer = QtCore.QTimer()
    timer.setInterval(gl.EEG_GRAPH_INTERVAL_MS)
    timer.start()
    window.setCentralWidget(vis)
    window.show()
    timer.timeout.connect(vis.update_spectrum)
 
    window2 = QMainWindow()
    vis2 = VisualizerHR()
    timer.timeout.connect(vis2.update_graph)
    window2.setCentralWidget(vis2)
    window2.show()


## Visualizer for topoplot:
    # window3 = QMainWindow()
    # central_widget = QWidget()
    # vis_topo = VisualizerTopoPlot(central_widget)
    # window3.setCentralWidget(vis_topo)
    # window3.show()




    sys.exit(app.exec())
