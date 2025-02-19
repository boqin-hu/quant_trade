import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List
from ..data.data_fetcher import DataFetcher
from ..config import SQLITE_DB_PATH
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)
Base = declarative_base()

class TradeRecord(Base):
    """交易记录数据模型"""
    __tablename__ = 'trade_records'
    
    id = Column(Integer, primary_key=True)
    ts_code = Column(String(20))
    direction = Column(String(4))  # buy/sell
    price = Column(Float)
    volume = Column(Integer)
    trade_time = Column(DateTime)
    strategy = Column(String(50))
    account = Column(String(20))
    status = Column(String(10))  # filled/canceled

class TradeExecutor:
    """交易执行模块"""
    
    def __init__(self, fetcher: DataFetcher):
        self.fetcher = fetcher
        self.engine = create_engine(f'sqlite:///{SQLITE_DB_PATH}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
    def execute_order(self, orders: List[Dict]):
        """执行交易订单"""
        session = self.Session()
        try:
            for order in orders:
                record = TradeRecord(
                    ts_code=order['ts_code'],
                    direction=order['direction'],
                    price=order['price'],
                    volume=order['volume'],
                    trade_time=datetime.now(),
                    strategy=order.get('strategy', 'manual'),
                    account=order.get('account', 'default'),
                    status='filled'
                )
                session.add(record)
                logger.info(f"执行订单: {order['direction']} {order['ts_code']} {order['volume']}股 @ {order['price']}")
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"交易执行失败: {str(e)}")
            raise
        finally:
            session.close()

    def get_position(self, account: str = 'default') -> pd.DataFrame:
        """获取当前持仓"""
        session = self.Session()
        try:
            query = f"""
                SELECT ts_code, 
                       SUM(CASE WHEN direction='buy' THEN volume ELSE -volume END) as position
                FROM trade_records 
                WHERE account='{account}' AND status='filled'
                GROUP BY ts_code
                HAVING position > 0
            """
            return pd.read_sql(query, session.connection())
        finally:
            session.close()

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, fetcher: DataFetcher):
        self.fetcher = fetcher
        self.engine = create_engine(f'sqlite:///{SQLITE_DB_PATH}')
        
    def run_backtest(self, strategy, start_date: str, end_date: str):
        """运行回测"""
        pass

if __name__ == "__main__":
    # 示例用法
    from ..data.data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    executor = TradeExecutor(fetcher)
    
    # 示例订单
    orders = [{
        'ts_code': '000001.SZ',
        'direction': 'buy',
        'price': 15.6,
        'volume': 1000,
        'strategy': 'momentum'
    }]
    executor.execute_order(orders)
    print(executor.get_position())
