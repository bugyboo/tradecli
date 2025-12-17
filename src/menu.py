from utils import get_db_path
from settings import Settings, load_settings
import load_data
import migrate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime
from trade import deposit_funds, withdraw_funds, update_trade

import sqlite3

def get_funds(settings: Settings=Settings()):
    # Connect to database
    conn = sqlite3.connect(get_db_path( settings.default_account ))
    cursor = conn.cursor()
    cursor.execute("SELECT ID, opr, fund_date, source, amount_SAR, amount_USD, rate_exchange FROM FUNDS ORDER BY ID")
    funds = cursor.fetchall()
    conn.close()
    return funds

def main_menu(settings: Settings, settings_path: str):
    console = Console()
    # Show main menu
    console.print("[blue]Options:[/blue] A[dim]ccount[/dim], R[dim]eset Data[/dim], L[dim]oad Data[/dim], F[dim]unds[/dim], D[dim]eposit[/dim], W[dim]ithdraw[/dim], P[dim]osition[/dim] or S[dim]ettings[/dim]")
    choicee = input("Enter choice: ").strip().lower()
    if choicee == 'a':
        # Change account
        console.print("Available Accounts:")
        for idx, acc in enumerate(settings.accounts):
            console.print(f"{idx + 1}. {acc.name} (Exchange Rate: {acc.exchange_rate} {acc.exchange_rate_label}, Ticker: {acc.selected_ticker}, Fees: ${acc.fees_usd})")
        console.print("[blue]Options[/blue] [dim]Enter account[/dim] number [dim]to select or[/dim] N. [dim]Create New Account[/dim]")
        acc_choice = input("Enter choice: ").strip().lower()
        if acc_choice == 'n':
            account_name = input("Enter account name (no spaces or special characters): ").strip()
            settings.default_account = account_name
            settings.save(settings_path)
            console.print(f"[green]New account '{account_name}' created and set as default.[/green]")
            settings = load_settings(settings_path)  # Reload settings
            migrate.check_and_migrate( settings ) 
            input("Press Enter to continue...")
        else:
            try:
                acc_index = int(acc_choice) - 1
                if 0 <= acc_index < len(settings.accounts):
                    settings.default_account = settings.accounts[acc_index].name
                    settings.save(settings_path)
                    settings = load_settings(settings_path)  # Reload settings
                    migrate.check_and_migrate( settings )
                    console.print(f"[green]Switched to account '{settings.default_account}'.[/green]")
                    input("Press Enter to continue...")
                else:
                    console.print("[red]Invalid account selection.[/red]")
                    input("Press Enter to continue...")
            except ValueError:
                console.print("[red]Invalid input.[/red]")
                input("Press Enter to continue...")
                
    elif choicee == 'r':
        # run schema migration
        try:
            migrate.migrate_db( settings.default_account )
            console.print("[green]Schema migration completed successfully.[/green]")
        except Exception as e:
            console.print(f"[red]Error during migration: {e}[/red]")
        input("Press Enter to continue...")
    elif choicee == 'l':
        # Funds deposit/withdraw/trades load_data.py
        load_data.main()
        console.print("[green]Funds/trades operation completed.[/green]")
        input("Press Enter to continue...")
    elif choicee == 'f':
        # List funds
        funds = get_funds(settings=settings)
        
        if funds:
            while True:
                console.clear()
                funds_table = Table(title="Funds History")
                funds_table.add_column("#", style="yellow")
                funds_table.add_column("Operation", justify="center")
                funds_table.add_column("Date", style="dim")
                funds_table.add_column("Source", style="cyan")
                funds_table.add_column(f"Amount {settings.get_account().exchange_rate_label}", justify="right")
                funds_table.add_column("Amount USD", justify="right")
                funds_table.add_column("Exchange Rate", justify="right")

                for fund in funds:
                    ID, opr, fund_date, source, amount_SAR, amount_USD, rate_exchange = fund
                    opr_text = f"[green]{opr} [/green]" if opr.lower() == 'deposit' else f"[red]{opr}[/red]"
                    funds_table.add_row(str(ID), f"{opr_text}", str(fund_date), source, f"{amount_SAR:,.2f}", f"${amount_USD:,.2f}", f"{rate_exchange:.4f}")

                console.print(funds_table)
                
                # Print panel for total deposits and withdrawals
                total_deposits_sar = sum(fund[4] for fund in funds if fund[1].lower() == 'deposit')
                total_withdrawals_sar = sum(fund[4] for fund in funds if fund[1].lower() == 'withdraw')
                total_deposits_usd = sum(fund[5] for fund in funds if fund[1].lower() == 'deposit')
                total_withdrawals_usd = sum(fund[5] for fund in funds if fund[1].lower() == 'withdraw')
                deposits_panel = Panel(f"""
    [green]Total Deposits:[/green] {settings.get_account().exchange_rate_label} {total_deposits_sar:,.2f} | ${total_deposits_usd:,.2f}   
    [red]Total Withdrawals:[/red]  {settings.get_account().exchange_rate_label} {total_withdrawals_sar:,.2f} | ${total_withdrawals_usd:,.2f} 
    Total {settings.get_account().exchange_rate_label} = {total_deposits_sar - total_withdrawals_sar:,.2f}   
    Total USD = {total_deposits_usd - total_withdrawals_usd:,.2f}   
                """, title="Funds Summary", expand=False)
                console.print(deposits_panel)
                
                console.print("[blue]Filter Funds by:[/blue] D[dim]ate range,[/dim] S[dim]ource[/dim], R[dim]eset Filter or[/dim] E[dim]nter[/dim]")            
                filter_choice = input("Enter choice: ").strip().lower()
                if filter_choice == 'd':
                    try:
                        month_year_str = input("Enter month and year to filter (MM/YYYY) or (YYYY): ").strip()
                        if month_year_str and len(month_year_str) == 4:
                            filtered_funds = [fund for fund in funds if fund[2].endswith(month_year_str)]
                        else:
                            month_year = datetime.strptime(month_year_str, "%m/%Y")
                            month_year_str = month_year.strftime("%m/%Y")
                            filtered_funds = [fund for fund in funds if fund[2][3:10] == month_year_str]
                        funds = filtered_funds
                    except ValueError:
                        console.print(f"[red]Invalid month/year format.[/red]")
                        input("Press Enter to continue...")
                elif filter_choice == 's':
                    source_str = input("Enter source to filter: ").strip().lower()
                    filtered_funds = [fund for fund in funds if source_str in fund[3].lower()]
                    funds = filtered_funds
                elif filter_choice == 'r':
                    funds = get_funds(settings=settings)
                else:
                    break  # Exit filtering loop

        else:
            console.print("No funds records found.")             
            input("Press Enter to continue...")
            
    elif choicee == 'd':
        # deposit fund
        try:
            fund_date = input("Enter fund date (DD/MM/YYYY): ").strip() or datetime.today().strftime("%d/%m/%Y")
            source = input("Enter source: ").strip()
            amount_SAR = float(input(f"Enter amount in {settings.get_account().exchange_rate_label}: ").strip())
            amount_USD = float(input("Enter amount in USD: ").strip())
            rate_exchange = amount_SAR / amount_USD
            deposit_funds(fund_date, source, amount_SAR, amount_USD, rate_exchange, settings=settings)

        except ValueError as e:
            console.print(f"[red]Invalid input: {e}[/red]")
        input("Press Enter to continue...")
    elif choicee == 'w':
        # withdraw fund
        try:
            fund_date = input("Enter fund date (DD/MM/YYYY): ").strip() or datetime.today().strftime("%d/%m/%Y")
            source = input("Enter source: ").strip()
            amount_SAR = float(input(f"Enter amount in {settings.get_account().exchange_rate_label}: ").strip())
            amount_USD = float(input("Enter amount in USD: ").strip())
            rate_exchange = amount_SAR / amount_USD
            withdraw_funds(fund_date, source, amount_SAR, amount_USD, rate_exchange, settings=settings)

        except ValueError as e:
            console.print(f"[red]Invalid input: {e}[/red]")
        input("Press Enter to continue...")
    elif choicee == 'p':
        # Connect to database
        conn = sqlite3.connect(get_db_path( settings.default_account ))
        cursor = conn.cursor()
        trade_id_input = input("Enter Trade ID to view trade details: ").strip()
        if trade_id_input.isdigit():
            trade_id = int(trade_id_input)
            cursor.execute("SELECT ID, trade_date, symbol, opr, filled_qty, price, fees, vat, cost_value, profit_loss, is_position_open FROM TRADES WHERE ID = ?", (trade_id,))
            trade = cursor.fetchone()
            if trade:
                ID, trade_date, symbol, opr, filled_qty, price, fees, vat, cost_value, profit_loss, is_position_open = trade
                is_position_open_text = "OPEN" if is_position_open == 1 else "CLOSED"
                console.print(f"""
Trade Details:
ID: {ID}
Date: {trade_date}
Symbol: {symbol}
Operation: {opr} ({is_position_open_text})
Quantity: {filled_qty}
Price: ${price:,.2f}
Fees: ${fees:,.2f}
VAT: ${vat:,.2f}
Cost Value: ${cost_value:,.2f}
Profit/Loss: ${profit_loss:,.2f}
                """)
                console.print("[blue]Options for Trade:[/blue] C[dim]lose Position,[/dim] O[dim]pen Position or[/dim] Enter [dim]to go back[/dim]")
                mark_pos_input = input("Enter choice: ").strip().lower()
                if mark_pos_input == 'c':
                    # Close position
                    pl_input = input("Enter realized Profit/Loss for this trade (or press Enter to keep existing): ").strip()
                    if pl_input:
                        try:
                            profit_loss = float(pl_input)
                            update_trade(trade_id, profit_loss=profit_loss, is_position_open=0, settings=settings)
                            console.print(f"[green]Trade ID {trade_id} marked as CLOSED.[/green]")
                        except ValueError:
                            console.print("[red]Invalid Profit/Loss input. Keeping existing value.[/red]")
                    else:
                        update_trade(trade_id, is_position_open=0, settings=settings)
                        console.print(f"[green]Trade ID {trade_id} marked as CLOSED.[/green]")
                elif mark_pos_input == 'o':
                    # Open position
                    update_trade(trade_id, is_position_open=1, settings=settings)
                    console.print(f"[green]Trade ID {trade_id} marked as OPEN.[/green]")
            else:
                console.print(f"[red]No trade found with ID {trade_id}.[/red]")
        else:
            console.print("[red]Invalid Trade ID input.[/red]")
        input("Press Enter to continue...")
        conn.close()
        
    elif choicee == 's':
        sar = float(input(f"Enter USD to {settings.get_account().exchange_rate_label} exchange rate (current {settings.get_account().exchange_rate}): ").strip() or settings.get_account().exchange_rate)
        fees_usd = float(input(f"Enter per trade fees in USD (current {settings.get_account().fees_usd}): ").strip() or settings.get_account().fees_usd)
        selected_ticker = input(f"Enter ticker symbol to track (current {settings.get_account().selected_ticker}): ").strip().upper() or settings.get_account().selected_ticker
        settings.get_account().selected_ticker = selected_ticker
        settings.get_account().fees_usd = fees_usd
        settings.get_account().exchange_rate = sar
        settings.save(settings_path)
        console.print(f"[green]Settings updated.[/green]")
        input("Press Enter to continue...")    
    