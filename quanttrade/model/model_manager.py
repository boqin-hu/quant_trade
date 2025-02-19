import pandas as pd
import numpy as np
import logging
import joblib
from datetime import datetime, timedelta
from typing import Dict, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from ..data.data_fetcher import DataFetcher
from ..config import DATA_STORAGE

logger = logging.getLogger(__name__)

class ModelManager:
    """模型管理类，负责模型的训练、更新和预测"""
    
    def __init__(self, fetcher: DataFetcher):
        self.fetcher = fetcher
        self.models: Dict[str, any] = {}
        self.model_storage = DATA_STORAGE['model']
        self.model_storage.mkdir(parents=True, exist_ok=True)
        
    def train_model(self, model_type: str = 'random_forest', **params):
        """训练新模型"""
        try:
            # 获取训练数据
            X, y = self._prepare_training_data()
            
            # 划分训练测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42)
            
            # 初始化模型
            if model_type == 'random_forest':
                model = RandomForestClassifier(
                    n_estimators=params.get('n_estimators', 100),
                    max_depth=params.get('max_depth', 5),
                    random_state=42
                )
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")
                
            # 训练模型
            model.fit(X_train, y_train)
            
            # 评估模型
            train_acc = accuracy_score(y_train, model.predict(X_train))
            test_acc = accuracy_score(y_test, model.predict(X_test))
            logger.info(f"模型训练完成 | 训练集准确率: {train_acc:.2%} | 测试集准确率: {test_acc:.2%}")
            
            # 保存模型
            model_name = f"{model_type}_{datetime.now().strftime('%Y%m%d%H%M')}.pkl"
            self._save_model(model, model_name)
            return model
            
        except Exception as e:
            logger.error(f"模型训练失败: {str(e)}")
            raise
    
    def update_model(self, model_name: str, sliding_window: int = 30):
        """推进式建模更新"""
        try:
            # 获取最新数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=sliding_window)
            new_data = self.fetcher.get_stock_data(
                "",  # 获取全市场数据
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d")
            )
            
            # 准备增量数据
            X_new, y_new = self._prepare_training_data(new_data)
            
            # 加载现有模型
            model = self._load_model(model_name)
            
            # 增量训练
            model.fit(X_new, y_new)
            logger.info(f"模型 {model_name} 已更新")
            
            # 保存更新后的模型
            self._save_model(model, model_name)
            
        except Exception as e:
            logger.error(f"模型更新失败: {str(e)}")
            raise
    
    def predict(self, model_name: str, X: pd.DataFrame) -> pd.Series:
        """使用指定模型进行预测"""
        model = self._load_model(model_name)
        return pd.Series(model.predict(X), index=X.index)
    
    def _prepare_training_data(self, data: Optional[pd.DataFrame] = None) -> tuple:
        """准备训练数据"""
        if data is None:
            # 获取全量历史数据
            data = self.fetcher.get_stock_data(
                "", 
                start_date="20100101",
                end_date=datetime.now().strftime("%Y%m%d")
            )
            
        # 特征工程
        features = data[['open', 'high', 'low', 'close', 'vol']].copy()
        features['returns'] = data['close'].pct_change()
        features['volatility'] = features['returns'].rolling(5).std()
        features['ma5'] = data['close'].rolling(5).mean()
        features['ma20'] = data['close'].rolling(20).mean()
        features = features.dropna()
        
        # 目标变量：未来5日收益率是否为正
        target = (data['close'].shift(-5) > data['close']).astype(int)
        target = target[features.index]
        
        return features, target
    
    def _save_model(self, model, filename: str):
        """保存模型到本地"""
        path = self.model_storage / filename
        joblib.dump(model, path)
        logger.info(f"模型已保存至 {path}")
        
    def _load_model(self, filename: str):
        """从本地加载模型"""
        path = self.model_storage / filename
        if not path.exists():
            raise FileNotFoundError(f"模型文件 {path} 不存在")
        return joblib.load(path)

if __name__ == "__main__":
    # 示例用法
    from ..data.data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    manager = ModelManager(fetcher)
    
    # 训练新模型
    model = manager.train_model(n_estimators=150, max_depth=7)
    
    # 进行预测
    X_new, _ = manager._prepare_training_data()
    predictions = manager.predict(model, X_new[-100:])
    print("最新预测结果:", predictions.tail())
