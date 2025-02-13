import sqlite3

def init_database():
    conn = sqlite3.connect('trading.db')
    cursor = conn.cursor()
    
    # 账户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            initial_balance REAL NOT NULL,
            current_balance REAL NOT NULL,
            holdings TEXT,  -- JSON格式存储持仓 {股票代码: 数量}
            daily_pnl REAL DEFAULT 0,
            total_pnl REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 交易记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            stock_code TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            action TEXT CHECK(action IN ('BUY', 'SELL')),
            timestamp INTEGER NOT NULL,
            FOREIGN KEY(account_id) REFERENCES accounts(account_id)
        )
    ''')
    
    # 策略信号表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategy_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            signal_type TEXT CHECK(signal_type IN ('GOLDEN_CROSS', 'DEATH_CROSS')),
            short_ma REAL NOT NULL,
            long_ma REAL NOT NULL,
            timestamp INTEGER NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully")
