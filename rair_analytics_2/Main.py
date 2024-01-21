import sys
from PyQt5 import QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QGraphicsScene
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objs as go
import plotly.io as pio
from DATA225utils import make_connection, dataframe_query
from Mainwindow import Ui_MainWindow

wh_config = "local_wh" if "--local" in sys.argv else "rairdata_wh"
config_path = "../config.ini"

class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setMinimumSize(800, 600)

        # Connect the button click to the slot
        self.avgPricePushButton.clicked.connect(self.show_avg_price_page)
        self.TotalSalesPushButton.clicked.connect(self.show_TotalSales_page)
        self.NbCategoryPushButton.clicked.connect(self.show_NbCategory_Page)
        self.AgeGroupButton.clicked.connect(self.show_AgeGroupView_Page)
        self.GenderButton.clicked.connect(self.show_GenderView_Page)
        self.LocationButton.clicked.connect(self.show_LocationView_page)

        # Initialize the Average Price page
        self.init_avg_price_page()
        
        # Initialize the Total Sales page
        self.init_TotalSales_page()

        self.init_PieChart_page()

        # Set the default page to Average Price
        self.first_dashboard_page()

    def first_dashboard_page(self):
        self.stackedWidget.setCurrentIndex(0)

    def init_avg_price_page(self):
        # Assuming you have a QStackedWidget named stackedWidget
        # and the page index for Average Price is 0
        self.stackedWidget.setCurrentIndex(1)

        # Create a QListWidget for categories
        self.category_list_widget = self.CategoryList
        self.category_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.category_list_widget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        categories = ['Automotive', 'Baby Care', 'Bags, Wallets & Belts',
                        'Beauty and Personal Care', 'Cameras & Accessories', 'Clothing',
                        'Computers', 'Footwear', 'Furniture', 'Home Decor & Festive Needs',
                        'Home Furnishing', 'Home Improvement', 'Jewellery',
                        'Kitchen & Dining', 'Mobiles & Accessories', 'Pens & Stationery',
                        'Sports & Fitness', 'Tools & Hardware', 'Toys & School Supplies',
                        'Watches']
        self.category_list_widget.addItems(categories)

        # Create a QPushButton for updating the plot
        update_button = self.selectButton
        update_button.clicked.connect(self.AveragePriceBar)

        # Create Matplotlib figure and canvas for the plot
        self.avg_price_figure, self.avg_price_ax = plt.subplots(figsize=(12, 6))
        self.avg_price_canvas = FigureCanvas(self.avg_price_figure)

        # Embed Matplotlib canvas into QGraphicsView
        layout = QtWidgets.QVBoxLayout(self.AvgPriceChartView)
        layout.addWidget(self.avg_price_canvas)

    def AveragePriceBar(self):
        # Get the selected categories from the list widget
        selected_categories = [item.text() for item in self.category_list_widget.selectedItems()]

        if not selected_categories:
            print("Please select at least one category.")
            return

        # Construct SQL query with the selected categories
        categories_str = ', '.join([f"'{category}'" for category in selected_categories])
        sql_query = f"""
            SELECT category, AVG(price) as 'Average Price'
            FROM dim_products
            WHERE category IN ({categories_str})
            GROUP BY category
        """

        # Replace with your database connection logic
        conn = make_connection(config_path, wh_config)
        _, df = dataframe_query(conn, sql_query)
        conn.close()

        # Clear existing plot
        self.avg_price_ax.clear()

        # Set the style for Seaborn
        sns.set(style="whitegrid")

        # Create a bar plot using Seaborn with custom colors
        bar_plot = sns.barplot(x='category', y='Average Price', data=df, palette=['#2b2b2b'], ax=self.avg_price_ax)

        # Set background color
        self.AvgPriceChartView.setStyleSheet("background-color: #c06c84; border-radius: 8px; border: none;")

        # Set x-axis and y-axis labels
        self.avg_price_ax.set(xlabel='Category', ylabel='Average Price', title='Average Price for Each Category')

        # Rotate x-axis tick labels
        bar_plot.set_xticklabels(bar_plot.get_xticklabels(), rotation=45, horizontalalignment='right')

        # Customize grid and ticks
        self.avg_price_ax.grid(True, linestyle='--', alpha=0.7)

        # Customize y-axis formatter
        self.avg_price_ax.yaxis.set_major_formatter('${x:,.0f}')

        # Customize legend
        self.avg_price_ax.legend(['Average Price'], loc='upper left')

        # Redraw the canvas
        self.avg_price_figure.tight_layout()
        self.avg_price_canvas.draw()

    def init_TotalSales_page(self):
        self.stackedWidget.setCurrentIndex(2)

        # Connect radio buttons to the slot
        self.YearButton.toggled.connect(lambda: self.update_total_sales_chart('year'))
        self.QuarterButton.toggled.connect(lambda: self.update_total_sales_chart('quarter'))
        self.MonthButton.toggled.connect(lambda: self.update_total_sales_chart('month'))

        # Create Matplotlib figure and canvas for the plot
        self.total_sales_figure, self.total_sales_ax = plt.subplots(figsize=(12, 6))
        self.total_sales_canvas = FigureCanvas(self.total_sales_figure)

        layout = QtWidgets.QVBoxLayout(self.TotalSalesView)
        layout.addWidget(self.total_sales_canvas)

        # Initial chart with default date as 'year'
        # self.update_total_sales_chart('year')

    def update_total_sales_chart(self, date):
        # Construct SQL query with the selected date
        sql_query = f"""
            SELECT SUM(f.final_order_sale_amount) as 'Total Sales Amount', d.{date}
            FROM fct_order_and_order_items f
            join dim_datetime d on d.datetime_key = f.datetime_key
            GROUP BY d.{date}
            {'ORDER BY d.' + date if date != 'month' else "ORDER BY FIELD(d.month, 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December')"}
        """

        # Replace with your database connection logic
        conn = make_connection(config_path, wh_config)
        _, df = dataframe_query(conn, sql_query)
        conn.close()

        # Clear existing plot
        self.total_sales_ax.clear()

        # Set the style for Seaborn
        sns.set(style="whitegrid")

        # Create a line plot using Seaborn with added styling
        line_plot = sns.lineplot(x=date, y='Total Sales Amount', data=df, color='#2b2b2b', marker='o', markersize=8, linewidth=2, ax=self.total_sales_ax)

        # Set title and labels
        line_plot.set(xlabel=date, ylabel='Total Sales Amount', title=f'Total Sales Amount for each {date}')

        # Customize grid and ticks
        self.total_sales_ax.grid(True, linestyle='--', alpha=0.7)
        # self.total_sales_ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=10))
        self.total_sales_ax.yaxis.set_major_formatter('${x:,.0f}')

        # Customize legend
        self.total_sales_ax.legend(['Total Sales'], loc='upper left')

        # Redraw the canvas
        self.total_sales_figure.tight_layout()
        self.total_sales_canvas.draw()

    def init_PieChart_page(self):
        self.stackedWidget.setCurrentIndex(4)
        self.update_pie_chart_in_page()

    def update_pie_chart_in_page(self):
            # Your data retrieval logic here
        sql_query = """
            SELECT cd.age_group AS AgeGroup, SUM(o.final_order_sale_amount) AS TotalSales 
            FROM fct_order_and_order_items o JOIN dim_customer_demographics cd ON o.customer_demographic_key = cd.customer_demographic_key 
            GROUP BY cd.age_group
        """
        conn = make_connection(config_path, wh_config)
        _, df = dataframe_query(conn, sql_query)
        conn.close()

            # Calculate percentage
        df['Percentage'] = (df['TotalSales'] / df['TotalSales'].sum()) * 100

        # Sort the dataframe by TotalSales in descending order
        df = df.sort_values(by='TotalSales', ascending=False)

        # Create a pie chart using Plotly
        fig = go.Figure(data=[go.Pie(labels=df['AgeGroup'], values=df['TotalSales'], hole=0.3)])
        # Update layout for better aesthetics
        fig.update_traces(textinfo='percent+label', pull=[0.1] + [0] * (len(df) - 1), textposition='inside', showlegend=False)
        fig.update_layout(title_text='Total Sales Percentage by Age Group')
        
        # Convert Plotly figure to an image
        img_bytes = pio.to_image(fig, format='png', width=800, height=600)
        img = QImage.fromData(img_bytes)

        # Convert QImage to QPixmap
        pixmap = QPixmap.fromImage(img)

        # Display the QPixmap in the QGraphicsView
        scene = QGraphicsScene()
        scene.addPixmap(pixmap)
        self.AgeGroupView.setScene(scene)

    def show_avg_price_page(self):
        # Assuming you have a QStackedWidget named stackedWidget
        # and the page index for Average Price is 0
        self.stackedWidget.setCurrentIndex(1)

    def show_TotalSales_page(self):
        self.stackedWidget.setCurrentIndex(2)

    def show_NbCategory_Page(self):
        self.stackedWidget.setCurrentIndex(3)

    def show_AgeGroupView_Page(self):
        self.stackedWidget_2.setCurrentIndex(0)
    
    def show_GenderView_Page(self):
        self.stackedWidget_2.setCurrentIndex(1)

        sql_query = """
        SELECT gender as Gender, COUNT(*) AS Count FROM dim_customer_demographics GROUP BY gender
        """

        conn = make_connection(config_path, wh_config)
        _, df = dataframe_query(conn, sql_query)
        conn.close()

        df['Percentage'] = (df['Count'] / df['Count'].sum()) * 100
        df = df.sort_values(by='Count', ascending=False)

        fig = go.Figure(data=[go.Pie(labels=df['Gender'], values=df['Count'], hole=0.3)])
        fig.update_traces(textinfo='percent+label', textposition='inside', showlegend=False)
        fig.update_layout(title_text='Percentage of Customer Gender Distribution')

        img_bytes = pio.to_image(fig, format='png', width=800, height=600)
        img = QImage.fromData(img_bytes)

        pixmap = QPixmap.fromImage(img)
        scene = QGraphicsScene()
        scene.addPixmap(pixmap)
        self.GenderView.setScene(scene)

    def show_LocationView_page(self):
        self.stackedWidget_2.setCurrentIndex(2)

        sql_query = """
            Select state as State, count(*) as Count
            From dim_customer_locations Group By state"""

        conn = make_connection(config_path, wh_config)
        _, df = dataframe_query(conn, sql_query)
        conn.close()

        # Create a new Figure and Axes for the pie chart
        # Calculate percentage
        df['Percentage'] = (df['Count'] / df['Count'].sum()) * 100

        # Sort the dataframe by Count in descending order
        df = df.sort_values(by='Count', ascending=False)

        # Create a pie chart using Plotly
        fig = go.Figure(data=[go.Pie(labels=df['State'], values=df['Count'], hole=0.3)])

        # Update layout for better aesthetics
        fig.update_traces(textinfo='percent+label', pull=[0.1] + [0] * (len(df) - 1), textposition='inside', showlegend=False)
        fig.update_layout(title_text='Percentage of Customer Location Distribution')

        # Convert Plotly figure to an image
        img_bytes = pio.to_image(fig, format='png', width=800, height=600)
        img = QImage.fromData(img_bytes)

        # Convert QImage to QPixmap
        pixmap = QPixmap.fromImage(img)

     # Display the QPixmap in the QGraphicsView
        scene = QGraphicsScene()
        scene.addPixmap(pixmap)
        self.LocationView.setScene(scene)


def main():
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show() 
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
