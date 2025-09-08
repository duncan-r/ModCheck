
'''
@summary: Various graphing dialogs

@author: Duncan R.
@organization: Ermeview Environmental Ltd
@created 5th April 2021
@copyright: Ermeview Environmental Ltd
@license: LGPL v2
'''

from datetime import datetime
import re
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import dates as mdates
from matplotlib.dates import DateFormatter
import numpy as np
import math

import pyqtgraph as pg

from ..forms import ui_graph_dialog as graph_ui
from ..forms import ui_text_dialog as text_ui


def isDark(q_color):
    r = q_color.red()
    g = q_color.green()
    b = q_color.blue()
    hsp = math.sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b))
    if (hsp > 127.5):
        return False
    else:
        return True
    
def getHighlightColor(is_dark, alpha=100):
    if is_dark:
        if alpha == False:
            return (255, 255, 255)
        else:
            return (255, 255, 255, alpha)
    else:
        if alpha == False:
            return (0, 0, 0)
        else:
            return (0, 0, 0, alpha)

def getBackColor(is_dark, alpha=100):
    if is_dark:
        if alpha == False:
            return (0, 0, 0)
        else:
            return (0, 0, 0, alpha)
    else:
        if alpha == False:
            return (255, 255, 255)
        else:
            return (255, 255, 255, alpha)
        
