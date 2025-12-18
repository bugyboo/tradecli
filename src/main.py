import sqlite3
from datetime import datetime
from rich.console import Console
from rich.table import Table
from filter_trades import filter_menu
from calculator import calc_menu
from trade import buy_menu, sell_menu, delete_trade, delete_trade_menu
from planner import plan_menu
from menu import main_menu
from utils import get_db_path, get_exec_path
import migrate
from settings import load_settings
import yfinance as yf   

def main():
    
    console = Console()    
    
    try:
        
        settings_path = get_exec_path( 'settings.json' )    
        
        selected_price = None     
        
        current_prices = {}        
        
        settings = load_settings(settings_path)
            
        selected_ticker = settings.get_account().selected_ticker
            
        migrate.check_and_migrate( settings )    
        
        while True:    
        
            # Connect to database
            conn = sqlite3.connect(get_db_path( settings.default_account ))
            cursor = conn.cursor()

            # Total Funds USD
            cursor.execute("SELECT COALESCE(SUM(CASE WHEN opr='deposit' THEN amount_USD ELSE -amount_USD END), 0) FROM FUNDS")
            total_funds = cursor.fetchone()[0]
            
            # Total Funds SAR
            cursor.execute("SELECT COALESCE(SUM(CASE WHEN opr='deposit' THEN amount_SAR ELSE -amount_SAR END), 0) FROM FUNDS")
            total_funds_sar = cursor.fetchone()[0]

            # Total Net Profit (realized amount)
            cursor.execute("SELECT COALESCE(SUM(profit_loss), 0) FROM TRADES")
            all_net_profit = cursor.fetchone()[0]                
            
            # Total Cash = Total buy cost value - Total sell cost value
            cursor.execute("SELECT COALESCE(SUM(CASE WHEN opr='buy' THEN cost_value ELSE -cost_value END), 0) FROM TRADES")
            total_cost = cursor.fetchone()[0]
            total_cash = total_funds - total_cost        
            
            # Total Fees, VAT
            cursor.execute("SELECT SUM(fees), SUM(vat) FROM TRADES")
            fees_vat = cursor.fetchone()
            total_fees = fees_vat[0] if fees_vat[0] else 0
            total_vat = fees_vat[1] if fees_vat[1] else 0
            
            # Total Trades buy count
            cursor.execute("SELECT COUNT(*) FROM TRADES WHERE opr='buy'")
            trade_buy_counts = cursor.fetchall()
            total_buy_trades = trade_buy_counts[0][0] if trade_buy_counts else 0
            
            # Total Trades sell count
            cursor.execute("SELECT COUNT(*) FROM TRADES WHERE opr='sell'")
            trade_sell_counts = cursor.fetchall()
            total_sell_trades = trade_sell_counts[0][0] if trade_sell_counts else 0

            # Ticker data
            cursor.execute("""
            SELECT symbol,
            SUM(CASE WHEN opr='buy' THEN filled_qty ELSE -filled_qty END) as net_shares,
            SUM(CASE WHEN opr='buy' THEN cost_value ELSE -cost_value END) as total_cost,
            COALESCE(SUM(profit_loss), 0) as profit,
            (SELECT price FROM TRADES t2 WHERE t2.symbol = t.symbol AND opr = 'buy' ORDER BY price DESC LIMIT 1) as last_price
            FROM TRADES t
            GROUP BY symbol
            HAVING net_shares != 0
            """)
            tickers = cursor.fetchall()

            # Initialize current prices with last price
            if not current_prices or selected_ticker not in current_prices:
                current_prices = {row[0]: row[4] for row in tickers}        
            if selected_price:
                try:
                    current_prices[selected_ticker] = float(selected_price)
                except ValueError:
                    console.print(f"[red]Invalid price input for {selected_ticker}. Using last price from database.[/red]")

            # Get open positions for all tickers
            symbols = [row[0] for row in tickers]
            trades = []
            if symbols:
                placeholders = ','.join('?' * len(symbols))
                cursor.execute(f"SELECT ID, trade_date, symbol, opr, filled_qty, price, fees, vat, cost_value, profit_loss FROM TRADES WHERE symbol IN ({placeholders}) AND is_position_open = 1 ORDER BY price", symbols)
                trades = cursor.fetchall()

            conn.close()

            # Get ticker data with current prices
            ticker_data = []
            for row in tickers:
                symbol, ticker_net_shares, ticker_total_cost, ticker_profit, _ = row
                ticker_current_price = current_prices.get(symbol, 0)
                ticker_data.append((symbol, ticker_net_shares, ticker_total_cost, ticker_profit, ticker_current_price))

            # Calculations
            total_market_value = sum(row[1] * row[4] for row in ticker_data)
            total_unrealized_pl = total_market_value - total_cost
            total_pl = all_net_profit + total_unrealized_pl

            # Clear console and display panels
            console.clear()

            # Trades table
            if trades:
                trades_table = Table(title="Open Positions")
                trades_table.add_column("#", style="yellow")            
                trades_table.add_column("Date", style="dim")
                trades_table.add_column("Ticker", style="cyan")
                trades_table.add_column("Operation", justify="left")
                trades_table.add_column("Qty", justify="right")
                trades_table.add_column("Price", justify="right", style="yellow")
                trades_table.add_column("Cost Value", justify="right")
                trades_table.add_column("Cost Price", justify="right", style="yellow")
                trades_table.add_column("Profit/Loss", justify="right")
                trades_table.add_column(f" {settings.get_account().exchange_rate_label} ", justify="right")

                counter = 1
                total_qty = 0
                total_cost_value = 0
                sub_pl = 0
                for trade in trades:
                    ID, trade_date, symbol, opr, filled_qty, price, fees, vat, cost_value, profit_loss = trade
                    current_price = current_prices.get(symbol, price)
                    if opr.lower() == 'buy':
                        pl = ( (current_price - price) * filled_qty ) - settings.get_account().fees_usd * 2
                    else:
                        pl = profit_loss or 0
                    pl_text = f"[red]${pl:,.2f}[/red]" if pl < 0 else f"${pl:,.2f}"
                    pl_text_percent = (pl / cost_value) if cost_value != 0 else 0
                    pl_text_sar = f"[red]{pl * settings.get_account().exchange_rate:,.2f}[/red]" if pl < 0 else f"{pl * settings.get_account().exchange_rate :,.2f}"
                    opr_text = f"[green]{opr}[/green]" if opr.lower() == 'buy' else f"[red]{opr}[/red]"
                    trades_table.add_row(str(counter), str(trade_date), symbol, f"{opr_text} #{str(ID)}", str(filled_qty), f"${price:,.2f}", f"${cost_value:,.2f}", f"{((filled_qty * price) + settings.get_account().fees_usd) / filled_qty :,.2f}", F"{pl_text} [dim]{pl_text_percent:.2%}[/dim]", pl_text_sar)
                    counter += 1
                    total_qty += filled_qty
                    total_cost_value += cost_value
                    sub_pl += pl

                # Add totals row
                trades_table.add_row("---", "---", "---", "---", "---", "---", "---", "---", "---")
                pl_text_total = f"[red]${sub_pl:,.2f}[/red]" if sub_pl < 0 else f"${sub_pl:,.2f}"
                pl_text_percent_total = (sub_pl / total_cost_value) if total_cost_value != 0 else 0
                pl_text_sar_total = f"[red]{sub_pl * settings.get_account().exchange_rate:,.2f}[/red]" if sub_pl < 0 else f"{sub_pl * settings.get_account().exchange_rate:,.2f}"
                trades_table.add_row("Total", "", "", "", str(total_qty), f"{total_cost_value / total_qty :,.2f}", f"${total_cost_value:,.2f}", "", f"{pl_text_total} [dim]{pl_text_percent_total:.2%}[/dim]", pl_text_sar_total)

                console.print(trades_table)
                
            if total_market_value == 0:
                cash_ratio = 0
            else:
                cash_ratio = total_cash / total_market_value
                

            # Ticker summary table
            table = Table(title="Summary of Holdings")
            table.add_column("Ticker", style="cyan")
            table.add_column("Shares", justify="right")
            table.add_column("Total Cost", justify="right")
            table.add_column("Market Value", justify="right", style="yellow")
            table.add_column("Unrealized P/L", justify="right")
            table.add_column("Realized P/L", justify="right")
            table.add_column("%, avg", justify="right")

            for row in ticker_data:
                symbol, net_shares, total_cost, profit, current_price = row
                market_value = net_shares * current_price
                unrealized_pl = market_value - total_cost
                unrealized_text = f"[red]${unrealized_pl:,.2f}[/red]" if unrealized_pl < 0 else f"${unrealized_pl:,.2f}"
                unrealized_text_sar = f"[red]{settings.get_account().exchange_rate_label} {unrealized_pl * settings.get_account().exchange_rate:,.2f}[/red]" if unrealized_pl < 0 else f"{settings.get_account().exchange_rate_label} {unrealized_pl * settings.get_account().exchange_rate:,.2f}"            
                profit_text = f"[red]${profit:,.2f}[/red]" if profit < 0 else f"${profit:,.2f}"
                profit_text_sar = f"[red]{settings.get_account().exchange_rate_label} {profit * settings.get_account().exchange_rate:,.2f}[/red]" if profit < 0 else f"{settings.get_account().exchange_rate_label} {profit * settings.get_account().exchange_rate:,.2f}"
                table.add_row(symbol, str(net_shares), f"${total_cost:,.2f}", f"${market_value:,.2f}", unrealized_text, profit_text, f"{unrealized_pl/total_funds:.2%}")
                table.add_row(f"[magenta]{current_price}[/magenta]", "", f"{settings.get_account().exchange_rate_label} {total_cost * settings.get_account().exchange_rate:,.2f}", f"{settings.get_account().exchange_rate_label} {market_value * settings.get_account().exchange_rate:,.2f}", unrealized_text_sar, profit_text_sar, f"{total_cost/net_shares:.2f}")
            console.print(table)
                
            # Account Totals table
            totals_table = Table(title=f"Account Totals ({settings.default_account})")
            totals_table.add_column("Funds", justify="right")
            totals_table.add_column(f"Cash [dim]{cash_ratio:.2%}[/dim]", justify="right", style="magenta")
            totals_table.add_column("Fees", justify="right")
            totals_table.add_column("VAT", justify="right")
            totals_table.add_column("Net Worth", justify="right", style="green")
            totals_table.add_column("Trades", justify="left")
            
            totals_table.add_row(f"${total_funds:,.2f}", f"${total_cash:,.2f}", f"${total_fees:,.2f}", f"${total_vat:,.2f}", f"${total_market_value + total_cash:,.2f}", f"{total_buy_trades} buy")
            totals_table.add_row(f"{settings.get_account().exchange_rate_label} {total_funds_sar:,.2f}", f"{settings.get_account().exchange_rate_label} {total_cash * settings.get_account().exchange_rate:,.2f}", f"{settings.get_account().exchange_rate_label} {total_fees * settings.get_account().exchange_rate:,.2f}", f"{settings.get_account().exchange_rate_label} {total_vat * settings.get_account().exchange_rate:,.2f}", f"{settings.get_account().exchange_rate_label} {(total_market_value + total_cash) * settings.get_account().exchange_rate:,.2f}", f"{total_sell_trades} sell")
            
            console.print(totals_table)
                    
            # ===============================================================================================
            # Prompt for input
            # ===============================================================================================
            
            console.print("[blue]Options:[/blue] M[dim]enu[/dim], B[dim]uy[/dim], S[dim]ell[/dim], D[dim]elete[/dim], T[dim]icker[/dim], F[dim]ilter[/dim], P[dim]lan[/dim], U[dim]pdate[/dim], C[dim]alculator[/dim] or Q[dim]uit[/dim]")
            user_input = input(f"Enter price for {selected_ticker} or options: ").strip()
            if user_input.lower() == 'q':
                break
            elif user_input.lower() == 'u':
                # Update current price for all tickers from yfinance lib
                console.print("[blue]Updating prices from yfinance...[/blue]")
                for symbol in symbols:
                    try:
                        stock = yf.Ticker(symbol.replace("$", ""))
                        current_prices[symbol] = stock.info['regularMarketPrice']
                        console.print(f"[green]Updated {symbol}: ${stock.info['regularMarketPrice']:.2f}[/green]")
                    except Exception as e:
                        console.print(f"[red]Failed to fetch price for {symbol}: {e}[/red]")
                if selected_ticker in current_prices:
                    selected_price = current_prices[selected_ticker]
                console.print("[green]Price update completed.[/green]")
                input("Press Enter to continue...")
            elif user_input.lower() == 'p':
                # Planning menu
                plan_menu(trades, selected_ticker, current_prices, settings)
            elif user_input.lower() == 'b':
                # Buy trade
                buy_menu(selected_ticker, current_prices, total_cash, settings=settings)
            elif user_input.lower() == 's':
                # Sell trade
                sell_menu(ticker_data, trades, selected_ticker, current_prices, settings=settings)
            elif user_input.lower() == 'd':
                # Delete trade
                delete_trade_menu(settings=settings)
            elif user_input.lower() == 't':
                # Change ticker
                selected_ticker = input("Enter new ticker symbol: ").strip().upper()
            elif user_input.lower() == 'f':
                # Filter trades menu
                filter_menu(settings=settings, current_prices=current_prices)
                
            elif user_input.lower() == 'm':
                # Main menu
                main_menu(settings, settings_path)
            
            elif user_input.lower() == 'c':
                calc_menu(settings=settings)

            else:
                # Assume price update
                try:
                    selected_price = float(user_input)
                except ValueError:
                    pass
    except KeyboardInterrupt:
        console.print("\n[red]Exiting application.[/red]")

if __name__ == "__main__":
    main()
