# In db.py

import pyodbc

#TODO: REMOVE THIS BEFORE GOING PUBLIC REPO ACCESS
DB_HOST = 'db-abeer.database.windows.net'
DB_USER = 'admin1@db-abeer'
DB_PASSWORD = 'F68e.NH97NbF.q='
DB_NAME = 'cs-480-final'

#For WSL/Linux
#https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver17&tabs=ubuntu18-install%2Calpine17-install%2Cdebian8-install%2Credhat7-13-install%2Crhel7-offline
#For Windows
#https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver17

ODBC_DRIVER = '{ODBC Driver 18 for SQL Server}'


def get_connection():
    # ... rest of the function remains the same ...
    connection_string = f'DRIVER={ODBC_DRIVER};SERVER={DB_HOST};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD};Encrypt=yes;TrustServerCertificate=no;LoginTimeout=30;'

    #Remove this after checking connection
    try:
        conn = pyodbc.connect(connection_string)
        print("Database connection successful!")
        return conn
    except pyodbc.Error as ex:
        print(f"Database connection failed: {ex}")
        return None