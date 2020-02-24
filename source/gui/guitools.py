
from PyQt5.QtWidgets import QFrame, QComboBox, QLabel, \
    QDialog, QHBoxLayout, QVBoxLayout, QDialogButtonBox
from qwt import QwtScaleDraw, QwtText
import logging

import source.tools.exceptionLogging
from source.tools.constants import *
from source.tools.sqlBrewingComms import SQLFermentMonitor

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)



class TimeScaleDraw(QwtScaleDraw):
    _logname = 'TimeScaleDraw'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, timeStamps, *args):
        QwtScaleDraw.__init__(self, *args)
        self.timeStamps = timeStamps
        self.fmtFull='%H:%M:%S\n%Y-%m-%d'
        self.fmtTime='%H:%M:%S'

    def display_time(self, seconds, granularity=2):
        result = []
        for name, count in TIME_INTERVALS:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        return '\n '.join(result[:granularity])

class FermentTimeScaleDraw(TimeScaleDraw):

    _logname = 'FermentTimeScaleDraw'
    _log = logging.getLogger(f'{_logname}')


    def label(self, value):
        self._log.debug(f"VALUE: {value}")
        self._log.debug(f"timestamp length: {len(self.timeStamps)}")
        
        try:
            dt = self.timeStamps[int(value)][0]
            return QwtText(dt.strftime(self.fmtFull))
        except IndexError:
            return QwtText(self.timeStamps[-1][0].strftime(self.fmtFull))


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
                logging.getLogger('AxisDraw').debug(f"INDEX ERROR: {value}")
                dt = (self.timeStamps[0] - self.timeStamps[0]).total_seconds()
                return QwtText(self.display_time(dt))
        except IndexError:
            logging.getLogger('AxisDraw').debug(f"PROPER INDEX ERROR: {value}")
            return QwtText("0 Secs")


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
        SQLFermentMonitor(self.LOGIN, self.recipeData['batchID'], self.selectedTank)
        self._log.info('Batch {} sent to fermentation tank {}'.format(self.recipeData['batchID'],self.selectedTank))
        self.accept()