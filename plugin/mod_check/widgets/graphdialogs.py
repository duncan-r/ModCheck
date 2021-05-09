
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

from ..forms import ui_graph_dialog as graph_ui
from ..forms import ui_text_dialog as text_ui


class LocalHelpDialog(QDialog, text_ui.Ui_TextDialog):

    def __init__(self, title='Help'):
        QDialog.__init__(self)
        self.setupUi(self)
        self.title = title
        self.setWindowTitle(title)
        
    def showText(self, text):
        self.textEdit.setText(text)


class ModelFileDialog(QDialog, text_ui.Ui_TextDialog):
    
    def __init__(self, title='Model File'):
        QDialog.__init__(self)
        self.setupUi(self)
        self.title = title
        self.setWindowTitle(title)
        
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
            
            
class MbCheckIndividualGraphicsView(QGraphicsView):
    """GraphicsView to display the Individual MB Check tab graphs.
    """
    
    def __init__(self):
        QGraphicsView.__init__(self)

        scene = QGraphicsScene()
        self.setScene(scene)
        self.fig = Figure()
        self.axes = self.fig.gca()
        self.axes2 = self.axes.twinx()
        self.fig.tight_layout()
        self.canvas = FigureCanvas(self.fig)
        proxy_widget = scene.addWidget(self.canvas)
        
    def drawPlot(self, graph_series, results, title):
        plot_colors = ['-b', '-g', '-r', '-c', '-m', '-y', '-k',]
        color_count = 0
        labels = []
        plot_lines = []
        self.axes2.clear()
        self.axes.clear()
        self.fig.clear()
        self.axes = self.fig.gca()
        self.axes2 = self.axes.twinx()
    
        x = results['Time (h)']
        self.axes.set_xlabel('Time (h)')
        self.axes.set_title(title)

        for gs in graph_series[0]:
            s = results[gs]
            left_plot = self.axes.plot(x, s, plot_colors[color_count], label=gs)
            pl = [p for p in left_plot]
            plot_lines += pl
            labels += ['(L) ' + l.get_label() for l in pl]
            color_count += 1
            if color_count > len(plot_colors):
                color_count = 0
            
        if graph_series[1]:
            for gs in graph_series[1]:
                s = results[gs]
                right_plot = self.axes2.plot(x, s, plot_colors[color_count], label=gs)
                pl = [p for p in right_plot]
                plot_lines += pl
                labels += ['(R) ' + l.get_label() for l in pl]
                color_count += 1
                if color_count > len(plot_colors):
                    color_count = 0

        self.axes.legend(plot_lines, labels, loc='upper right')
        self.fig.tight_layout()
        self.canvas.draw()
        
        