def rgbToHex(rgb_tuple):
    # Strip off alpha channel if found
    if len(rgb_tuple) > 3:
        no_alpha = (rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
        hex = '#%02x%02x%02x' % no_alpha
        return hex
    hex = '#%02x%02x%02x' % rgb_tuple
    return hex


def fitLevelToSectionData(x_vals, y_vals, peak_level):

    def interpolate(x1, x2, y1, y2, water_level):
            m = 1.0
            # Check for div/0
            if abs(x1 - x2) > 0.001:
                m = (y1 - y2) / (x1 - x2)
            else:
                m = (y1 - y2) / 0.001
            c = y1 - m * x1
            x = (water_level - c) / m
            return round(x, 3)

    # Need to interpolate new points between bed geometry to account for the water
    # level landed in between
    peak_x = []
    peak_y = []
    x = x_vals
    y = y_vals
    for i, level in enumerate(y):
        if i > 0:
            # Left point dry, right point wet
            if y[i-1] > peak_level and y[i] < peak_level:
                new_x = interpolate(x[i-1], x[i], y[i-1], y[i], peak_level)
                # New point
                peak_x.append(new_x)
                peak_y.append(peak_level)
                # Existing point
                peak_x.append(x[i])
                peak_y.append(peak_level)
                continue

            # Left point wet, right point dry
            elif y[i] > peak_level and y[i-1] < peak_level:
                new_x = interpolate(x[i-1], x[i], y[i-1], y[i], peak_level)
                peak_x.append(new_x)
                peak_y.append(peak_level)
                peak_x.append(x[i])
                peak_y.append(y[i])
                continue

            # Point is wet (previous point wet is implied by previous logic)
            elif y[i] <= peak_level:
                peak_x.append(x[i])
                peak_y.append(peak_level)
                continue
            
            # Both points are dry
            else:
                peak_x.append(x[i])
                peak_y.append(y[i])

        # First point in the section is either wet or dry
        else:
            peak_x.append(x[i])
            if peak_level > y[i]:
                peak_y.append(peak_level)
            else:
                peak_y.append(y[i])

    return peak_x, peak_y


class LocalHelpDialog(QDialog, text_ui.Ui_TextDialog):

    def __init__(self, title='Help'):
        QDialog.__init__(self)
        self.setupUi(self)
        self.title = title
        self.setWindowTitle(title)
        
    def showText(self, text, wrap_text=True):
        self.textEdit.setText(text)
        if not wrap_text:
            self.textEdit.setLineWrapMode(QTextEdit.NoWrap)


class ModelFileDialog(QDialog, text_ui.Ui_TextDialog):
    
    def __init__(self, title='Model File'):
        QDialog.__init__(self)
        self.setupUi(self)
        self.title = title
        self.setWindowTitle(title)
        self.textEdit.setLineWrapMode(QTextEdit.NoWrap)
        
    def showText(self, text, pattern):
        self.title = pattern
        self.setWindowTitle(self.title)
        self.textEdit.setText(text)
        pattern = re.escape(pattern)

        # Setup the desired format for matches
        text_format = QTextCharFormat()
        text_format.setBackground(QBrush(QColor("yellow")))

        # Highlight the values that are different in red
        cursor = self.textEdit.textCursor()

        # Setup the regex engine
#         pattern = "!!!"
        regex = QRegExp(pattern)

        # Process the displayed document
        pos = 0
        index = regex.indexIn(self.textEdit.toPlainText(), pos)
        while (index != -1):
            # Select the matched text and apply the desired text_format
            cursor.setPosition(index)
            cursor.movePosition(QTextCursor.EndOfLine, 1)
            cursor.mergeCharFormat(text_format)
            # Move to the next match
            pos = index + regex.matchedLength()
            index = regex.indexIn(self.textEdit.toPlainText(), pos)
            
            
class MbSummaryGraphicsView():
    """GraphicsView for displaying multiple mb/dvol series.
    """
    
    def __init__(self, graphics_view):
        self.gv = graphics_view
        self.back_color = QgsProject.instance().backgroundColor()
        self.gv.setBackground(self.back_color)
        self.is_dark = isDark(self.back_color)
        self.highlight_color = getHighlightColor(self.is_dark, alpha=False)
        self.back_color = getBackColor(self.is_dark)
        self.series_types = []
        self.results = None
        self.title = ""
        self.show_hover = True
        self.dvol_color = pg.mkColor(25, 40, 207)
        self.cme_color = pg.mkColor(217, 28, 44)
        self.dvol_color_alpha = pg.mkColor(25, 40, 207, 90)
        self.cme_color_alpha = pg.mkColor(217, 28, 44, 90)
        
    def clearPlot(self):
        try:
            self.p1.clear()
        except: pass
        try:
            self.p2.clear()
        except: pass

    def setupPlot(self, results, show_dvol):
        self.results = results
        self.show_dvol = show_dvol
        
        self.p1 = self.gv.plotItem
        self.p1.getAxis('bottom').setLabel("Time (h)", color=self.highlight_color, **{'font-size': '10pt'})
        self.p2 = pg.ViewBox()
        self.p1.showAxis('right')
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.p1)
        
        self.p1.showGrid(x=True, y=False, alpha=0.2)

        pen = pg.mkPen(color=self.highlight_color, width=1)
        self.p1.getAxis('left').setPen(pen)
        self.p1.getAxis('bottom').setPen(pen)
        self.p1.getAxis('right').setPen(pen)
        self.p1.getAxis('left').enableAutoSIPrefix(False)
        self.p1.getAxis('right').enableAutoSIPrefix(False)
        
        self.p1.setContentsMargins(5,10,5,5)
        self.p1.vb.sigResized.connect(self.updateViews)
        self.updatePlot()
        
    def updatePlot(self):
        # Get the time series with the largest range
        max_time = -1
        count = -1

        for i, r in enumerate(self.results):
            temp = max(r['data']['Time (h)'])
            if temp > max_time:
                max_time = temp
                count = i

        # Plot recommended cme boundary lines
        x = self.results[count]['data']['Time (h)']
        cme_min = [1 for i in x]
        cme_max = [-1 for i in x]
        self.p1.plot()
        self.p1.getAxis('left').setLabel("CME %", color="#d91c2c", **{'font-size': '10pt'})
        self.p1.getAxis('right').setLabel("dVol", color="#1928cf", **{'font-size': '10pt'})
        self.p1.addItem(pg.InfiniteLine(
            pos=cme_min, angle=0, name="CME min recommended", pen=({
                'color': pg.mkColor(154, 28, 158, 95), 'width': 3, 'style': Qt.DashLine,
            })
        ))
        self.p1.addItem(pg.InfiniteLine(
            pos=cme_max, angle=0, name="CME max recommended", pen=({
                'color': pg.mkColor(154, 28, 158, 95), 'width': 3, 'style': Qt.DashLine,
            })
        ))
        hl_index = -1
        for i, r in enumerate(self.results):
            if r['draw']:
                # Store index of highlight section and skip
                if r['highlight']:
                    hl_index = i
                    continue

                x = r['data']['Time (h)']
                cme = r['data']['Cum ME (%)']
                self.p1.addItem(pg.PlotDataItem(
                    x, cme, name="CME",
                    pen=({'color': self.cme_color_alpha, 'width': 1.5}), antialias=True
                ))
                if self.show_dvol:
                    dvol = r['data']['dVol']
                    self.p2.addItem(pg.PlotCurveItem(
                        x, dvol, name="dVol",
                        pen=({'color': self.dvol_color_alpha, 'width': 1.5}), antialias=True
                    ))
        
        # Draw the series to highlight last so it shows up on top
        if hl_index > -1:
            x = self.results[hl_index]['data']['Time (h)']
            cme = self.results[hl_index]['data']['Cum ME (%)']
            self.p1.addItem(pg.PlotDataItem(
                x, cme, name="CME",
                pen=({'color': self.cme_color, 'width': 2}), antialias=True
            ))
            if self.show_dvol:
                dvol = self.results[hl_index]['data']['dVol']
                self.p2.addItem(pg.PlotCurveItem(
                    x, dvol, name="dVol",
                    pen=({'color': self.dvol_color, 'width': 2}), antialias=True
                ))

    def updateViews(self):
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)
    
    def drawPlot(self, results, show_dvol):
        self.clearPlot()
        if not self.results:
            self.setupPlot(results, show_dvol)
        else:
            self.results = results
            self.show_dvol = show_dvol
            self.clearPlot()
            self.updatePlot()
        

