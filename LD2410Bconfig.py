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
    receivedAck = pyqtSignal(bytes)

    # Serial object:
    ser = serial.Serial()
    baudrate = 256000
    port = ''
    openflag = 0
    sendCmd = b''

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
        print('Starting....')
        if self.openflag:
            self.ser.reset_input_buffer()
        else:
            return
        i = 0
        state = 0
        intraframedata = b''
        ackintraframedata = b''

        # Parsing the frame data:
        while (self.openflag):
            s = self.ser.read(1)
            #sint = int.from_bytes(s,'little')
            if (s == b'\xF4'): # Start of Reporting Frame data
                #print(s)
                #print('ok')
                s = self.ser.read(3)
                if (s == b'\xF3\xF2\xF1'): # Reporting Frame data init
                    s = self.ser.read(2) # Read intra frame data lenght
                    datalen = int.from_bytes(s,'little')
                    intraframedata = self.ser.read(datalen) # Read intra frame data
                    s = self.ser.read(4) # Read End of Frame
                    if (s == b'\xF8\xF7\xF6\xF5'):
                        self.received.emit(intraframedata) # Ok, end of frame detected, send intraframe data.
                        self.progress.emit(i)
                        i = i + 1
            elif (s == b'\xFD'):    # Start of an ACK frame
                s = self.ser.read(3)
                if (s == b'\xFC\xFB\xFA'): # ACK command frame data init
                    s = self.ser.read(2) # Read intra frame data lenght
                    datalen = int.from_bytes(s,'little')
                    ackintraframedata = self.ser.read(datalen) # Read intra frame data
                    s = self.ser.read(4) # Read End of Frame
                    if (s == b'\x04\x03\x02\x01'):
                        self.receivedAck.emit(ackintraframedata) # Ok, end of frame detected, send intraframe data.                    
                        self.progress.emit(i)
                        i = i + 1
            #self.received.emit(s)
                        
            if (self.sendCmd):
                self.ser.write(bytes.fromhex('FDFCFBFA0400FF00010004030201')) # Enable config command
                self.ser.write(self.sendCmd)
                self.ser.write(bytes.fromhex('FDFCFBFA0200FE0004030201')) # End of config command
                self.sendCmd = 0
            
            
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

        # Connect UI events:
        self.btnSerialRefresh.clicked.connect(self.onbtnSerialRefresh)
        self.btnOpenPort.clicked.connect(self.onbtnOpenPort)
        self.btnClosePort.clicked.connect(self.onbtnClosePort)
        self.btnSendCmd.clicked.connect(self.onbtnSendCommand)
        self.comboBoxCommands.currentIndexChanged.connect(self.onComboCommandsChanged)
    
    # ********* Buttons event handlers: ************
    def onbtnSerialRefresh(self):
        self.updatePortsList()
    
    def onbtnOpenPort(self):
        self.serialThread = QThread()           # Create a QThread object
        self.worker = SerialWorkerThread()      # Create a worker object

        self.worker.baudrate = int(self.comboBoxBaud.currentText())# self.lineEditBoud.text())
        self.worker.port = self.comboSerial.currentText()
        # Qthread stuff:
        self.worker.moveToThread(self.serialThread)   # Move worker to the thread
        # Connect Thread signals and slots
        self.serialThread.started.connect(self.worker.run)    # When thread is started
        self.worker.finished.connect(self.serialThread.quit)  # When finished
        self.worker.finished.connect(self.worker.deleteLater)
        self.serialThread.finished.connect(self.serialThread.deleteLater)
        self.worker.progress.connect(self.reportProgress)   # Progress signal.
        self.worker.received.connect(self.onReceivedData)
        self.worker.receivedAck.connect(self.onReceivedAck)
        #self.serialThread.finished.connect(self.onSerialWorkerFinished)
        self.worker.finished.connect(self.onSerialWorkerFinished) 

        # Open serial port:
        self.worker.openSerial()
        # Star thread        
        self.serialThread.start() # Start receiving
    
    def onbtnClosePort(self):
        self.worker.closeSerial()
    
    def onbtnSendCommand(self):
        """
        Send a command.
        """
        enableCfgcmd = 'FDFCFBFA0400FF00010004030201'
        endCfgcmd = 'FDFCFBFA0200FE0004030201'

        if(self.worker.openflag):
            self.worker.sendCmd = bytes.fromhex(enableCfgcmd)
        
    def onComboCommandsChanged(self, index):
        """
        Fill the TextEdit with the selected command hex string.
        """
        cmdstr = ''
        if (index == 0): # Turn ON bluetooth
            cmdstr = 'FDFCFBFA0400A400010004030201'
        elif (index == 1): # Turn OFF bluetooth
            cmdstr = 'FDFCFBFA0400A400000004030201'
        else:
            self.statusBar().showMessage(_translate("MainWindow", "Command not implemented yet.", None),5000)
            self.statusBar().repaint()
        self.lineEditSendCmd.setText(cmdstr)
        

    # ********* Other methods: ************
    def onSerialWorkerFinished(self):
        #self.labelbytes.setText("Long-Running Step: 0")
        print('Thread finished')
    
    def onReceivedData(self, val):
        if (self.checkBoxData.isChecked()):
            self.textEditMessagesLog.moveCursor(QTextCursor.End)
            self.textEditMessagesLog.insertPlainText(val.hex())
            self.textEditMessagesLog.insertPlainText('\r\n')

    def onReceivedAck(self, val):
        if (self.checkBoxAck.isChecked()):
            self.textEditMessagesLog.moveCursor(QTextCursor.End)
            self.textEditMessagesLog.insertPlainText(val.hex())
            self.textEditMessagesLog.insertPlainText('\r\n')

    def reportProgress(self, n):
        #self.labelbytes.setText(f"Long-Running Step: {n}")
        self.statusBar().showMessage(_translate("MainWindow", f"Received frames: {n}", None),5000) 
        self.statusBar().repaint()

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
        #self.serialThread.quit()
        #self.serialThread.deleteLater()
        event.accept()


# Run de application:
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    #app.setStyle('Fusion')
    locale = QtCore.QLocale.system().name()
    # If not portuguese, instal english translator:
    #if (locale != 'pt_BR' and locale != 'pt_PT'):
    #    translator = QtCore.QTranslator()
    #    translator.load("LabControl3_en.qm")
    #    app.installTranslator(translator)
    win = LD2410AppWindow()
    win.show()
    app.exec_()