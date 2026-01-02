import sqlite3
from utils import get_db_path
from rich.console import Console
from rich.panel import Panel
from settings import Settings

def get_open_positions(ticker, account_name):
    """
    Retrieves open positions for a given ticker from the database.
    Returns a list of (filled_qty, price) tuples.
    """
    conn = sqlite3.connect(get_db_path(account_name))
    cursor = conn.cursor()
    cursor.execute("SELECT filled_qty, price FROM TRADES WHERE symbol = ? AND opr = 'buy' AND is_position_open = 1", (ticker,))
    positions = cursor.fetchall()
    conn.close()
    return positions

def calculate_position_summary(positions):
    """
    Calculates total shares and average cost from open positions.
    """
    if not positions:
        return 0, 0.0
    total_shares = sum(qty for qty, _ in positions)
    total_cost = sum(qty * price for qty, price in positions)
    avg_cost = total_cost / total_shares if total_shares > 0 else 0.0
    return total_shares, avg_cost

def collect_technical_levels(positions, ticker, current_price):
    """
    Asks the user for technical levels for the ticker.
    """
    ath_position = max(positions, key=lambda x: x[1]) if positions else (0, 0.0)
    current_resistance_position = max((pos for pos in positions if pos[1] < current_price), default=(0, 0.0), key=lambda x: x[1])
    avg_position_price = sum(qty * price for qty, price in positions) / sum(qty for qty, _ in positions) if positions else 0.0
    print(f"Collecting technical levels for {ticker}:")

    all_time_high = float(input(f"Enter all-time high zone (e.g., {ath_position[1]}): ") or ath_position[1])
    current_resistance = float(input(f"Enter current resistance (e.g., {current_resistance_position[1]}): ") or current_resistance_position[1])
    key_support1 = float(input(f"Enter key support 1 (e.g., {ath_position[1] * 0.9}): ") or ath_position[1] * 0.9)
    key_support2 = float(input(f"Enter key support 2 (e.g., {ath_position[1] * 0.8}): ") or ath_position[1] * 0.8)
    deeper_support = float(input(f"Enter deeper support (e.g., {avg_position_price:.2f}): ") or avg_position_price)
    return {
        'current_price': current_price,
        'all_time_high': all_time_high,
        'current_resistance': current_resistance,
        'key_support1': key_support1,
        'key_support2': key_support2,
        'deeper_support': deeper_support
    }

def calculate_risk_levels(shares, avg_cost, levels):
    """
    Calculates risk levels based on position and technical levels.
    """
    current_value = shares * levels['current_price']
    risks = {}
    for level_name, price in levels.items():
        if level_name == 'current_price':
            continue
        drawdown = (levels['current_price'] - price) / levels['current_price'] * 100
        value_at_level = shares * price
        loss = current_value - value_at_level
        risks[level_name] = {
            'price': price,
            'drawdown_percent': drawdown,
            'potential_loss': loss,
        }
    # Additional risk rules
    risks['normal_hold'] = f"Never risk more than 15-20% drawdown. Stop at ~${avg_cost * 0.8:.2f}/share"
    risks['swing_add'] = f"Risk 8-12% to support. Stop below ${levels['key_support1']:.2f}"
    risks['bear_protection'] = f"Cut 50% on weekly close below ${levels['key_support2']:.2f}"
    return risks

