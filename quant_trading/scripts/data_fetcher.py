import os
import requests
from bs4 import BeautifulSoup
import sqlite3
from dotenv import load_dotenv
import time
import random

load_dotenv()

class EastMoneyFetcher:
    def __init__(self):
        self.username = os.getenv('EAST_MONEY_USER')
        self.password = os.getenv('EAST_MONEY_PASS')
        self.session = requests.Session()
        self.base_url = "http://quote.eastmoney.com/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'tradegf.eastmoney.com',
            'Origin': 'https://tradegf.eastmoney.com',
            'Referer': 'https://tradegf.eastmoney.com/Login/Index',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
    def login(self):
        login_url = "https://tradegf.eastmoney.com/Login/LoginSubmit"
        payload = {
            'userCode': self.username,
            'password': self.password,
            'validateCode': '',
            'holdAccount': 'false'
        }
        response = self.session.post(login_url, data=payload, headers=self.headers)
        try:
            return response.json().get('success', False)
        except Exception as e:
            print(f"登录响应解析失败: {response.text}")
            return False

    def fetch_realtime_data(self, stock_code):
        url = f"{self.base_url}/usstock/{stock_code}.html"
        time.sleep(random.uniform(1, 3))  # 添加随机延迟
        proxies = {
            'http': 'http://proxy.example.com:8080',
            'https': 'http://proxy.example.com:8080'
        }
        response = self.session.get(url, headers=self.headers, proxies=proxies)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        price = soup.find('div', class_='stock-price').text.strip()
        volume = soup.find('div', class_='stock-volume').text.strip()
        return {
            'code': stock_code,
            'price': float(price),
            'volume': int(volume),
            'timestamp': int(time.time())
        }

class DataManager:
    def __init__(self):
        self.conn = sqlite3.connect('/Users/huboqin/work/vscode/quant_trading/data/trading.db')
        self.create_tables()
        
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                price REAL NOT NULL,
                volume INTEGER NOT NULL,
                timestamp INTEGER NOT NULL
            )
        ''')
        self.conn.commit()

    def save_market_data(self, data):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO market_data (code, price, volume, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (data['code'], data['price'], data['volume'], data['timestamp']))
        self.conn.commit()

if __name__ == "__main__":
    fetcher = EastMoneyFetcher()
    if fetcher.login():
        print("Login successful")
        sh600519 = fetcher.fetch_realtime_data('SH600519')
        manager = DataManager()
        manager.save_market_data(sh600519)
    else:
        print("Login failed")
