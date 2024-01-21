import os
import random
import pandas as pd
from datetime import datetime
from configparser import ConfigParser
from mysql.connector import MySQLConnection, Error

# Edit these as desired
LOCAL = True
random.seed(42)
min_orders = 1000
max_orders = 3000
max_items_per_order = 10
max_qty_per_item = 5

def make_connection(config_file = 'config.ini', section = 'mysql'):
    parser = ConfigParser()
    parser.read(config_file)
    config = {}
    items = parser.items(section)
    for item in items:
        config[item[0]] = item[1]
    try:
        conn = MySQLConnection(**config)
        if conn.is_connected():
            return conn
    except Error as e:
        raise Exception(f'Connection failed: {e}')

ini_file = "config.ini"
db_conf = 'local_db' if LOCAL else 'rairdata_db'
wh_conf = 'local_wh' if LOCAL else 'rairdata_wh'

if not os.path.isfile(ini_file):
    print("Missing config file. Create config file from template 'config.ini.tmp'")
    exit()

print("Generating data...")

# initial tables generated from mockaroo
users = pd.read_csv("./data/users_mock.csv")
promo_codes = pd.read_csv("./data/promo_codes_mock.csv")
# datasource: https://www.kaggle.com/datasets/PromptCloudHQ/flipkart-products

products = pd.read_csv("./data/flipkart_com-ecommerce_sample.csv")
users["is_admin"] = False

users.loc[len(users)] = { 'id': len(users)+1, 'email': 'user@rair.com', 'password': '12345678',
                        'name': 'Sample User', 'street': '1234 Apple Street', 'city': 'San Jose',
                        'state': 'California', 'zip': '94088', 'date_of_birth': '2000-01-01', 'gender': 'Male', 'is_admin': False }

users.loc[len(users)] = { 'id': len(users)+1, 'email': 'admin@rair.com', 'password': '12345678',
                        'name': 'Sample Admin', 'street': '1235 Apple Street', 'city': 'San Jose',
                        'state': 'California', 'zip': '94088', 'date_of_birth': '2000-01-01', 'gender': 'Male', 'is_admin': True }

promo_codes["id"] = promo_codes.index + 1
promo_codes = promo_codes[["id", "code", "expired", "discount"]]
for x in promo_codes["code"].value_counts().index.to_list():
    promo_x = promo_codes.loc[promo_codes["code"] == x]
    promo_codes.loc[promo_x.index, "expired"] = 1
    promo_codes.loc[promo_x.index[-1], "expired"] = 0

products = products[["product_name","product_category_tree", "retail_price", "description" ]]
products["category"] = products["product_category_tree"].apply(lambda x: x.split(">>")[0].strip()[2:])
products["stock"] = products["product_name"].apply(lambda x: random.randint(0,10*len(x)))
products = products[["product_name", "retail_price", "description", "category", "stock"]]
products = products.drop_duplicates(subset="product_name", keep="first")
products = products[products["product_name"].apply(lambda x: x.isascii())]
products = products[~products["product_name"].str.lower().duplicated(keep="first")]
products = products.loc[products["product_name"].str.len() < 120]

categories = products.groupby('category').size().reset_index(name='count').sort_values(by='count', ascending=False)
categories = categories[categories['count'] > 50][['category']].reset_index(drop=True)
categories['id'] = categories.index + 1
categories.columns = ['name', 'id']
categories = categories[["id", "name"]]
products = (
    products.set_index("category")
            .join(categories.set_index("name"))
            .reset_index()
            .dropna()
            .reset_index(drop=True)
            [["product_name", "retail_price", "stock", "id"]]
            .rename(columns={"product_name": "name", "retail_price": "price", "id": "category_id"})
)

