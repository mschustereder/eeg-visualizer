# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'visualizer.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QMainWindow, QMenuBar, QSizePolicy,
    QStatusBar, QWidget)

class Ui_EegVisualizer(object):
    def setupUi(self, EegVisualizer):
        if not EegVisualizer.objectName():
            EegVisualizer.setObjectName(u"EegVisualizer")
        EegVisualizer.resize(800, 600)
        self.centralwidget = QWidget(EegVisualizer)
        self.centralwidget.setObjectName(u"centralwidget")
        EegVisualizer.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(EegVisualizer)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        EegVisualizer.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(EegVisualizer)
        self.statusbar.setObjectName(u"statusbar")
        EegVisualizer.setStatusBar(self.statusbar)

        self.retranslateUi(EegVisualizer)

        QMetaObject.connectSlotsByName(EegVisualizer)
    # setupUi

    def retranslateUi(self, EegVisualizer):
        EegVisualizer.setWindowTitle(QCoreApplication.translate("EegVisualizer", u"EegVisualizer", None))
    # retranslateUi

