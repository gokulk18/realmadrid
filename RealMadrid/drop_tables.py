import sqlite3

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# SQL statements to drop tables
tables = [
    "UserHandle_ticketpayment",
    "UserHandle_ticketitem",
    "UserHandle_ticketorder",
    "UserHandle_section",
    "UserHandle_stand",
    "UserHandle_match"
]

# Drop each table
for table in tables:
    try:
        cursor.execute(f'DROP TABLE IF EXISTS "{table}"')
        print(f"Dropped table {table}")
    except Exception as e:
        print(f"Error dropping {table}: {e}")

# Commit the changes and close the connection
conn.commit()
conn.close()
print("Done")