class MbCheckIndividualGraphicsView():
    
    def __init__(self, graphics_view):
        self.gv = graphics_view
        self.back_color = QgsProject.instance().backgroundColor()
        self.gv.setBackground(self.back_color)
        self.is_dark = isDark(self.back_color)
        self.highlight_color = getHighlightColor(self.is_dark, alpha=False)
        self.back_color = getBackColor(self.is_dark)
        self.series_types = []
        self.results = None
        self.title = ""
        self.show_hover = True
        
    def _mouseMoved(self, evt):
        if not self.show_hover:
            self.display_text.hide()
            return
        
        pos = evt
        if self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.p1.vb.mapSceneToView(pos)
            mousePoint2 = self.p2.mapSceneToView(pos)
            index = int(mousePoint.x())
            series_1 = self.results[self.series_types[0]]
            series_2 = self.results[self.series_types[1]]
            if index >= 0 and index < len(series_1):
                self.display_text.setText(
                    "Time = {x:.3f}\n{y1name} = {y1:.3f}\n{y2name} = {y2:.3f}".format(
                        x=mousePoint.x(), 
                        y1name=self.series_types[0], y1=mousePoint.y(),
                        y2name=self.series_types[1], y2=mousePoint2.y()
                    )
                )
                self.display_text.setPos(mousePoint.x(), mousePoint.y())
                self.display_text.show()
            else:
                self.display_text.hide()
        
    def setupPlot(self, graph_series, results, title):
        self.series_types = graph_series
        self.results = results
        self.title = title
        highlight_hex = rgbToHex(self.highlight_color)
        
        series_1 = self.series_types[0]
        series_2 = self.series_types[1]
        
        self.p1 = self.gv.plotItem
        # self.p1.setDefaultPadding(0.1)
        self.p1.getAxis('bottom').setLabel("Time (h)", color=highlight_hex, **{'font-size': '10pt'})
        self.p2 = pg.ViewBox()
        self.p1.showAxis('right')
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.p1)
        
        self.p1.showGrid(x=True, y=False, alpha=0.2)

        pen = pg.mkPen(color=(0,0,0), width=1)
        self.p1.getAxis('left').setPen(pen)
        self.p1.getAxis('bottom').setPen(pen)
        self.p1.getAxis('right').setPen(pen)
        self.p1.getAxis('left').enableAutoSIPrefix(False)
        self.p1.getAxis('right').enableAutoSIPrefix(False)
        
        self.p1.setContentsMargins(5,10,5,5)
        self.p1.vb.sigResized.connect(self.updateViews)
        self.p1.scene().sigMouseMoved.connect(self._mouseMoved)
        self.updatePlot()
        
    def updatePlot(self):
        series_1 = self.series_types[0]
        series_2 = self.series_types[1]

        self.p1.getAxis('left').setLabel(series_1, color='blue', **{'font-size': '10pt'})
        self.p1.getAxis('right').setLabel(series_2, color='red', **{'font-size': '10pt'})
        self.p1.plot(
            self.results['Time (h)'], self.results[series_1],
            pen=({'color': "b", 'width': 1.5}), antialias=True
        )
        self.p2.addItem(pg.PlotCurveItem(
            self.results['Time (h)'], self.results[series_2], 
            pen=({'color': "r", 'width': 1.5}), antialias=True, hoverable=True
        ))
        self.display_text = pg.TextItem(
            text="", color=self.highlight_color, anchor=(0,1), fill=self.back_color, border=self.highlight_color
        )
        self.display_text.hide()
        self.gv.addItem(self.display_text)
        self.p1.vb.autoRange()
        self.updateViews()
        
    def updateViews(self):
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)
    
    def drawPlot(self, graph_series, results, title=""):
        if not self.series_types or not self.results:
            self.setupPlot(graph_series, results, title)
        else:
            self.series_types = graph_series
            self.results = results
            self.title = title
            self.p1.clear()
            self.p2.clear()
            self.updatePlot()
            

class HpcCheckIndividualGraphicsView():
            
    def __init__(self, graphics_view):
        self.gv = graphics_view
        self.back_color = QgsProject.instance().backgroundColor()
        self.gv.setBackground(self.back_color)
        self.is_dark = isDark(self.back_color)
        self.highlight_color = getHighlightColor(self.is_dark, alpha=False)
        self.back_color = getBackColor(self.is_dark)
        self.series_types = []
        self.results = np.empty(1)
        self.title = ""
        self.show_hover = True
        
    def _mouseMoved(self, evt):
        if not self.show_hover:
            self.display_text.hide()
            return
        
        pos = evt
        if self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.p1.vb.mapSceneToView(pos)
            index = int(mousePoint.x())
            series_1 = self.results[self.series_types[0]]
            if index >= 0 and index < len(series_1):
                self.display_text.setText(
                    "Time = {x:.3f}\n{y1name} = {y1:.3f}".format(
                        x=mousePoint.x(), y1name=self.series_types[1], y1=mousePoint.y()
                    )
                )
                self.display_text.setPos(mousePoint.x(), mousePoint.y())
                self.display_text.show()
            else:
                self.display_text.hide()
        
    def setupPlot(self, series_meta, results, title):
        self.series_types = series_meta
        self.results = results
        self.title = title
        highlight = rgbToHex(self.highlight_color)
        
        series_1 = self.series_types[0]
        self.p1 = self.gv.plotItem
        self.p1.setDefaultPadding(0.1)
        self.p1.getAxis('bottom').setLabel("Time (h)", color=highlight, **{'font-size': '10pt'})
        # self.p1.getAxis('bottom').setLabel("Time (h)", **{'font-size': '12pt', 'color': highlight})
        self.p1.showGrid(x=True, y=False, alpha=0.2)
        
        pen = pg.mkPen(color=self.highlight_color, width=1)
        self.p1.getAxis('left').setPen(pen)
        self.p1.getAxis('bottom').setPen(pen)
        self.p1.getAxis('left').enableAutoSIPrefix(False)
        
        self.p1.setContentsMargins(5,10,5,5)
        self.p1.vb.sigResized.connect(self.updateViews)
        self.p1.scene().sigMouseMoved.connect(self._mouseMoved)
        self.updatePlot()
        
    def updatePlot(self):
        self.p1.clear()
        highlight = rgbToHex(self.highlight_color)
        series_1 = self.series_types[0]
        series_1_name = self.series_types[1]


        tol_max = None
        if series_1_name in ['Nc', 'Nu', 'Nd']:
            if series_1_name == 'Nc' or series_1_name == 'Nu':
                tol_max = 1.0
            else:
                tol_max = 0.3

        self.p1.plot(
            self.results[:,1], self.results[:,series_1],
            pen=({'color': "b", 'width': 1}), antialias=True
        )

        self.p1.getAxis('left').setLabel(series_1_name, color=highlight, **{'font-size': '10pt'})
        # self.p1.getAxis('left').setLabel(series_1_name, **{'font-size': '12pt', 'color': highlight})
        if tol_max:
            self.p1.addItem(pg.InfiniteLine(
                pos=tol_max, angle=0, name="Max recommended", pen=({
                    'color': pg.mkColor(154, 28, 158, 95), 'width': 3, 'style': Qt.DashLine,
                })
            ))
        self.display_text = pg.TextItem(
            text="", color=self.highlight_color, anchor=(0,1), fill=self.back_color, border=self.highlight_color
        )
        self.display_text.hide()
        self.gv.addItem(self.display_text)
        self.p1.vb.autoRange()
        # self.updateViews()
        
    def updateViews(self):
        pass
    
    def drawPlot(self, series_meta, results, title=""):
        do_setup = False
        if not series_meta: do_setup = True
        elif results.any(): do_setup = True
        
        if do_setup:
            self.setupPlot(series_meta, results, title)
        else:
            self.series_types = series_meta
            self.results = results
            self.title = title
            self.updatePlot()

        
