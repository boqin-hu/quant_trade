import sqlite3
import time
from config.config import Config
from datetime import datetime

class DataReader:
    def __init__(self):
        self.db_path = Config.DB_URI.split('///')[1]
        self.conn = sqlite3.connect(self.db_path)
        
    def realtime_monitor(self):
        last_timestamp = None
        while True:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''SELECT * FROM realtime_data 
                               ORDER BY timestamp DESC LIMIT 1''')
                latest = cursor.fetchone()
                
                if latest and latest[0] != last_timestamp:
                    print(f"\nNew Data @ {latest[0]}")
                    print(f"Price: {latest[1]:.2f}")
                    print(f"Volume: {latest[2]}")
                    print(f"MA10: {latest[3]:.2f}")
                    print(f"MA50: {latest[4]:.2f}")
                    last_timestamp = latest[0]
                    
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                
            time.sleep(0.5)  # 更快的刷新频率

if __name__ == "__main__":
    reader = DataReader()
    reader.realtime_monitor()
