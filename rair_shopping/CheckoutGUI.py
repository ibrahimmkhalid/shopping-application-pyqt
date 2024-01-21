from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QHeaderView
from rair_shopping.UtilsClass import DBUtils, error_window
from rair_shopping.CartData import CartData
from rair_shopping.UserData import UserData


class CheckoutGUI(QDialog):
    checkout_successful = QtCore.pyqtSignal()
    checkout_fail = QtCore.pyqtSignal()
    
    def __init__(self, utils: DBUtils, cart: CartData, user: UserData):
        super().__init__()
        self.utils = utils
        self.cart = cart
        self.user = user
        self.ui = uic.loadUi('./rair_shopping/ui/checkout_gui.ui')

        self.ui.shipping_address_label.setText(f"Shipping to: {self.user.get_formatted_address()}")

        self.ui.order_details_table.setRowCount(0)
        self.ui.order_details_table.setColumnCount(3)
        self.ui.order_details_table.verticalHeader().setVisible(False)
        self.ui.order_details_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.order_details_table.setColumnWidth(1, 70)
        self.ui.order_details_table.setColumnWidth(2, 50)
        self.ui.order_details_table.setHorizontalHeaderLabels(["Name", "Price", "Qty"])

        self.ui.order_details_table.setRowCount(0)
        for _, product in self.cart.get_items():
            row = self.ui.order_details_table.rowCount()
            self.ui.order_details_table.insertRow(row)
            self.ui.order_details_table.setItem(row, 0, QTableWidgetItem(str(product["name"])))
            self.ui.order_details_table.setItem(row, 1, QTableWidgetItem(str(product["price"])))
            self.ui.order_details_table.setItem(row, 2, QTableWidgetItem(str(product["qty"])))

        self.ui.promo_button.clicked.connect(self.try_promo)

        self.ui.promo_applied_label.setText("")

        self.ui.grand_total_label.setText(f"Grand Total: ${self.cart.calculate_sub_total():.2f}")

        self.ui.checkout_button.clicked.connect(self.try_checkout)
        self.ui.cancel_button.clicked.connect(self.reject)
    
    def reject(self):
        self.ui.close()
        return super().reject()

    
    def try_promo(self):
        try:
            promo = self.utils.check_promo(self.ui.promo_code_entry.text())
            self.cart.add_promo_code(promo[1], promo[0], promo[3])
            self.ui.grand_total_label.setText(f"Grand Total: ${self.cart.calculate_grand_total():.2f}")
            self.ui.promo_applied_label.setText(f"Promo ({self.cart.get_promo_code()}) applied succesfully!")
        except Exception as e:
            error_window(e)
        pass

    def try_checkout(self):
        try:
            self.utils.checkout(self.user, self.cart)
            self.checkout_successful.emit()
            self.ui.close()
            self.done(0)
        except Exception as e:
            error_window(e)
            self.checkout_fail.emit()

    def show_dialog(self):
        self.ui.show()
