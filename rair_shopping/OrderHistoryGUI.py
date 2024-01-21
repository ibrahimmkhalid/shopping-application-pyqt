from PyQt5 import uic
from PyQt5.QtWidgets import QTableWidgetItem, QPushButton, QDialog, QHeaderView
from rair_shopping.OrderDetailGUI import OrderDetailGUI
from rair_shopping.UtilsClass import DBUtils
from rair_shopping.UserData import UserData


class OrderHistoryGUI(QDialog):

    def __init__(self, utils: DBUtils, user: UserData):
        super().__init__()
        self.utils = utils
        self.user = user
        self.ui = uic.loadUi('./rair_shopping/ui/order_history.ui')
        
        self.page = 0
        self.num_per_page = 19

        self.ui.next_page_button.clicked.connect(self.load_next_page)
        self.ui.prev_page_button.clicked.connect(self.load_prev_page)
        self.ui.prev_page_button.setEnabled(False)

        self.initialize_order_history()

    def show_dialog(self):
        self.ui.show()

    def initialize_order_history(self):
        self.ui.order_result_table.setRowCount(0)
        self.ui.order_result_table.setColumnCount(5)
        self.ui.order_result_table.verticalHeader().setVisible(False)
        self.ui.order_result_table.setColumnWidth(0, 70)
        self.ui.order_result_table.setColumnWidth(1, 130)
        self.ui.order_result_table.setColumnWidth(2, 70)
        self.ui.order_result_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.ui.order_result_table.setColumnWidth(4, 70)
        self.ui.order_result_table.setHorizontalHeaderLabels(["Order #", "Date", "Total", "Shipping Address", "Details"])
        self.load_orders()

    def load_prev_page(self):
        self.ui.order_result_table.setRowCount(0)
        self.page -= 1
        self.load_orders()
        self.ui.next_page_button.setEnabled(True)
        if self.page == 0:
            self.ui.prev_page_button.setEnabled(False)

    def load_next_page(self):
        self.ui.order_result_table.setRowCount(0)
        self.page += 1
        self.load_orders()
        self.ui.prev_page_button.setEnabled(True)
        if self.page == self.max_page:
            self.ui.next_page_button.setEnabled(False)

    def load_orders(self):
        self.ui.order_result_table.setRowCount(0)

        orders, total = self.utils.get_order_history(self.user.user_id, self.page, self.num_per_page)

        self.max_page = total // self.num_per_page
        self.ui.page_count_label.setText(f"Page: {self.page + 1}/{self.max_page + 1}")

        if self.max_page == 0:
            self.ui.next_page_button.setEnabled(False)

        for order in orders:
            row = self.ui.order_result_table.rowCount()
            self.ui.order_result_table.insertRow(row)
            self.ui.order_result_table.setItem(row, 0, QTableWidgetItem(str(order[0])))
            self.ui.order_result_table.setItem(row, 1, QTableWidgetItem(str(order[1])))
            self.ui.order_result_table.setItem(row, 2, QTableWidgetItem(f"${order[2]:.2f}"))
            self.ui.order_result_table.setItem(row, 3, QTableWidgetItem(f"{order[3]}, {order[4]}, {order[5]} {order[6]}"))
            add_to_cart_button = QPushButton("Show")
            add_to_cart_button.clicked.connect(self.show_order_detail_dialog)
            self.ui.order_result_table.setCellWidget(row, 4, add_to_cart_button)
    
    def show_order_detail_dialog(self):
        button = self.sender()
        if button:
            row = self.ui.order_result_table.indexAt(button.pos()).row()
            order_id = self.ui.order_result_table.item(row, 0)
            order_date = self.ui.order_result_table.item(row, 1)
            order_total = self.ui.order_result_table.item(row, 2)
            order_address = self.ui.order_result_table.item(row, 3)
            
            if order_id and order_date and order_total and order_address:
                order_details = [
                    order_id.text(),
                    order_date.text(),
                    order_total.text(),
                    order_address.text()
                ]
                self.__orderDetailGUIDialog = OrderDetailGUI(self.utils, self.user, order_details)
                self.__orderDetailGUIDialog.show_dialog()
