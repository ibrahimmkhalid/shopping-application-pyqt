from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QMainWindow, QProgressDialog, QTableWidgetItem, QDateEdit, QComboBox, QCheckBox, QTableWidget, QHeaderView, QPushButton
from rair_shopping.UtilsClass import DBUtils, WHUtils, error_window, confirm_window, success_window
from rair_shopping.UserData import UserData

import sys
import os
import subprocess

class AdminGUI(QMainWindow):
    def __init__(self, utils: DBUtils, ui, user:UserData, ini_file, wh_config):
        super().__init__()
        self.db_utils = utils
        self.wh_utils = WHUtils(ini_file, wh_config)
        self.ui = ui
        self.user = user


        self.ui.dashboard_1_button.clicked.connect(self.open_dashboard_1)
        self.ui.dashboard_2_button.clicked.connect(self.open_dashboard_2)
        self.ui.etl_button.clicked.connect(self.perform_etl)

        self.dashboard_1_process = None
        self.dashboard_2_process = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_dashboards)
        self.timer.start(500)

        self.ui.product_admin_button.clicked.connect(self.open_product_admin)
        self.ui.user_admin_button.clicked.connect(self.open_user_admin)
        self.ui.promo_admin_button.clicked.connect(self.open_promo_admin)
        self.open_product_admin()

        self.ui.product_prev_page_button.clicked.connect(self.load_prev_product_page)
        self.ui.product_next_page_button.clicked.connect(self.load_next_product_page)
        self.ui.promo_next_page_button.setEnabled(False)
        self.ui.product_admin_search_button.clicked.connect(self.do_search)
        self.ui.product_admin_category_select.currentIndexChanged.connect(self.do_search)
        self.ui.product_create_button.clicked.connect(self.create_product)
        
        self.ui.customer_edit_apply_button.clicked.connect(self.apply_customer_edit)
        self.ui.customer_edit_reset_button.clicked.connect(self.reset_customer_edit)
        self.ui.customer_search_button.clicked.connect(self.search_customer)

        self.ui.promo_prev_page_button.clicked.connect(self.load_prev_promo_page)
        self.ui.promo_next_page_button.clicked.connect(self.load_next_promo_page)
        self.ui.promo_prev_page_button.setEnabled(False)
        self.ui.promo_reload_button.clicked.connect(self.reset_promo_edit)
        self.ui.promo_create_button.clicked.connect(self.create_promo)
    
    def __del__(self):
        self.kill_subprocesses()
    
    def open_user_admin(self):
        self.ui.product_admin_button.setEnabled(True)
        self.ui.user_admin_button.setEnabled(False)
        self.ui.admin_widgets.setCurrentIndex(1)
        self.ui.promo_admin_button.setEnabled(True)
        self.reset_customer_edit()
        pass

    def reset_customer_edit(self):
        self.selected_customer_id = None
        self.selected_customer_email = None
        self.old_is_admin = None
        self.ui.edit_customer_info_table.setRowCount(0)
        self.ui.edit_customer_info_table.setRowCount(8)
        self.ui.edit_customer_info_table.setColumnCount(1)
        self.ui.edit_customer_info_table.horizontalHeader().setVisible(False)
        self.ui.edit_customer_info_table.horizontalHeader().setStretchLastSection(True)
        self.ui.edit_customer_info_table.setVerticalHeaderLabels([
                "Name", "Street", "City", "State",
                "Zip Code", "Date of Birth", "Gender", "Has admin privileges",
            ])
        self.ui.customer_search_bar.setText("")
        self.ui.customer_search_bar.setFocus()
        self.ui.customer_id_label.setText("Customer ID: ")
        self.ui.customer_email_label.setText("Customer Email: ")
        self.ui.customer_edit_apply_button.setEnabled(False)
        self.ui.customer_edit_reset_button.setEnabled(False)

    def search_customer(self):
        email = self.ui.customer_search_bar.text()
        if email == "": return
        try:
            customer = self.db_utils.get_customer_by_email(email)
        except Exception as e:
            self.reset_customer_edit()
            error_window(e)
            return
        self.reset_customer_edit()
        self.ui.customer_edit_apply_button.setEnabled(True)
        self.ui.customer_edit_reset_button.setEnabled(True)
        self.selected_customer_id = customer[0]
        self.selected_customer_email = customer[1]
        self.ui.customer_id_label.setText(f"Customer ID: {customer[0]}")
        self.ui.customer_email_label.setText(f"Customer Email: {customer[1]}")
        self.ui.edit_customer_info_table.setItem(0, 0, QTableWidgetItem(str(customer[2])))
        self.ui.edit_customer_info_table.setItem(1, 0, QTableWidgetItem(str(customer[3])))
        self.ui.edit_customer_info_table.setItem(2, 0, QTableWidgetItem(str(customer[4])))
        self.ui.edit_customer_info_table.setItem(3, 0, QTableWidgetItem(str(customer[5])))
        self.ui.edit_customer_info_table.setItem(4, 0, QTableWidgetItem(str(customer[6])))
        dob_edit = QDateEdit()
        dob_edit.setDate(customer[7])
        dob_edit.setDisplayFormat("yyyy-MM-dd")
        self.ui.edit_customer_info_table.setCellWidget(5, 0, dob_edit)
        gender_edit = QComboBox()
        gender_list = ['Male', 'Female', 'Non-binary', 'Genderfluid', 'Agender', 'Polygender', 'Bigender', 'Genderqueer']
        user_gender = customer[8]
        gender_edit.addItems(gender_list)
        user_gender_index = gender_list.index(user_gender)
        gender_edit.setCurrentIndex(user_gender_index)
        self.ui.edit_customer_info_table.setCellWidget(6, 0, gender_edit)
        admin_edit = QCheckBox()
        admin_edit.setChecked(customer[9])
        self.old_is_admin = customer[9]
        self.ui.edit_customer_info_table.setCellWidget(7, 0, admin_edit)

    def apply_customer_edit(self):
        if self.selected_customer_id is None: return
        try:
            name = self.ui.edit_customer_info_table.item(0, 0).text()
            street = self.ui.edit_customer_info_table.item(1, 0).text()
            city = self.ui.edit_customer_info_table.item(2, 0).text()
            state = self.ui.edit_customer_info_table.item(3, 0).text()
            zip_code = self.ui.edit_customer_info_table.item(4, 0).text()
            dob = self.ui.edit_customer_info_table.cellWidget(5, 0).date().toPyDate()
            gender = self.ui.edit_customer_info_table.cellWidget(6, 0).currentText()
            admin = self.ui.edit_customer_info_table.cellWidget(7, 0).isChecked()

            if not name:
                raise Exception("Name cannot be empty.")
            
            if not street:
                raise Exception("Street cannot be empty.")
            
            if not city:
                raise Exception("City cannot be empty.")
            
            if not state:
                raise Exception("State cannot be empty.")
            
            if not zip_code:
                raise Exception("Zip code cannot be empty.")
            
            if not zip_code.isdigit():
                raise Exception("Zip code must be a numeric value.")
            
            if len(zip_code) != 5:
                raise Exception("Zip code must be 5 digits.")

            if self.old_is_admin != admin:
                msg = "Are you sure you want to change this user's admin privileges?"
                if not confirm_window(msg):
                    return
        except Exception as e:
            error_window(e)
            return
        try:
            self.db_utils.edit_customer_by_id(self.selected_customer_id, name, street, city, state, zip_code, dob, gender, admin)
            success_window("Customer edit successful!")
            self.ui.customer_search_bar.setText(self.selected_customer_email)
            self.search_customer()
        except Exception as e:
            self.ui.customer_search_bar.setText(self.selected_customer_email)
            self.search_customer()
            error_window(e)
            return
        pass

    def open_promo_admin(self):
        self.ui.product_admin_button.setEnabled(True)
        self.ui.user_admin_button.setEnabled(True)
        self.ui.promo_admin_button.setEnabled(False)
        self.ui.admin_widgets.setCurrentIndex(2)
        self.reset_promo_edit()
        pass

    def reset_promo_edit(self):
        self.page = 0
        self.ui.promo_result_table.setRowCount(0)
        self.ui.promo_result_table.setColumnCount(4)
        self.ui.promo_result_table.setHorizontalHeaderLabels(["Code", "Discount Amount", "Expire", "ID"])
        self.ui.promo_result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.promo_result_table.verticalHeader().setVisible(False)
        self.ui.promo_result_table.setColumnWidth(1, 120)
        self.ui.promo_result_table.setColumnWidth(2, 100)
        self.ui.promo_result_table.setColumnHidden(3, True)
        self.ui.promo_result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.load_promos()
        pass

    def load_promos(self):
        self.ui.promo_result_table.setRowCount(0)
        self.ui.promo_next_page_button.setEnabled(True)
        self.ui.promo_prev_page_button.setEnabled(False)

        max_per_page = 20
        promos, total = self.db_utils.get_promos(self.page, max_per_page)
        if total == max_per_page:
            self.max_page = 0
        else:
            self.max_page = total // max_per_page
        
        if self.max_page == 0:
            self.ui.promo_next_page_button.setEnabled(False)

        self.ui.promo_page_count_label.setText(f"Page: {self.page + 1}/{self.max_page + 1}")
        for promo in promos:
            row = self.ui.promo_result_table.rowCount()
            self.ui.promo_result_table.insertRow(row)
            self.ui.promo_result_table.setItem(row, 0, QTableWidgetItem(promo[1]))
            self.ui.promo_result_table.setItem(row, 1, QTableWidgetItem(str(promo[3])))
            expire_promo_button = QPushButton("End this promo")
            expire_promo_button.clicked.connect(self.expire_promo)
            self.ui.promo_result_table.setCellWidget(row, 2, expire_promo_button)
            self.ui.promo_result_table.setItem(row, 3, QTableWidgetItem(str(promo[0])))
        pass

    def expire_promo(self):
        button = self.sender()
        if button:
            msg = "Are you sure you want to expire this promo?"
            if not confirm_window(msg):
                return
            row = self.ui.promo_result_table.indexAt(button.pos()).row()
            promo_id = self.ui.promo_result_table.item(row, 3)
            if promo_id:
                try:
                    self.db_utils.expire_promo(promo_id.text())

                except Exception as e:
                    error_window(e)
                    return
        self.reset_promo_edit()

    def load_prev_promo_page(self):
        self.ui.promo_result_table.setRowCount(0)
        self.page -= 1
        self.load_promos()
        self.ui.promo_next_page_button.setEnabled(True)
        if self.page == 0:
            self.ui.promo_prev_page_button.setEnabled(False)

    def load_next_promo_page(self):
        self.ui.promo_result_table.setRowCount(0)
        self.page += 1
        self.load_promos()
        self.ui.promo_prev_page_button.setEnabled(True)
        if self.page == self.max_page:
            self.ui.promo_next_page_button.setEnabled(False)
    
    def create_promo(self):
        code = self.ui.new_promo_code_input.text()
        discount = self.ui.new_promo_discount_input.text()
        try:
            if not code:
                raise Exception("Code cannot be empty.")
            if not discount:
                raise Exception("Discount cannot be empty.")
            if "." in discount:
                if not discount.replace(".", "", 1).isdigit():
                    raise Exception("Discount must be a valid float value.")
            else:
                if not discount.isdigit():
                    raise Exception("Discount must be a valid float value.")
            if float(discount) > 100:
                raise Exception("Discount cannot be greater than 100%.")
            if float(discount) < 0:
                raise Exception("Discount cannot be less than 0%.")
            self.db_utils.create_promo(code.upper(), discount)
            self.reset_promo_edit()
        except Exception as e:
            error_window(e)
            return
        pass

    def open_product_admin(self):
        self.ui.product_admin_button.setEnabled(False)
        self.ui.admin_widgets.setCurrentIndex(0)
        self.ui.user_admin_button.setEnabled(True)
        self.ui.promo_admin_button.setEnabled(True)
        self.reset_product_edit()
        pass

    def reset_product_edit(self):
        self.page = 0
        self.ui.product_admin_result_table.setRowCount(0)
        self.ui.product_admin_result_table.setColumnCount(5)
        self.ui.product_admin_result_table.setHorizontalHeaderLabels(["Name", "Price($)", "Stock", "Apply", "ID"])
        self.ui.product_admin_result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.product_admin_result_table.verticalHeader().setVisible(False)
        self.ui.product_admin_result_table.setColumnWidth(1, 70)
        self.ui.product_admin_result_table.setColumnWidth(2, 70)
        self.ui.product_admin_result_table.setColumnWidth(3, 120)
        self.ui.product_admin_result_table.setColumnHidden(4, True)
        self.categories = {}
        self.load_categories(self.db_utils.get_categories())
        self.ui.product_admin_search_bar.setText("")
        self.ui.product_admin_category_select.setCurrentIndex(0)
        self.category_id = 0
        self.search_term = ""
        self.load_products()

    def load_categories(self, data):
        all_cat = "- All Categories -"
        self.categories[all_cat] = 0
        self.ui.product_admin_category_select.addItem(all_cat)
        self.ui.new_product_category_select.addItem("- Select a Category -")
        for datum in data:
            self.categories[datum[1]] = datum[0]
            self.ui.product_admin_category_select.addItem(datum[1])
            self.ui.new_product_category_select.addItem(datum[1])

    def do_search(self):
        self.ui.product_admin_result_table.setRowCount(0)
        self.ui.product_next_page_button.setEnabled(True)
        self.ui.product_prev_page_button.setEnabled(False)
        self.page = 0
        self.load_products()

    def load_products(self):
        self.ui.product_admin_result_table.setRowCount(0)
        category_id = self.ui.product_admin_category_select.currentIndex()
        search_term = self.ui.product_admin_search_bar.text()

        if category_id != self.category_id or search_term != self.search_term:
            self.page = 0
        self.category_id = category_id
        self.search_term = search_term

        num_per_page = 19
        if search_term == "":
            products, total = self.db_utils.get_products(category_id, self.page, num_per_page)
        else:
            products, total = self.db_utils.get_products_search(category_id, search_term, self.page, num_per_page)

        if num_per_page == total:
            self.max_page = 0
        else:
            self.max_page = total // num_per_page
        self.ui.product_page_count_label.setText(f"Page: {self.page + 1}/{self.max_page + 1}")

        if self.max_page == 0:
            self.ui.product_next_page_button.setEnabled(False)

        for product in products:
            row = self.ui.product_admin_result_table.rowCount()
            self.ui.product_admin_result_table.insertRow(row)
            self.ui.product_admin_result_table.setItem(row, 0, QTableWidgetItem(product[1]))
            self.ui.product_admin_result_table.item(row, 0).setFlags(Qt.ItemIsEnabled)
            self.ui.product_admin_result_table.setItem(row, 1, QTableWidgetItem(str(product[2])))
            self.ui.product_admin_result_table.setItem(row, 2, QTableWidgetItem(str(product[3])))
            apply_changes_button = QPushButton("Apply Changes")
            apply_changes_button.clicked.connect(self.apply_changes_to_product)
            apply_changes_button.setEnabled(False)
            self.ui.product_admin_result_table.setCellWidget(row, 3, apply_changes_button)
            self.ui.product_admin_result_table.setItem(row, 4, QTableWidgetItem(str(product[0])))
            self.ui.product_admin_result_table.itemChanged.connect(self.product_table_item_changed)

    def load_prev_product_page(self):
        self.ui.product_admin_result_table.setRowCount(0)
        self.page -= 1
        self.load_products()
        self.ui.product_next_page_button.setEnabled(True)
        if self.page == 0:
            self.ui.product_prev_page_button.setEnabled(False)

    def load_next_product_page(self):
        self.ui.product_admin_result_table.setRowCount(0)
        self.page += 1
        self.load_products()
        self.ui.product_prev_page_button.setEnabled(True)
        if self.page == self.max_page:
            self.ui.product_next_page_button.setEnabled(False)

    def apply_changes_to_product(self):
        button = self.sender()
        if button:
            row = self.ui.product_admin_result_table.indexAt(button.pos()).row()
            product_id = self.ui.product_admin_result_table.item(row, 4)
            product_price = self.ui.product_admin_result_table.item(row, 1)
            product_stock = self.ui.product_admin_result_table.item(row, 2)
            if product_id and product_price and product_stock:
                product_id = product_id.text()
                product_price = product_price.text()
                product_stock = product_stock.text()
                if "." in product_price:
                    if not product_price.replace(".", "", 1).isdigit():
                        error_window("Price must be a valid float value.")
                        return
                else:
                    if not product_price.isdigit():
                        error_window("Price must be a valid float value.")
                        return
                if not product_stock.isdigit():
                    error_window("Stock must be a valid integer value.")
                    return
                
                if int(product_stock) < 0:
                    error_window("Stock cannot be less than 0.")
                    return

                try:
                    self.db_utils.edit_product_by_id(product_id, product_price, product_stock)
                    success_window("Product edit successful!")
                except Exception as e:
                    error_window(e)
                    return
            button.setEnabled(False)
    
    def product_table_item_changed(self, item):
        if item.column() == 1 or item.column() == 2:
            row = item.row()
            button = self.ui.product_admin_result_table.cellWidget(row, 3)
            if button:
                button.setEnabled(True)

    def create_product(self):
        try:
            name = self.ui.new_product_name_input.text()
            price = self.ui.new_product_price_input.text()
            stock = self.ui.new_product_stock_input.text()
            category = self.ui.new_product_category_select.currentIndex()

            if not name:
                raise Exception("Name cannot be empty.")
            if not price:
                raise Exception("Price cannot be empty.")
            if "." in price:
                if not price.replace(".", "", 1).isdigit():
                    raise Exception("Price must be a valid float value.")
            else:
                if not price.isdigit():
                    raise Exception("Price must be a valid float value.")
            if not stock:
                raise Exception("Stock cannot be empty.")
            if not stock.isdigit():
                raise Exception("Stock must be a valid integer value.")
            if int(stock) < 0:
                raise Exception("Stock cannot be less than 0.")
            if category == 0:
                raise Exception("Please select a category.")

            self.db_utils.create_product(name, price, stock, category)
            success_window("Product created successfully!")
            self.ui.new_product_name_input.setText("")
            self.ui.new_product_price_input.setText("")
            self.ui.new_product_stock_input.setText("")
            self.ui.new_product_category_select.setCurrentIndex(0)
        except Exception as e:
            error_window(e)
            return
        pass

    def kill_subprocesses(self):
        if self.dashboard_1_process is not None:
            self.dashboard_1_process.kill()
        if self.dashboard_2_process is not None:
            self.dashboard_2_process.kill()
    
    def open_dashboard_1(self):
        self.ui.dashboard_1_button.setEnabled(False)
        self.open_dashboard("rair_analytics_1", "main.py", 1)
    
    def open_dashboard_2(self):
        self.ui.dashboard_2_button.setEnabled(False)
        self.open_dashboard("rair_analytics_2", "Main.py", 2)

    def open_dashboard(self, path, enter_file, process):
        try:
            os.chdir("./" + path)
            args = [sys.executable, enter_file]
            if "--local" in sys.argv:
                args.append("--local")
            if process == 1:
                self.dashboard_1_process = subprocess.Popen(args)
            else:
                self.dashboard_2_process = subprocess.Popen(args)
        except Exception:
            error_window(Exception(f"Dashboard \"{path}\" is not installed."))
        finally:
            if os.name == "nt":
                split_char = "\\"
            else:
                split_char = "/"
            if os.getcwd().split(split_char)[-1] == path:
                os.chdir("..")

    def check_dashboards(self):
        if self.dashboard_1_process is not None and self.dashboard_1_process.poll() is not None and self.ui.dashboard_1_button.isEnabled() is False:
            self.ui.dashboard_1_button.setEnabled(True)
        if self.dashboard_2_process is not None and self.dashboard_2_process.poll() is not None and self.ui.dashboard_2_button.isEnabled() is False:
            self.ui.dashboard_2_button.setEnabled(True)

    def start_admin_gui(self, user: UserData):
        self.user = user
        self.ui.show()

    def perform_etl(self):
        msg = "This will reset all the data in the Data Warehouse\nThis will also close any dashboard windows open\nAre you sure you want to do this?"
        if confirm_window(msg):
            try:
                waiting_to_complete_dialog = QProgressDialog()
                waiting_to_complete_dialog.setWindowTitle("Please Wait")
                waiting_to_complete_dialog.setCancelButton(None)
                waiting_to_complete_dialog.show()
                self.kill_subprocesses()
                self.wh_utils.perform_etl()
                waiting_to_complete_dialog.accept()
                success_window("ETL completed successfully!")
            except Exception as e:
                error_window(e)

