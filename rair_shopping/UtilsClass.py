import os
from configparser import ConfigParser
from mysql.connector.errors import IntegrityError
from mysql.connector import MySQLConnection, Error
from rair_shopping.CartData import CartData
from rair_shopping.UserData import UserData
from PyQt5.QtWidgets import QMessageBox

def ensure_connection(func):
    def wrapper(self, *args, **kwargs):
        if self.conn is None or self.cursor is None or not self.conn.is_connected():
            error_window(Exception("Connection to database lost! Attempting to reconnect..."))
            try:
                self.make_connection(self.ini_file, self.config_header)
            except Exception:
                error_window(Exception("Reconnection failed! Application will now close.\nPlease try again later."))
        return func(self, *args, **kwargs)
    return wrapper

class MySQLUtils():
    def __init__(self, ini_file, config_header):
        self.ini_file = ini_file
        self.config_header = config_header
        self.conn = None
        self.cursor = None
        self.make_connection(self.ini_file, self.config_header)

    def make_connection(self, ini_file, config_header):
        try:
            parser = ConfigParser()
            if os.path.isfile(ini_file):
                parser.read(ini_file)
            else:
                raise Exception(f"Configuration file '{ini_file}' doesn't exist.")
            db_config = {}
            if parser.has_section(config_header):
                items = parser.items(config_header)
                for item in items:
                    db_config[item[0]] = item[1]
            else:
                raise Exception(f'Section [{config_header}] missing in config file {ini_file}')
            conn = MySQLConnection(**db_config)

            if conn.is_connected():
                self.conn = conn
                self.cursor = self.conn.cursor()

        except Error as e:
            error_window(Exception("Connection failed! Application will now close.\nPlease try again later."))
            raise Exception(f'Connection failed: {e}')

    def __del__(self):
        if self.cursor is not None:
            self.cursor.close()
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()

