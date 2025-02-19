import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Songti SC', 'STHeiti', 'PingFang HK']  # 优先使用宋体，备选黑体和平方字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 显式加载字体
font_path = '/System/Library/Fonts/Supplemental/Songti.ttc'  # macOS系统宋体路径
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
from datetime import datetime
from sqlalchemy import create_engine
import numpy as np
from ..config import SQLITE_DB_PATH
from ..trade.trade_executor import TradeRecord

plt.style.use('seaborn-v0_8')
sns.set_theme(style="whitegrid", palette="husl")

class ReportGenerator:
    """回测结果可视化报告生成"""
    
    def __init__(self):
        self.engine = create_engine(f'sqlite:///{SQLITE_DB_PATH}')
        
    def generate_full_report(self, account: str = 'default'):
        """生成完整绩效报告"""
        plt.figure(figsize=(15, 12))
        
        # 资金曲线
        plt.subplot(3, 2, 1)
        self.plot_equity_curve(account)
        
        # 回撤分析
        plt.subplot(3, 2, 2)
        self.plot_drawdown(account)
        
        # 月度收益分布
        plt.subplot(3, 2, 3)
        self.plot_monthly_returns_heatmap(account)
        
        # 持仓分布
        plt.subplot(3, 2, 4)
        self.plot_position_distribution(account)
        
        # 交易信号分布
        plt.subplot(3, 2, 5)
        self.plot_trade_signals(account)
        
        plt.tight_layout()
        plt.savefig(f'reports/{account}_performance_report.png')
        plt.close()

    def plot_equity_curve(self, account: str):
        """绘制资金曲线"""
        equity = self._get_equity_data(account)
        equity['equity'].plot(title='资金曲线', lw=2)
        plt.xlabel('日期')
        plt.ylabel('净值')
        plt.grid(True)

    def plot_drawdown(self, account: str):
        """绘制回撤曲线"""
        equity = self._get_equity_data(account)
        rolling_max = equity['equity'].cummax()
        drawdown = (equity['equity'] - rolling_max) / rolling_max
        drawdown.plot(title='回撤分析', color='r', lw=1)
        plt.fill_between(drawdown.index, drawdown.values, color='red', alpha=0.3)
        plt.xlabel('日期')
        plt.ylabel('回撤比例')
        plt.grid(True)

    def plot_monthly_returns_heatmap(self, account: str):
        """月度收益热力图"""
        returns = self._get_equity_data(account)['returns']
        # 创建包含年份和月份的多重索引
        monthly_ret = returns.resample('ME').apply(lambda x: (1 + x).prod() - 1)
        monthly_ret.index = pd.MultiIndex.from_arrays([
            monthly_ret.index.year.rename('year'),
            monthly_ret.index.month.rename('month')
        ])
        monthly_ret = monthly_ret.unstack().reset_index() * 100
        
        sns.heatmap(monthly_ret.fillna(0), annot=True, fmt=".1f", 
                   cmap="RdYlGn", center=0, linewidths=0.5)
        plt.title('月度收益分布 (%)')
        plt.xlabel('月份')
        plt.ylabel('年份')

    def plot_position_distribution(self, account: str):
        """持仓分布饼图"""
        positions = pd.read_sql(f"""
            SELECT ts_code, SUM(volume) as shares 
            FROM trade_records 
            WHERE account='{account}' AND direction='buy'
            GROUP BY ts_code
        """, self.engine)
        positions.set_index('ts_code').plot.pie(y='shares', autopct='%1.1f%%')
        plt.title('持仓分布')
        plt.ylabel('')

    def plot_trade_signals(self, account: str):
        """交易信号分布"""
        trades = pd.read_sql(f"""
            SELECT strategy, COUNT(*) as count 
            FROM trade_records 
            WHERE account='{account}'
            GROUP BY strategy
        """, self.engine)
        trades.plot.bar(x='strategy', y='count', legend=False)
        plt.title('交易信号分布')
        plt.xlabel('策略名称')
        plt.ylabel('交易次数')
        plt.xticks(rotation=45)

    def _get_equity_data(self, account: str) -> pd.DataFrame:
        """获取账户净值数据"""
        df = pd.read_sql(f"""
            SELECT trade_time, SUM(price*volume) as equity 
            FROM trade_records 
            WHERE account='{account}'
            GROUP BY trade_time
            ORDER BY trade_time
        """, self.engine, parse_dates=['trade_time'])
        df = df.set_index('trade_time')
        df['returns'] = df['equity'].pct_change().fillna(0)
        return df

if __name__ == "__main__":
    # 示例用法
    generator = ReportGenerator()
    generator.generate_full_report()
    print("绩效报告已生成至 reports/ 目录")
