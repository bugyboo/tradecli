from datetime import datetime
import sqlite3
from utils import get_db_path
from settings import Settings
from rich.console import Console
from rich.table import Table

def view_trade(trade_id, settings=Settings()):
    """
    View a trade from the TRADES table by ID.
    """
    console = Console()
    conn = sqlite3.connect(get_db_path(settings.default_account))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM TRADES WHERE ID = ?", (trade_id,))
    trade = cursor.fetchone()
    conn.close()
    if trade:
        table = Table(title="Trade Details")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        fields = ["ID", "Trade Date", "Symbol", "Operation", "Filled Qty", "Price", "Fees", "VAT", "Cost Value", "Profit/Loss", "Position Open"]
        for field, value in zip(fields, trade):
            table.add_row(field, str(value))
        console.print(table)
    else:
        console.print(f"No trade found with ID {trade_id}.")
    

def buy_trade(trade_date, symbol, filled_qty, price, fees=0.0, vat=0.0, cost_value=0.0, settings=Settings()):
    """
    Insert a buy trade into the TRADES table.
    """
    console = Console()
    try:
        conn = sqlite3.connect(get_db_path(settings.default_account))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO TRADES (trade_date, symbol, opr, filled_qty, price, fees, vat, cost_value, profit_loss, is_position_open)
            VALUES (?, ?, 'buy', ?, ?, ?, ?, ?, 0, 1)
        """, (trade_date, symbol, filled_qty, price, fees, vat, cost_value))
        conn.commit()
        conn.close()
        console.print("[green]Buy trade saved successfully.[/green]")
    except sqlite3.Error as e:
        console.print(f"[red]Error saving buy trade: {e}[/red]")

def sell_trade(trade_date, symbol, filled_qty, price, fees=0.0, vat=0.0, cost_value=0.0, profit_loss=0.0, close_position=None, settings=Settings()):
    """
    Insert a sell trade into the TRADES table.
    """
    console = Console()
    try:
        conn = sqlite3.connect(get_db_path(settings.default_account))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO TRADES (trade_date, symbol, opr, filled_qty, price, fees, vat, cost_value, profit_loss, is_position_open)
            VALUES (?, ?, 'sell', ?, ?, ?, ?, ?, ?, 0)
        """, (trade_date, symbol, filled_qty, price, fees, vat, cost_value, profit_loss))
        conn.commit()
        conn.close()
        console.print("[green]Sell trade saved successfully.[/green]")
        if close_position:
            # Update the corresponding buy trade to mark position as closed
            conn = sqlite3.connect(get_db_path(settings.default_account))
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE TRADES
                SET is_position_open = 0
                WHERE ID = ? AND opr = 'buy'
            """, (close_position,))
            conn.commit()
            conn.close()
            console.print(f"[yellow]Position for buy trade ID {close_position} closed.[/yellow]")
    except sqlite3.Error as e:
        console.print(f"[red]Error saving sell trade: {e}[/red]")

def delete_trade(trade_id, settings=Settings()):
    """
    Delete a trade from the TRADES table by ID.
    """
    console = Console()
    try:
        conn = sqlite3.connect(get_db_path(settings.default_account))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM TRADES WHERE ID = ?", (trade_id,))
        if cursor.rowcount > 0:
            console.print(f"[green]Trade with ID {trade_id} deleted successfully.[/green]")
        else:
            console.print(f"[yellow]No trade found with ID {trade_id}.[/yellow]")
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        console.print(f"[red]Error deleting trade: {e}[/red]")
    
def update_trade(trade_id, trade_date=None, symbol=None, opr=None, filled_qty=None, price=None, fees=None, vat=None, cost_value=None, profit_loss=None, is_position_open=None, settings=Settings()):
    """
    Update a trade in the TRADES table by ID.
    Only non-None parameters will be updated.
    """
    console = Console()
    try:
        conn = sqlite3.connect(get_db_path(settings.default_account))
        cursor = conn.cursor()
        fields = []
        values = []
        if trade_date is not None:
            fields.append("trade_date = ?")
            values.append(trade_date)
        if symbol is not None:
            fields.append("symbol = ?")
            values.append(symbol)
        if opr is not None:
            fields.append("opr = ?")
            values.append(opr)
        if filled_qty is not None:
            fields.append("filled_qty = ?")
            values.append(filled_qty)
        if price is not None:
            fields.append("price = ?")
            values.append(price)
        if fees is not None:
            fields.append("fees = ?")
            values.append(fees)
        if vat is not None:
            fields.append("vat = ?")
            values.append(vat)
        if cost_value is not None:
            fields.append("cost_value = ?")
            values.append(cost_value)
        if profit_loss is not None:
            fields.append("profit_loss = ?")
            values.append(profit_loss)
        if is_position_open is not None:
            fields.append("is_position_open = ?")
            values.append(is_position_open)
        
        values.append(trade_id)
        sql = f"UPDATE TRADES SET {', '.join(fields)} WHERE ID = ?"
        cursor.execute(sql, values)
        if cursor.rowcount > 0:
            console.print(f"[green]Trade with ID {trade_id} updated successfully.[/green]")
        else:
            console.print(f"[yellow]No trade found with ID {trade_id}.[/yellow]")
        conn.commit()
        conn.close()
        console.print("[green]Trade update operation completed.[/green]")
    except sqlite3.Error as e:
        console.print(f"[red]Error updating trade: {e}[/red]")
    
def deposit_funds(fund_date, source, amount_SAR, amount_USD, rate_exchange, settings=Settings()):
    """
    Insert a deposit record into the FUNDS table.
    """
    console = Console()
    try:
        conn = sqlite3.connect(get_db_path(settings.default_account))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO FUNDS (fund_date, opr, source, amount_SAR, amount_USD, rate_exchange)
            VALUES (?, 'deposit', ?, ?, ?, ?)
        """, (fund_date, source, amount_SAR, amount_USD, rate_exchange))
        conn.commit()
        conn.close()
        console.print("[green]Funds deposit inserted successfully.[/green]")
    except sqlite3.Error as e:
        console.print(f"[red]Error depositing funds: {e}[/red]")
    