class SectionPropertiesGraphicsView(QGraphicsView):
    """GraphicsView to display section properties graphs.
    
    Contains methods for drawing conveyance and banktop issues.
    """
    
    def __init__(self):
        QGraphicsView.__init__(self)
        scene = QGraphicsScene()
        self.setScene(scene)
        self.fig = Figure()
        self.axes = self.fig.gca()
        self.axes2 = self.axes.twinx()
        self.fig.tight_layout()
        self.canvas = FigureCanvas(self.fig)
        proxy_widget = scene.addWidget(self.canvas)
        
    def drawConveyancePlot(self, section_data, section_id):
        """Plot the conveyance and cross section data provided.
        
        Args:
            section_data(dict): containing lists of the 'xvals', 'yvals',
            'panels' and 'conveyance' data to be drawn on the graph.
            section_id(str): the node id for this section.
        """
        self.axes2.clear()
        self.axes.clear()
        self.fig.clear()
        self.axes = self.fig.gca()
        self.axes2 = self.axes.twinx()
        
        minx = section_data['xvals'][0]
        maxx = section_data['xvals'][-1]
        miny = min(section_data['yvals'])
        maxy = max(section_data['yvals'])
        
        x = section_data['xvals']
        y = section_data['yvals']
        
        self.axes.set(
            ylabel='Elevation (mAOD)',
            xlabel='Chainage (m)',
            title="Node Name: {0}".format(section_id)
        )

        xs_plot = self.axes.plot(x, y, "-k", label="Cross Section")
        p_plot = None

        panel_count = 0
        for i, panel in enumerate(section_data['panels']):
            if panel:
                panel_count += 1
                panel_label = 'Panel {}'.format(panel_count)
                panelx = [section_data['xvals'][i], section_data['xvals'][i]]
                panely = [miny, maxy]
                p_plot = self.axes.plot(panelx, panely, "-b", label=panel_label)
        
        cx = []
        cy = []
        for c in section_data['conveyance']:
            cx.append(c[0])
            cy.append(c[1])
        self.axes2 = self.axes.twiny()
        k_plot = self.axes2.plot(cx, cy, "-r", label="Conveyance")
        self.axes2.set_xlabel('Conveyance (m3/s)', color='r')

        plot_lines = xs_plot + k_plot
        labels = [l.get_label() for l in plot_lines]
        if p_plot is not None: 
            plot_lines += p_plot
            labels.append('Panels')
        self.axes.legend(plot_lines, labels, loc='lower right')

        self.axes.grid(True)
        self.fig.tight_layout()
        self.canvas.draw()

    def drawBanktopsPlot(self, section_data, section_id):
        """Plot the bad banks and cross section data provided.
        
        Args:
            section_data(dict): containing lists of the 'xvals', 'yvals',
            'left_drop' and 'right_drop' data for the section.
            section_id(str): the node id for this section.
            
        The left_drop and right_drop values are the difference between the
        highest section elevation on the left and right sides and the extreme
        left and right elevations (the misplaces bank elevation).
        """
        self.axes2.clear()
        self.axes.clear()
        self.fig.clear()
        self.axes = self.fig.gca()
        self.axes2 = self.axes.twinx()
        
        x = section_data['xvals']
        y = section_data['yvals']
        
        self.axes.set(
            ylabel='Elevation (mAOD)',
            xlabel='Chainage (m)',
            title="Node Name: {0}".format(section_id)
        )

        xs_plot = self.axes.plot(x, y, "-k", label="Cross Section")
        fill_plot = self.axes.fill(np.NaN, np.NaN, 'r', alpha=0.5)
        
        if section_data['left_drop'] > 0:
            line_x = x[:(section_data['max_left_idx']+1)]
            line_y = y[:(section_data['max_left_idx']+1)]
            line_elev = [section_data['max_left'] for i in line_x]
            self.axes.plot(
                line_x, line_elev, '-r'
            )
            self.axes.fill_between(line_x, line_y, line_elev, interpolate=True, alpha=0.5, color='r')
        if section_data['right_drop'] > 0:
            line_x = x[section_data['max_right_idx']:]
            line_y = y[section_data['max_right_idx']:]
            line_elev = [section_data['max_right'] for i in line_x]
            self.axes.plot(
                line_x, line_elev, '-r'
            )
            self.axes.fill_between(line_x, line_y, line_elev, interpolate=True, alpha=0.5, color='r')

        self.axes.legend(xs_plot + fill_plot, ['Cross Section', 'Poor Banks'], loc='lower right')
        self.axes.grid(True)
        self.fig.tight_layout()
        self.canvas.draw()


