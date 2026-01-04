"""
工具函数模块
"""
from datetime import datetime, timezone, timedelta
import socket


# 北京时间时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


def get_beijing_time() -> datetime:
    """
    获取北京时间
    使用系统时间并转换为北京时间 (UTC+8)
    """
    utc_now = datetime.now(timezone.utc)
    beijing_now = utc_now.astimezone(BEIJING_TZ)
    return beijing_now


def get_beijing_date() -> datetime:
    """获取北京时间的日期（时间部分为00:00:00）"""
    beijing_now = get_beijing_time()
    return beijing_now.replace(hour=0, minute=0, second=0, microsecond=0)


def format_currency(amount: float, symbol: str = "¥") -> str:
    """
    格式化货币显示
    
    Args:
        amount: 金额
        symbol: 货币符号，默认人民币
    
    Returns:
        格式化后的字符串，如 "¥1,234.56"
    """
    if amount < 0:
        return f"-{symbol}{abs(amount):,.2f}"
    return f"{symbol}{amount:,.2f}"


def format_date(dt: datetime, fmt: str = "%Y-%m-%d") -> str:
    """
    格式化日期显示
    
    Args:
        dt: 日期时间对象
        fmt: 格式化模板
    
    Returns:
        格式化后的日期字符串
    """
    return dt.strftime(fmt)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间显示"""
    return dt.strftime(fmt)


def parse_date(date_str: str, fmt: str = "%Y-%m-%d") -> datetime:
    """
    解析日期字符串
    
    Args:
        date_str: 日期字符串
        fmt: 格式化模板
    
    Returns:
        日期时间对象
    """
    return datetime.strptime(date_str, fmt)


def get_week_range() -> tuple:
    """获取本周的起止日期"""
    today = get_beijing_date()
    # 计算本周一
    start = today - timedelta(days=today.weekday())
    # 本周日
    end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return start, end


def get_month_range() -> tuple:
    """获取本月的起止日期"""
    today = get_beijing_date()
    # 本月第一天
    start = today.replace(day=1)
    # 下月第一天减一秒
    if today.month == 12:
        end = today.replace(year=today.year + 1, month=1, day=1)
    else:
        end = today.replace(month=today.month + 1, day=1)
    end = end - timedelta(seconds=1)
    return start, end


def get_year_range() -> tuple:
    """获取本年的起止日期"""
    today = get_beijing_date()
    start = today.replace(month=1, day=1)
    end = today.replace(month=12, day=31, hour=23, minute=59, second=59)
    return start, end


def get_recent_days_range(days: int = 30) -> tuple:
    """获取最近N天的起止日期"""
    end = get_beijing_time()
    start = end - timedelta(days=days)
    return start.replace(hour=0, minute=0, second=0, microsecond=0), end
