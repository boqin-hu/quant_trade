import pandas as pd
import numpy as np
import logging
from typing import List, Dict
from tqdm import tqdm
from ..data.data_fetcher import DataFetcher
from ..config import LOG_CONFIG

logger = logging.getLogger(__name__)

class StockSelectionStrategy:
    """选股策略基类"""
    
    def __init__(self, fetcher: DataFetcher):
        self.fetcher = fetcher
        self.params = self.default_params()
        
    def default_params(self) -> Dict:
        """返回策略默认参数"""
        return {}
    
    def set_params(self, **kwargs):
        """动态更新策略参数"""
        self.params.update(kwargs)
        
    def screen(self, universe: List[str], date: str) -> List[str]:
        """执行选股逻辑"""
        raise NotImplementedError

class ValueInvestingStrategy(StockSelectionStrategy):
    """价值投资策略（市盈率+市净率+股息率）"""
    
    def default_params(self):
        return {
            'pe_max': 15,
            'pb_max': 1.5,
            'div_min': 3,
            'market_cap_min': 50  # 单位：亿
        }
    
    def screen(self, universe: List[str], date: str) -> List[str]:
        selected = []
        
        for ts_code in tqdm(universe, desc="价值选股"):
            try:
                # 获取基本面数据
                df = self.fetcher.fetch_financial_data(ts_code)
                latest = df.iloc[-1]
                
                # 估值指标筛选
                if (latest.pe_ttm <= self.params['pe_max'] and 
                    latest.pb <= self.params['pb_max'] and 
                    latest.dividend_yield >= self.params['div_min']/100 and 
                    latest.total_mv >= self.params['market_cap_min']*1e8):
                    selected.append(ts_code)
                    
            except Exception as e:
                logger.error(f"{ts_code} 数据处理失败: {str(e)}")
                
        return selected

class MomentumStrategy(StockSelectionStrategy):
    """动量效应策略"""
    
    def default_params(self):
        return {
            'lookback_window': 20,
            'return_threshold': 0.15,
            'volume_growth': 0.3
        }
    
    def screen(self, universe: List[str], date: str) -> List[str]:
        selected = []
        
        for ts_code in tqdm(universe, desc="动量选股"):
            try:
                # 获取历史数据
                df = self.fetcher.get_stock_data(ts_code, 
                    start_date=pd.to_datetime(date)-pd.DateOffset(days=60),
                    end_date=date)
                
                if len(df) < self.params['lookback_window']:
                    continue
                    
                # 计算收益率和成交量变化
                returns = df['close'].pct_change(self.params['lookback_window']).iloc[-1]
                vol_growth = df['vol'].iloc[-self.params['lookback_window']:].mean() / \
                            df['vol'].iloc[-2*self.params['lookback_window']:-self.params['lookback_window']].mean() - 1
                
                if returns >= self.params['return_threshold'] and vol_growth >= self.params['volume_growth']:
                    selected.append(ts_code)
                    
            except Exception as e:
                logger.error(f"{ts_code} 动量分析失败: {str(e)}")
                
        return selected

class FactorCompositeStrategy(StockSelectionStrategy):
    """多因子合成策略"""
    
    def default_params(self):
        return {
            'factors': ['pe', 'pb', 'roe', 'momentum'],
            'weights': [0.3, 0.2, 0.3, 0.2],
            'top_n': 30
        }
    
    def screen(self, universe: List[str], date: str) -> List[str]:
        scores = []
        
        for ts_code in tqdm(universe, desc="多因子选股"):
            try:
                # 获取财务数据
                fin_data = self.fetcher.fetch_financial_data(ts_code).iloc[-1]
                # 获取行情数据
                price_data = self.fetcher.get_stock_data(ts_code, 
                    start_date=pd.to_datetime(date)-pd.DateOffset(days=60),
                    end_date=date)
                
                # 计算各因子
                factors = {
                    'pe': 1 / fin_data.pe_ttm,
                    'pb': 1 / fin_data.pb,
                    'roe': fin_data.roe,
                    'momentum': price_data['close'].pct_change(20).iloc[-1]
                }
                
                # 合成得分
                score = sum(factors[f]*w for f,w in zip(self.params['factors'], self.params['weights']))
                scores.append((ts_code, score))
                
            except Exception as e:
                logger.error(f"{ts_code} 因子计算失败: {str(e)}")
                continue
                
        # 按得分排序取前N
        scores.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in scores[:self.params['top_n']]]

if __name__ == "__main__":
    # 示例用法
    from ..data.data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    strategy = FactorCompositeStrategy(fetcher)
    
    test_universe = ['000001.SZ', '600000.SH', '300750.SZ']
    selected = strategy.screen(test_universe, '20231231')
    print(f"选中股票: {selected}")
