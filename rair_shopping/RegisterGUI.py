from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QDialog
from rair_shopping.UtilsClass import DBUtils, error_window
from rair_shopping.UserData import UserData


class RegisterGUI(QDialog):
    register_successful = QtCore.pyqtSignal(UserData)
    register_fail = QtCore.pyqtSignal()

    def __init__(self, utils: DBUtils):
        super().__init__()
        self.utils = utils
        self.ui = uic.loadUi('./rair_shopping/ui/register_gui.ui')
        self.user = None
        self.ui.gender.addItems(['Male', 'Female', 'Non-binary', 'Genderfluid', 'Agender', 'Polygender', 'Bigender', 'Genderqueer'])
        self.ui.buttonBox.accepted.connect(self.try_register)
        self.ui.buttonBox.rejected.connect(self.back_to_login)

    def back_to_login(self):
        self.register_fail.emit()
        self.done(0)

    def show_dialog(self):
        self.ui.email1.setFocus()
        self.ui.email1.setText("")
        self.ui.email2.setText("")
        self.ui.password1.setText("")
        self.ui.password2.setText("")
        self.ui.name.setText("")
        self.ui.street.setText("")
        self.ui.city.setText("")
        self.ui.state.setText("")
        self.ui.zip_code.setText("")
        self.ui.dob.setDate(QtCore.QDate.fromString("2000-01-01", "yyyy-MM-dd"))
        self.ui.gender.setCurrentIndex(0)
        self.ui.show()

    def try_register(self):
        email1 = self.ui.email1.text()
        email2 = self.ui.email2.text()
        password1 = self.ui.password1.text()
        password2 = self.ui.password2.text()
        name = self.ui.name.text()
        street = self.ui.street.text()
        city = self.ui.city.text()
        state = self.ui.state.text()
        zip_code = self.ui.zip_code.text()
        dob = self.ui.dob.text()
        gender = self.ui.gender.currentText()

        # validations
        if not email1:
            error_window(Exception("Email cannot be empty."))
            self.ui.email1.setText("")
            self.ui.email1.setFocus()
            self.ui.show()
            return super().accept()

        if email1 != email2:
            error_window(Exception("Emails do not match."))
            self.ui.email2.setText("")
            self.ui.email2.setFocus()
            self.ui.show()
            return super().accept()

        if not name:
            error_window(Exception("Name cannot be empty."))
            self.ui.name.setText("")
            self.ui.name.setFocus()
            self.ui.show()
            return super().accept()
        
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

        if not password1:
            error_window(Exception("Password cannot be empty."))
            self.ui.password1.setText("")
            self.ui.password2.setText("")
            self.ui.password1.setFocus()
            self.ui.show()
            return super().accept()
    
        if password1 != password2:
            error_window(Exception("Passwords do not match."))
            self.ui.password1.setText("")
            self.ui.password2.setText("")
            self.ui.password1.setFocus()
            self.ui.show()
            return super().accept()
        
        try:
            data = self.utils.register(email1, password1, name, street, city, state, zip_code, dob, gender)
            self.user = UserData(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8])
            self.register_successful.emit(self.user)
        except Exception as e:
            error_window(e)
            self.register_fail.emit()
