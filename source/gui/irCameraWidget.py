import numpy as np
import logging
import warnings
warnings.filterwarnings("ignore")
import sys
import os


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy.ndimage.filters import gaussian_filter

from PyQt5 import Qt, QtCore,
from PyQt5.QtWidgets import QWidget,  QSlider
from PyQt5.QtCore import QTimer

# if running from command line, need to append the parent directories to the PATH
# so python knows where to find "source.file"
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
import source.tools.exceptionLogging

##Embedd a matplotlib plot into Qt for IR camera data display
class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=3, height=3, dpi=100):
        
        self.midpoint = 23
        self.scale = 50

        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


        self.ax = self.figure.add_subplot(111)
        self.ax.set_title('Ir camera')
        self.ax.axes.get_yaxis().set_visible(False)
        self.ax.axes.get_xaxis().set_visible(False)
        self.data  = np.ones((8,8,3), dtype = int)

    ##Convert a given temprature to  blue->red heatmap
    def convertTempToColour(self,value):
        red, green, blue = 255, 255, 255

        if value < self.midpoint:
            value = np.abs(value -self.midpoint)
            red -=  value*self.scale
            green -= value*self.scale

        elif value > self.midpoint:
            value = np.abs(value -self.midpoint)
            blue -= value*self.scale
            green -= value*self.scale
        elif value == self.midpoint:
            pass

        return int(red), int(green), int(blue)


    ##Plot the given data
    def plot(self, datain=None):
        
        self.midpoint = ((np.max(datain) - np.min(datain)) / 2) +np.min(datain)
        self.ax.clear()
        for i in range(len(datain)):
            for j in range(len(datain[i])):
                self.data[i][j] = self.convertTempToColour(datain[i][j])
                self.ax.text(j-0.4 ,i, datain[i][j],fontsize=7)

        self.ax.set_title('Ir camera')
        self.ax.imshow(self.data)

        self.draw()

class IrCameraWidget(QWidget):
    _logname = 'IrCameraWidget'
    _log = logging.getLogger(f'{_logname}')
    def __init__(self, radio=None, parent = None):
        assert radio is not None

        slider = QSlider(QtCore.Qt.Vertical)
        slider.setMinimum(0)
        slider.setMaximum(50)
        slider.setValue(10)
        cameraPlot = PlotCanvas(self, width=4, height=4)
        slider.valueChanged.connect(lambda: cameraPlot.scale = slider.value())

        updateTimer = QTimer(self)
        updateTimer.timeout.connect(lambda: cameraPlot.plot(radio.irTemp))
        updateTimer.start(5000)


        ircameralayout = QHBoxLayout()
        ircameralayout.addWidget(cameraPlot)
        ircameralayout.addWidget(slider)

        setLayout(ircameralayout)


