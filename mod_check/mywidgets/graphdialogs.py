
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
            
            
class MbCheckMultipleGraphicsView(QGraphicsView):
    """GraphicsView for displaying multiple mb/dvol series.
    """
    
    def __init__(self):
        QGraphicsView.__init__(self)
        scene = QGraphicsScene()
        self.setScene(scene)
        self.fig = Figure()
        self.axes = self.fig.gca()
        self.axes2 = None
        self.fig.tight_layout()
        self.canvas = FigureCanvas(self.fig)
        proxy_widget = scene.addWidget(self.canvas)
        
    def resetPlot(self):
        if self.axes2 is not None:
            self.axes2.clear()
            self.axes2 = None
        self.axes.clear()
        self.fig.clear()
        self.axes = self.fig.gca()
        
    def drawPlot(self, results, show_dvol):
        """Update the graph plot."""
        self.resetPlot()

        # Get the time series with the largest range
        max_time = -1
        count = -1
        for i, r in enumerate(results):
            temp = max(r['data']['Time (h)'])
            if temp > max_time:
                max_time = temp
                count = i
        x = results[count]['data']['Time (h)']
        
        self.axes.set_ylabel('CME (%)', color='m')
        self.axes.set_xlabel('Time (h)')
        if show_dvol:
            self.axes2 = self.axes.twinx()
        
        # Plot recommended cme boundary lines
        cme_min = [1 for i in x]
        cme_max = [-1 for i in x]
        mb_max_plot = self.axes.plot(x, cme_min, "-g", alpha=0.5, label="CME max recommended", dashes=[6,2])
        mb_min_plot = self.axes.plot(x, cme_max, "-g", alpha=0.5, label="CME min recommended", dashes=[6,2])

        hl_index = -1
        for i, r in enumerate(results):
            if r['draw']:
                # Store index of highlight section and skip
                if r['highlight']:
                    hl_index = i
                    continue

                x = r['data']['Time (h)']
                cme = r['data']['Cum ME (%)']
                mb_plot = self.axes.plot(x, cme, '-m', alpha=0.4, label="CME")
                if show_dvol:
                    dvol = r['data']['dVol']
                    dvol_plot = self.axes2.plot(x, dvol, '-c', alpha=0.4, label="dVol")
                    self.axes2.set_ylabel('dVol', color='c')
        
        # Draw the series to highlight last so it shows up on top
        if hl_index > -1:
            self.axes.set_title("Selected: {0}".format(results[hl_index]['name']))
            x = results[hl_index]['data']['Time (h)']
            cme = results[hl_index]['data']['Cum ME (%)']
            mb_plot = self.axes.plot(x, cme, '-r', alpha=1, label="CME")
            if show_dvol:
                dvol = results[hl_index]['data']['dVol']
                dvol_plot = self.axes2.plot(x, dvol, '-b', alpha=1, label="dVol")
                self.axes2.set_ylabel('dVol')

        # Add a legend describing the cme max tolerance boundary lines
        plot_lines = mb_max_plot
        labels = [l.get_label() for l in plot_lines]
        self.axes.legend(plot_lines, labels, loc='lower right')

        self.axes.grid(True)
        self.fig.tight_layout()
        self.canvas.draw()
            
            
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

        self.axes.grid(True)
        self.axes.legend(plot_lines, labels, loc='lower right')
        self.fig.tight_layout()
        self.canvas.draw()
        

class HpcCheckIndividualGraphicsView(QGraphicsView):
    """GraphicsView to display the Individual MB Check tab graphs.
    """
    
    def __init__(self):
        QGraphicsView.__init__(self)

        scene = QGraphicsScene()
        self.setScene(scene)
        self.fig = Figure()
        self.axes = self.fig.gca()
        self.fig.tight_layout()
        self.canvas = FigureCanvas(self.fig)
        proxy_widget = scene.addWidget(self.canvas)
        
    def drawPlot(self, series_meta, results, title):
        plot_colors = ['-b', '-g', '-r', '-c', '-m', '-y', '-k',]
        color_count = 0
        labels = []
        plot_lines = []
        self.axes.clear()
        self.fig.clear()
        self.axes = self.fig.gca()
        
        x = results[:,1]
        self.axes.set_xlabel('tEnd (h)')
        self.axes.set_title(title)

        gtype = series_meta[1]
        if gtype in ['Nc', 'Nu', 'Nd']:
            if gtype == 'Nc' or gtype == 'Nu':
                tol_max = [1.0 for i in x]
            else:
                tol_max = [0.3 for i in x]

            max_plot = self.axes.plot(x, tol_max, "-g", alpha=0.5, label="Max recommended", dashes=[6,2])
            pl = [p for p in max_plot]
            plot_lines += pl
            labels += [l.get_label() for l in pl]
    

        s = results[:,series_meta[0]]
        left_plot = self.axes.plot(x, s, plot_colors[color_count], label=gtype)
        self.axes.set_ylabel(gtype)
        pl = [p for p in left_plot]
        plot_lines += pl
        labels += [l.get_label() for l in pl]
        color_count += 1
        if color_count > len(plot_colors):
            color_count = 0
            
        self.axes.grid(True)
        self.axes.legend(plot_lines, labels, loc='lower right')
        self.fig.tight_layout()
        self.canvas.draw()
        

