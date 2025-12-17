import pandas as pd
import sqlite3
from utils import get_db_path
from settings import Settings

def read_and_print_rows(df, section, row_indices, quiet=False, settings=Settings()):
    """
    Prints the specified rows from the DataFrame and saves to DB.

    :param df: Pandas DataFrame containing the data
    :param row_indices: List of row indices (1-based) to print
    """
    
    for idx in row_indices:
        if 1 <= idx <= len(df):
            row = df.iloc[idx-1]
            if not quiet:
                print(f"Row {idx}:")
                for col_name, value in row.items():
                    print(f"{col_name}: {value}")
                print("-" * 50)
            
            # Insert based on section
            try:
                if section == 'deposit' or section == 'withdraw':
                    insert_fund(
                        opr=str(section),
                        fund_date=str(row[2]),
                        source=str(row[3]),
                        amount_SAR=float(row[4]),
                        amount_USD=float(row[5]),
                        rate_exchange=float(row[6]),
                        settings=settings
                    )
                    if not quiet:
                        print("Fund inserted successfully.")
                elif section == 'buy':
                    insert_trade(
                        trade_date=str(row[2]),
                        symbol=str(row[3]),
                        opr=str(section),
                        filled_qty=float(row[4]),
                        price=float(row[5]),
                        fees=float(row[6]) if pd.notna(row[6]) else 0,
                        vat=float(row[7]) if pd.notna(row[7]) else 0,
                        cost_value=float(row[9]) if pd.notna(row[9]) else 0,
                        is_position_open=row[0] if pd.notna(row[0]) else 0,
                        settings=settings
                    )
                    if not quiet:
                        print("Trade inserted successfully.")
                elif section == 'sell':
                    insert_trade(
                        trade_date=str(row[2]),
                        symbol=str(row[3]),
                        opr=str(section),
                        filled_qty=float(row[4]),
                        price=float(row[5]),
                        fees=float(row[6]) if pd.notna(row[6]) else 0,
                        vat=float(row[7]) if pd.notna(row[7]) else 0,
                        cost_value=float(row[9]) if pd.notna(row[9]) else 0,
                        profit_loss=float(row[10]) if pd.notna(row[10]) else 0,
                        is_position_open=0,
                        settings=settings
                    )
                    if not quiet:
                        print("Trade inserted successfully.")
            except (IndexError, ValueError, TypeError) as e:
                print(f"Error inserting row {idx}: {e}")
        else:
            print(f"Row {idx} is out of range.")

def insert_trade(trade_date, symbol, opr, filled_qty, price, fees=0.0, vat=0.0, market_value=0.0, cost_value=0.0, profit_loss=0.0, is_position_open=1, settings=Settings()):
    """
    Insert a trade into the TRADES table.
    """
    conn = sqlite3.connect(get_db_path(settings.default_account))
    cursor = conn.cursor() 
    cursor.execute("""
        INSERT INTO TRADES (trade_date, symbol, opr, filled_qty, price, fees, vat, cost_value, profit_loss, is_position_open)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (trade_date, symbol, opr, filled_qty, price, fees, vat, cost_value, profit_loss, is_position_open))
    conn.commit()
    conn.close()

def insert_fund(opr, fund_date, source, amount_SAR, amount_USD, rate_exchange, settings=Settings()):
    """
    Insert a fund operation into the FUNDS table.
    """
    conn = sqlite3.connect(get_db_path(settings.default_account))
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO FUNDS (opr, fund_date, source, amount_SAR, amount_USD, rate_exchange)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (opr, fund_date, source, amount_SAR, amount_USD, rate_exchange))
    conn.commit()
    conn.close()