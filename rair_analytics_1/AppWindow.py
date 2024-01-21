from PyQt5 import uic
from PyQt5.QtGui import QWindow
from TabDialog import TabDialog
from EDADialog import EDADialog

class AppWindow(QWindow):
    """
    The main application window.
    """
    
    def __init__(self):
        """
        Load the UI and initialize its components.
        """
        super().__init__()
        
        self.ui = uic.loadUi('gui_app_1.ui')
        self.ui.show();
                
        # Tabular dialog.
        self._tabular_dialog = TabDialog()
        self.ui.pushTAB.clicked.connect(self._show_tabular_dialog)
        
        
        # EDA dialog.
        self._eda_dialog = EDADialog()
        self.ui.pushEDA.clicked.connect(self._show_eda_dialog)

    def _show_tabular_dialog(self):
        """
        Show the tabular dialog.
        """
        self._tabular_dialog.show_dialog()

   
    def _show_eda_dialog(self):
        """
        Show the eda dialog.
        """
        self._eda_dialog.show_dialog()

