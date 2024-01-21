from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QPushButton, QHeaderView, QTableWidget
from rair_shopping.OrderHistoryGUI import OrderHistoryGUI
from rair_shopping.ChangeAddressGUI import ChangeAddressGUI
from rair_shopping.CheckoutGUI import CheckoutGUI
from rair_shopping.UtilsClass import DBUtils
from rair_shopping.UserData import UserData
from rair_shopping.CartData import CartData


class ShopperGUI(QMainWindow):

    def __init__(self, utils: DBUtils, ui, user: UserData):
        super().__init__()
        self.utils = utils
        self.user = user
        self.ui = ui

        self.page = 0
        self.num_per_page = 19
        self.search_term = ""
        self.category_id = 0
        self.cart = CartData()
        self.categories = {}

        self.set_sub_total()
        self.ui.search_button.clicked.connect(self.do_search)
        self.ui.category_select.currentIndexChanged.connect(self.do_search)

        self.ui.next_page_button.clicked.connect(self.load_next_page)
        self.ui.prev_page_button.clicked.connect(self.load_prev_page)
        self.ui.prev_page_button.setEnabled(False)

        self.ui.checkout_button.clicked.connect(self.show_checkout_dialog)
        self.ui.checkout_button.setEnabled(False)

        self.ui.order_history_button.clicked.connect(self.show_order_history_dialog)
        self.ui.change_address_button.clicked.connect(self.change_address)
    
    def start_shopper_gui(self, user: UserData):
        self.user = user
        self.load_categories(self.utils.get_categories())
        self.initialize_product_table()
        self.initialize_cart()
        self.render_cart()

        self.ui.welcome_label.setText("Welcome, " + self.user.name)
        self.ui.show()

    def change_address(self):
        self.__changeAddressGUIDialog = ChangeAddressGUI(self.utils, self.user)
        self.__changeAddressGUIDialog.address_changed.connect(self.on_address_changed)
        self.__changeAddressGUIDialog.show_dialog()
    
    def on_address_changed(self, user: UserData):
        self.user = user

    def initialize_product_table(self):
        self.ui.product_result_table.setRowCount(0)
        self.ui.product_result_table.setColumnCount(5)
        self.ui.product_result_table.setHorizontalHeaderLabels(["Name", "Price", "Stock", "Cart", "ID"])
        self.ui.product_result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.product_result_table.verticalHeader().setVisible(False)
        self.ui.product_result_table.setColumnWidth(1, 70)
        self.ui.product_result_table.setColumnWidth(2, 70)
        self.ui.product_result_table.setColumnWidth(3, 50)
        self.ui.product_result_table.setColumnHidden(4, True)
        self.ui.product_result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.load_products()

    def initialize_cart(self):
        self.ui.current_cart_table.setRowCount(0)
        self.ui.current_cart_table.setColumnCount(5)
        self.ui.current_cart_table.setHorizontalHeaderLabels(["Name", "Price", "Qty", "Cart", "ID"])
        self.ui.current_cart_table.verticalHeader().setVisible(False)
        self.ui.current_cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.current_cart_table.setColumnWidth(1, 70)
        self.ui.current_cart_table.setColumnWidth(2, 70)
        self.ui.current_cart_table.setColumnWidth(3, 50)
        self.ui.current_cart_table.setColumnHidden(4, True)
        self.ui.current_cart_table.setEditTriggers(QTableWidget.NoEditTriggers)

    def set_sub_total(self, total=0.00):
        self.ui.sub_total_label.setText(f"Sub Total: ${total:.2f}")

    def load_categories(self, data):
        all_cat = "- All Categories -"
        self.categories[all_cat] = 0
        self.ui.category_select.addItem(all_cat)
        for datum in data:
            self.categories[datum[1]] = datum[0]
            self.ui.category_select.addItem(datum[1])

    def load_prev_page(self):
        self.ui.product_result_table.setRowCount(0)
        self.page -= 1
        self.load_products()
        self.ui.next_page_button.setEnabled(True)
        if self.page == 0:
            self.ui.prev_page_button.setEnabled(False)

    def load_next_page(self):
        self.ui.product_result_table.setRowCount(0)
        self.page += 1
        self.load_products()
        self.ui.prev_page_button.setEnabled(True)
        if self.page == self.max_page:
            self.ui.next_page_button.setEnabled(False)
    
    def do_search(self):
        self.ui.product_result_table.setRowCount(0)
        self.ui.next_page_button.setEnabled(True)
        self.ui.prev_page_button.setEnabled(False)
        self.page = 0
        self.load_products()

    def load_products(self):
        self.ui.product_result_table.setRowCount(0)
        category_id = self.ui.category_select.currentIndex()
        search_term = self.ui.product_search.text()

        if category_id != self.category_id or search_term != self.search_term:
            self.page = 0
        self.category_id = category_id
        self.search_term = search_term

        if search_term == "":
            products, total = self.utils.get_products(category_id, self.page, self.num_per_page)
        else:
            products, total = self.utils.get_products_search(category_id, search_term, self.page, self.num_per_page)

        if self.num_per_page == total:
            self.max_page = 0
        else:
            self.max_page = total // self.num_per_page
        self.ui.page_count_label.setText(f"Page: {self.page + 1}/{self.max_page + 1}")

        if self.max_page == 0:
            self.ui.next_page_button.setEnabled(False)

        for product in products:
            row = self.ui.product_result_table.rowCount()
            self.ui.product_result_table.insertRow(row)
            self.ui.product_result_table.setItem(row, 0, QTableWidgetItem(product[1]))
            self.ui.product_result_table.setItem(row, 1, QTableWidgetItem(f"${product[2]:.2f}"))
            self.ui.product_result_table.setItem(row, 4, QTableWidgetItem(str(product[0])))
            add_to_cart_button = QPushButton("+")
            remaining_stock = product[3] - self.cart.get_product_quantity(str(product[0]))
            if remaining_stock <= 0:
                add_to_cart_button.setEnabled(False)
            self.ui.product_result_table.setItem(row, 2, QTableWidgetItem(str(remaining_stock)))
            add_to_cart_button.clicked.connect(self.add_to_cart_window)
            self.ui.product_result_table.setCellWidget(row, 3, add_to_cart_button)
    
    def add_to_cart_window(self):
        button = self.sender()
        if button:
            row = self.ui.product_result_table.indexAt(button.pos()).row()
            name_item = self.ui.product_result_table.item(row, 0)
            price_item = self.ui.product_result_table.item(row, 1)
            product_id = self.ui.product_result_table.item(row, 4)
            current_stock = self.ui.product_result_table.item(row, 2)
            if name_item and price_item and product_id and current_stock:
                self.cart.add_to_cart(product_id.text(), price_item.text(), name_item.text())
                self.set_sub_total(self.cart.calculate_sub_total())
                self.remove_stock_from_table(current_stock, button)
                self.render_cart()

    def render_cart(self):
        self.ui.current_cart_table.setRowCount(0)
        for id, product in self.cart.get_items():
            row = self.ui.current_cart_table.rowCount()
            self.ui.current_cart_table.insertRow(row)
            self.ui.current_cart_table.setItem(row, 0, QTableWidgetItem(str(product["name"])))
            self.ui.current_cart_table.setItem(row, 1, QTableWidgetItem(str(product["price"])))
            self.ui.current_cart_table.setItem(row, 2, QTableWidgetItem(str(product["qty"])))
            self.ui.current_cart_table.setItem(row, 4, QTableWidgetItem(str(id)))
            remove_from_cart_button = QPushButton("-")
            remove_from_cart_button.clicked.connect(self.remove_from_cart_window)
            self.ui.current_cart_table.setCellWidget(row, 3, remove_from_cart_button)
        self.ui.checkout_button.setEnabled(not self.cart.is_empty())

    def remove_stock_from_table(self, current_stock, button):
        current_stock.setText(str(int(current_stock.text()) - 1))
        if int(current_stock.text()) == 0:
            button.setEnabled(False)
                
    def remove_from_cart_window(self):
        button = self.sender()
        if button:
            row = self.ui.current_cart_table.indexAt(button.pos()).row()
            product_id = self.ui.current_cart_table.item(row, 4)
            if product_id:
                self.cart.remove_from_cart(product_id.text())
                self.add_stock_to_table(product_id)
                self.set_sub_total(self.cart.calculate_sub_total())
                self.render_cart()

    def add_stock_to_table(self, product_id):
        for row in range(self.ui.product_result_table.rowCount()):
            if self.ui.product_result_table.item(row, 4).text() == product_id.text():
                current_stock = self.ui.product_result_table.item(row, 2)
                current_stock.setText(str(int(current_stock.text()) + 1))
                add_to_cart_button = self.ui.product_result_table.cellWidget(row, 3)
                add_to_cart_button.setEnabled(True)
                break

    def show_checkout_dialog(self):
        self.__checkoutGUIDialog = CheckoutGUI(self.utils, self.cart, self.user)
        self.__checkoutGUIDialog.checkout_successful.connect(self.on_checkout_successful)
        self.__checkoutGUIDialog.checkout_fail.connect(self.on_checkout_fail)
        self.__checkoutGUIDialog.show_dialog()
    
    def on_checkout_successful(self):
        self.cart.clear()
        self.render_cart()
        self.set_sub_total()
        self.page = 0
        self.ui.category_select.setCurrentIndex(0)
        self.ui.product_search.setText("")
        self.initialize_product_table()
    
    def on_checkout_fail(self):
        self.on_checkout_successful()

    def show_order_history_dialog(self):
        self.__orderHistoryGUIDialog = OrderHistoryGUI(self.utils, self.user)
        self.__orderHistoryGUIDialog.show_dialog()