products["id"] = products.index + 1
products = products[["id", "name", "price", "stock", "category_id"]]
products["price"] = products["price"] * 0.02
order_entries = random.randint(min_orders, max_orders)
orders = pd.DataFrame([], columns=["id", "datetime", "total", "street", "city", "state", "zip", "user_id", "promo_code_id"])
order_items = pd.DataFrame([], columns=["id", "order_id", "product_id", "qty"])
orders_idx = 0
order_items_idx = 0
dt = datetime(1971,1,1)
for j in range(order_entries):
    orders_idx += 1
    user_id = random.randint(1,len(users))
    user = users.loc[users["id"] == user_id].values[0]
    total = 0
    for i in range(random.randint(1,max_items_per_order)):
        order_items_idx += 1
        product_id = random.randint(1, len(products))
        qty = random.randint(1,max_qty_per_item)
        product = products.loc[products["id"] == product_id]
        price = product["price"].values[0]
        total += price * qty
        order_items.loc[len(order_items)] = {
            "id": order_items_idx,
            "order_id": orders_idx,
            "product_id": product_id,
            "qty": qty
        }
    dt = dt.fromtimestamp(dt.timestamp() + random.randint(100,59999))
    is_promo = True if random.randint(1,5) == 5 else False
    promo = None
    if is_promo:
        promo_id = random.randint(1,len(promo_codes))
        promo = promo_codes.loc[promo_codes["id"] == promo_id].values[0]
        total = total - (total * (promo[3]/100))
    orders.loc[len(orders)] = {
        "id": orders_idx,
        "datetime": dt.isoformat(),
        "total": total,
        "street": user[4],
        "city": user[5],
        "state": user[6],
        "zip": user[7],
        "user_id": user_id,
        "promo_code_id": promo[0] if is_promo else None
    }
