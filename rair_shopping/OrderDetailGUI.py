from PyQt5 import uic
from PyQt5.QtWidgets import QTableWidgetItem, QDialog, QHeaderView
from rair_shopping.UtilsClass import DBUtils
from rair_shopping.UserData import UserData


class OrderDetailGUI(QDialog):

    def __init__(self, utils: DBUtils, user: UserData, order_details):
        super().__init__()
        self.utils = utils
        self.user = user
        self.ui = uic.loadUi('./rair_shopping/ui/order_detail.ui')
        
        self.ui.order_items_table.setRowCount(0)
        self.ui.order_items_table.setColumnCount(4)
        self.ui.order_items_table.verticalHeader().setVisible(False)
        self.ui.order_items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.order_items_table.setColumnWidth(1, 70)
        self.ui.order_items_table.setColumnWidth(2, 70)
        self.ui.order_items_table.setColumnWidth(3, 70)
        self.ui.order_items_table.setHorizontalHeaderLabels(["Name", "Price", "Quantity", "Total"])
        self.ui.order_num_label.setText(f"Order Number: {order_details[0]}")
        self.ui.order_date_label.setText(f"Order Date: {order_details[1]}")
        self.ui.grand_total_label.setText(f"Grand Total: {order_details[2]}")
        self.ui.shipping_address_label.setText(f"Shipped to: {order_details[3]}")
        order_items = self.utils.get_order_details(order_details[0])
        promo = None
        for order_item in order_items:
            row = self.ui.order_items_table.rowCount()
            promo = order_item[4]
            self.ui.order_items_table.insertRow(row)
            self.ui.order_items_table.setItem(row, 0, QTableWidgetItem(str(order_item[2])))
            self.ui.order_items_table.setItem(row, 1, QTableWidgetItem(f"${order_item[3]:.2f}"))
            self.ui.order_items_table.setItem(row, 2, QTableWidgetItem(f"x{order_item[0]}"))
            self.ui.order_items_table.setItem(row, 3, QTableWidgetItem(f"${order_item[3] * order_item[0]}"))
        if promo:
            self.ui.promo_label.setText(f"Promo ({promo}) applied!")
        else:
            self.ui.promo_label.setText("")
    

    def show_dialog(self):
        self.ui.show()
