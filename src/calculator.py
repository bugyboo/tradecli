
from settings import Settings
from rich.console import Console

def calc_menu(settings: Settings=Settings()):
    console = Console()    
    try:
        account = settings.get_account()
        secondary_currency = account.exchange_rate_label
        exchange_rate = account.exchange_rate
        
        while True:
            console.print("\n[bold blue]Calculator Menu[/bold blue]")
            console.print("1. Percentage Calculation")
            console.print(f"2. Currency Conversion (USD to {secondary_currency})")
            choice = input("Select an option (1-2) or Enter to exit: ").strip()
            
            if choice == "1":
                percentage_calculation(console)
            elif choice == "2":
                currency_conversion(console, secondary_currency, exchange_rate)
            else:
                break
    except KeyboardInterrupt:
        console.print("\n[red]Exiting calculator menu.[/red]")
        input("Press Enter to continue...")

def percentage_calculation(console: Console):
    console.print("\n[bold cyan]Percentage Calculation[/bold cyan]")
    console.print("1. Calculate percentage of a number (X% of Y)")
    console.print("2. Calculate what percentage X is of Y")
    console.print("3. Calculate percentage change")
    
    sub_choice = input("Select option (1-3): ").strip()
    
    try:
        if sub_choice == "1":
            percentage = float(input("Enter percentage: ").strip())
            number = float(input("Enter number: ").strip())
            result = (percentage / 100) * number
            console.print(f"[green]{percentage}% of {number} = {result:,.4f}[/green]")
        elif sub_choice == "2":
            part = float(input("Enter the part (X): ").strip())
            whole = float(input("Enter the whole (Y): ").strip())
            if whole == 0:
                console.print("[red]Error: Division by zero![/red]")
                return
            result = (part / whole) * 100
            console.print(f"[green]{part} is {result:,.2f}% of {whole}[/green]")
        elif sub_choice == "3":
            old_value = float(input("Enter old value: ").strip())
            new_value = float(input("Enter new value: ").strip())
            if old_value == 0:
                console.print("[red]Error: Old value cannot be zero![/red]")
                return
            change = ((new_value - old_value) / old_value) * 100
            direction = "increase" if change > 0 else "decrease"
            console.print(f"[green]Percentage {direction}: {abs(change):,.2f}%[/green]")
        else:
            console.print("[red]Invalid option![/red]")
    except ValueError:
        console.print("[red]Invalid input. Please enter valid numbers.[/red]")

def currency_conversion(console: Console, secondary_currency: str, exchange_rate: float):
    console.print(f"\n[bold cyan]Currency Conversion (USD ↔ {secondary_currency})[/bold cyan]")
    console.print(f"Current exchange rate: 1 USD = {exchange_rate} {secondary_currency}")
    console.print(f"1. USD to {secondary_currency}")
    console.print(f"2. {secondary_currency} to USD")
    
    sub_choice = input("Select option (1-2): ").strip()
    
    try:
        if sub_choice == "1":
            usd_amount = float(input("Enter amount in USD: ").strip())
            result = usd_amount * exchange_rate
            console.print(f"[green]${usd_amount:,.2f} USD = {result:,.2f} {secondary_currency}[/green]")
        elif sub_choice == "2":
            secondary_amount = float(input(f"Enter amount in {secondary_currency}: ").strip())
            if exchange_rate == 0:
                console.print("[red]Error: Exchange rate cannot be zero![/red]")
                return
            result = secondary_amount / exchange_rate
            console.print(f"[green]{secondary_amount:,.2f} {secondary_currency} = ${result:,.2f} USD[/green]")
        else:
            console.print("[red]Invalid option![/red]")
    except ValueError:
        console.print("[red]Invalid input. Please enter valid numbers.[/red]")