def withdraw_funds(fund_date, source, amount_SAR, amount_USD, rate_exchange, settings=Settings()):
    """
    Insert a withdraw record into the FUNDS table.
    """
    console = Console()
    try:
        conn = sqlite3.connect(get_db_path(settings.default_account))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO FUNDS (fund_date, opr, source, amount_SAR, amount_USD, rate_exchange)
            VALUES (?, 'withdraw', ?, ?, ?, ?)
        """, (fund_date, source, amount_SAR, amount_USD, rate_exchange))
        conn.commit()
        conn.close()
        console.print("[green]Funds withdraw inserted successfully.[/green]")
    except sqlite3.Error as e:
        console.print(f"[red]Error withdrawing funds: {e}[/red]")
def buy_menu(selected_ticker, current_prices, total_cash, settings=Settings()):
    # Buy trade
    console = Console()
    try:
        symbol = input(f"Enter Symbol or {selected_ticker} = ").strip().upper() or selected_ticker
        price_str = input(f"Enter Price ({current_prices.get(symbol, 0)}) = ").strip()
        price = float(price_str or current_prices.get(symbol, 0))                
        max_qty = int(total_cash / current_prices.get(symbol, 1))
        filled_qty = int(input(f"Enter Quantity (Max {max_qty}) = ").strip() or max_qty)
        fees = float(input("Enter Fees (default 1.8) = ").strip() or 1.8)
        vat = float(input("Enter VAT (default 0.27) = ").strip() or 0.27)
        trade_date = input("Enter Trade Date (DD/MM/YYYY) = ").strip() or datetime.today().strftime("%d/%m/%Y")                
        cost_value = filled_qty * price + fees + vat
        
        if cost_value > total_cash:
            console.print(f"[red]Error: Insufficient cash to execute this buy trade. Available cash: ${total_cash:,.2f}, Required: ${cost_value:,.2f}[/red]")
            input("Press Enter to continue...")
            return
        
        # show confirmation
        console.print(f"Confirm [green]Buy[/green]: {filled_qty} shares of {symbol} at ${price:.2f}. Total cost: ${cost_value:.2f} | {settings.get_account().exchange_rate_label} {cost_value * settings.get_account().exchange_rate:.2f}")
        console.print(f"[red]No[/red] [dim]to cancel[/dim], Enter to [green]confirm[/green]...")
        confirm = input("").strip().lower()
        if confirm == 'no':
            console.print("[red]Buy trade cancelled.[/red]")
            input("Press Enter to continue...")
            return
        
        buy_trade(trade_date, symbol, filled_qty, price, fees, vat, cost_value, settings=settings)                
        
        input("Press Enter to continue...")
    except ValueError as e:
        console.print(f"[red]Invalid input: {e}[/red]")
        input("Press Enter to continue...")    
        
def sell_menu(ticker_data, trades, selected_ticker, current_prices, settings=Settings()):
    console = Console()
    # Sell trade
    try:
        symbol = input(f"Enter Symbol or {selected_ticker} = ").strip().upper() or selected_ticker
        price_str = input(f"Enter Price ({current_prices.get(symbol, 0)}) = ").strip()
        price = float(price_str or current_prices.get(symbol, 0))
        fees = float(input("Enter Fees (default 1.8) = ").strip() or 1.8)
        vat = float(input("Enter VAT (default 0.27) = ").strip() or 0.27)                
        # calculate profit/loss from open position if applicable
        close_position = input("Close Position Buy ID (or press Enter to skip): ").strip() or None
        if close_position:
            # Fetch the buy trade details from trades above
            filled_qty = 0
            profit_loss = 0.0
            buy_trade_details = next((trade for trade in trades if str(trade[0]) == close_position and trade[3].lower() == 'buy'), None)
            if buy_trade_details:
                _, _, cp_symbol, _, buy_filled_qty, _, _, _, buy_cost_value, _ = buy_trade_details
                symbol = cp_symbol
                filled_qty = buy_filled_qty                                                 
                profit_loss = ( (price * filled_qty ) - (fees + vat) ) - ( buy_cost_value )
        else:                                                                               
            filled_qty = int(input("Enter Quantity = ").strip())
            profit_loss = input("Enter Profit/Loss = ").strip() or 0.0
            profit_loss = float(profit_loss)
            # Check if enough shares to sell from ticker data
            ticker_info = next((row for row in ticker_data if row[0] == symbol), None)
            if not ticker_info or ticker_info[1] < filled_qty:
                console.print(f"[red]Error: Insufficient shares to sell. Available shares for {symbol}: {ticker_info[1] if ticker_info else 0}[/red]")
                input("Press Enter to continue...")
                return
            
                                
        trade_date = input("Enter Trade Date (DD/MM/YYYY) = ").strip() or datetime.today().strftime("%d/%m/%Y")           
            
        cost_value = (filled_qty * price) - (fees + vat)
        sell_pl_text = f"[red]${profit_loss:,.2f}[/red]" if profit_loss < 0 else f"[green]${profit_loss:,.2f}[/green]"
        console.print(f"Confirm [red]Sell[/red]: [green]{filled_qty}[/green] shares of [cyan]{symbol}[/cyan] at [yellow]${price:.2f}[/yellow]. Total Value: ${cost_value:.2f} {settings.get_account().exchange_rate_label} {cost_value * settings.get_account().exchange_rate:.2f} | Profit/Loss: {sell_pl_text} {settings.get_account().exchange_rate_label} {profit_loss * settings.get_account().exchange_rate:.2f}")
        console.print(f"[red]No[/red] [dim]to cancel[/dim], Enter to [green]confirm[/green]...")
        confirm = input("").strip().lower()
        if confirm == 'no':
            console.print("[red]Sell trade cancelled.[/red]")
            input("Press Enter to continue...")
            return
        
        sell_trade(trade_date, symbol, filled_qty, price, fees, vat, cost_value, profit_loss, close_position, settings=settings)
        
        input("Press Enter to continue...")
    except ValueError as e:
        console.print(f"[red]Invalid input: {e}[/red]")
        input("Press Enter to continue...")
        
def delete_trade_menu(settings=Settings()):
    console = Console()
    trade_id = input("Enter Trade ID to delete: ").strip()
    try:
        id = int(trade_id)
        view_trade(id, settings=settings)
        console.print(f"Confirm Delete Trade ID: {id}")
        confirm = input(f"Are you sure you want to delete trade ID {id}? Type 'yes' to confirm: ").strip().lower()
        if confirm == 'yes':
            delete_trade(id, settings=settings)
        else:
            console.print("[red]Delete trade cancelled.[/red]")
        input("Press Enter to continue...")
    except ValueError as e:
        console.print(f"[red]Invalid Trade ID: {e}[/red]")
        input("Press Enter to continue...")
    
