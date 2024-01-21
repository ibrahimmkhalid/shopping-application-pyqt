import sys
from rair_shopping import RairDataShopping

def main(argv):
    if '--help' in argv:
        print('Usage: python main.py [--local] [--auto-login|--auto-login-admin] [--help]')
        print('By default, the program will use the remote database and require manual login.')
        print('  --help:             show this message')
        print('  --local:            use local database')
        print('  --auto-login:       login automatically with saved normal user account')
        print('  --auto-login-admin: login automatically with saved admin user account')
        print('                      normal user account will be logged in if both --auto-login and --auto-login-admin are specified')
        return

    db_config = 'rairdata_db'
    wh_config = 'rairdata_wh'
    ini_file = './config.ini'

    if '--local' in argv:
        db_config = 'local_db'
        wh_config = 'local_wh'

    RairDataShopping(ini_file, db_config, wh_config)

if __name__ == "__main__":
    main(sys.argv)
