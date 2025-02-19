import pandas as pd
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from typing import Dict, List
from ..data.data_fetcher import DataFetcher
from ..config import EMAIL_CONFIG
import smtplib
from email.mime.text import MIMEText
from email.header import Header

logger = logging.getLogger(__name__)

class MarketMonitor:
    """市场异动监控基类"""
    
    def __init__(self, fetcher: DataFetcher):
        self.fetcher = fetcher
        self.scheduler = BackgroundScheduler()
        self.alert_rules = self.default_rules()
        self.history_data = pd.DataFrame()
        
    def default_rules(self) -> Dict:
        """默认监控规则"""
        return {
            'price_change_1h': 0.05,  # 1小时内涨跌幅超过5%
            'volume_spike': 3.0,       # 成交量突增3倍
            'pe_ratio_deviation': 0.3  # PE偏离历史均值30%
        }
    
    def start_monitoring(self):
        """启动定时监控"""
        self._load_history_data()
        self.scheduler.add_job(self.check_conditions, 'interval', minutes=5)
        self.scheduler.start()
        logger.info("市场监控系统已启动")
        
    def _load_history_data(self):
        """加载历史参考数据"""
        try:
            # 获取过去一年的市场数据
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            self.history_data = self.fetcher.pro.daily(
                ts_code='', 
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            logger.error(f"历史数据加载失败: {str(e)}")

    def check_conditions(self):
        """执行监控检查"""
        try:
            # 获取实时数据
            realtime_data = self.fetcher.get_realtime_data()
            
            # 检查价格异动
            self._check_price_change(realtime_data)
            
            # 检查成交量异动
            self._check_volume_spike(realtime_data)
            
            # 检查估值偏离
            self._check_valuation_deviation(realtime_data)
            
        except Exception as e:
            logger.error(f"监控检查失败: {str(e)}")

    def _check_price_change(self, data: pd.DataFrame):
        """价格波动检查"""
        threshold = self.alert_rules['price_change_1h']
        for _, row in data.iterrows():
            if abs(row['pct_chg']) > threshold * 100:  # 转换为百分比
                self.send_alert(
                    f"{row['ts_code']} 价格异动: 1小时内涨跌幅 {row['pct_chg']}%",
                    level='critical'
                )

    def _check_volume_spike(self, data: pd.DataFrame):
        """成交量突增检查"""
        threshold = self.alert_rules['volume_spike']
        avg_volume = self.history_data.groupby('ts_code')['vol'].mean()
        
        for _, row in data.iterrows():
            ts_code = row['ts_code']
            current_vol = row['vol']
            if ts_code in avg_volume and current_vol > avg_volume[ts_code] * threshold:
                self.send_alert(
                    f"{ts_code} 成交量突增: 当前 {current_vol/10000:.2f}万手 vs 平均 {avg_volume[ts_code]/10000:.2f}万手",
                    level='warning'
                )

    def _check_valuation_deviation(self, data: pd.DataFrame):
        """估值偏离检查"""
        threshold = self.alert_rules['pe_ratio_deviation']
        pe_history = self.history_data.groupby('ts_code')['pe_ttm'].mean()
        
        for _, row in data.iterrows():
            ts_code = row['ts_code']
            current_pe = row['pe_ttm']
            if ts_code in pe_history and current_pe != 0:
                deviation = abs(current_pe - pe_history[ts_code]) / pe_history[ts_code]
                if deviation > threshold:
                    self.send_alert(
                        f"{ts_code} PE偏离: 当前 {current_pe:.2f} vs 历史平均 {pe_history[ts_code]:.2f} (偏离 {deviation*100:.1f}%)",
                        level='notice'
                    )

    def send_alert(self, message: str, level: str = 'warning'):
        """发送预警信息"""
        try:
            msg = MIMEText(message, 'plain', 'utf-8')
            msg['Subject'] = Header(f"[量化交易预警] {level.upper()}级别预警", 'utf-8')
            msg['From'] = EMAIL_CONFIG['sender']
            msg['To'] = ",".join(EMAIL_CONFIG['receivers'])
            
            with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
                server.starttls()
                server.login(EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'])
                server.sendmail(
                    EMAIL_CONFIG['sender'],
                    EMAIL_CONFIG['receivers'],
                    msg.as_string()
                )
            logger.info(f"预警信息已发送: {message}")
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")

class PolicyMonitor:
    """政策面监控系统"""
    
    def __init__(self, fetcher: DataFetcher):
        self.fetcher = fetcher
        self.keywords = ['降准', '降息', 'IPO', '减持', '增持', '监管']
        
    def monitor_news(self):
        """监控财经新闻"""
        try:
            news = self.fetcher.get_financial_news()
            for item in news:
                if any(kw in item['title'] for kw in self.keywords):
                    self.send_alert(
                        f"政策面变化: {item['title']}\n链接: {item['url']}",
                        level='info'
                    )
        except Exception as e:
            logger.error(f"新闻监控失败: {str(e)}")

if __name__ == "__main__":
    # 示例用法
    from ..data.data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    monitor = MarketMonitor(fetcher)
    monitor.start_monitoring()