latest_datetime = pd.to_datetime(orders['datetime']).max()
day_difference = (datetime.now() - latest_datetime).days - 1
orders['datetime'] = pd.to_datetime(orders['datetime']) + pd.to_timedelta(day_difference, unit='D')
orders['datetime'] = orders['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
users['date_of_birth'] = pd.to_datetime(users['date_of_birth']).dt.strftime('%Y-%m-%d')

print("(Re)-uploading data to database...")

conn = make_connection(ini_file, db_conf)
cursor = conn.cursor()

cursor.execute("drop table if exists order_items")
cursor.execute("drop table if exists products")
cursor.execute("drop table if exists categories")
cursor.execute("drop table if exists orders")
cursor.execute("drop table if exists users")
cursor.execute("drop table if exists promo_codes")

cursor.execute("""
create table users
  (
     id            int not null auto_increment,
     email         varchar(120) not null unique,
     password      varchar(120) not null,
     name          varchar(120) not null,
     street        varchar(120) not null,
     city          varchar(120) not null,
     state         varchar(120) not null,
     zip           varchar(5) not null,
     date_of_birth datetime not null,
     gender        varchar(20) not null,
     is_admin      boolean not null default false,
     primary key (id)
  ); 
""")

cursor.execute("""
create table categories
  (
     id   int not null auto_increment,
     name varchar(120) not null,
     primary key (id)
  ); 
""")

cursor.execute("""
create table promo_codes
  (
     id       int not null auto_increment,
     code     varchar(120) not null,
     expired  boolean not null,
     discount float not null,
     primary key (id)
  ); 
""")

cursor.execute("""
create table products
  (
     id          int not null auto_increment,
     name        varchar(120) not null unique,
     price       float not null,
     stock       int not null,
     category_id int not null,
     primary key (id),
     foreign key (category_id) references categories(id)
  ); 
""")

cursor.execute("""
create table orders
  (
     id            int not null auto_increment,
     datetime      datetime not null,
     total         float not null,
     street        varchar(120) not null,
     city          varchar(120) not null,
     state         varchar(120) not null,
     zip           varchar(5) not null,
     user_id       int not null,
     promo_code_id int,
     primary key (id),
     foreign key (user_id) references users(id),
     foreign key (promo_code_id) references promo_codes(id)
  );
""")

cursor.execute("""
create table order_items
  (
     id         int not null auto_increment,
     qty        int not null,
     order_id   int not null,
     product_id int not null,
     primary key (id),
     foreign key (order_id) references orders(id),
     foreign key (product_id) references products(id)
  ); 
""")

def insert_dataframe_to_mysql(dataframe, table_name):
    columns = ', '.join(dataframe.columns)
    placeholders = ', '.join(['%s' for _ in range(len(dataframe.columns))])
    sql = f"insert into {table_name} ({columns}) values ({placeholders})"
    values = [tuple(row) for _, row in dataframe.iterrows()]
    cursor.executemany(sql, values)
    conn.commit()

insert_dataframe_to_mysql(categories, "categories")
insert_dataframe_to_mysql(products, "products")
insert_dataframe_to_mysql(promo_codes, "promo_codes")
insert_dataframe_to_mysql(users, "users")
insert_dataframe_to_mysql(orders, "orders")
insert_dataframe_to_mysql(order_items, "order_items")

cursor.close()
conn.close()

print("Making database stored procedures...")

conn = make_connection(ini_file, db_conf)
cursor = conn.cursor()

cursor.execute('drop procedure if exists CheckLoginCredentials')
cursor.execute("""
CREATE PROCEDURE CheckLoginCredentials(
    IN inputUsername VARCHAR(255),
    IN inputPassword VARCHAR(255)
)
BEGIN
    select id, email, name, street, city, state, zip, date_of_birth, gender, is_admin
    from users
    where email = inputUsername and password = inputPassword;
END;
""")

cursor.execute('DROP PROCEDURE IF EXISTS NewUserRecord')
cursor.execute("""
CREATE PROCEDURE NewUserRecord(
    IN new_email VARCHAR(120),
    IN new_password VARCHAR(120),
    IN new_name VARCHAR(120),
    IN new_street VARCHAR(120),
    IN new_city VARCHAR(120),
    IN new_state VARCHAR(120),
    IN new_zip VARCHAR(5),
    IN new_date_of_birth DATETIME,
    IN new_gender VARCHAR(20),
    OUT new_insertion_Result BOOLEAN,
    OUT newID INT
)
BEGIN
    DECLARE userCountNew INT;

    SELECT COUNT(*) INTO userCountNew
    FROM users
    WHERE email = new_email;

    IF userCountNew > 0 THEN
        SET new_insertion_Result = FALSE;
    ELSE
        insert into users ( email, password, name, street, city, state, zip, date_of_birth, gender) 
        values ( new_email, new_password, new_name, new_street, new_city, new_state, new_zip, new_date_of_birth, new_gender);

        select id into newID
        from users
        where email = new_email;
        SET new_insertion_Result = TRUE;
    END IF;
END;
""")

cursor.execute('DROP PROCEDURE IF EXISTS get_categories')
cursor.execute("""
create procedure get_categories()
begin
    select * from categories;
end
""")

cursor.execute('DROP PROCEDURE IF EXISTS get_products')
cursor.execute("""
CREATE PROCEDURE get_products(
    IN page INT,
    IN num INT,
    IN inputCategoryID INT,
    OUT Total_products INT
)
BEGIN
    DECLARE offset_value INT;

    SET offset_value = page * num;

    SELECT COUNT(*) INTO Total_products
    FROM products
    WHERE inputCategoryID = 0 OR category_id = inputCategoryID;

    SELECT id, name, price, stock
    FROM products
    WHERE inputCategoryID = 0 OR category_id = inputCategoryID
    LIMIT num OFFSET offset_value;
END;
""")

cursor.execute('DROP PROCEDURE IF EXISTS product_search')
cursor.execute("""
CREATE PROCEDURE product_search(
    IN page INT,
    IN num INT,
    IN inputCategoryID INT,
    IN search_term VARCHAR(120),
    OUT Total_products INT
)
BEGIN
    DECLARE offset_value INT;

    SET offset_value = page * num;

    SELECT COUNT(*) INTO Total_products
    FROM products
    WHERE (inputCategoryID = 0 OR category_id = inputCategoryID)
        AND name LIKE CONCAT('%', search_term, '%');

    SELECT id, name, price, stock
    FROM products
    WHERE (inputCategoryID = 0 OR category_id = inputCategoryID)
        AND name LIKE CONCAT('%', search_term, '%')
    LIMIT num OFFSET offset_value;
END;
""")

cursor.execute("DROP PROCEDURE IF EXISTS order_history")
cursor.execute("""
CREATE PROCEDURE order_history(
    IN input_user_id INT,
    IN page INT,
    IN num INT, 
    OUT total_orders INT
)
BEGIN
    DECLARE offset_value INT;
    SET offset_value = page * num;
    
    SELECT COUNT(*) INTO total_orders
    FROM orders
    WHERE user_id = input_user_id;

    SELECT id, datetime, total, street, city, state, zip, user_id
    FROM orders
    WHERE user_id = input_user_id
    LIMIT num OFFSET offset_value;
END
""")

cursor.execute("DROP PROCEDURE IF EXISTS order_details")
cursor.execute("""
CREATE PROCEDURE order_details(in input_order_id INT)
BEGIN
    SELECT order_items.qty, order_items.product_id, products.name, products.price, promo_codes.code
    FROM order_items
    JOIN products ON products.id = order_items.product_id
    LEFT JOIN orders ON orders.id = order_items.order_id
    LEFT JOIN promo_codes ON orders.promo_code_id = promo_codes.id
    WHERE order_items.order_id = input_order_id;
END;
""")

cursor.execute("DROP PROCEDURE IF EXISTS place_order")
cursor.execute("""
CREATE PROCEDURE place_order(
    IN input_total FLOAT,
    IN input_street VARCHAR(120),
    IN input_city VARCHAR(120),
    IN input_state VARCHAR(120),
    IN input_zip VARCHAR(5),
    IN input_user_id INT,
    IN input_promo_code_id INT,
    OUT new_order_id INT
)
BEGIN
    INSERT INTO orders (datetime, total, street, city, state, zip, user_id, promo_code_id)
    VALUES (NOW(), input_total, input_street, input_city, input_state, input_zip, input_user_id, input_promo_code_id);

    SET new_order_id = LAST_INSERT_ID();
    SELECT new_order_id AS new_order_id;
END;
""")

cursor.execute("DROP PROCEDURE IF EXISTS add_order_item")
cursor.execute("""
CREATE PROCEDURE `add_order_item`(
    IN input_qty INT,
    IN input_order_id INT, 
    IN input_product_id INT
)
BEGIN
    INSERT INTO order_items(qty, order_id, product_id)
    VALUES (input_qty, input_order_id, input_product_id);
END
""")

cursor.execute("DROP PROCEDURE IF EXISTS check_promo_validity")
cursor.execute("""
CREATE PROCEDURE check_promo_validity(IN input_code varchar(120))
BEGIN
    SELECT *
    FROM promo_codes
    WHERE code= input_code and expired = 0;
END;
""")

cursor.execute("DROP PROCEDURE if exists decrease_stock")
cursor.execute("""
CREATE PROCEDURE `decrease_stock`(
    IN input_product_id INT,
    IN input_qty INT
)
BEGIN
    DECLARE current_qty INT;

    SELECT stock INTO current_qty
    FROM products
    WHERE id = input_product_id
    LIMIT 1;

    IF current_qty IS NOT NULL THEN
        UPDATE products
        SET stock = current_qty - input_qty
        WHERE id = input_product_id;

    --        SELECT CONCAT('Quantity decreased successfully. New quantity: ', current_qty - input_qty) AS result;
    --    ELSE
    --        SELECT 'Product not found in products table.' AS result;
    END IF;
END
""")

cursor.execute("drop procedure if exists change_address")
cursor.execute("""
create procedure change_address(
    IN input_user_id INT,
    IN input_street VARCHAR(120),
    IN input_city VARCHAR(120),
    IN input_state VARCHAR(120),
    IN input_zip VARCHAR(5)
) begin
    update users set street = input_street, city = input_city, state = input_state, zip = input_zip where id = input_user_id;
    SELECT id, email, name, street, city, state, zip, date_of_birth, gender, is_admin
    from users where id = input_user_id;
end
""")

cursor.execute("drop procedure if exists get_customer_by_email")
cursor.execute("""
create procedure get_customer_by_email(
    IN input_email VARCHAR(120)
)
begin
    SELECT id, email, name, street, city, state, zip, date_of_birth, gender, is_admin
    from users where email = input_email;
end
""")

cursor.execute("drop procedure if exists edit_customer_by_id")
cursor.execute("""
create procedure edit_customer_by_id(
    IN input_id INT,
    IN input_name VARCHAR(120),
    IN input_street VARCHAR(120),
    IN input_city VARCHAR(120),
    IN input_state VARCHAR(120),
    IN input_zip VARCHAR(5),
    IN input_dob DATETIME,
    in input_gender VARCHAR(20),
    in input_admin BOOLEAN
) begin
    update users set 
    name = input_name,
    street = input_street,
    city = input_city,
    state = input_state,
    zip = input_zip,
    date_of_birth = input_dob,
    gender = input_gender,
    is_admin = input_admin
    where id = input_id;
end
""")

cursor.execute('drop procedure if exists get_promos')
cursor.execute("""
create procedure get_promos(
    in page int,
    in num int,
    out total_promos int
)
begin
    declare offset_value int;

    set offset_value = page * num;

    select count(*) into total_promos
    from promo_codes
    where expired = 0;

    select *
    from promo_codes
    where expired = 0
    limit num offset offset_value;
end;
""")

cursor.execute('drop procedure if exists expire_promo_by_id')
cursor.execute("""
    create procedure expire_promo_by_id(
        in input_id int
    )
    begin
        update promo_codes set expired = 1 where id = input_id;
    end;
""")

cursor.execute('drop procedure if exists add_promo')
cursor.execute("""
create procedure add_promo(
    in input_code varchar(120),
    in input_discount float,
    out created boolean
)
begin
    select count(*) into @code_count from promo_codes where code = input_code and expired = 0;
    if @code_count > 0 then
        set created = false;
    else
        set created = true;
        insert into promo_codes (code, expired, discount) values (input_code, 0, input_discount);
    end if;
end;
""")

cursor.execute('drop procedure if exists edit_product_by_id')
cursor.execute("""
    create procedure edit_product_by_id(
        in input_id int,
        in input_price float,
        in input_stock int
    )
    begin
        update products set price = input_price, stock = input_stock where id = input_id;
    end;  
""")

cursor.execute('drop procedure if exists add_new_product')
cursor.execute("""
    create procedure add_new_product(
        in input_name varchar(120),
        in input_price float,
        in input_stock int,
        in input_category_id int
    )
    begin
        insert into products (name, price, stock, category_id) values (input_name, input_price, input_stock, input_category_id);
    end;
""")

cursor.close()
conn.close()

print("(Re)-uploading data to warehouse...")

conn = make_connection(ini_file, wh_conf)
cursor = conn.cursor()

cursor.execute("drop table if exists fct_order_and_order_items")
cursor.execute("drop table if exists fct_promotions")
cursor.execute("drop table if exists dim_datetime")
cursor.execute("drop table if exists dim_customer_locations")
cursor.execute("drop table if exists dim_products")
cursor.execute("drop table if exists dim_customer_demographics")

cursor.execute( """
create table dim_datetime
  (
    datetime_key int not null auto_increment,
    full_date datetime not null,
    day_of_week varchar(10) not null,
    day_of_month int not null,
    quarter int not null,
    year int not null,
    month varchar(20) not null,
    hour int not null,
    minute int not null,
    primary key (datetime_key)
  );
""")

cursor.execute( """
create table dim_customer_locations
  (
    customer_location_key int not null auto_increment,
    street varchar(120) not null,
    city varchar(120) not null,
    state varchar(120) not null,
    zip varchar(5) not null,
    primary key (customer_location_key)
  );
""")

cursor.execute( """
create table dim_products
  (
    product_key int not null auto_increment,
    name varchar(120) not null,
    price float not null,
    category varchar(120) not null,
    primary key (product_key)
  );
""")

cursor.execute("""
create table dim_customer_demographics
  (
    customer_demographic_key int not null auto_increment,
    gender varchar(225) not null,
    age_group varchar(30) not null,
    primary key (customer_demographic_key)
  );
""")

cursor.execute("""
create table fct_order_and_order_items
  (
    final_order_sale_amount float not null,
    number_of_items_in_order int not null,
    quantity_of_order_item int not null,
    order_id int not null,
    final_order_cost float not null,
    datetime_key int not null,
    product_key int not null,
    customer_location_key int not null,
    customer_demographic_key int not null,
    foreign key (datetime_key) references dim_datetime(datetime_key),
    foreign key (product_key) references dim_products(product_key),
    foreign key (customer_location_key) references dim_customer_locations(customer_location_key),
    foreign key (customer_demographic_key) references dim_customer_demographics(customer_demographic_key)
  );
""")

cursor.execute("""
create table fct_promotions 
  (
    datetime_key int ,
    customer_demographic_key int,
    dollar_discounted_amount decimal(10, 2),
    promo_code_used varchar(50),
    foreign key (datetime_key) references dim_datetime(datetime_key),
    foreign key (customer_demographic_key) references dim_customer_demographics(customer_demographic_key)
  );
""")

print("Performing ETL with stored procedure...")

cursor.execute("drop procedure if exists perform_etl")
cursor.execute("""
create procedure perform_etl()
begin
    set foreign_key_checks = 0;

    truncate table dim_datetime;
    truncate table dim_customer_locations;
    truncate table dim_products;
    truncate table dim_customer_demographics;
    truncate table fct_order_and_order_items;
    truncate table fct_promotions;

    insert into dim_datetime (full_date, day_of_week, day_of_month, quarter, year, month, hour, minute)
    select
            datetime, 
            case dayofweek(datetime) 
            when 1 then 'Sunday' 
            when 2 then 'Monday' 
            when 3 then 'Tuesday' 
            when 4 then 'Wednesday' 
            when 5 then 'Thursday' 
            when 6 then 'Friday' 
            when 7 then 'Saturday' 
            end, 
            dayofmonth(datetime), quarter(datetime), year(datetime), monthname(datetime), hour(datetime), minute(datetime)
    from rairdata_db.orders;

    insert into dim_customer_locations (street, city, state, zip)
    select street, city, state, zip
    from rairdata_db.users;

    insert into dim_products (name, price, category)
    select p.name, p.price, c.name
    from rairdata_db.products p
    join rairdata_db.categories c
    on p.category_id = c.id
    order by p.id;

    create temporary table temp_results
    select distinct timestampdiff(year, date_of_birth, curdate()) as age
    from rairdata_db.users;
    
    alter table temp_results add column age_group varchar(10);
    
    update temp_results set age_group = case 
        when age between 0 and 10 then '0 to 10'
        when age between 11 and 20 then '11 to 20'
        when age between 21 and 30 then '21 to 30'
        when age between 31 and 40 then '31 to 40'
        when age between 41 and 50 then '41 to 50'
        when age between 51 and 60 then '51 to 60'
        when age between 61 and 70 then '61 to 70'
        when age between 71 and 80 then '71 to 80'
        when age between 81 and 90 then '81 to 90'
        when age between 91 and 100 then '91 to 100'
        else '100+'
    end;

    insert into dim_customer_demographics (gender, age_group)
    select distinct u.gender, t.age_group
    from rairdata_db.users u
    join temp_results t on t.age = TIMESTAMPDIFF(YEAR, u.date_of_birth, CURDATE())
    order by t.age_group, gender;

    insert into fct_order_and_order_items(final_order_sale_amount, number_of_items_in_order, quantity_of_order_item, order_id, final_order_cost,datetime_key, product_key, customer_location_key, customer_demographic_key)
    select 
        o.total as final_order_sale_amount, 
        sum(oi.qty) over(partition by o.id) as number_of_items_in_order,
        oi.qty as quantity_of_order_item, 
        o.id as order_id,
        sum(p.price * oi.qty) over(partition by o.id) as final_order_cost,
        dd.datetime_key,
        dp.product_key,
        dcl.customer_location_key,
        dcd.customer_demographic_key
    from rairdata_db.orders o 
    join rairdata_db.order_items oi on oi.order_id = o.id
    join rairdata_db.products p on p.id = oi.product_id
    join rairdata_db.users u on u.id = o.user_id
    join dim_datetime dd on dd.full_date = o.datetime
    join temp_results t on t.age = TIMESTAMPDIFF(YEAR, u.date_of_birth, CURDATE())
    join dim_customer_demographics dcd on dcd.gender = u.gender and dcd.age_group = t.age_group
    join dim_products dp on dp.name = p.name
    join dim_customer_locations dcl on dcl.street = o.street and dcl.city = o.city and dcl.state = o.state and dcl.zip = o.zip;

    insert into fct_promotions (datetime_key, customer_demographic_key, dollar_discounted_amount, promo_code_used)
    select dd.datetime_key, dcd.customer_demographic_key, o.total * pc.discount / 100, pc.code
    from rairdata_db.orders o
    inner join rairdata_db.promo_codes pc on o.promo_code_id = pc.id
    inner join rairdata_db.users u on o.user_id = u.id
    inner join dim_datetime dd on o.datetime = dd.full_date
    inner join temp_results t on t.age = TIMESTAMPDIFF(YEAR, u.date_of_birth, CURDATE())
    inner join dim_customer_demographics dcd on t.age_group = dcd.age_group and u.gender = dcd.gender;

    drop temporary table if exists temp_results;

    set foreign_key_checks = 1;
end
""")

cursor.callproc('perform_etl')
conn.commit()
cursor.close()
conn.close()

print("Done!")
