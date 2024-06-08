from PySide6.QtWidgets import QMainWindow

class EegVisualizerMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("EEG Visualizer Main Window")