class FmpStabilityGeometryGraphicsView(QGraphicsView):
    """GraphicsView to display the flow/stage for the Fmp stability check.
    """
    
    def __init__(self):
        QGraphicsView.__init__(self)

        scene = QGraphicsScene()
        self.setScene(scene)
        self.fig = Figure()
        self.axes = self.fig.gca()
#         self.axes2 = self.axes.twinx()
        self.fig.tight_layout()
        self.canvas = FigureCanvas(self.fig)
        proxy_widget = scene.addWidget(self.canvas)
        
    def clearPlot(self, redraw=True):
        self.axes.clear()
        self.fig.clear()
        if redraw:
            self.canvas.draw()
        
    def drawPlot(self, geom_data, node_name, stage):
        self.clearPlot(redraw=False)
        self.axes = self.fig.gca()
    
        x = geom_data[0]
        y = geom_data[1]
        s = [stage for i in x]

        self.axes.set_xlabel('Chainage (m)')
        self.axes.set_ylabel('Elevation (mAOD)')
        self.axes.set_title(node_name)

        bed_plot = self.axes.plot(x, geom_data[1], '-k')
        stage_plot = self.axes.plot(x, s, '-b')
        self.axes.fill_between(x, y, s, where=y<=stage, interpolate=True, alpha=0.5, color='b')

        self.fig.tight_layout()
        self.canvas.draw()
        
class FmpStabilityGraphicsView(QGraphicsView):
    """GraphicsView to display the flow/stage for the Fmp stability check.
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
        
    def drawPlot(self, time_data, results, derivs, timestep, series_type, 
                 node_name, show_derivs=False):
        labels = []
        plot_lines = []
        self.axes2.clear()
        self.axes.clear()
        self.fig.clear()
        self.axes = self.fig.gca()
        self.axes2 = self.axes.twinx()
    
        x = time_data
        self.axes.set_xlabel('Time (h)')
        fail_times = ''
        if derivs['status'] == 'Failed':
            fail_times = '(First fail: {} - Last Fail: {})'.format(derivs['fail_times'][0], derivs['fail_times'][-1])
        status_text = '{} {}'.format(node_name, fail_times) #'Dy2 Fail = {}   :   {}'.format(derivs['status'], fail_times)
        self.axes.set_title(status_text)
        self.axes.set_ylabel('Stage (mAOD)')
        self.axes2.set_ylabel('Flow (m3/s)')
        
        if series_type == 'Stage':
            s1_plot = self.axes.plot(x, results[0], '-b')
            s2_plot = self.axes2.plot(x, derivs['f'], '-r')
        else:
            s1_plot = self.axes2.plot(x, derivs['f'], '-r')
            s2_plot = self.axes.plot(x, results[0], '-b')
        
        time_x = [timestep, timestep]
        time_y = [min(results[0]), max(results[0])]
        time_plot = self.axes.plot(time_x, time_y, '-k')

        # User doesn't need derivative graphs, just for debugging
        if show_derivs:
            x2 = x[:-1]
            right_plot = self.axes2.plot(x2, derivs['dy'], '-g', alpha=0.5)
            x3 = x2[:-1]
            right_plot2 = self.axes2.plot(x3, derivs['dy2'], '-k', alpha=0.5)

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
        
    # def drawConveyancePlot(self, k_data, section_data, section_id):
    def drawConveyancePlot(self, k_data, section_id):
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
        
        section = k_data['section']
        
        self.axes.set(
            ylabel='Elevation (mAOD)',
            xlabel='Chainage (m)',
            title="Node Name: {0}".format(section_id)
        )

        xs_plot = self.axes.plot(section.xs_x, section.xs_y, "-k", label="Cross Section")
        xs_plot_active = self.axes.plot(section.xs_active_x, section.xs_active_y, "limegreen", label="Cross Section Active")
        p_plot = None

        for panel in section.panels:
            panel_label = 'Panel {}'.format(section.panel_count)
            p_plot = self.axes.plot(panel['x'], panel['y'], "-b", label=panel_label)

        self.axes2 = self.axes.twiny()
        k_plot = self.axes2.plot(section.conveyance['x'], section.conveyance['y'], "-r", label="Conveyance")
        self.axes2.set_xlabel('Conveyance (m3/s)', color='r')
        
        plot_lines = xs_plot + xs_plot_active + k_plot
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

