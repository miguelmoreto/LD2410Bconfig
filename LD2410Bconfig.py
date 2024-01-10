#!/usr/bin/ python3
# -*- coding: utf-8 -*-

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets
)

from PyQt5.Qt import Qt
from PyQt5.uic import loadUi

import serial
import images_rc

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)


class LD2410AppWindow(QtWidgets.QMainWindow):#,MainWindow.Ui_MainWindow):
    """
    hwl is inherited from both QtGui.QDialog and hw.Ui_Dialog
    """

    def __init__(self,parent=None):
        super(LD2410AppWindow,self).__init__(parent)
        loadUi('mainwindow.ui', self)


# Run de application:
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    app.setStyle('Fusion')
    locale = QtCore.QLocale.system().name()
    # If not portuguese, instal english translator:
    #if (locale != 'pt_BR' and locale != 'pt_PT'):
    #    translator = QtCore.QTranslator()
    #    translator.load("LabControl3_en.qm")
    #    app.installTranslator(translator)
    win = LD2410AppWindow()
    win.show()
    app.exec_()