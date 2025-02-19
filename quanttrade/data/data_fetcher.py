import requests
import pandas as pd
import tushare as ts
import logging
import time
from typing import Dict, Optional
from pathlib import Path
from fake_useragent import UserAgent
from ..config import TUSHARE_TOKEN, DATA_STORAGE

logger = logging.getLogger(__name__)

class DataFetcher:
    """统一数据获取接口，支持Tushare和网络爬虫"""
    
    def __init__(self):
        self.pro = ts.pro_api(TUSHARE_TOKEN)
        self.session = requests.Session()
        self.ua = UserAgent()
        self.cache_dir = DATA_STORAGE['stock_daily']
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置请求头
        self.headers = {
            'User-Agent': self.ua.random,
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
    def get_stock_data(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从Tushare获取股票日线数据"""
        try:
            df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            self._save_to_cache(df, f"{ts_code}_{start_date}_{end_date}.parquet")
            return df
        except Exception as e:
            logger.error(f"Tushare数据获取失败: {str(e)}")
            raise
            
    def fetch_financial_data(self, ts_code: str, report_type: str = 'annual') -> pd.DataFrame:
        """获取财务数据"""
        for _ in range(3):  # 重试机制
            try:
                if report_type == 'annual':
                    return self.pro.fina_indicator(ts_code=ts_code)
                elif report_type == 'quarterly':
                    return self.pro.fina_mainbz(ts_code=ts_code)
            except Exception as e:
                logger.warning(f"财务数据获取失败，重试中... ({str(e)})")
                time.sleep(2)
        raise Exception("财务数据获取失败")
    
    def crawler_get(self, url: str, params: Optional[Dict] = None, retry: int = 3) -> str:
        """通用爬虫GET方法"""
        for attempt in range(retry):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers={**self.headers, 'User-Agent': self.ua.random},
                    timeout=10
                )
                response.encoding = response.apparent_encoding
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.warning(f"请求失败 ({attempt+1}/{retry}): {str(e)}")
                time.sleep(2**attempt)
        raise Exception("爬虫请求失败")
    
    def _save_to_cache(self, df: pd.DataFrame, filename: str) -> None:
        """保存数据到本地缓存"""
        path = self.cache_dir / filename
        df.to_parquet(path)
        logger.info(f"数据已缓存至 {path}")

class AlternativeDataCrawler:
    """另类数据爬取基类"""
    
    def __init__(self, fetcher: DataFetcher):
        self.fetcher = fetcher
        
    def parse_html(self, html: str) -> pd.DataFrame:
        """解析HTML内容（需子类实现）"""
        raise NotImplementedError

class SinaStockCrawler(AlternativeDataCrawler):
    """新浪财经实时数据爬取"""
    
    def parse_html(self, html: str) -> pd.DataFrame:
        # 实现具体的HTML解析逻辑
        # 示例解析代码
        try:
            tables = pd.read_html(html)
            return tables[0]  # 假设目标数据在第一个表格
        except Exception as e:
            logger.error(f"HTML解析失败: {str(e)}")
            return pd.DataFrame()

if __name__ == "__main__":
    # 单元测试
    fetcher = DataFetcher()
    test_data = fetcher.get_stock_data("000001.SZ", "20230101", "20231231")
    print(test_data.head())