class DBUtils(MySQLUtils):
    def __init__(self, ini_file, config_header):
        super().__init__(ini_file, config_header)

    @ensure_connection
    def login(self, email, password):
        self.cursor.callproc("CheckLoginCredentials", [email, password])
        result = self.cursor.stored_results().__next__().fetchone()
        if result is not None:
            return result
        else:
            raise Exception("Wrong password or email!")

    @ensure_connection
    def register(self, email, password, name, street, city, state, zip_code, dob, gender):
        try:
            result = self.cursor.callproc("NewUserRecord", [email, password, name, street, city, state, zip_code, dob, gender, 0, 0])
            if result[-2] == 1:
                self.conn.commit()
                return result[-1], email, name, street, city, state, zip_code, dob, gender
            else:
                raise Exception("A user with that email already exists! Try loging in.")
        except IntegrityError:
            raise Exception("A user with that email already exists! Try loging in.")

    @ensure_connection
    def get_categories(self):
        self.cursor.callproc("get_categories")
        result = self.cursor.stored_results().__next__().fetchall()
        return result

    @ensure_connection
    def get_products(self, category_id, page, num_per_page):
        product_count = self.cursor.callproc("get_products", [page, num_per_page, category_id, 0])
        result = self.cursor.stored_results().__next__().fetchall()
        return result, product_count[3]

    @ensure_connection
    def get_products_search(self, category_id, search_term, page, num_per_page):
        product_count = self.cursor.callproc("product_search", [page, num_per_page, category_id, search_term, 0])
        result = self.cursor.stored_results().__next__().fetchall()
        return result, product_count[4]

    @ensure_connection
    def check_promo(self, promo_code):
        self.cursor.callproc("check_promo_validity", [promo_code])
        result = self.cursor.stored_results().__next__().fetchone()
        if result is not None:
            return result
        else:
            raise Exception("Invalid promo code!")

    @ensure_connection
    def expire_promo(self, promo_code_id):
        self.cursor.callproc("expire_promo_by_id", [promo_code_id])
        self.conn.commit()

    @ensure_connection
    def get_promos(self, page, num_per_page):
        promo_count = self.cursor.callproc("get_promos", [page, num_per_page, 0])
        result = self.cursor.stored_results().__next__().fetchall()
        return result, promo_count[-1]

    @ensure_connection
    def create_promo(self, promo_code, discount):
        try:
            result = self.cursor.callproc("add_promo", [promo_code, discount, 0])
            self.conn.commit()
            if result[-1] == 0:
                raise Exception("Promo code already exists!")
        except Exception as e:
            raise Exception(f'Create promo failed: {e}')

    @ensure_connection
    def checkout(self, user: UserData, cart: CartData):
        self.conn.commit()
        self.conn.start_transaction()
        total = cart.calculate_grand_total()
        promo_code_id = cart.promo_code_id
        result = self.cursor.callproc("place_order", [total, user.street, user.city, user.state, user.zip_code, user.user_id, promo_code_id, 0])
        order_id = result[-1]
        for id, product in cart.get_items():
            self.cursor.callproc("add_order_item", [product["qty"], order_id, id])
            self.cursor.callproc("decrease_stock", [id, product["qty"]])
            _ = self.cursor.stored_results()
        self.conn.commit()
        
    @ensure_connection
    def get_order_history(self, user_id, page, num_per_page):
        order_count = self.cursor.callproc("order_history", [user_id, page, num_per_page, 0])
        result = self.cursor.stored_results().__next__().fetchall()
        return result, order_count[-1]

    @ensure_connection
    def get_order_details(self, order_id):
        self.cursor.callproc("order_details", [order_id])
        data = self.cursor.stored_results().__next__().fetchall()
        return data 

    @ensure_connection
    def change_address(self, user_id, street, city, state, zip_code):
        try:
            self.conn.commit()
            self.conn.start_transaction()
            self.cursor.callproc("change_address", [user_id, street, city, state, zip_code])
            self.conn.commit()
            result = self.cursor.stored_results().__next__().fetchone()
            if result is not None:
                return result
        except Exception as e:
            self.conn.rollback()
            raise Exception(f'Change address failed: {e}')
        
    @ensure_connection
    def get_customer_by_email(self, email):
        self.cursor.callproc("get_customer_by_email", [email])
        result = self.cursor.stored_results().__next__().fetchone()
        if result is not None:
            return result
        else:
            raise Exception("No customer with that email!")
            
    @ensure_connection
    def edit_customer_by_id(self, id, name, street, city, state, zip_code, dob, gender, admin):
        try:
            self.conn.commit()
            self.conn.start_transaction()
            self.cursor.callproc("edit_customer_by_id", [id, name, street, city, state, zip_code, dob, gender, admin])
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise Exception(f'Edit customer failed: {e}')
    
    @ensure_connection
    def edit_product_by_id(self, id, price, stock):
        try:
            self.conn.commit()
            self.conn.start_transaction()
            self.cursor.callproc("edit_product_by_id", [id, price, stock])
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise Exception(f'Edit product failed: {e}')

    @ensure_connection
    def create_product(self, name, price, stock, category):
        try:
            self.conn.commit()
            self.conn.start_transaction()
            self.cursor.callproc("add_new_product", [name, price, stock, category])
            self.conn.commit()
        except IntegrityError:
            self.conn.rollback()
            raise Exception("A product with that name already exists!")
        except Exception as e:
            self.conn.rollback()
            raise Exception(f'Create product failed: {e}')

class WHUtils(MySQLUtils):
    def __init__(self, ini_file, config_header):
        super().__init__(ini_file, config_header)

    @ensure_connection
    def perform_etl(self):
        try:
            self.conn.start_transaction()
            self.cursor.callproc("perform_etl")
            _ = self.cursor.stored_results()
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise Exception(f'ETL failed: {e}')

def error_window(e: Exception):
    msg = QMessageBox()
    msg.setWindowTitle("ERROR")
    msg.setText(e.__str__())
    msg.exec_()

def confirm_window(message_string: str):
    msg = QMessageBox()
    msg.setWindowTitle("Confirm")
    msg.setText(message_string)
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.Yes)
    return msg.exec_() == QMessageBox.Yes

def success_window(message_string: str):
    msg = QMessageBox()
    msg.setWindowTitle("Success")
    msg.setText(message_string)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setDefaultButton(QMessageBox.Ok)
    msg.exec_()