def print_risk_plan(ticker, shares, avg_cost, levels, risks, settings: Settings):
    """
    Prints the risk management plan to the console.
    """
    console = Console()
    content = f"Ticker : [magenta]{ticker}[/magenta]\n"
    content += f"Open Position: {shares} shares @ avg cost ${avg_cost:.2f} = ${shares * avg_cost:.2f} / {shares * avg_cost * settings.get_account().exchange_rate:.2f}\n"
    content += f"Current Value: ${shares * levels['current_price']:.2f} / {shares * levels['current_price'] * settings.get_account().exchange_rate:.2f}\n"
    content += "\n[yellow]Technical Levels:[/yellow]\n"
    for name, price in levels.items():
        content += f"  {name.replace('_', ' ').title()}: ${price:.2f}\n"
    content += "\n[yellow]Risk Scenarios:[/yellow]\n"
    for level, data in risks.items():
        if isinstance(data, dict):
            content += f"  {level.replace('_', ' ').title()}: ${data['price']:.2f} | Drawdown: {data['drawdown_percent']:.2f}% | Loss: ${data['potential_loss']:.2f} / {settings.get_account().exchange_rate * data['potential_loss']:.2f}\n"
        else:
            content += f"  {level.replace('_', ' ').title()}: {data}\n"
    content += "\n[yellow]Practical Plan:[/yellow]\n"
    content += "- Core position: Long-term hold, trailing stop never >20-22% drawdown.\n"
    content += "- Trading portion: Active risk, stop below key support 1.\n"
    content += "- Max portfolio risk: Keep under 20-25% of total assets.\n"
    
    panel = Panel(content, title="Risk Management Plan")
    console.print(panel)   
    input("\nPress Enter to continue...")
    
def plan( ticker, current_price, settings: Settings ):
    positions = get_open_positions(ticker, settings.default_account )
    if not positions:
        print(f"No open positions for {ticker}.")
        return
    shares, avg_cost = calculate_position_summary(positions)
    levels = collect_technical_levels(positions, ticker, current_price)
    risks = calculate_risk_levels(shares, avg_cost, levels)
    print_risk_plan(ticker, shares, avg_cost, levels, risks, settings)
    
def plan_menu(trades, selected_ticker, current_prices, settings: Settings):
    console = Console()
    console.print("[blue]Plan Options:[/blue] C[dim]alculate exit price or[/dim] Enter [dim]to go to planning[/dim]")
    plan_choice = input(f"Enter choice: ").strip().lower()
    if plan_choice == 'c':
        # Calculate exit price
        try:
            # enter trade Id's to calculate exit price form open positions
            trade_ids_input = input("Enter Trade IDs to calculate exit price (comma separated): ").strip()
            trade_ids = [int(tid.strip()) for tid in trade_ids_input.split(",") if tid.strip().isdigit()]
            if not trade_ids:
                console.print("[red]No valid Trade IDs entered.[/red]")
                input("Press Enter to continue...")
                return
            # Fetch the trades from trades above
            selected_trades = [trade for trade in trades if trade[0] in trade_ids]
            if not selected_trades:
                console.print("[red]No matching trades found for the given IDs.[/red]")
                input("Press Enter to continue...")
                return
            total_qty = sum(trade[4] for trade in selected_trades)
            total_cost_value = sum(trade[8] for trade in selected_trades)
            exit_choice = input("Calculate exit position for (P)rice profit or (D)esired profit in USD? ( P or D): ").strip().lower()
            if exit_choice == 'p':
                target_price = float(input("Enter target exit price: ").strip())
                exit_price = target_price
                achieved_profit_usd = (exit_price * total_qty) - total_cost_value
                console.print(f"[green]Calculated Exit Price: ${exit_price:.2f} for total quantity {total_qty} achieving profit of ${achieved_profit_usd:.2f}[/green]")
            elif exit_choice == 'd':
                desired_profit_usd = float(input("Enter desired profit in USD: ").strip())
                exit_price = (total_cost_value + desired_profit_usd) / total_qty
                console.print(f"[green]Calculated Exit Price: ${exit_price:.2f} for total quantity {total_qty} to achieve desired profit of ${desired_profit_usd:.2f}[/green]")
            input("Press Enter to continue...")
            return
        except ValueError as e:
            console.print(f"[red]Invalid input: {e}[/red]")
        except KeyboardInterrupt:
            console.print("\n[red]Exit price calculation cancelled by user.[/red]")
        input("Press Enter to continue...")
    else:
        # Go to planning
        plan( selected_ticker, current_prices[selected_ticker], settings )    
        
def main():
    ticker = input("Enter ticker symbol: ").upper()
    current_price = float(input("Enter current price: "))
    settings = Settings()
    plan(ticker, current_price, settings)

if __name__ == "__main__":
    main()