class FmpStabilityGeometryGraphicsView():
    """GraphicsView to display the flow/stage for the Fmp stability check.
    """
    
    def __init__(self, graphics_view):
        self.gv = graphics_view
        self.back_color = QgsProject.instance().backgroundColor()
        self.gv.setBackground(self.back_color)
        self.is_dark = isDark(self.back_color)
        self.highlight_color = getHighlightColor(self.is_dark)
        self.back_color = getBackColor(self.is_dark)
        self.show_hover = True
        self.node_name = ""
        self.geom_data = None
        self.stage = 0
        self.title = ""
        self.p1 = None

    def _mouseMoved(self, evt):
        if not self.show_hover:
            self.display_text.hide()
            return
        
        pos = evt
        if self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.p1.vb.mapSceneToView(pos)
            index = int(mousePoint.x())
            series_1 = self.geom_data[0]
            if index >= 0 and index < len(series_1):
                self.display_text.setText(
                    "X = {x:.3f}\n{y1name} = {y1:.3f}\n{y2name} = {y2:.3f}".format(
                        x=mousePoint.x(),
                        y1name="Y", y1=mousePoint.y(),
                        y2name="WL", y2=self.stage,
                    )
                )
                self.display_text.setPos(mousePoint.x(), mousePoint.y())
                self.display_text.show()
            else:
                self.display_text.hide()
        
    def clearPlot(self, redraw=True):
        try:
            self.p1.clear()
        except: pass

    def setupPlot(self, geom_data, node_name, stage):
        self.geom_data = geom_data
        self.node_name = node_name
        self.stage = stage
        
        self.p1 = self.gv.plotItem
        self.p1.setDefaultPadding(0.1)
        self.p1.getAxis('bottom').setLabel("X (m)", color=self.highlight_color, **{'font-size': '10pt'})
        self.p1.showGrid(x=True, y=True, alpha=0.1)
        self.p1.setContentsMargins(5,10,5,5)

        pen = pg.mkPen(color=self.highlight_color, width=1)
        self.p1.getAxis('left').setPen(pen)
        self.p1.getAxis('bottom').setPen(pen)
        self.p1.getAxis('left').enableAutoSIPrefix(False)
        self.p1.getAxis('left').setLabel("Level (mAOD)", color=self.highlight_color, **{'font-size': '10pt'})
        self.p1.scene().sigMouseMoved.connect(self._mouseMoved)
        self.updatePlot()
        
    def updatePlot(self):
        """
        """
        def interpolate(x1, x2, y1, y2, water_level):
            m = 1.0
            # Check for div/0
            if abs(x1 - x2) > 0.001:
                m = (y1 - y2) / (x1 - x2)
            else:
                m = (y1 - y2) / 0.001
            c = y1 - m * x1
            x = (water_level - c) / m
            return round(x, 3)

        self.p1.clear()

        # Need to interpolate new points between bed geometry to account for the water
        # level landed in between
        water_x = []
        water_y = []
        x = self.geom_data[0]
        y = self.geom_data[1]
        for i, level in enumerate(y):
            if i > 0:
                # Left point dry, right point wet
                if y[i-1] > self.stage and y[i] < self.stage:
                    new_x = interpolate(x[i-1], x[i], y[i-1], y[i], self.stage)
                    # New point
                    water_x.append(new_x)
                    water_y.append(self.stage)
                    # Existing point
                    water_x.append(x[i])
                    water_y.append(self.stage)
                    continue

                # Left point wet, right point dry
                elif y[i] > self.stage and y[i-1] < self.stage:
                    new_x = interpolate(x[i-1], x[i], y[i-1], y[i], self.stage)
                    water_x.append(new_x)
                    water_y.append(self.stage)
                    water_x.append(x[i])
                    water_y.append(y[i])
                    continue

                # Point is wet (previous point wet is implied by previous logic)
                elif y[i] <= self.stage:
                    water_x.append(x[i])
                    water_y.append(self.stage)
                    continue
                
                # Both points are dry
                else:
                    water_x.append(x[i])
                    water_y.append(y[i])

            # First point in the section is either wet or dry
            else:
                water_x.append(x[i])
                if self.stage > y[i]:
                    water_y.append(self.stage)
                else:
                    water_y.append(y[i])

        bed = pg.PlotCurveItem(
            self.geom_data[0], self.geom_data[1],
            pen=({'color': "k", 'width': 1.5}), antialias=True
        )
        water = pg.PlotCurveItem(
            water_x, water_y,
            pen=({'color': "b", 'width': 1.5}), antialias=True
        )
        self.p1.plot()
        self.p1.addItem(water)
        self.p1.addItem(bed)
        self.p1.addItem(pg.FillBetweenItem(
            bed, water, brush=pg.mkBrush(color=(33, 33, 255, 60)),
        ))
        self.display_text = pg.TextItem(
            text="", color=self.highlight_color, anchor=(0,1), fill=self.back_color,
            border=self.highlight_color
        )
        self.display_text.hide()
        self.gv.addItem(self.display_text)
        self.p1.vb.autoRange()
        
    def drawPlot(self, geom_data, node_name, stage):
        if not self.geom_data:
            self.setupPlot(geom_data, node_name, stage)
        else:
            self.geom_data = geom_data
            self.node_name = node_name
            self.stage = stage
            self.updatePlot()


