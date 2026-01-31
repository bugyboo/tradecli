"""
Trade Chart Visualization using Rich Console
Vertical chart (Price on X-axis, Time on Y-axis) for better clarity and range filtering.
"""
import sqlite3
import os
import math
from datetime import datetime
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt, FloatPrompt, Confirm
from utils import get_db_path
from settings import Settings


def get_trades_for_chart(symbol: str, settings: Settings = Settings()) -> list:
    """
    Fetch all trades for a given symbol from the database.
    Returns list of tuples: (id, trade_date, opr, filled_qty, price, is_position_open)
    """
    try:
        conn = sqlite3.connect(get_db_path(settings.default_account))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, trade_date, opr, filled_qty, price, is_position_open 
            FROM TRADES 
            WHERE symbol = ?
            ORDER BY price DESC, SUBSTR(trade_date, 7, 4) ASC
        """, (symbol,))
        trades = cursor.fetchall()
        conn.close()
        return trades
    except sqlite3.Error:
        return []


def draw_chart(symbol: str, current_price: float = None, 
               focus_price: float = None, price_range: float = None,
               settings: Settings = Settings()):
    """
    Draw a vertical text-based chart using Rich console.
    X-Axis: Price range
    Y-Axis: Trades (trade_date sorted list)
    """
    console = Console()
    console.clear()
    
    trades = get_trades_for_chart(symbol, settings)
    
    if not trades:
        console.print(Panel(
            f"[yellow]No trades found for symbol: {symbol}[/yellow]",
            title="Chart",
            border_style="red"
        ))
        return
    
    # Filter trades if focus params are provided
    min_filter = None
    max_filter = None
    
    if focus_price is not None and price_range is not None:
        min_filter = focus_price - price_range
        max_filter = focus_price + price_range
        
        # Keep original count for info
        total_trades = len(trades)
        trades = [t for t in trades if min_filter <= t[4] <= max_filter]
        
        if not trades:
            console.print(Panel(
                f"[yellow]No trades found in range ${min_filter:.2f} - ${max_filter:.2f}[/yellow]\n"
                f"[dim]Total trades for {symbol}: {total_trades}[/dim]",
                title="Chart Filtered",
                border_style="red"
            ))
            return

    # Determine Chart Price Bounds
    prices = [t[4] for t in trades]
    if current_price:
        prices.append(current_price)
        
    data_min = min(prices)
    data_max = max(prices)
    
    if min_filter is not None:
        # Use user defined range, but ensure we show at least the data inside to avoid confusing empty edges?
        chart_min = min_filter
        chart_max = max_filter
    else:
        # Auto-scale
        padding = (data_max - data_min) * 0.1 if data_max != data_min else data_max * 0.05
        chart_min = max(0, data_min - padding)
        chart_max = data_max + padding

    if chart_min >= chart_max:
        chart_min = chart_max - 1.0

    chart_span = chart_max - chart_min
    
    # Layout configuration
    # Info: "MM/YY $PRICE |"
    # Width: 5 + 1 + 4 + 1 + 2 + 1 = ~14 chars
    info_width = 16
    # Determine available width for the plot
    term_width = console.size.width
    available_width = max(40, term_width - info_width - 6)
    
    def price_to_col(p):
        if chart_span == 0: return 0
        rel = (p - chart_min) / chart_span
        col = int(rel * (available_width - 1))
        return max(0, min(available_width - 1, col))

    def make_axis_row():
        # Generate ticks (e.g., 5-7 ticks)
        num_ticks = max(3, available_width // 10)
        tick_step = chart_span / (num_ticks - 1)
        row = [" "] * available_width
        
        for i in range(num_ticks):
            val = chart_min + i * tick_step
            col = price_to_col(val)
            label = f"{val:.0f}"
            
            # Center label
            start = col - len(label) // 2
            for j, c in enumerate(label):
                if 0 <= start + j < available_width:
                    row[start + j] = c
        return "".join(row)

    # Build the Chart Content
    chart_text = Text()
    
    # Header: Axis
    chart_text.append(f"{' ' * ( info_width - 1 )}", style="")
    chart_text.append(make_axis_row(), style="dim cyan")
    chart_text.append("\n")
    
    chart_text.append(f"{'Date':>5} {'Price':>6} ", style="bold underline")
    chart_text.append(" └" + "─" * available_width + "┘\n", style="cyan")
    
    for i, trade in enumerate(trades):
        t_id, t_date, opr, qty, price, is_open = trade
        
        # 1. Info Column
        # Substring date to MM/YY
        try:
            dt_mm_str = t_date[3:5]  # MM/DD/YYYY -> MM
            dt_yy_str = t_date[8:10]  # MM/DD/YYYY -> YY
            dt_str = f"{dt_mm_str}/{dt_yy_str}"
        except:
            dt_str = t_date

            
        # Color coding
        if opr == 'buy':
            style_color = "blue" if is_open else "green"
            icon = "◆" if is_open else "●"
        else:
            style_color = "red"
            icon = "○"
            
        line_prefix = f"{dt_str:>5} {price:>4.2f} │ "
        chart_text.append(line_prefix, style=f"bold {style_color}")
        
        # 2. Plot Column
        row_chars = [" "] * (available_width)
        
        # Add current price indicator line logic (vertical line represented in each row)
        # We can just put a faint '|' for current market price if provided
        if current_price and chart_min <= current_price <= chart_max:
             cp_col = price_to_col(current_price)
             row_chars[cp_col] = "│"
             
        # Place trade marker
        col = price_to_col(price)
        row_chars[col] = icon
        
        # Render row
        row_text = Text("".join(row_chars))
        
        # Color the current price line
        if current_price and chart_min <= current_price <= chart_max:
             cp_col = price_to_col(current_price)
             row_text.stylize("dim magenta", cp_col, cp_col+1)
             
        # Color the trade marker
        row_text.stylize(f"bold {style_color}", col, col+1)
        
        chart_text.append(row_text)
        chart_text.append(" │\n", style="dim")
        
        # Every 30 rows, repeat axis for readability
        if (i + 1) % 35 == 0:
            chart_text.append(f"{' ' * (info_width - 2)}└{'─' * available_width}┘\n", style="cyan")
            chart_text.append(f"{' ' * (info_width - 2)} ", style="")
            chart_text.append(make_axis_row(), style="dim cyan")
            chart_text.append("\n")
        
    # Bottom Axis repeated
    chart_text.append(f"{' ' * (info_width - 2)}┌{'─' * available_width}┐\n", style="cyan")
    chart_text.append(f"{' ' * (info_width - 2)} ", style="")
    chart_text.append(make_axis_row(), style="dim cyan")
    
    # Footer info
    footer = f"\n\n  [bold]Legend:[/bold] [blue]◆ Open Buy[/blue] | [green]● Closed Buy[/green] | [red]○ Sell[/red]"
    if current_price:
        footer += f" | [magenta]│ Current: ${current_price:.2f}[/magenta]"        
    
    title = f"Trade Chart: {symbol}"
    if min_filter:
        title += f" [Filter: {min_filter:.1f} - {max_filter:.1f}]"
        
    console.print(Panel(chart_text, title=title, border_style="blue"))
    console.print(footer)


def show_chart_menu(current_price=None, settings: Settings = Settings()):
    """
    Interactive menu to select symbol and display chart.
    """
    console = Console()
    
    while True:
        console.clear()
        
        # Fetch all unique symbols
        try:
            conn = sqlite3.connect(get_db_path(settings.default_account))
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT symbol FROM TRADES")
            symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
        except sqlite3.Error:
            console.print("[red]Error fetching symbols from database.[/red]")
            return
        
        if not symbols:
            console.print("[yellow]No trades found. Add some trades first.[/yellow]")
            Prompt.ask("\nPress Enter to return")
            return
        
        console.print(Panel("[bold cyan]📊 Trade Chart Viewer[/bold cyan]", border_style="blue"))
        console.print("\n[bold]Available Symbols:[/bold]")
        
        for i, symbol in enumerate(symbols, 1):
            console.print(f"  {i}. {symbol}")
        
        console.print(f"\n  0. Back to main menu")
        
        choice = Prompt.ask("\nSelect symbol number", default="0")
        
        if choice == '0':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(symbols):
                selected_symbol = symbols[idx]                
                
                # Filter Dialog
                if Confirm.ask("Do you want to focus on a specific price range?", default=True):
                    try:
                        focus_p = FloatPrompt.ask("Enter center price")
                        rng = FloatPrompt.ask("Enter +/- range", default=20.0)
                        
                        draw_chart(selected_symbol, current_price=focus_p, 
                                   focus_price=focus_p, price_range=rng,
                                   settings=settings)
                    except ValueError:
                        console.print("[red]Invalid numbers provided.[/red]")
                elif current_price is not None:                    
                    draw_chart(selected_symbol, current_price=current_price, focus_price=None, price_range=None, settings=settings)
                
                Prompt.ask("\nPress Enter to continue")
            else:
                console.print("[red]Invalid selection.[/red]")
                Prompt.ask("Press Enter to continue")
        except ValueError:
            console.print("[red]Invalid input.[/red]")
            Prompt.ask("Press Enter to continue")

if __name__ == "__main__":
    show_chart_menu()
