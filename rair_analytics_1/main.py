import sys
from PyQt5.QtWidgets import QApplication
from AppWindow import AppWindow

app = QApplication(sys.argv)
form = AppWindow()
app.exec_()
