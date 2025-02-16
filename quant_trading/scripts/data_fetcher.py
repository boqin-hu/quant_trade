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
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'jywg.18.cn',
            'Origin': 'https://jywg.18.cn',
            'Referer': 'https://jywg.18.cn/Login/Login',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
    def get_verify_code(self):
        verify_url = "https://jywg.18.cn/Login/GetVerifyCode"
        response = self.session.get(verify_url)
        with open("verify_code.jpg", "wb") as f:
            f.write(response.content)
        print("验证码已保存为verify_code.jpg，请查看并输入验证码")
        return input("请输入验证码: ")

    def login(self, retries=3):
        for attempt in range(retries):
            login_url = "https://jywg.18.cn/Login/Authentication"
            verify_code = self.get_verify_code()
            payload = {
                "userId": self.username,
                "password": self.password,
                "randNumber": verify_code,
                "identifyCode": "" 
            }
            time.sleep(2 ** attempt)  # 指数退避
        print(f"发送登录请求到: {login_url}")
        print(f"请求头: {self.headers}")
        print(f"请求参数: {payload}")
        response = self.session.post(login_url, data=payload, headers=self.headers)
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        print(f"响应内容: {response.text[:500]}")  # 显示前500字符
        try:
            return response.json().get('success', False)
        except Exception as e:
            print(f"登录响应解析失败: {str(e)}")
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
