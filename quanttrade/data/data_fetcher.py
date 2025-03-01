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
        
    def get_stock_daily_data(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从Tushare获取股票日线数据"""
        try:
            df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            self._save_to_cache(df, f"{ts_code}_{start_date}_{end_date}.parquet")
            return df
        except Exception as e:
            logger.error(f"Tushare数据获取日线数据失败: {str(e)}")
            raise

    def get_stock_list_data(self) -> pd.DataFrame:
        """从Tushare获取股票列表数据
        输入参数
        名称	类型	必选	描述
        ts_code	str	N	TS股票代码
        name	str	N	名称
        market	str	N	市场类别 （主板/创业板/科创板/CDR/北交所）
        list_status	str	N	上市状态 L上市 D退市 P暂停上市，默认是L
        exchange	str	N	交易所 SSE上交所 SZSE深交所 BSE北交所
        is_hs	str	N	是否沪深港通标的，N否 H沪股通 S深股通
        输出参数
        名称	类型	默认显示	描述
        ts_code	str	Y	TS代码
        symbol	str	Y	股票代码
        name	str	Y	股票名称
        area	str	Y	地域
        industry	str	Y	所属行业
        fullname	str	N	股票全称
        enname	str	N	英文全称
        cnspell	str	Y	拼音缩写
        market	str	Y	市场类型（主板/创业板/科创板/CDR）
        exchange	str	N	交易所代码
        curr_type	str	N	交易货币
        list_status	str	N	上市状态 L上市 D退市 P暂停上市
        list_date	str	Y	上市日期
        delist_date	str	N	退市日期
        is_hs	str	N	是否沪深港通标的，N否 H沪股通 S深股通
        act_name	str	Y	实控人名称
        act_ent_type	str	Y	实控人企业性质"""

        try:
        # enname	str	N	英文全称
            df = self.pro.query('stock_basic', exchange='', list_status='L', fields='ts_code,symbol,name,area,\
                industry,fullname,enname,cnspell,market,,exchange,curr_type,\
                    list_status,list_date,delist_date,is_hs,act_name,act_ent_type')
            df.to_csv('data/stock_list.csv',index=False)
            # print(test_data.head())
            # self._save_to_cache(df, f"{ts_code}_{start_date}_{end_date}.parquet")
            return df
        except Exception as e:
            logger.error(f"Tushare数据获取股票列表失败: {str(e)}")
            raise
    
    def get_name_change_data(self, ts_code: str) -> pd.DataFrame:
        """" 描述：历史名称变更记录
        输入参数
        名称	类型	必选	描述
        ts_code	str	N	TS代码
        start_date	str	N	公告开始日期
        end_date	str	N	公告结束日期
        输出参数
        名称	类型	默认输出	描述
        ts_code	str	Y	TS代码
        name	str	Y	证券名称
        start_date	str	Y	开始日期
        end_date	str	Y	结束日期
        ann_date	str	Y	公告日期
        change_reason	str	Y	变更原因"""
        try:
            df = self.pro.namechange(ts_code=ts_code, fields='ts_code,name,start_date,end_date,change_reason')
            # print(df)
            self._save_to_cache(df, f"{ts_code}_namechange.parquet")
            return df
        except Exception as e:
            logger.error(f"Tushare数据获取名称变更信息失败: {str(e)}")
            raise

    def get_all_stock_basic_data(self) -> pd.DataFrame:
        """上市公司基本信息
        输入参数
        名称	类型	必须	描述
        ts_code	str	N	股票代码
        exchange	str	N	交易所代码 ，SSE上交所 SZSE深交所 BSE北交所
        输出参数
        名称	类型	默认显示	描述
        ts_code	str	Y	股票代码
        com_name	str	Y	公司全称
        com_id	str	Y	统一社会信用代码
        exchange	str	Y	交易所代码
        chairman	str	Y	法人代表
        manager	str	Y	总经理
        secretary	str	Y	董秘
        reg_capital	float	Y	注册资本(万元)
        setup_date	str	Y	注册日期
        province	str	Y	所在省份
        city	str	Y	所在城市
        introduction	str	N	公司介绍
        website	str	Y	公司主页
        email	str	Y	电子邮件
        office	str	N	办公室
        employees	int	Y	员工人数
        main_business	str	N	主要业务及产品
        business_scope	str	N	经营范围"""
        try:
            df = self.pro.stock_company(exchange='SZSE', fields='ts_code,chairman,manager,secretary,reg_capital,setup_date,province,main_business,business_scope')
            # print(test_data.head())
            df.to_csv('data/all_stock_basic.csv',index=False)
        except Exception as e:
            logger.error(f"Tushare数据获取所有股票基本数据失败: {str(e)}")
            raise

    def get_ipo_list_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """IPO新股列表
        输入参数
        名称	类型	必选	描述
        start_date	str	N	上网发行开始日期
        end_date	str	N	上网发行结束日期
        输出参数
        名称	类型	默认显示	描述
        ts_code	str	Y	TS股票代码
        sub_code	str	Y	申购代码
        name	str	Y	名称
        ipo_date	str	Y	上网发行日期
        issue_date	str	Y	上市日期
        amount	float	Y	发行总量（万股）
        market_amount	float	Y	上网发行总量（万股）
        price	float	Y	发行价格
        pe	float	Y	市盈率
        limit_amount	float	Y	个人申购上限（万股）
        funds	float	Y	募集资金（亿元）
        ballot	float	Y	中签率"""
        try:
            df = self.pro.new_share(start_date=start_date, end_date=end_date)
            # print(df)
            self._save_to_cache(df, f"IPO_list_{start_date}_{end_date}.parquet")
            return df
        except Exception as e:
            logger.error(f"Tushare数据获取所有股票基本数据失败: {str(e)}")
            raise
    
    def get_history_stock_list_data(self, trade_date: str) -> pd.DataFrame:
        """股票历史列表（历史每天股票列表）
        输入参数
        名称	类型	必选	描述
        trade_date	str	N	交易日期
        ts_code	str	N	股票代码
        输出参数
        名称	类型	默认显示	描述
        trade_date	str	Y	交易日期
        ts_code	str	Y	TS股票代码
        name	str	Y	股票名称
        industry	str	Y	行业
        area	str	Y	地域
        pe	float	Y	市盈率（动）
        float_share	float	Y	流通股本（亿）
        total_share	float	Y	总股本（亿）
        total_assets	float	Y	总资产（亿）
        liquid_assets	float	Y	流动资产（亿）
        fixed_assets	float	Y	固定资产（亿）
        reserved	float	Y	公积金
        reserved_pershare	float	Y	每股公积金
        eps	float	Y	每股收益
        bvps	float	Y	每股净资产
        pb	float	Y	市净率
        list_date	str	Y	上市日期
        undp	float	Y	未分配利润
        per_undp	float	Y	每股未分配利润
        rev_yoy	float	Y	收入同比（%）
        profit_yoy	float	Y	利润同比（%）
        gpr	float	Y	毛利率（%）
        npr	float	Y	净利润率（%）
        holder_num	int	Y	股东人数"""
        try:
            df = self.pro.bak_basic(trade_date=trade_date, fields='trade_date,ts_code,name,industry,pe')
            print(df)
            df.to_csv('data/{trade_date}_history_stock_list.csv',index=False)
        except Exception as e:
            logger.error(f"Tushare数据获取股票历史列表失败: {str(e)}")
            raise
    
    def get_realtime_data(self, ts_code: str, source: str) -> pd.DataFrame:
        """实时盘口TICK快照(爬虫版)
        接口：realtime_quote，A股实时行情
        描述：本接口是tushare org版实时接口的顺延，数据来自网络，且不进入tushare服务器，属于爬虫接口，请将tushare升级到1.3.3版本以上。
        权限：0积分完全开放，但需要有tushare账号，如果没有账号请先注册。
        说明：由于该接口是纯爬虫程序，跟tushare服务器无关，因此tushare不对数据内容和质量负责。数据主要用于研究和学习使用，如做商业目的，请自行解决合规问题。
        输入参数
        名称	类型	必选	描述
        ts_code	str	N	股票代码，需按tushare股票和指数标准代码输入，比如：000001.SZ表示平安银行，000001.SH表示上证指数
        src	str	N	数据源 （sina-新浪 dc-东方财富，默认sina）
        src数据源说明：
        src源	说明	描述
        sina	新浪财经	支持多个多个股票同时输入，举例：ts_code='600000.SH,000001.SZ'），一次最多不能超过50个股票
        dc	东方财富	只支持单个股票提取
        输出参数
        名称	类型	描述
        name	str	股票名称
        ts_code	str	股票代码
        date	str	交易日期
        time	str	交易时间
        open	float	开盘价
        pre_close	float	昨收价
        price	float	现价
        high	float	今日最高价
        low	float	今日最低价
        bid	float	竞买价，即“买一”报价（元）
        ask	float	竞卖价，即“卖一”报价（元）
        volume	int	成交量（src=sina时是股，src=dc时是手）
        amount	float	成交金额（元 CNY）
        b1_v	float	委买一（量，单位：手，下同）
        b1_p	float	委买一（价，单位：元，下同）
        b2_v	float	委买二（量）
        b2_p	float	委买二（价）
        b3_v	float	委买三（量）
        b3_p	float	委买三（价）
        b4_v	float	委买四（量）
        b4_p	float	委买四（价）
        b5_v	float	委买五（量）
        b5_p	float	委买五（价）
        a1_v	float	委卖一（量，单位：手，下同）
        a1_p	float	委卖一（价，单位：元，下同）
        a2_v	float	委卖二（量）
        a2_p	float	委卖二（价）
        a3_v	float	委卖三（量）
        a3_p	float	委卖三（价）
        a4_v	float	委卖四（量）
        a4_p	float	委卖四（价）
        a5_v	float	委卖五（量）
        a5_p	float	委卖五（价）"""
        try:
            df = ts.realtime_quote(ts_code=ts_code, src=source)
            print(df)
            self._save_to_cache(df, f"{ts_code}_realtime_data.parquet")
        except Exception as e:
            logger.error(f"Tushare数据获取股票实时行情失败: {str(e)}")
            raise
    
    def get_stock_capital_data(self) -> pd.DataFrame:
        """股票股本情况to be define"""
    def get_company_manager_info(self, ts_code: str) -> pd.DataFrame:
        """上市公司高管信息to be define"""
    def get_company_rewards_info(self, ts_code: str) -> pd.DataFrame:
        """上市公司高管薪酬信息 to be define"""
    def get_stock_minute_data(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """分钟行情 to be define"""
    def get_stock_weekly_data(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """周线行情 to be define"""
    def get_stock_monthly_data(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """月线行情 to be define"""
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
    # fetcher.get_name_change_data('002008.SZ')
    # fetcher.get_ipo_list_data('20250210','20250226')
    # fetcher.get_history_stock_list_data('20250227')
    fetcher.get_realtime_data('301601.SZ','dc')
    #交易日历  获取途径 1.tushare 权限2000 
    # test_data = fetcher.pro.query('trade_cal', start_date='20180101', end_date='20181231')
    # print(test_data.head())

    # 已测试
    # 股票列表数据 获取途径 1.tushare 权限2000(120也可以？)积分，2.爬虫 注意爬取频率！
    # test_data = fetcher.pro.query('stock_basic', exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    # print(test_data.head())

    #股票股本数据 获取途径 1.爬虫

    #获取股票现金流  获取途径 1.爬虫
    #SINA_CASHFLOW_URL = 'http://money.finance.sina.com.cn/corp/go.php/vDOWN_CashFlow/displaytype/4/stockid/%s/ctrl/all.phtml'

    #已测试
    #股票曾用名 获取途径 1.tushare 权限0积分
    # test_data = fetcher.pro.namechange(ts_code='601949.SH', fields='ts_code,name,start_date,end_date,change_reason')
    # print(test_data.head())

    #沪深股通成分股列表 获取途径 1. tushare 权限0积分
    # test_data = fetcher.pro.hs_const(hs_type='SH')
    # print(test_data.head())
    # test_data = fetcher.pro.hs_const(hs_type='SZ')
    # print(test_data.head())

    # 已测试
    #上市公司基本信息 获取途径 1.tushare 权限120积分
    # test_data = fetcher.pro.stock_company(exchange='SZSE', fields='ts_code,chairman,manager,secretary,reg_capital,setup_date,province,main_business,business_scope')
    # print(test_data.head())

    #上市公司高管信息 获取途径 1.tushare 权限2000积分 2.爬虫
    #pro.stk_managers(ts_code='000001.SZ,600000.SH')

    #上市公司管理层薪酬和持股 获取途径 1.tushare 权限2000积分 2.爬虫
    #pro.stk_rewards(ts_code='000001.SZ,600000.SH')

    #已测试
    #IPO新股列表 获取途径 1.tushare 权限120积分
    # test_data = fetcher.pro.new_share(start_date='20250101', end_date='20250320')
    # print(test_data.head())

    #已测试
    #股票历史列表（历史每天股票列表）获取途径 1.tushare 
    # test_data = fetcher.pro.bak_basic(trade_date='20250221', fields='trade_date,ts_code,name,industry,pe')
    # print(test_data.head())

    # 股票日K行情 获取途径 1.tushare 权限100积分
    # test_data = fetcher.get_stock_data("000001.SZ", "20230101", "20231231")
    # print(test_data.head())

    #股票分钟行情 获取途径 1.tushare 权限120积分 可调取两次
    #pro.stk_mins(ts_code='600000.SH', freq='1min', start_date='2023-08-25 09:00:00', end_date='2023-08-25 19:00:00')

    #股票周线行情 获取途径 1.tushare 权限2000积分
    #pro.weekly(ts_code='000001.SZ', start_date='20180101', end_date='20181101', fields='ts_code,trade_date,open,high,low,close,vol,amount')

    #股票月线行情 获取途径 1.tushare 权限2000积分
    # pro.monthly(trade_date='20181031', fields='ts_code,trade_date,open,high,low,close,vol,amount')

    #A股复权行情 获取途径 1.tushare
    # test_data = ts.pro_bar(ts_code='000001.SZ', adj='qfq', start_date='20180101', end_date='20181011')
    # print(test_data.head())

    #单只股票的复权因子 获取途径 1.tushare 权限2000
    # pro.adj_factor(ts_code='', trade_date='20180718') 或者 pro.query('adj_factor',  trade_date='20180718')

    #实时行情 获取途径 1. tushare
    #sina数据
    # df = ts.realtime_quote(ts_code='600000.SH,000001.SZ,000001.SH')
    # print(df.head())
    #东财数据
    # df = ts.realtime_quote(ts_code='600000.SH', src='dc')

    #实时成交数据 获取途径 1.tushare (源码做了限制 0.5s爬一次 速度很慢) src='sina' 'tx' 'dc'
    # df = ts.realtime_tick(ts_code='002600.SZ')
    # print(df)

    #实时涨跌幅排名 获取途径 1.tushare src='sina' 'dc' 
    # df = ts.realtime_list(src='sina') #重复运行本函数会被新浪暂时封 IP 需要用代理
    # print(df)
    # df = ts.realtime_list(src='dc') #建议用东财快一些 IP 需要用代理
    # print(df)
    # df.to_csv('ranklist.csv',index=False)

    #每日指标 
    # 接口：daily_basic，可以通过数据工具调试和查看数据。
    # 更新时间：交易日每日15点～17点之间
    # 描述：获取全部股票每日重要的基本面指标，可用于选股分析、报表展示等。
    # 积分：至少2000积分才可以调取，5000积分无总量限制，具体请参阅积分获取办法
    # pro.daily_basic(ts_code='', trade_date='20180726', fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pb')

    #涨跌停价格
    # 接口：stk_limit
    # 描述：获取全市场（包含A/B股和基金）每日涨跌停价格，包括涨停价格，跌停价格等，每个交易日8点40左右更新当日股票涨跌停价格。
    # 限量：单次最多提取5800条记录，可循环调取，总量不限制
    # 积分：用户积2000积分可调取，单位分钟有流控，积分越高流量越大，请自行提高积分，具体请参阅积分获取办法 
    #获取单日全部股票数据涨跌停价格
    # df = pro.stk_limit(trade_date='20190625')
    #获取单个股票数据
    # df = pro.stk_limit(ts_code='002149.SZ', start_date='20190115', end_date='20190615')

    #每日停复牌信息
    # 接口：suspend_d
    # 更新时间：不定期
    # 描述：按日期方式获取股票每日停复牌信息
    # df = fetcher.pro.suspend_d(suspend_type='S', trade_date='20250225')
    # print(df)

    #沪深股通十大成交股
    # 接口：hsgt_top10
    # 描述：获取沪股通、深股通每日前十大成交详细数据，每天18~20点之间完成当日更新
    # df = fetcher.pro.hsgt_top10(trade_date='20250224', market_type='1')
    # print(df)

    #港股通十大成交股
    # 接口：ggt_top10
    # 描述：获取港股通每日成交数据，其中包括沪市、深市详细数据，每天18~20点之间完成当日更新
    # df = fetcher.pro.ggt_top10(trade_date='20250224')
    # print(df)

    #港股通每日成交统计
    # 接口：ggt_daily
    # 描述：获取港股通每日成交信息，数据从2014年开始
    # 限量：单次最大1000，总量数据不限制
    # 积分：用户积2000积分可调取，5000积分以上频次相对较高，请自行提高积分，具体请参阅积分获取办法
    #获取单日全部统计
    # df = pro.ggt_daily(trade_date='20190625')
    # #获取多日统计信息
    # df = pro.ggt_daily(trade_date='20190925,20180924,20170925')
    # #获取时间段统计信息
    # df = pro.ggt_daily(start_date='20180925', end_date='20190925)

    #港股通每月成交统计
    # 接口：ggt_monthly
    # 描述：港股通每月成交信息，数据从2014年开始
    # 限量：单次最大1000
    # 积分：用户积5000积分可调取，请自行提高积分，具体请参阅积分获取办法
    #获取单月全部统计
    # df = pro.ggt_monthly(trade_date='201906')
    # #获取多月统计信息
    # df = pro.ggt_monthly(trade_date='201906,201907,201709')
    # #获取时间段统计信息
    # df = pro.ggt_monthly(start_date='201809', end_date='201908')

    #备用行情
    # 接口：bak_daily
    # 描述：获取备用行情，包括特定的行情指标(数据从2017年中左右开始，早期有几天数据缺失，近期正常)
    # 限量：单次最大7000行数据，可以根据日期参数循环获取，正式权限需要5000积分。
    # df = pro.bak_daily(trade_date='20211012', fields='trade_date,ts_code,name,close,open')

    #利润表
    # 接口：income，可以通过数据工具调试和查看数据。
    # 描述：获取上市公司财务利润表数据
    # 积分：用户需要至少2000积分才可以调取，具体请参阅积分获取办法
    # df = fetcher.pro.income(ts_code='600000.SH', start_date='20180101', end_date='20180730', fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,basic_eps,diluted_eps')
    # print(df)

    #资产负债表
    # 接口：balancesheet，可以通过数据工具调试和查看数据。
    # 描述：获取上市公司资产负债表
    # 积分：用户需要至少2000积分才可以调取，具体请参阅积分获取办法
    # df = pro.balancesheet(ts_code='600000.SH', start_date='20180101', end_date='20180730', fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,cap_rese')

    #现金流量表
    # 接口：cashflow，可以通过数据工具调试和查看数据。
    # 描述：获取上市公司现金流量表
    # 积分：用户需要至少2000积分才可以调取，具体请参阅积分获取办法
    # df = pro.cashflow(ts_code='600000.SH', start_date='20180101', end_date='20180730')

    # 业绩预告
    # 接口：forecast，可以通过数据工具调试和查看数据。
    # 描述：获取业绩预告数据
    # 权限：用户需要至少2000积分才可以调取，具体请参阅积分获取办法
    # pro.forecast(ann_date='20190131', fields='ts_code,ann_date,end_date,type,p_change_min,p_change_max,net_profit_min')

    # 业绩快报
    # 接口：express
    # 描述：获取上市公司业绩快报
    # 权限：用户需要至少2000积分才可以调取，具体请参阅积分获取办法
    # pro.express(ts_code='600000.SH', start_date='20180101', end_date='20180701', fields='ts_code,ann_date,end_date,revenue,operate_profit,total_profit,n_income,total_assets')

    # 分红送股
    # 接口：dividend
    # 描述：分红送股数据
    # 权限：用户需要至少2000积分才可以调取，具体请参阅积分获取办法
    # df = pro.dividend(ts_code='600848.SH', fields='ts_code,div_proc,stk_div,record_date,ex_date')

    # 财务指标数据
    # 接口：fina_indicator，可以通过数据工具调试和查看数据。
    # 描述：获取上市公司财务指标数据，为避免服务器压力，现阶段每次请求最多返回60条记录，可通过设置日期多次请求获取更多数据。
    # 权限：用户需要至少2000积分才可以调取，具体请参阅积分获取办法
    # df = pro.query('fina_indicator', ts_code='600000.SH', start_date='20170101', end_date='20180801')