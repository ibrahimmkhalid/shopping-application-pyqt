from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QDialog
from rair_shopping.UtilsClass import DBUtils, error_window, success_window
from rair_shopping.UserData import UserData

class ChangeAddressGUI(QDialog):
    address_changed = QtCore.pyqtSignal(UserData)  

    def __init__(self, utils: DBUtils, user: UserData):
        super().__init__()
        self.utils = utils
        self.ui = uic.loadUi('./rair_shopping/ui/change_address.ui')
        self.user = user
        self.ui.buttonBox.accepted.connect(self.try_address_change)
        self.ui.buttonBox.rejected.connect(self.reject)

    def show_dialog(self):
        self.ui.name.setText(self.user.name)
        self.ui.name.setReadOnly(True)
        self.ui.name.setStyleSheet("background-color: rgb(211, 211, 211);")
        self.ui.street.setText(self.user.street)
        self.ui.city.setText(self.user.city)
        self.ui.state.setText(self.user.state)
        self.ui.zip_code.setText(self.user.zip_code)
        self.ui.show()

    def try_address_change(self):

        street = self.ui.street.text()
        city = self.ui.city.text()
        state = self.ui.state.text()
        zip_code = self.ui.zip_code.text()

        
        if not street:
            error_window(Exception("Street cannot be empty."))
            self.ui.street.setText("")
            self.ui.street.setFocus()
            self.ui.show()
            return super().accept()
        
        if not city:
            error_window(Exception("City cannot be empty."))
            self.ui.city.setText("")
            self.ui.city.setFocus()
            self.ui.show()
            return super().accept()
        
        if not state:
            error_window(Exception("State cannot be empty."))
            self.ui.state.setText("")
            self.ui.state.setFocus()
            self.ui.show()
            return super().accept()
        
        if not zip_code:
            error_window(Exception("Zip code cannot be empty."))
            self.ui.zip_code.setText("")
            self.ui.zip_code.setFocus()
            self.ui.show()
            return super().accept()
        
        if not zip_code.isdigit():
            error_window(Exception("Zip code must be a numeric value."))
            self.ui.zip_code.setText("")
            self.ui.zip_code.setFocus()
            self.ui.show()
            return super().accept()
        
        if len(zip_code) != 5:
            error_window(Exception("Zip code must be 5 digits."))
            self.ui.zip_code.setText("")
            self.ui.zip_code.setFocus()
            self.ui.show()
            return super().accept()

        try:
            data = self.utils.change_address(self.user.user_id, street, city, state, zip_code)
            self.user = UserData(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8])
        except Exception as e:
            error_window(e)
            return super().accept()
        success_window("Address changed successfully!")
        self.address_changed.emit(self.user)