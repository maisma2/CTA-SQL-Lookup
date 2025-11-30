# Some content is AI generated, ie. formatting the debugger
import pandas as pd
import pyodbc

# Assuming 'db' module and get_connection function are correctly defined elsewhere
from db import get_connection


def import_csv_to_table(csv_path, table_name, conn):
    """
    Import CSV file into SQL Server table.
    Includes verbose error reporting and row-by-row progress reporting.
    """
    df = None
    try:
        # 1. Read CSV with quoted fields
        df = pd.read_csv(csv_path, quotechar='"')

        # 2. Get cursor
        cursor = conn.cursor()

        # 3. Prepare insert statement
        columns = ', '.join(df.columns)
        placeholders = ', '.join(['?' for _ in df.columns])
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # 4. Insert data row by row with verbose error handling
        total_rows = len(df)
        print(f"--- Starting import of {total_rows} rows into {table_name} from {csv_path} ---")

        for index, row in df.iterrows():
            current_row_number = index + 1

            # DEBUG: Print the first row immediately to confirm the loop is executing
            if current_row_number == 1:
                print("=========================================================================")
                print(f"DEBUG: Processing Row 1 data (SHOULD PRINT IMMEDIATELY):")
                print(row.to_string())
                print("=========================================================================")

            # **MODIFICATION: Print progress every 100 rows**
            if current_row_number % 100 == 0:
                # Flush=True ensures the print output appears immediately, which is crucial for monitoring hangs
                print(f"Progress: Inserting row {current_row_number} of {total_rows}...", flush=True)

            try:
                # Pass row data as a tuple to the execute method
                cursor.execute(insert_query, tuple(row))

            except pyodbc.IntegrityError as e:
                # Specific handling for Integrity Errors (like Foreign Key violations)
                print("=========================================================================")
                print(f"✗ FOREIGN KEY VIOLATION DETECTED on table: {table_name}")
                print(f"✗ FAILED ON ROW INDEX: {index} (1-based row number: {index + 2} in CSV file)")
                print(f"✗ FAILING DATA: \n{row.to_string()}")
                print(f"✗ ERROR MESSAGE: {e}")
                print("=========================================================================")

                # Rollback and re-raise to stop the import process immediately
                conn.rollback()
                raise

            except Exception as e:
                # Catch all other specific execution errors
                print("=========================================================================")
                print(f"✗ GENERAL EXECUTION ERROR DETECTED on table: {table_name}")
                print(f"✗ FAILED ON ROW INDEX: {index} (1-based row number: {index + 2} in CSV file)")
                print(f"✗ FAILING DATA: \n{row.to_string()}")
                print(f"✗ ERROR MESSAGE: {e}")
                print("=========================================================================")

                conn.rollback()
                raise

        # 5. Commit transaction if all rows succeeded
        conn.commit()
        print(f"Successfully imported {total_rows} rows into {table_name}")

    except Exception as e:
        # Catch errors from CSV reading or setup
        if df is None:
            print(f"✗ Error reading CSV or connecting to database for {csv_path}: {e}")
        else:
            # Re-raising the exception caught inside the loop
            print(f"Import failed for {table_name}. Check the detailed error message above.")

        # We re-raise the exception to stop the script as requested
        raise


# Main import process
if __name__ == "__main__":
    conn = None
    try:
        conn = get_connection()

        # Import data in order
        # The preceding imports were commented out in the original script and are left that way:
        # import_csv_to_table('originals/Stations.csv', 'StationName', conn)
        print("Imported stations names")

        # import_csv_to_table('originals/StopDetails.csv', 'StationLine', conn)
        print("Imported stations to lines")

        # print("Imported lines")
        # print("Imported station lines")

        # The target import for the 1.3M rows:
        import_csv_to_table('originals/CTA_L_Daily_Ridership.csv', 'StationRidership', conn)
        print("Imported ridership")

        print("\n All data imported successfully!")

    except Exception as e:
        print(f"\nImport failed: {e}")
    finally:
        if conn:
            conn.close()
