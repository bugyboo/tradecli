
from utils import get_db_path
from settings import Settings
from rich.console import Console
from rich.table import Table
from datetime import datetime

import sqlite3

def filter_menu(settings: Settings=Settings(), current_prices={}):
    console = Console()
    while True:
        # Connect to database
        conn = sqlite3.connect(get_db_path( settings.default_account ))
        cursor = conn.cursor()
        
        # filter trades by operation type
        console.print("[blue]Filter Trades by:[/blue] B[dim]uy[/dim], S[dim]ell[/dim], P[dim]rice[/dim], D[dim]ate[/dim], A[dim]ll[/dim] or Enter to skip")
        opr_filter = input("Enter choice: ").strip().lower()
        if opr_filter == 'b':
            cursor.execute("SELECT ID, trade_date, symbol, opr, filled_qty, price, cost_value, profit_loss, is_position_open FROM TRADES WHERE opr='buy' ORDER BY price")
        elif opr_filter == 's':
            cursor.execute("SELECT ID, trade_date, symbol, opr, filled_qty, price, cost_value, profit_loss, is_position_open FROM TRADES WHERE opr='sell' ORDER BY price")
        elif opr_filter == 'p':
            try:
                price_start = float(input("Enter price start range to filter (e.g., 100.00): ").strip())
                price_end = float(input("Enter price end range to filter (e.g., 200.00): ").strip())
            except ValueError:
                console.print(f"[red]Invalid price range input.[/red]")
                input("Press Enter to continue...")
                continue
            cursor.execute("SELECT ID, trade_date, symbol, opr, filled_qty, price, cost_value, profit_loss, is_position_open FROM TRADES WHERE price >= ? AND price <= ? ORDER BY price", (price_start, price_end))
        elif opr_filter == 'd':
            month_year_str = input("Enter month and year to filter (MM/YYYY) or (YYYY): ").strip()
            try:
                if month_year_str and len(month_year_str) == 4:
                    cursor.execute("SELECT ID, trade_date, symbol, opr, filled_qty, price, cost_value, profit_loss, is_position_open FROM TRADES WHERE SUBSTR(trade_date, 7, 4) = ? ORDER BY price", (month_year_str,))
                else:
                    month_year = datetime.strptime(month_year_str, "%m/%Y")
                    month_year_str = month_year.strftime("%m/%Y")
                    cursor.execute("SELECT ID, trade_date, symbol, opr, filled_qty, price, cost_value, profit_loss, is_position_open FROM TRADES WHERE SUBSTR(trade_date, 4, 7) = ? ORDER BY price", (month_year_str,))
            except ValueError:
                console.print(f"[red]Invalid month/year format.[/red]")
                input("Press Enter to continue...")
        elif opr_filter == 'a':
            # Fetch all trades sorted by price descending
            cursor.execute("SELECT ID, trade_date, symbol, opr, filled_qty, price, cost_value, profit_loss, is_position_open FROM TRADES ORDER BY price")
        else:
            conn.close()
            break  # Exit filter menu
            
        all_trades = cursor.fetchall()
        conn.close()

        if all_trades:
            query_table = Table(title="Filtered Trades Sorted by Price (Descending)")
            query_table.add_column("#", style="yellow")
            query_table.add_column("Date", style="dim")
            query_table.add_column("Symbol", style="cyan")
            query_table.add_column("Operation", justify="center")
            query_table.add_column("Qty", justify="right")
            query_table.add_column("Price", justify="right", style="yellow")
            query_table.add_column("Cost Value", justify="right")
            query_table.add_column("Profit/Loss", justify="right")
            query_table.add_column("Position", justify="center")

            counter = 1
            total_trades_qty = 0
            total_trades_cost_value = 0
            total_trades_pl = 0
            total_open_qty = 0
            for trade in all_trades:
                ID, trade_date, symbol, opr, filled_qty, price, cost_value, profit_loss, is_position_open = trade
                if is_position_open and is_position_open == 1:
                    profit_loss = filled_qty * (current_prices.get(symbol, price) - price)
                pl_text = f"[red]${profit_loss:,.2f}[/red]" if profit_loss and profit_loss < 0 else f"[green]${profit_loss:,.2f}[/green]" if profit_loss > 0 else "-"
                opr_text = f"[green]{opr} [/green]" if opr.lower() == 'buy' else f"[red]{opr}[/red]"
                is_position_open_text = "OPEN" if is_position_open == 1 else " "
                query_table.add_row(str(counter), str(trade_date), symbol, f"{opr_text} #{str(ID)}", str(filled_qty), f"${price:,.2f}", f"${cost_value:,.2f}", pl_text, is_position_open_text)
                counter += 1
                if opr.lower() == 'buy':                        
                    total_trades_qty += filled_qty
                    total_trades_cost_value += cost_value
                    if is_position_open and is_position_open == 1:
                        total_open_qty += filled_qty
                else:
                    total_trades_qty -= filled_qty
                    total_trades_cost_value -= cost_value
                if opr_filter == 'd':
                    if not is_position_open or is_position_open == 0:
                        total_trades_pl += profit_loss
                else:
                    total_trades_pl += profit_loss
            # Add totals row
            query_table.add_row("---", "---", "---", "---", "---", "---", "---", "---", "---")
            pl_text_total = f"[red]${total_trades_pl:,.2f}[/red]" if total_trades_pl < 0 else f"[green]${total_trades_pl:,.2f}[/green]" if total_trades_pl > 0 else "-"
            query_table.add_row("Total", "", "", "", str(total_trades_qty), f"${total_trades_cost_value / total_trades_qty:.2f}", f"${total_trades_cost_value:,.2f}", pl_text_total, str(total_open_qty))
            query_table.add_row(settings.get_account().exchange_rate_label, "", "", "", "", "", f"{total_trades_cost_value * settings.get_account().exchange_rate:,.2f}", f"{total_trades_pl * settings.get_account().exchange_rate:,.2f}","") 

            console.print(query_table)
        else:
            console.print("No trades found.")    