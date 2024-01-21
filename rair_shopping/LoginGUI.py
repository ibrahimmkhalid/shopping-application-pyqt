from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QDialog, QPushButton, QDialogButtonBox
from rair_shopping.RegisterGUI import RegisterGUI
from rair_shopping.UtilsClass import DBUtils, error_window
from rair_shopping.UserData import UserData


class LoginGUI(QDialog):
    login_successful = QtCore.pyqtSignal(UserData)
    login_fail = QtCore.pyqtSignal()
    
    def __init__(self, utils: DBUtils):
        super().__init__()
        self.utils = utils
        self.user = None
        self.ui = uic.loadUi('./rair_shopping/ui/login_gui.ui')
        self.ui.login_button = QPushButton()
        self.ui.login_button.setText("Login")
        self.ui.login_button.clicked.connect(self.try_login)
        self.ui.buttonBox.addButton(self.ui.login_button, QDialogButtonBox.AcceptRole)
        self.ui.register_button = QPushButton()
        self.ui.register_button.setText("Register")
        self.ui.register_button.clicked.connect(self.try_register)
        self.ui.buttonBox.addButton(self.ui.register_button, QDialogButtonBox.AcceptRole)
        self.__registerGUIDialog = RegisterGUI(utils)
        self.__registerGUIDialog.register_successful.connect(self.on_register_successful)
        self.__registerGUIDialog.register_fail.connect(self.on_register_fail)

    def auto_login(self):
        self.ui.email_input.setText("user@rair.com")
        self.ui.password_input.setText("12345678")
        self.try_login()

    def auto_login_admin(self):
        self.ui.email_input.setText("admin@rair.com")
        self.ui.password_input.setText("12345678")
        self.try_login()

    def try_register(self):
        self.__registerGUIDialog.show_dialog()

    def try_login(self):
        email = self.ui.email_input.text()
        password = self.ui.password_input.text()
        if len(email) == 0 or len(password) == 0:
            error_window(Exception("Please enter a valid password or email"))
            self.login_fail.emit()
            return

        try:
            data = self.utils.login(email, password)
            self.user = UserData(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9])
            self.login_successful.emit(self.user)
            self.done(0)
            
        except Exception as e:
            error_window(e)
            self.login_fail.emit()

    def on_register_successful(self, user_data:UserData):
        self.user = user_data
        self.__registerGUIDialog.accept()
        self.login_successful.emit(self.user)
        self.accept()

    def on_register_fail(self):
        self.show_dialog()

    def show_dialog(self):
        self.ui.show()
