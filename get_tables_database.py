import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('atm_database.db')
cursor = conn.cursor()

# Function to get all tables in the database
def get_all_tables():
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    return [table[0] for table in tables]

# Get and print all tables
all_tables = get_all_tables()
print("Tables in the database:")
for table in all_tables:
    print(table)
    # Display Table Structure
    cursor.execute(f"PRAGMA table_info({table});")
    structure_data = cursor.fetchall()
    print("Table Structure:")
    for column_info in structure_data:
        print(column_info)

    # Display Table Contents
    cursor.execute(f"SELECT * FROM {table};")
    contents_data = cursor.fetchall()
    print("\nTable Contents:")
    for row in contents_data:
          print(row)

# Close the connection
conn.close()
