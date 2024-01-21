import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QApplication, QTableWidgetItem, QComboBox
from DATA225utils import make_connection

wh_config = "local_wh" if "--local" in sys.argv else "rairdata_wh"
config_path = "../config.ini"

class TabDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('selectUpdate.ui')
        self.ui.comboBox.currentIndexChanged.connect(self.clear_table)
        self.ui.pushButton.clicked.connect(self.populate_table)
        self.populate_combo_box()

    def populate_combo_box(self):
        geek_list = ["dim_products", "dim_customer_locations", "dim_customer_demographics",
                     "fct_promotions", "dim_datetime", "fct_order_and_order_items"]
        self.ui.comboBox.addItems(geek_list)

    def clear_table(self):
        self.ui.tableWidget.clear()

    def populate_table(self):
        #self.clear_table()  # Clear table before populating with new data

        tablename = self.ui.comboBox.currentText()

        conn = make_connection(config_path, wh_config)
        cursor = conn.cursor()
        
        sql = "SELECT * FROM {}".format(tablename)
        cursor.execute(sql)
        rows = cursor.fetchall()
        table_columns = {
            'dim_products': ['product_key', 'name', 'price', 'category'],
            'dim_customer_locations': ['customer_location_key', 'street', 'city', 'state', 'zip'],
            'dim_customer_demographics': ['customer_demographic_key', 'gender', 'age_group'],
            'fct_promotions': ['datetime_key', 'customer_demographic_key', 'dollar_discounted_amount', 'promo_code_used'],
            'dim_datetime': ['datetime_key', 'full_date', 'day_of_week', 'day_of_month', 'quarter', 'year', 'month', 'hour', 'minute'],
            'fct_order_and_order_items': ['final_order_sale_amount', 'number_of_items_in_order', 'quantity_of_order_item', 'order_id', 'final_order_cost', 'datetime_key', 'product_key', 'customer_location_key', 'customer_demographic_key']
        }

        column_names = table_columns.get(tablename, [])
        self.ui.tableWidget.setColumnCount(len(column_names))
        self.ui.tableWidget.setHorizontalHeaderLabels(column_names)

        self.ui.tableWidget.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column_index, data in enumerate(row):
                item = QTableWidgetItem(str(data))
                self.ui.tableWidget.setItem(row_index, column_index, item)

        cursor.close()
        conn.close()

    def show_dialog(self):
        """
        Show this dialog.
        """
        self.ui.show()  
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = TabDialog()
    form.show_dialog()
    sys.exit(app.exec_()) 