class FmpStabilityGraphicsView():
    """GraphicsView to display the flow/stage for the Fmp stability check.
    """
    
    def __init__(self, graphics_view):
        self.gv = graphics_view
        self.back_color = QgsProject.instance().backgroundColor()
        self.gv.setBackground(self.back_color)
        self.is_dark = isDark(self.back_color)
        self.highlight_color = getHighlightColor(self.is_dark)
        self.back_color = getBackColor(self.is_dark)
        self.show_hover = True
        self.series_type = ""
        self.node_name = ""
        self.time_data = []
        self.results = None
        self.title = ""
 
    def _mouseMoved(self, evt):
        if not self.show_hover:
            self.display_text.hide()
            return
        
        pos = evt
        if self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.p1.vb.mapSceneToView(pos)
            mousePoint2 = self.p2.mapSceneToView(pos)
            index = int(mousePoint.x())

            series_1 = None
            series_1_name = ''
            series_2_name = ''
            if self.series_type == 'Stage':
                series_1 = self.results['stage'][0].to_numpy()
                series_1_name = "Stage"
                series_2_name = "Flow"
            else:
                series_1 = self.results['flow'][0].to_numpy()
                series_1_name = "Flow"
                series_2_name = "Stage"

            if index >= 0 and index < len(series_1):
                self.display_text.setText(
                    "Time = {x:.3f}\n{y1name} = {y1:.3f}\n{y2name} = {y2:.3f}".format(
                        x=mousePoint.x(),
                        y1name=series_1_name, y1=mousePoint.y(),
                        y2name=series_2_name, y2=mousePoint2.y(),
                    )
                )
                self.display_text.setPos(mousePoint.x(), mousePoint.y())
                self.display_text.show()
            else:
                self.display_text.hide()

    def clearPlot(self, redraw=True):
        try:
            self.p2.clear()
        except: pass
        try:
            self.p1.clear()
        except: pass
        
    def setupPlot(self, time_data, results, derivs, timestep, series_type, 
                 node_name, show_derivs=False):
        self.series_type = series_type
        self.node_name = node_name
        self.timestep = timestep
        self.time_data = time_data
        self.results = results
        self.derivs = derivs
        
        self.p1 = self.gv.plotItem
        self.p1.setDefaultPadding(0.1)
        self.p1.getAxis('bottom').setLabel("Time (h)", color=self.highlight_color, **{'font-size': '10pt'})
        self.p2 = pg.ViewBox()
        self.p1.showAxis('right')
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.p1)
        
        self.p1.showGrid(x=True, y=False, alpha=0.1)

        pen = pg.mkPen(color=self.highlight_color, width=1)
        self.p1.getAxis('left').setPen(pen)
        self.p1.getAxis('bottom').setPen(pen)
        self.p1.getAxis('right').setPen(pen)
        self.p1.getAxis('left').enableAutoSIPrefix(False)
        self.p1.getAxis('right').enableAutoSIPrefix(False)
        
        self.p1.setContentsMargins(5,10,5,5)
        self.p1.vb.sigResized.connect(self.updateViews)
        self.p1.scene().sigMouseMoved.connect(self._mouseMoved)
        self.updatePlot()

    def updatePlot(self):
        self.p1.clear()
        self.p2.clear()
        
        stage_series = self.results['stage'][0].to_numpy()
        flow_series = self.results['flow'][0].to_numpy()
        stage_ds_series = None
        if len(self.results['stage']) > 1:
            stage_ds_series = self.results['stage'][1].to_numpy()
        
        fail_times = ''
        if self.derivs['status'] == 'Failed':
            fail_times = '(First fail: {:.3f} - Last Fail: {:.3f})'.format(self.derivs['fail_times'][0], self.derivs['fail_times'][-1])
        status_text = '{} {}'.format(self.node_name, fail_times) #'Dy2 Fail = {}   :   {}'.format(derivs['status'], fail_times)
        self.title = status_text

        if stage_ds_series is not None:
            self.p1.addLegend()

        # Set the primary series based on whether we're checking stage or flow
        # TODO: refactor to avoid duplicate code
        if self.series_type == 'Stage':
            self.p1.getAxis('left').setLabel('Stage', color='blue', **{'font-size': '10pt'})
            self.p1.getAxis('right').setLabel('Flow', color='red', **{'font-size': '10pt'})
            self.p1.plot(
                self.time_data, stage_series,
                pen=({'color': "b", 'width': 1.5}), antialias=True, title=self.title
            )
            self.p2.addItem(pg.PlotCurveItem(
                self.time_data, flow_series,
                pen=({'color': "r", 'width': 1.5}), antialias=True, hoverable=True
            ))
            if stage_ds_series is not None:
                self.p1.addItem(pg.PlotCurveItem(
                    self.time_data, stage_ds_series,
                    pen=({'color': "g", 'width': 1.5}), antialias=True
                ))
        else:
            self.p1.getAxis('left').setLabel('Flow', color='red', **{'font-size': '10pt'})
            self.p1.getAxis('right').setLabel('Stage', color='blue', **{'font-size': '10pt'})
            self.p1.plot(
                self.time_data, flow_series,
                pen=({'color': "b", 'width': 1.5}), antialias=True, title=self.title
            )
            self.p2.addItem(pg.PlotCurveItem(
                self.time_data, stage_series,
                pen=({'color': "r", 'width': 1.5}), antialias=True, hoverable=True
            ))
            if stage_ds_series is not None:
                self.p2.addItem(pg.PlotCurveItem(
                    self.time_data, stage_ds_series,
                    pen=({'color': "g", 'width': 1.5}), antialias=True
                ))

        self.p1.addItem(pg.InfiniteLine(
            pos=self.timestep, angle=90, pen=({
                'color': getHighlightColor(self.is_dark, alpha=70),
                'width': 2, 'style': Qt.DashLine
            })
        ))
        self.display_text = pg.TextItem(
            # text="", color=text_color, anchor=(1,0), fill=self.back_color, border=pg.mkColor(0,0,0,100)
            text="", color=self.highlight_color, anchor=(1,0), fill=self.back_color, border=self.highlight_color
        )
        self.gv.addItem(self.display_text)
        self.display_text.hide()
        self.p1.vb.autoRange()
        self.updateViews()
        
    def updateViews(self):
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)

    def drawPlot(
            self, time_data, results, derivs, timestep, series_type, 
            node_name, show_derivs=False
        ):
        if not self.series_type or not self.results:
            self.setupPlot(
                time_data, results, derivs, timestep, series_type,  node_name,
                show_derivs=show_derivs
            )
        else:
            self.series_type = series_type
            self.node_name = node_name
            self.timestep = timestep
            self.time_data = time_data
            self.results = results
            self.derivs = derivs
            self.updatePlot()


