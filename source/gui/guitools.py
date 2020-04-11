##@package guitools
#Tools package to help with ome gui functionality


from PyQt5.QtWidgets import QFrame, QComboBox, QLabel, \
    QDialog, QHBoxLayout, QVBoxLayout, QDialogButtonBox, QWidget, QSizePolicy
from qwt import QwtScaleDraw, QwtText
import logging


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy.ndimage.filters import gaussian_filter
import time
import numpy as np
import datetime 


import source.tools.exceptionLogging
from source.tools.constants import *
from source.tools.sqlBrewingComms import SQLFermentMonitor

##Draw a horizontal Line
class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

##Draw a vertical Line
class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)

##Draw a coloured box (RGB)
class QBoxColour(QFrame):
    def __init__(self, rgb: tuple):
        super(QBoxColour, self).__init__()
        self.setStyleSheet("background-color: rgb({}, {}, {});".format(rgb[0],rgb[1],rgb[3]))

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
        for i in range(8):
            for j in range(8):
                self.data[i][j] = self.convertTempToColour(datain[i][j])
                self.ax.text(j-0.4 ,i, datain[i][j],fontsize=7)

        self.ax.set_title('Ir camera')
        self.ax.imshow(self.data)

        self.draw()


##convert database timestamps into xaxis values for a graph
class TimeScaleDraw(QwtScaleDraw):
    _logname = 'TimeScaleDraw'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, timeStamps=None, names=True, granularity=2, *args):
        QwtScaleDraw.__init__(self, *args)
        self.timeStamps = timeStamps
        self.fmtFull='%H:%M:%S\n%Y-%m-%d'
        self.fmtTime='%H:%M:%S'
        self.granularity=granularity
        self.names = names

    def display_time(self, seconds):
        result = []
        for name, count in TIME_INTERVALS:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')

                if self.names:
                    result.append("{} {}".format(int(value), name))
                else:
                    result.append("{}".format(int(value)))

        if self.names:
            return '\n '.join(result[:self.granularity])
        else:
            return '.'.join(result[:self.granularity])

    def label(self, value):
        return QwtText(self.display_time(seconds=value))

class DateTimeTimeScaleDraw(TimeScaleDraw):
    _logname = 'DateTimeTimeScaleDraw'
    _log = logging.getLogger(f'{_logname}')

    def label(self,value):
        # output = QwtText(datetime.timedelta(seconds=value))

        return QwtText(str(datetime.timedelta(seconds=value)))



##convert database timestamps into xaxis time for fermenting
class FermentTimeScaleDraw(TimeScaleDraw):

    _logname = 'FermentTimeScaleDraw'
    _log = logging.getLogger(f'{_logname}')


    def label(self, value):
#        self._log.debug(f"VALUE: {value}")
#        self._log.debug(f"timestamp length: {len(self.timeStamps)}")
        try:
            try:
                dt = self.timeStamps[int(value)][0]
                return QwtText(dt.strftime(self.fmtFull))
            except IndexError:
                return QwtText(self.timeStamps[-1][0].strftime(self.fmtFull))

        except IndexError:
#            self._log.debug(f"PROPER INDEX ERROR: {value}")
            return QwtText("0 Secs")

##convert database timestamps into xaxis time for fboiling and mashing
class BoilMashTimeScaleDraw(TimeScaleDraw):

    _logname = 'BoilMashTimeScaleDraw'
    _log = logging.getLogger(f'{_logname}')

    def label(self, value):
        try:
            # if value > len(self.timeStamps):
            #     return QwtText(self.timeStamps[0][0].strftime(self.fmt))
            # else:
            try:
                dt = (self.timeStamps[int(value)] - self.timeStamps[0]).total_seconds()
                return QwtText(self.display_time(dt))
            except IndexError:
#                self._log.debug(f"INDEX ERROR: {value}")
                dt = (self.timeStamps[0] - self.timeStamps[0]).total_seconds()
                return QwtText(self.display_time(dt))
        except IndexError:
#            self._log.debug(f"PROPER INDEX ERROR: {value}")
            return QwtText("0 Secs")


##Popup dialog to select what fermentation tank to send brew after boiling.
class BoilFinishedPopup(QDialog):

    _logname = 'BoilFinishedPopup'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, LOGIN, recipeData, parent=None):
        super().__init__(parent)
        self.recipeData = recipeData
        self.LOGIN = LOGIN
        label = QLabel("Send to fermentation tank:")
        self.combo = QComboBox()
        for i in range(NUMBER_OF_FERMENTATION_TANKS):
            self.combo.addItem('{}'.format(i+1))


        box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            centerButtons=True,
        )
        box.accepted.connect(self.accepted)
        box.rejected.connect(self.reject)

        self.fermLayout = QHBoxLayout()
        self.fermLayout.addWidget(label)
        self.fermLayout.addWidget(self.combo)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addStretch(10)
        self.mainLayout.addLayout(self.fermLayout)
        self.mainLayout.addWidget(box)
        self.mainLayout.addStretch(10)
        self.setWindowTitle("Select fermentation tank")
        self.selectedTank = None

    def accepted(self):
        '''
        setup Fermentation
        '''
        self.selectedTank = self.combo.currentIndex()+1
        # fermtank = SQLFermentMonitor(self.LOGIN, self.recipeData['batchID'], self.selectedTank)
        # fermtank.record(None,None,None)
        self._log.info('Batch {} sent to fermentation tank {}'.format(self.recipeData['batchID'],self.selectedTank))
        self.accept()
