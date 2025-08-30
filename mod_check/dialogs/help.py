
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget
from ..forms import ui_help_dialog as help_ui
from ..tools import help, globaltools
# from ..tools import settings as mrt_settings
from PyQt5.pyrcc_main import showHelp

DATA_DIR = './data'
TEMP_DIR = './temp'
class HelpPageDialog(QDialog, help_ui.Ui_HelpDialog):
    """Display the plugin help page dialog."""

    def __init__(self, iface, project):
        QDialog.__init__(self)
        self.iface = iface
        self.project = project
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        
        self.help = help.ModCheckHelp()
        self.setupHelpList()
        self.helpSelectList.currentTextChanged.connect(self.changeHelpPage)
        
    def setupHelpList(self):
        self.helpSelectList.clear()
        help_items = self.help.helpList()
        for item in help_items:
            self.helpSelectList.addItem(item)
        
    def changeHelpPage(self, tool_name):
        contents = self.help.helpContents(tool_name)
        self.helpDisplayTextBrowser.setText(contents)