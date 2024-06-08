from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget


class EegVisualizerMainWindow(QMainWindow):
    def __init__(self, visualizer_3d, visualizer_hr):
        super().__init__()

        self.setWindowTitle("EEG Visualizer Main Window")

        layout = QVBoxLayout()

        layout.addWidget(visualizer_3d)
        layout.addWidget(visualizer_hr)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)