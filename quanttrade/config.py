import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# Tushare配置
TUSHARE_TOKEN = "202f61d85cc37115af06d6912bc1195a66bb2332fb327b5c32c0c378"
TUSHARE_ENDPOINT = "http://api.tushare.pro"

# 数据库配置
SQLITE_DB_PATH = BASE_DIR / "data/trading.db"  # 修正数据库文件名与实际创建文件一致
os.makedirs(BASE_DIR / "data", exist_ok=True)  # 确保数据目录存在
Path(SQLITE_DB_PATH).touch()  # 创建空数据库文件

# 日志配置
LOG_DIR = BASE_DIR / "logs"
LOG_CONFIG = {
    "version": 1,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "quant_trade.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "detailed",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detailed"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file", "console"]
    }
}

# 数据存储路径
DATA_STORAGE = {
    "stock_daily": BASE_DIR / "data/daily",
    "financial_reports": BASE_DIR / "data/financial",
    "alternative_data": BASE_DIR / "data/alternative"
}

# 邮件预警配置
EMAIL_CONFIG = {
    "smtp_server": "smtp.example.com",
    "smtp_port": 587,
    "sender": "your_email@example.com",
    "password": "your_password",
    "receivers": ["receiver1@example.com"]
}
