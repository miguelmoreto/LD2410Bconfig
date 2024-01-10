#!/usr/bin/ python3
# -*- coding: utf-8 -*-

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets
)

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor

from PyQt5.Qt import Qt
from PyQt5.uic import loadUi
from time import sleep

import serial
import serial.tools.list_ports
import images_rc

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

# Theread example from https://realpython.com/python-pyqt-qthread/
class SerialWorkerThread(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    received = pyqtSignal(bytes)

    # Serial object:
    ser = serial.Serial()
    baudrate = 256000
    port = ''
    openflag = 0

    def openSerial(self):
        ret = 0
        self.ser.baudrate = self.baudrate
        self.ser.port = self.port
        self.ser.timeout = 1
        
        try:
            self.ser.open()
        except (OSError, serial.SerialException):
            print('Error opening the serial device.')
            self.openflag = 0
        else:
            self.openflag = 1
            print('Serial open')
    
    def closeSerial(self):
        self.openflag = 0
        

    def run(self):
        """Long-running task."""
        if self.openflag:
            self.ser.reset_input_buffer()
        else:
            return
        i = 0
        #for i in range(10):
        #    #sleep(1)
        #    s = self.ser.read(1)
        #    self.received.emit(s)
        #    self.progress.emit(i+1)
        while (self.openflag):
            s = self.ser.read(1)
            self.received.emit(s)
            self.progress.emit(i)
            i = i + 1
        self.ser.close()
        self.finished.emit()

class LD2410AppWindow(QtWidgets.QMainWindow):#,MainWindow.Ui_MainWindow):
    """
    hwl is inherited from both QtGui.QDialog and hw.Ui_Dialog
    """

    def __init__(self,parent=None):
        super(LD2410AppWindow,self).__init__(parent)
        loadUi('mainwindow.ui', self)

        # Serial object:
        self.ser = serial.Serial()

        # Initial actions:
        self.updatePortsList()

        # Thread stuff:
        self.serialThread = QThread()           # Create a QThread object
        self.worker = SerialWorkerThread()      # Create a worker object
        self.worker.moveToThread(self.serialThread)   # Move worker to the thread

        # Connect Thread signals and slots
        self.serialThread.started.connect(self.worker.run)    # When thread is started
        self.worker.finished.connect(self.serialThread.quit)  # When finished
        self.worker.finished.connect(self.worker.deleteLater)
        self.serialThread.finished.connect(self.serialThread.deleteLater)
        self.worker.progress.connect(self.reportProgress)   # Progress signal.
        self.worker.received.connect(self.onReceivedBytes)
        self.serialThread.finished.connect(self.onSerialWorkerFinished)
        # Connect UI events:
        self.btnSerialRefresh.clicked.connect(self.onbtnSerialRefresh)
        self.btnOpenPort.clicked.connect(self.onbtnOpenPort)
        self.btnClosePort.clicked.connect(self.onbtnClosePort)
    
    # ********* Buttons event handlers: ************
    def onbtnSerialRefresh(self):
        self.updatePortsList()
    
    def onbtnOpenPort(self):
        self.worker.baudrate = int(self.lineEditBoud.text())
        self.worker.port = self.comboSerial.currentText()
        #self.ser.port = 
        #self.ser.baudrate = 
        #self.startSerialThread()
        #self.serialThread.start() # Start receiving
        self.worker.openSerial()
        self.serialThread.start() # Start receiving
    
    def onbtnClosePort(self):
        self.worker.closeSerial()
        


    # ********* Other methods: ************
    def onSerialWorkerFinished(self):
        #self.labelbytes.setText("Long-Running Step: 0")
        print('Thread finished')
    
    def onReceivedBytes(self, val):
        self.textEditMessagesLog.moveCursor(QTextCursor.End)
        self.textEditMessagesLog.insertPlainText(val.hex())

    def reportProgress(self, n):
        self.labelbytes.setText(f"Long-Running Step: {n}")

    def updatePortsList(self):
        # Remove existing itens:
        self.comboSerial.clear()
        # Add itens:
        for port in serial.tools.list_ports.comports():
            print(port.device)
            self.comboSerial.insertItem(0,port.device)
    
    # ********* Other events: ************
    def closeEvent(self, event):
        print('Closing application.')
        self.worker.closeSerial()
        event.accept()


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