class SectionPropertiesGraphicsView():
    """GraphicsView to display section properties graphs.
    
    Contains methods for drawing conveyance and banktop issues.
    """
    
    def __init__(self, graphics_view):
        self.gv = graphics_view
        self.back_color = QgsProject.instance().backgroundColor()
        self.gv.setBackground(self.back_color)
        self.is_dark = isDark(self.back_color)
        self.highlight_color = getHighlightColor(self.is_dark, alpha=False)
        self.highlight_color_alpha = getHighlightColor(self.is_dark, alpha=100)
        self.back_color = getBackColor(self.is_dark)
        self.title = ""
        self.show_hover = True
        
        self.cur_plot_type = ''
        self.section = None
        self.section_id = ''
        
    def _mouseMoved(self, evt):
        if not self.show_hover:
            self.display_text.hide()
            return
        
        pos = evt
        if self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.p1.vb.mapSceneToView(pos)
            index = int(mousePoint.x())
            series_1 = self.section.xs_x.to_numpy()

            if self.cur_plot_type == 'conveyance':
                if index >= 0 and (index < len(series_1) or index < len(self.section.active_k['x'])):
                    mousePoint2 = self.p2.mapSceneToView(pos)
                    self.display_text.setText(
                        "X = {x:.3f}\n{y1name} = {y1:.3f}\n{x2name} = {x2:.3f}".format(
                            x=mousePoint.x(),
                            y1name="Elevation", y1=mousePoint.y(),
                            x2name="Conveyance", x2=mousePoint2.x(),
                        )
                    )
                    self.display_text.setPos(mousePoint.x(), mousePoint.y())
                    self.display_text.show()
                else:
                    self.display_text.hide()
            else:
                if index >= 0 and index < len(series_1):
                    self.display_text.setText(
                        "X = {x:.3f}\n{y1name} = {y1:.3f}\n".format(
                            x=mousePoint.x(), y1name="Elevation", y1=mousePoint.y(),
                        )
                    )
                    self.display_text.setPos(mousePoint.x(), mousePoint.y())
                    self.display_text.show()
                else:
                    self.display_text.hide()
        
    def clearPlot(self):
        try:
            self.p2.clear()
        except: pass
        try:
            self.p1.clear()
        except: pass
        self.gv.clear()

    def setupConveyancePlot(self, section, section_id):
        self.clearPlot()
        self.section = section
        self.section_id = section_id
        highlight = rgbToHex(self.highlight_color)
        
        self.p1 = self.gv.plotItem
        self.p1.setDefaultPadding(0.1)
        self.p1.getAxis('bottom').setLabel("X (m)", color=highlight, **{'font-size': '10pt'})
        self.p2 = pg.ViewBox()
        self.p1.showAxis('top')
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis('top').linkToView(self.p2)
        self.p2.setYLink(self.p1)
        self.p1.showGrid(x=False, y=True, alpha=0.2)
        
        pen = pg.mkPen(color=self.highlight_color, width=1)
        self.p1.getAxis('left').setPen(pen)
        self.p1.getAxis('bottom').setPen(pen)
        self.p1.getAxis('top').setPen(pen)
        self.p1.getAxis('left').enableAutoSIPrefix(False)
        self.p1.getAxis('top').enableAutoSIPrefix(False)
        
        self.p1.setContentsMargins(5,10,5,5)
        self.p1.vb.sigResized.connect(self.updateConveyanceViews)
        self.p1.scene().sigMouseMoved.connect(self._mouseMoved)
        
        highlight = rgbToHex(self.highlight_color)

        self.p1.plot()
        for panel in self.section.panels:
            self.p1.addItem(pg.InfiniteLine(
                pos=panel['x'], angle=90, pen=({
                    'color': 'b', 'width': 1.2, 'style': Qt.DashLine
                })
            ))
            
        self.p1.addItem(pg.PlotDataItem(
            self.section.xs_x.values, self.section.xs_y.values, name='Section',
            pen=({'color': self.highlight_color_alpha, 'width': 1.2, 'style': Qt.DashLine}), antialias=True
        ))
        self.p1.addItem(pg.PlotDataItem(
            self.section.xs_active_x.values, self.section.xs_active_y.values, name='Active section',
            pen=({'color': self.highlight_color, 'width': 1.5}), antialias=True
        ))
        
        self.p2.addItem(pg.PlotDataItem(
            self.section.active_k['x'], self.section.active_k['y'], name='Conveyance',
            pen=({'color': "r", 'width': 1.5}), antialias=True
        ))

        self.p1.getAxis('left').setLabel("Elevation (mAOD)", color=highlight, **{'font-size': '10pt'})
        self.p1.getAxis('top').setLabel('Conveyance', color=highlight, **{'font-size': '10pt'})
        self.display_text = pg.TextItem(
            text="", color=self.highlight_color, anchor=(1,0), fill=self.back_color, border=self.highlight_color
        )
        self.gv.addItem(self.display_text)
        self.display_text.hide()
        self.p1.vb.autoRange()
        self.updateConveyanceViews()

    def updateConveyanceViews(self):
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p2.linkedViewChanged(self.p1.vb, self.p2.YAxis)

    def drawConveyancePlot(self, section, section_id):
        self.cur_plot_type = 'conveyance'
        self.setupConveyancePlot(section, section_id)

    def setupBanksPlot(self, section, section_id):
        self.clearPlot()
        self.section = section
        self.section_id = section_id
        highlight = rgbToHex(self.highlight_color)
        
        self.p1 = self.gv.plotItem
        self.p1.setDefaultPadding(0.1)
        self.p1.getAxis('bottom').setLabel("X (m)", color=highlight, **{'font-size': '10pt'})
        self.p1.showGrid(x=True, y=True, alpha=0.2)
        
        pen = pg.mkPen(color=self.highlight_color, width=1)
        self.p1.getAxis('left').setPen(pen)
        self.p1.getAxis('bottom').setPen(pen)
        self.p1.getAxis('left').enableAutoSIPrefix(False)
        self.p1.hideAxis('top')
        
        self.p1.setContentsMargins(5,10,5,5)
        self.p1.scene().sigMouseMoved.connect(self._mouseMoved)

        self.p1.plot()
        self.p1.addItem(pg.PlotDataItem(
            self.section.xs_x.values, self.section.xs_y.values, name='Section',
            pen=({'color': self.highlight_color_alpha, 'width': 1.2, 'style': Qt.DashLine}), antialias=True
        ))
        active_bed = pg.PlotDataItem(
            self.section.xs_active_x.values, self.section.xs_active_y.values, name='Active section',
            pen=({'color': self.highlight_color, 'width': 1.5}), antialias=True
        )
        self.p1.addItem(active_bed)

        if self.section.bad_banks['fail_left'] and self.section.bad_banks['drop_left'] > 0:
            bad_x = self.section.xs_x[self.section.bad_banks['xs_start']:(self.section.bad_banks['max_left_idx']+1)].values
            bad_y = self.section.xs_y[self.section.bad_banks['xs_start']:(self.section.bad_banks['max_left_idx']+1)].values
            lb_x, lb_y = fitLevelToSectionData(
                bad_x, bad_y, self.section.bad_banks['max_left']
            )
            bad_left = pg.PlotDataItem(
                lb_x, lb_y, name='Bad banks',
                pen=({'color': "r", 'width': 1.2}), antialias=True
            )
            bed_left = pg.PlotDataItem(
                bad_x, bad_y, 
                pen=({'color': self.highlight_color, 'width': 0.5}), antialias=True
            )
            self.p1.addItem(bad_left)
            self.p1.addItem(pg.FillBetweenItem(
                bed_left, bad_left, brush=pg.mkBrush(color=(176, 11, 46, 60)),
            ))

        if self.section.bad_banks['fail_right'] and self.section.bad_banks['drop_right'] > 0:
            bad_x = self.section.xs_x[self.section.bad_banks['max_right_idx']:self.section.bad_banks['xs_end']+1].values
            bad_y = self.section.xs_y[self.section.bad_banks['max_right_idx']:self.section.bad_banks['xs_end']+1].values
            rb_x, rb_y = fitLevelToSectionData(
                bad_x, bad_y, self.section.bad_banks['max_right']
            )
            # rb_y_new = [y if y > self.section.bad_banks['max_right'] else self.section.bad_banks['max_right'] for y in rb_y]

            bad_right = pg.PlotDataItem(
                rb_x, rb_y, name='Bad banks',
                pen=({'color': "r", 'width': 1.2}), antialias=True
            )
            bed_right = pg.PlotDataItem(
                bad_x, bad_y,
                pen=({'color': self.highlight_color_alpha, 'width': 0.5}), antialias=True
            )
            self.p1.addItem(bad_right)
            self.p1.addItem(pg.FillBetweenItem(
                bed_right, bad_right, brush=pg.mkBrush(color=(176, 11, 46, 60)),
            ))
            
            
            # rb_x = self.section.xs_x[self.section.bad_banks['max_right_idx']:self.section.bad_banks['xs_end']+1]
            # rb_y = self.section.xs_y[self.section.bad_banks['max_right_idx']:self.section.bad_banks['xs_end']+1]
            # rb_y_new = [y if y > self.section.bad_banks['max_right'] else self.section.bad_banks['max_right'] for y in rb_y]
            #
            # bad_right = pg.PlotDataItem(
            #     rb_x.values, rb_y_new, name='Bad banks',
            #     pen=({'color': "r", 'width': 1.2}), antialias=True
            # )
            # bed_right = pg.PlotDataItem(
            #     rb_x.values, rb_y.values, 
            #     pen=({'color': self.highlight_color_alpha, 'width': 0.5}), antialias=True
            # )
            # self.p1.addItem(bad_right)
            # self.p1.addItem(pg.FillBetweenItem(
            #     bed_right, bad_right, brush=pg.mkBrush(color=(176, 11, 46, 60)),
            # ))
        self.display_text = pg.TextItem(
            text="", color=self.highlight_color, anchor=(1,0), fill=self.back_color, border=self.highlight_color
        )
        self.gv.addItem(self.display_text)
        self.display_text.hide()
        self.p1.vb.autoRange()

    def drawBanktopsPlot(self, section, section_id):
        self.cur_plot_type = 'banks'
        self.setupBanksPlot(section, section_id)


