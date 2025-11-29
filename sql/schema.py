import pyodbc
from db import get_connection
# Assuming 'conn' is an established pyodbc connection object
conn = get_connection()

# --- 1. Define SQL Statements ---
# Splitting DDL commands is generally more reliable with pyodbc
drop_statements = [
    "DROP TABLE IF EXISTS StationLine;",
    "DROP TABLE IF EXISTS Ridership;",
    "DROP TABLE IF EXISTS test_connection;",
    "DROP TABLE IF EXISTS Station;",
    "DROP TABLE IF EXISTS Line;"
]

create_station_table = """
CREATE TABLE Station (
    stop_id INT NOT NULL PRIMARY KEY,
    station_id INT NOT NULL,
    stop_name NVARCHAR(100) NOT NULL,
    direction CHAR(1) NOT NULL,
    ada BIT NOT NULL, -- BIT for boolean (0 or 1)
    latitude DECIMAL(9, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL
);
"""

create_station_name_table = """
CREATE TABLE StationName 
(
    station_id INT NOT NULL PRIMARY KEY,
    station_name NVARCHAR(100) NOT NULL,
);
"""

create_station_line_table = """
DROP TABLE IF EXISTS StationLine;
CREATE TABLE StationLine 
(
    stop_id INT NOT NULL,
    line_id INT NOT NULL,
    
    PRIMARY KEY(stop_id, line_id)
);
"""

create_station_ridership_table = """
DROP TABLE IF EXISTS StationRidership;
CREATE TABLE StationRidership 
(
    station_id INT NOT NULL,
    station_name NVARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    day_type CHAR(1) NOT NULL,
    rides INT NOT NULL,

    PRIMARY KEY(station_id, date)
);
"""

try:
    # 2. Create a cursor
    cursor = conn.cursor()
    print("Executing SQL schema script...")

    # 3. Execute DROP statements individually
    #print("Dropping existing tables...")
    #for statement in drop_statements:
    #    cursor.execute(statement)

    # 4. Execute CREATE TABLE statement
    #print("Creating Station table...")
    #cursor.execute(create_station_table)

    # 4a. Execute CREATE TABLE statement for StationName
    #print("Create station name table")
    #cursor.execute(create_station_name_table)

    # 4b. creating STop to Line table
    print("Create station line table")
    cursor.execute(create_station_line_table)

    # 4c. Creating station ridership
    #print("Create station ridership table")
    #cursor.execute(create_station_ridership_table)

    # 5. Commit the changes
    conn.commit()
    print("✅ SQL script executed and committed successfully.")

except pyodbc.Error as ex:
    sqlstate = ex.args[0]
    print(f"❌ An error occurred: {sqlstate}")
    # Rollback in case of an error
    conn.rollback()

finally:
    # 6. Close the cursor
    if 'cursor' in locals() and cursor:
        cursor.close()