from PySide6 import QtGui, QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np


class Visualizer3DColorBar(QtWidgets.QWidget):

    def __init__(self, cm = pg.colormap.get('turbo'), parent = None) -> None:
        super().__init__(parent)
        self.gradient = QtGui.QLinearGradient()
        self.cm = cm
        self.levels = [0, 1]

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        #draw gradient
        painter = QtGui.QPainter(self)
        background = QtCore.QRect(0, 0, self.width(), self.height())
        painter.fillRect(background, QtGui.QColor("black"))
        painter.setPen("white")
        stops = self.cm.getStops(pg.ColorMap.FLOAT)
        colors = self.cm.getColors(pg.ColorMap.QCOLOR)
        gradient = QtGui.QLinearGradient(0, 0, 0, self.height())
        for stop, color in zip(stops[0], colors):
            gradient.setColorAt(1-stop, color)

        text_field_size = 35
        margin_y = self.height()*0.1
        text_size_y = round(painter.fontInfo().pixelSize()*2)    
        text_size_x = 50
        margin_x = self.width()*0.1
        gradient_width = self.width()-text_field_size-3*margin_x
        rect_grade = QtCore.QRect(margin_x, margin_y + text_size_y, gradient_width, self.height()-2*margin_y-text_size_y)
        border_width = 1
        rect_border = QtCore.QRect(margin_x-border_width, margin_y-border_width + text_size_y, self.width()-text_field_size-3*margin_x + 2*border_width, self.height()-2*margin_y+2*border_width-text_size_y)
        painter.fillRect(rect_border, QtGui.QColor("white"))
        painter.fillRect(rect_grade, gradient)

        #draw unit label
        rect = QtCore.QRect(margin_x + round((gradient_width-text_size_x)/2), margin_y, text_size_x, text_size_y)
        painter.drawText(rect, QtGui.Qt.AlignmentFlag.AlignCenter, "Power")

        #draw values
        font_size = painter.fontInfo().pixelSize()
        y_pos_top = margin_y + text_size_y
        y_pos_bottom = self.height()-margin_y
        y_span = y_pos_bottom - y_pos_top #y axis inverted to value axis
        value_span = self.levels[1] - self.levels[0]


        for val in np.linspace(self.levels[0], self.levels[1], 5):
            mapped_value = (1-(val-self.levels[0])/value_span) * y_span + y_pos_top
            position = QtCore.QPoint(self.width()-text_field_size-margin_x, mapped_value+round(font_size/2))
            painter.drawText(position, str(round(val, 2)))
        
    def update_values(self,  levels):
        self.levels = levels
        self.update()

    def set_color_map(self, cm):
        self.cm = cm