# class SectionPropertiesGraphicsView(QGraphicsView):
#     """GraphicsView to display section properties graphs.
#     
#     Contains methods for drawing conveyance and banktop issues.
#     """
#     
#     def __init__(self):
#         QGraphicsView.__init__(self)
#         self.canvas = None
#         
#     def drawConveyancePlot(self, section_data, section_id):
#         """Plot the conveyance and cross section data provided.
#         
#         Args:
#             section_data(dict): containing lists of the 'xvals', 'yvals',
#             'panels' and 'conveyance' data to be drawn on the graph.
#             section_id(str): the node id for this section.
#         """
#         if self.canvas is None:
#             scene = QGraphicsScene()
#             self.setScene(scene)
#         fig = Figure()
#         axes = fig.gca()
#         
#         minx = section_data['xvals'][0]
#         maxx = section_data['xvals'][-1]
#         miny = min(section_data['yvals'])
#         maxy = max(section_data['yvals'])
#         
#         x = section_data['xvals']
#         y = section_data['yvals']
#         
# #         axes.set_ylabel('Elevation (mAOD)')
# #         axes.set_xlabel('Chainage (m)')
# #         axes.set_title="ID: {0}".format(section_id)
#         axes.set(
#             ylabel='Elevation (mAOD)',
#             xlabel='Chainage (m)',
#             title="Node Name: {0}".format(section_id)
#         )
# 
#         xs_plot = axes.plot(x, y, "-k", label="Cross Section")
#         p_plot = None
# 
#         panel_count = 0
#         for i, panel in enumerate(section_data['panels']):
#             if panel:
#                 panel_count += 1
#                 panel_label = 'Panel {}'.format(panel_count)
#                 panelx = [section_data['xvals'][i], section_data['xvals'][i]]
#                 panely = [miny, maxy]
#                 p_plot = axes.plot(panelx, panely, "-b", label=panel_label)
#         
#         cx = []
#         cy = []
#         for c in section_data['conveyance']:
#             cx.append(c[0])
#             cy.append(c[1])
#         axes2 = axes.twiny()
#         k_plot = axes2.plot(cx, cy, "-r", label="Conveyance")
#         axes2.set_xlabel('Conveyance (m3/s)', color='r')
# 
#         plot_lines = xs_plot + k_plot
#         labels = [l.get_label() for l in plot_lines]
#         if p_plot is not None: 
#             plot_lines += p_plot
#             labels.append('Panels')
#         axes.legend(plot_lines, labels, loc='lower right')
# #         axes.legend()
# #         axes2.legend()
# 
#         axes.grid(True)
#         fig.tight_layout()
# #         self.canvas = FigureCanvas(fig)
# #         proxy_widget = scene.addWidget(self.canvas)
#         if self.canvas is None:
#             self.canvas = FigureCanvas(fig)
#             proxy_widget = scene.addWidget(self.canvas)
#         else:
#             self.canvas.figure = fig
#             self.canvas.draw()
# 
#     def drawBanktopsPlot(self, section_data, section_id):
#         """Plot the bad banks and cross section data provided.
#         
#         Args:
#             section_data(dict): containing lists of the 'xvals', 'yvals',
#             'left_drop' and 'right_drop' data for the section.
#             section_id(str): the node id for this section.
#             
#         The left_drop and right_drop values are the difference between the
#         highest section elevation on the left and right sides and the extreme
#         left and right elevations (the misplaces bank elevation).
#         """
#         if self.canvas is None:
#             scene = QGraphicsScene()
#             view = self.setScene(scene)
#         fig = Figure()
#         axes = fig.gca()
#         
#         x = section_data['xvals']
#         y = section_data['yvals']
#         
#         axes.set(
#             ylabel='Elevation (mAOD)',
#             xlabel='Chainage (m)',
#             title="Node Name: {0}".format(section_id)
#         )
# 
#         xs_plot = axes.plot(x, y, "-k", label="Cross Section")
#         fill_plot = axes.fill(np.NaN, np.NaN, 'r', alpha=0.5)
#         
#         if section_data['left_drop'] > 0:
#             line_x = x[:(section_data['max_left_idx']+1)]
#             line_y = y[:(section_data['max_left_idx']+1)]
#             line_elev = [section_data['max_left'] for i in line_x]
#             axes.plot(
#                 line_x, line_elev, '-r'
#             )
#             axes.fill_between(line_x, line_y, line_elev, interpolate=True, alpha=0.5, color='r')
#         if section_data['right_drop'] > 0:
#             line_x = x[section_data['max_right_idx']:]
#             line_y = y[section_data['max_right_idx']:]
#             line_elev = [section_data['max_right'] for i in line_x]
#             axes.plot(
#                 line_x, line_elev, '-r'
#             )
#             axes.fill_between(line_x, line_y, line_elev, interpolate=True, alpha=0.5, color='r')
# 
#         axes.legend(xs_plot + fill_plot, ['Cross Section', 'Poor Banks'], loc='lower right')
#         axes.grid(True)
#         fig.tight_layout()
# #         self.canvas = FigureCanvas(fig)
# #         proxy_widget = scene.addWidget(self.canvas)
#         if self.canvas is None:
#             self.canvas = FigureCanvas(fig)
#             proxy_widget = scene.addWidget(self.canvas)
#         else:
#             self.canvas.figure = fig
#             self.canvas.draw()


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

