import time
import sqlite3
from datetime import datetime
import requests
from config.config import Config

class DataStorer:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_URI.split('///')[1])
        self.create_table()
        
    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS realtime_data
                         (timestamp DATETIME PRIMARY KEY,
                          price REAL,
                          volume INTEGER,
                          ma10 REAL,
                          ma50 REAL)''')
        self.conn.commit()

    def fetch_and_store(self):
        while True:
            try:
                # 模拟实时数据获取（替换为实际API调用）
                data = {
                    'timestamp': datetime.now(),
                    'price': 100 + (0.5 - time.time() % 1),
                    'volume': int(10000 * (0.5 + time.time() % 1)),
                    'ma10': 99.8 + time.time() % 0.5,
                    'ma50': 100.2 - time.time() % 0.3
                }
                
                cursor = self.conn.cursor()
                cursor.execute('''INSERT INTO realtime_data 
                               VALUES (?, ?, ?, ?, ?)''',
                               (data['timestamp'], data['price'], 
                                data['volume'], data['ma10'], data['ma50']))
                self.conn.commit()
                print(f"Stored data at {data['timestamp']}")
                
            except Exception as e:
                print(f"Error: {e}")
            
            time.sleep(1)  # 1秒间隔

if __name__ == "__main__":
    storer = DataStorer()
    storer.fetch_and_store()
