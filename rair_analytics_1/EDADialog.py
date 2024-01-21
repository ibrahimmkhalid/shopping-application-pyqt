import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QApplication, QVBoxLayout
from DATA225utils import make_connection
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.optimize import curve_fit
import numpy as np
import statsmodels.api as sm

wh_config = "local_wh" if "--local" in sys.argv else "rairdata_wh"
config_path = "../config.ini"

class EDADialog(QDialog):
    '''
    The EDA dialog
    '''
    
    def __init__(self):
        """
        Load the UI and initialize its components.
        """
        super().__init__()
        
        # Load the dialog components.
        self.ui = uic.loadUi('eda_1.ui')
        self.ui.pushButton1.clicked.connect(self.select_data1)
        self.ui.pushButton2.clicked.connect(self.select_data2)
        self.ui.pushButton3.clicked.connect(self.select_data3)
        self.ui.pushButton4.clicked.connect(self.select_data4)
        
        # Initialize a figure and axis for plotting
        #self.figure = Figure(figsize=(8,8))
        #self.ax = self.figure.add_subplot()

    def select_data1(self):
        conn = make_connection(config_path, wh_config)
        cursor = conn.cursor()
        
        sql = ("SELECT gender, COUNT(*) AS Count FROM dim_customer_demographics GROUP BY gender")
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        df = pd.DataFrame(rows, columns=['gender', 'COUNT'])
        labels = df['gender'].tolist()
        counts = df['COUNT'].tolist()
        
        self.figure = Figure(figsize=(8,8))
        self.ax = self.figure.add_subplot()
        
        
        self.ax.clear()

        # Plotting a pie chart using Matplotlib
        self.ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=140)
        self.ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        self.ax.set_title('Customer Demographics Distribution')

        # Create a canvas for the figure
        canvas = FigureCanvas(self.figure)

        # Show the canvas in a dialog window
        dialog = MyDialog(canvas)
        dialog.exec_()
        
        
    def select_data2(self):
        conn = make_connection(config_path, wh_config)
        cursor = conn.cursor()
        
        sql = ("""SELECT 
                d.day_of_week,
                SUM(o.final_order_sale_amount) AS total_sales
                FROM dim_datetime d
                JOIN fct_order_and_order_items o ON d.datetime_key = o.datetime_key
                GROUP BY d.day_of_week
                ORDER BY CASE 
                    WHEN d.day_of_week = 'Monday' THEN 1
                    WHEN d.day_of_week = 'Tuesday' THEN 2
                    WHEN d.day_of_week = 'Wednesday' THEN 3
                    WHEN d.day_of_week = 'Thursday' THEN 4
                    WHEN d.day_of_week = 'Friday' THEN 5
                    WHEN d.day_of_week = 'Saturday' THEN 6
                    WHEN d.day_of_week = 'Sunday' THEN 7
                    ELSE 8 END""")
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
       
        df = pd.DataFrame(rows, columns=['day_of_week', 'total_sales'])
        labels = df.iloc[0:,0].tolist()
        counts = df.iloc[0:,1].tolist()
        
        self.figure = Figure(figsize=(8,8))
        self.ax = self.figure.add_subplot()
        
        
        self.ax.clear()


        # Plotting a pie chart using Matplotlib
        self.ax.plot(labels, counts, marker='o', color='skyblue', linewidth=2, markersize=8)
        self.ax.bar(labels, counts, color='skyblue')
        self.ax.set_xlabel('Day of the Week')
        self.ax.set_ylabel('Total Sales')
        self.ax.set_title('Total Sales per Day of the Week')
        for tick in self.ax.get_xticklabels():
            tick.set_rotation(45)
        #self.ax.set_xticks(labels, rotation=45)  # Set x-axis ticks for each hour (0-23)
        
        # Adding labels on data points
        for i, txt in enumerate(counts):
            self.ax.annotate(int(txt), (labels[i], counts[i]), textcoords="offset points", xytext=(0,10), ha='center')

        # Create a canvas for the figure
        canvas = FigureCanvas(self.figure)

        # Show the canvas in a dialog window
        dialog = MyDialog(canvas)
        dialog.exec_()    
 


    # Function for ARIMA time series analysis
    def select_data3(self, sender=None, event=None):
        # Assuming SQLite database and sqlite3 connector
        conn = make_connection(config_path, wh_config)
        cursor = conn.cursor()
    
        sql = ("""SELECT d.hour AS HourOfDay, COUNT(*) AS OrderCount
            FROM fct_order_and_order_items o
            JOIN dim_datetime d ON o.datetime_key = d.datetime_key
            GROUP BY d.hour
            ORDER BY d.hour""")
    
        cursor.execute(sql)
        rows = cursor.fetchall()
    
        cursor.close()
        conn.close()
  
        df = pd.DataFrame(rows, columns=['HourOfDay', 'OrderCount'])
        labels = df['HourOfDay'].tolist()
        counts = df['OrderCount'].tolist()

        self.figure = Figure(figsize=(8,8))
        self.ax = self.figure.add_subplot()
   
        # Perform ARIMA time series analysis
        model = sm.tsa.ARIMA(df['OrderCount'], order=(1, 1, 1))  # Example order, adjust as needed
        results = model.fit()

        # Forecast
        forecast = results.predict(start=0, end=len(df))  # Example forecast range, adjust as needed


        self.ax.plot(df.index, df['OrderCount'], label='Original Order Count',)
        self.ax.plot(forecast.index, forecast, linestyle='--', color='red', label = 'ARIMA Time Series Forecast')
        self.ax.set_xlabel('Hour of the Day')
        self.ax.set_ylabel('Order Count')
        self.ax.set_title('Order Count by Hour of the Day')
        self.ax.set_xticks(range(24))  # Set x-axis ticks for each hour (0-23)
        self.ax.legend()
    
        # Create a canvas for the figure
        canvas = FigureCanvas(self.figure)
    
        # Show the canvas in a dialog window
        dialog = MyDialog(canvas)
        dialog.exec_()
    
    
    def select_data4(self):
        conn = make_connection(config_path, wh_config)
        cursor = conn.cursor()
        
        sql = ("""SELECT cd.gender AS Gender, COUNT(fp.promo_code_used) AS PromoCodeUsage
                FROM fct_promotions fp
                JOIN dim_customer_demographics cd ON fp.customer_demographic_key = cd.customer_demographic_key
                GROUP BY cd.gender""")
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        df = pd.DataFrame(rows, columns=['Gender', 'PromoCodeUsage'])
        labels = df['Gender'].tolist()
        counts = df['PromoCodeUsage'].tolist()
        
        self.figure = Figure(figsize=(8,8))
        self.ax = self.figure.add_subplot()
        
        
        self.ax.clear()

        # Plotting a pie chart using Matplotlib
        self.ax.pie(counts, labels = labels, autopct='%1.1f%%', startangle=120, colors=['lightblue', 'lightcoral'])
        self.ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        self.ax.set_title('Distribution of Promo Code Usage by Gender')

        # Create a canvas for the figure
        canvas = FigureCanvas(self.figure)

        # Show the canvas in a dialog window
        dialog = MyDialog(canvas)
        dialog.exec_()
        
    
    
    
    def show_dialog(self):
        """
        Show this dialog.
        """
        self.ui.show()

# Create a QDialog to embed the canvas
class MyDialog(QDialog):
    def __init__(self, canvas):
        super().__init__()

        # Create layout
        layout = QVBoxLayout(self)

        # Embed Matplotlib canvas into layout
        layout.addWidget(canvas)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = EDADialog()
    form.show_dialog()
    sys.exit(app.exec_())
