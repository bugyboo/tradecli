from __future__ import annotations
import json
import os
from rich.console import Console
from dataclasses import dataclass, asdict, field

@dataclass
class Account:
    name: str
    exchange_rate_label: str = "SAR"
    exchange_rate: float = 3.7487
    selected_ticker: str = "$TSLA"
    fees_usd: float = 2.08    

@dataclass
class Settings:
    default_account: str = "traders"
    accounts: list[Account] = field(default_factory=list)
    
    def __init__(self, default_account: str = "traders", accounts: list[Account] | None = None):
        self.default_account = default_account
        if accounts is None:
            self.accounts = [Account(name="traders")]
        else:
            self.accounts = accounts

    def to_dict(self) -> dict:
        return asdict(self)
    
    def has_account(self, account_name: str) -> bool:
        return any(account.name == account_name for account in self.accounts)   
    
    def get_account(self) -> Account:
        for account in self.accounts:
            if account.name == self.default_account:
                return account
        # If not found, return a default account
        return Account(name=self.default_account) 

    @classmethod
    def from_dict(cls, data: dict) -> Settings:
        if "default_account" not in data:
            data["default_account"] = "traders"
        if "accounts" not in data:
            data["accounts"] = []
            acc = Account(name="traders")
            data["accounts"].append(asdict(acc))
        if data["default_account"] and not any(acc["name"] == data["default_account"] for acc in data["accounts"]):
            acc = Account(name=data["default_account"])
            data["accounts"].append(asdict(acc))            
            
        accounts = [Account(**acc) for acc in data["accounts"]]
        return cls(default_account=data["default_account"], accounts=accounts)

    def save(self, path: str) -> None:
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load(cls, path: str) -> Settings | None:
        if not os.path.exists(path):
            return cls()
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, ValueError):
            # If JSON is invalid or empty, return default settings            
            return None
        
def load_settings(settings_path: str) -> Settings:
    # Load or create settings
    console = Console()
    
    if not os.path.exists(settings_path):
        try:
            account_name = input("Enter account name (default traders) No spaces or special characters: ").strip() or "traders"
            scar_label_input = "Enter secondary currency label (default SAR): "
            scar_label = input(scar_label_input).strip().upper() or "SAR"
            scar_input = input(f"Enter USD to {scar_label} exchange rate: ").strip()
            scar = float(scar_input) or 3.7487     
            selected_ticker = input("Enter default ticker symbol to track (e.g., $TSLA): ").strip().upper() or "$TSLA"
            fees_usd = float(input("Enter per trade fees in USD (default 2.08): ").strip() or 2.08)
            account = Account(name=account_name, exchange_rate=scar, exchange_rate_label=scar_label, selected_ticker=selected_ticker, fees_usd=fees_usd)           
            settings = Settings(default_account=account_name, accounts=[account])
            settings.save(settings_path)
            return settings
        except ValueError:
            console.print("[red]Invalid input. Using defaults rate[/red]")
            settings = Settings()
            settings.save(settings_path)
            return settings
    else:
        settings = Settings.load(settings_path)
        if settings is None:
            console.print("[red]Settings file is corrupted. Using default settings.[/red]")
            settings = Settings()
        settings.save(settings_path)
        return settings 
