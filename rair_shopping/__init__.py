import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication
from rair_shopping.LoginGUI import LoginGUI
from rair_shopping.ShopperGUI import ShopperGUI
from rair_shopping.AdminGUI import AdminGUI
from rair_shopping.UtilsClass import DBUtils, confirm_window
from rair_shopping.UserData import UserData

class RairDataShopping():
    def __init__(self, ini_file, db_config, wh_config):
        self.ini_file = ini_file
        self.db_config = db_config
        self.wh_config = wh_config

        app = QApplication(sys.argv)
        self.allow_auto_login = True
        self.utils = DBUtils(self.ini_file, self.db_config)
        self.user = None
        self.ui = uic.loadUi('./rair_shopping/ui/application.ui')
        self.ui.logout_button.clicked.connect(self.logout)
        self.ui.admin_logout_button.clicked.connect(self.logout)
        self.shopper_gui = ShopperGUI(self.utils, self.ui, self.user)
        self.admin_gui = AdminGUI(self.utils, self.ui, self.user, self.ini_file, self.wh_config)
        self.show_login_dialog()
        app.exec_()

    def start_shopper_gui(self):
        self.shopper_gui.start_shopper_gui(self.user)

    def start_admin_gui(self):
        self.admin_gui.start_admin_gui(self.user)
    
    def show_login_dialog(self):
        self.loginGUIDialog = LoginGUI(self.utils)
        self.loginGUIDialog.login_successful.connect(self.on_login_successful)
        self.loginGUIDialog.login_fail.connect(self.on_login_fail)
        if "--auto-login" in QApplication.arguments() and self.allow_auto_login:
            self.loginGUIDialog.auto_login()
        elif "--auto-login-admin" in QApplication.arguments() and self.allow_auto_login:
            self.loginGUIDialog.auto_login_admin()
        else:
            self.loginGUIDialog.show_dialog()

    def logout(self):
        self.user = None
        self.ui.product_search.setText("")
        self.ui.current_cart_table.setRowCount(0)
        self.ui.hide()
        self.admin_gui.kill_subprocesses()
        self.show_login_dialog()

    def on_login_successful(self, user_data:UserData):
        self.user = user_data
        if self.user.is_admin:

            if "--auto-login-admin" in QApplication.arguments() and self.allow_auto_login:
                self.allow_auto_login = False
                self.ui.stackedWidget.setCurrentIndex(1)
                self.start_admin_gui()
                self.loginGUIDialog.accept()
                return

            msg = "Admin account detected!\nWould you like to continue as an admin?"
            if confirm_window(msg):
                self.allow_auto_login = False
                self.ui.stackedWidget.setCurrentIndex(1)
                self.start_admin_gui()
                self.loginGUIDialog.accept()
                return

        self.allow_auto_login = False
        self.ui.stackedWidget.setCurrentIndex(0)
        self.start_shopper_gui()
        self.loginGUIDialog.accept()

    def on_login_fail(self):
        self.loginGUIDialog.reject()
        self.show_login_dialog()
    