class AmaxGraphDialog(QDialog, graph_ui.Ui_GraphDialog):
    
    def __init__(self, title="AMAX"):
        QDialog.__init__(self)
        self.setupUi(self)
        self.title = title
        self.setWindowTitle(title)

    def setupGraph(self, series, station):
        try:
            self.setWindowTitle('{} - {} {}'.format(self.title, station['id']))
        except: pass
        
        flow = []
        years = []
        for s in series:
            flow.append(s['flow'])
            years.append(int(s['datetime'][:4]))
            
        scene = QGraphicsScene()
        view = self.graphGraphicsView.setScene(scene)
        fig = Figure()
        axes = fig.gca()
        
        axes.bar(years, flow)
#         axes.xaxis.set_major_formatter(DateFormatter("%Y"))
#         axes.xaxis.set_major_locator(mdates.YearLocator(5, month=1, day=1))
        axes.set(
            xlabel="Year",
            ylabel="Flow (m3/s)",
            title="AMAX Flow Data at ({0}) {1}".format(station['id'], station['name'])
        )
        canvas = FigureCanvas(fig)
        proxy_widget = scene.addWidget(canvas)


class PotGraphDialog(QDialog, graph_ui.Ui_GraphDialog):
    
    def __init__(self, title="POT"):
        QDialog.__init__(self)
        self.setupUi(self)
        self.title = title
        self.setWindowTitle(title)

    def setupGraph(self, series, station):
        try:
            self.setWindowTitle('{} - {} {}'.format(self.title, station['id']))
        except: pass
        
        flow = []
        years = []
        for s in series:
            flow.append(s['flow'])
            years.append(int(s['datetime'][:4]))
            
        scene = QGraphicsScene()
        view = self.graphGraphicsView.setScene(scene)
        fig = Figure()
        axes = fig.gca()
        
        axes.scatter(years, flow, marker='x', s=3, alpha=0.7)
