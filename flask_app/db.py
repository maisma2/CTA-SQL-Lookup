import os
from dotenv import load_dotenv
import pymssql

load_dotenv()

def get_connection():
    """
    Returns a connection to the Azure SQL Server database using pymssql.
    This does NOT use ODBC at all.
    """

    server = os.getenv("DB_HOST")      # e.g. yourserver.database.windows.net
    database = os.getenv("DB_NAME")    # e.g. cta_project
    user = os.getenv("DB_USER")        # e.g. your-username
    password = os.getenv("DB_PASSWORD")  # your password

    # as_dict=True -> rows come back as dictionaries instead of tuples
    conn = pymssql.connect(
        server=server,
        user=user,
        password=password,
        database=database,
        port=1433,
        as_dict=True
    )
    return conn
