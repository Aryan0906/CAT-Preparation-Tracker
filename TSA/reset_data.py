import sqlite3
import os
import shutil

def reset_database():
    # Check if database file exists
    if os.path.exists('cat_prep.db'):
        # Option 1: Delete the database file completely
        try:
            os.remove('cat_prep.db')
            print("Database file deleted successfully!")
        except Exception as e:
            print(f"Error deleting database file: {e}")

            # Option 2: If deletion fails, try to drop all tables
            try:
                # Connect to the database
                conn = sqlite3.connect('cat_prep.db')
                c = conn.cursor()

                # Get all table names
                c.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = c.fetchall()

                # Drop all tables
                for table in tables:
                    table_name = table[0]
                    c.execute(f"DROP TABLE IF EXISTS {table_name}")

                conn.commit()
                conn.close()

                print("All tables dropped successfully!")
            except Exception as e:
                print(f"Error dropping tables: {e}")
    else:
        print("Database file not found. No data to reset.")

    # Also clear any session state files if they exist
    if os.path.exists('.streamlit'):
        try:
            shutil.rmtree('.streamlit')
            print("Streamlit session data cleared!")
        except Exception as e:
            print(f"Error clearing Streamlit session data: {e}")

if __name__ == "__main__":
    # Confirm with the user
    confirm = input("Are you sure you want to reset all data? This cannot be undone. (yes/no): ")

    if confirm.lower() == 'yes':
        reset_database()
    else:
        print("Reset cancelled.")
