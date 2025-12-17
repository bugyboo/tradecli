import sqlite3
import os
from utils import get_db_path
from settings import Settings

schema_funds_sql = """
CREATE TABLE FUNDS (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    opr TEXT NOT NULL CHECK (opr IN ('deposit', 'withdraw')),
    fund_date TEXT NOT NULL,
    source TEXT NOT NULL,
    amount_SAR REAL NOT NULL,
    amount_USD REAL NOT NULL,
    rate_exchange REAL NOT NULL
);
"""

schema_trades_sql = """
CREATE TABLE TRADES (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    opr TEXT NOT NULL CHECK (opr IN ('buy', 'sell')),
    filled_qty INTEGER NOT NULL,
    price REAL NOT NULL,
    fees REAL NOT NULL,
    vat REAL NOT NULL,
    cost_value REAL,
    profit_loss REAL,   
    is_position_open INTEGER,
    closed_position_price REAL,
    closed_position_amount REAL
);
"""

def migrate_db( account_name: str ):
    print("Starting database schema operations...", sqlite3.sqlite_version)

    try:        
        # Delete DB file if exists
        db_path = get_db_path( account_name )
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Existing database file deleted.")
        
        # Create the database and tables
        create_funds_table( account_name )
        create_trades_table( account_name )
        
        print("DB created successfully.")
    except FileNotFoundError:
        print("Error: file not found.")
        input("Press Enter to continue...")
        
def create_funds_table( account_name: str ):
    try:
        db_path = get_db_path( account_name )
        # Open a connection to a SQLite database (creates the file if it doesn't exist)
        conn = sqlite3.connect(db_path)

        # Create a cursor object to execute SQL commands
        cursor = conn.cursor()        

        # Execute the schema SQL
        cursor.executescript(schema_funds_sql)

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        print("Funds table created successfully.")    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        input("Press Enter to continue...")
        
def create_trades_table( account_name: str):
    try:
        db_path = get_db_path(account_name)
        # Open a connection to a SQLite database (creates the file if it doesn't exist)
        conn = sqlite3.connect(db_path)

        # Create a cursor object to execute SQL commands
        cursor = conn.cursor()        

        # Execute the schema SQL
        cursor.executescript(schema_trades_sql)

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        print("Trades table created successfully.")    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        input("Press Enter to continue...")
    

def check_and_migrate( settings: Settings ):
    db_path = get_db_path( settings.default_account )
    if not os.path.exists(db_path):
        print("Database not found. Running migration...")
        migrate_db( settings.default_account )
        return
    # Check if tables exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='FUNDS'")
    if not cursor.fetchone():
        print("FUNDS table not found. Running migration...")
        conn.close()
        create_funds_table( settings.default_account )
        return
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TRADES'")
    if not cursor.fetchone():
        print("TRADES table not found. Running migration...")
        conn.close()
        create_trades_table( settings.default_account )
        return
    conn.close()