#         axes.xaxis.set_major_formatter(DateFormatter("%Y"))
#         axes.xaxis.set_major_locator(mdates.YearLocator(5, month=1, day=1))
        axes.set(
            xlabel="Year",
            ylabel="Flow (m3/s)",
            title="POT Flow Data at ({0}) {1}".format(station['id'], station['name'])
        )
        canvas = FigureCanvas(fig)
        proxy_widget = scene.addWidget(canvas)
        
        
class DailyFlowsGraphDialog(QDialog, graph_ui.Ui_GraphDialog):
    
    def __init__(self, title="Daily Flows"):
        QDialog.__init__(self)
        self.setupUi(self)
        self.title = title
        self.setWindowTitle(title)

    def setupGraph(self, series, station, year):
        try:
            self.setWindowTitle('{0} {1} - {2}'.format(self.title, year, station['id']))
        except: pass
        
        flow = []
        dates = []
        for s in series:
            flow.append(s['flow'])
            date = datetime.strptime(s['date'], '%Y-%m-%d').date()
            dates.append(date)
            
        scene = QGraphicsScene()
        view = self.graphGraphicsView.setScene(scene)
        fig = Figure()
        axes = fig.gca()
        
        plot = axes.plot(dates, flow, "-b", label="Flow")
        axes.xaxis.set_major_formatter(DateFormatter("%m-%d"))
#         axes.xaxis.set_major_locator(mdates.YearLocator(5, month=1, day=1))
        axes.set(
            xlabel="Date",
            ylabel="Flow (m3/s)",
            title="{0} Daily Flow Data: ({1}) {2}".format(year, station['id'], station['name'])
        )
        canvas = FigureCanvas(fig)
        proxy_widget = scene.addWidget(canvas)

