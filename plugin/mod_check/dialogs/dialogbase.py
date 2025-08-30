
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget

from ..forms import ui_help_dialog as help_ui
from ..tools import help, globaltools
from ..mywidgets import graphdialogs as graphs
from PyQt5.pyrcc_main import showHelp


class DialogBase(QDialog):
    """Base class interface for standard functionality in Dialog classes.
    
    """
    closing = pyqtSignal(str)
    
    def __init__(self, dialog_name, iface, project, help_key):
        QDialog.__init__(self)
        self.dialog_name = dialog_name
        self.iface = iface
        self.project = project
        self.help_key = help_key
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        
        self.buttonBox.clicked.connect(self.buttonBoxClicked)
        
    def buttonBoxClicked(self, btn):
        name = btn.text()
        if name == 'Close':
            self.close()
        elif name == 'Help':
            self.showHelp()
            
    def signalClose(self):
        """Notify listeners that the dialog is being closed."""
        self.closing.emit(self.dialog_name)
        
    def closeEvent(self, *args, **kwargs):
        """Override the close event to emit a signal.
        
        Overrides: QDialog.closeEvent.
        """
        self.signalClose()
        return QDialog.closeEvent(self, *args, **kwargs)

    def showHelp(self):
        dialog = graphs.LocalHelpDialog('{0} - {1}'.format('Help', self.help_key))
        dialog.showText(help.helpText(self.help_key))
        dialog.exec_()