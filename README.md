# RAIR Data Shopping Application
_Course project for DATA-225 (Database Systems for Analytics)_

Team Members:
- Ibrahim Khalid
- Rutuja Kokate
- Sung Won Lee
- Ravjot Singh

Technologies used:
- MySQL
- Python
- PyQt5

Datasources:
- `./data/users_mock.csv` and `./data/promo_codes_mock.csv` are generated files from mockaroo.com 
- `./data/flipkart_com-ecommerce_sample.csv` is a dataset from https://www.kaggle.com/datasets/PromptCloudHQ/flipkart-products

---

## Instructions to run project
1. Make a copy of 'config.ini.tmp' and name it 'config.ini'. Replace with relevant credentials
2. Note the config options at the top of the data.py script and configure them to your requirements
3. Make sure the following databases are avaialble to connect to
    > rairdata_db  
    > rairdata_wh  
4. Run the data.py script to initialize the databases
5. Run the command "python main.py"  
   Optionally, you can use some command line arguments for ease of use as described bellow  
   ```
   Usage: python main.py [--local] [--auto-login|--auto-login-admin] [--help]
   By default, the program will use the remote database and require manual login.
   --help:             show this message
   --local:            use local database
   --auto-login:       login automatically with saved normal user account
   --auto-login-admin: login automatically with saved admin user account
                       normal user account will be logged in if both --auto-login 
                       and --auto-login-admin are specified
   ```

If logging in manually, use the following login credentials

User account:
- email: user@rair.com
- password: 12345678

Admin account:
- email: admin@rair.com
- password: 12345678
