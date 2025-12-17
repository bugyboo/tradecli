-- Schema For TraderCLI application in SQLite

CREATE TABLE FUNDS (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    opr TEXT NOT NULL CHECK (opr IN ('deposit', 'withdraw')),
    fund_date TEXT NOT NULL,
    source TEXT NOT NULL,
    amount_SAR REAL NOT NULL,
    amount_USD REAL NOT NULL,
    rate_exchange REAL NOT NULL
);

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
