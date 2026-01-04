"""
数据库操作模块
使用 SQLite 进行数据持久化
"""
import sqlite3
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
from contextlib import contextmanager

from .models import IncomeRecord

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class Database:
    """数据库操作类"""

    def __init__(self, db_path: str = None):
        """初始化数据库连接"""
        if db_path is None:
            # 默认数据库路径
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "income.db")
        
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        # check_same_thread=False 允许在不同线程中使用连接，适合 GUI 异步操作
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)
        conn.execute("PRAGMA busy_timeout = 5000")  # 5秒超时，防止锁等待
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_db(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 开启 WAL 模式以提高并发性能
            cursor.execute("PRAGMA journal_mode=WAL;")
            
            # 收入记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS income_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            # 创建索引以加速日期查询
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_income_date 
                ON income_records(date)
            """)
            
            # 设置表 (用于存储配置，如预算、主题偏好等)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

    def add_income(self, record: IncomeRecord) -> int:
        """添加收入记录，返回新记录ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO income_records (amount, category, description, date, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                record.amount,
                record.category,
                record.description,
                record.date.isoformat(),
                record.created_at.isoformat()
            ))
            return cursor.lastrowid

    def update_income(self, record: IncomeRecord) -> bool:
        """更新收入记录"""
        if record.id is None:
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE income_records 
                SET amount = ?, category = ?, description = ?, date = ?
                WHERE id = ?
            """, (
                record.amount,
                record.category,
                record.description,
                record.date.isoformat(),
                record.id
            ))
            return cursor.rowcount > 0

    def delete_income(self, record_id: int) -> bool:
        """删除收入记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM income_records WHERE id = ?", (record_id,))
            return cursor.rowcount > 0

    def get_income_by_id(self, record_id: int) -> Optional[IncomeRecord]:
        """根据ID获取记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, amount, category, description, date, created_at
                FROM income_records WHERE id = ?
            """, (record_id,))
            row = cursor.fetchone()
            if row:
                return IncomeRecord.from_db_row(tuple(row))
            return None

    def get_incomes(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[IncomeRecord]:
        """获取收入记录列表，支持筛选"""
        query = "SELECT id, amount, category, description, date, created_at FROM income_records WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date.isoformat())
        
        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY date DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [IncomeRecord.from_db_row(tuple(row)) for row in rows]

    def get_total_income(self) -> float:
        """获取总收入"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM income_records")
            return cursor.fetchone()[0]

    def get_yearly_income(self, year: int = None) -> float:
        """获取年收入"""
        if year is None:
            year = datetime.now().year
        
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM income_records
                WHERE date >= ? AND date <= ?
            """, (start_date.isoformat(), end_date.isoformat()))
            return cursor.fetchone()[0]

    def get_monthly_income(self, days: int = 30) -> float:
        """获取近N天收入"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM income_records
                WHERE date >= ? AND date <= ?
            """, (start_date.isoformat(), end_date.isoformat()))
            return cursor.fetchone()[0]

    def get_daily_average(self) -> float:
        """获取日均收入（基于有记录的天数）"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 获取有记录的天数
            cursor.execute("""
                SELECT COUNT(DISTINCT DATE(date)) FROM income_records
            """)
            days = cursor.fetchone()[0]
            
            if days == 0:
                return 0.0
            
            # 获取总收入
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM income_records")
            total = cursor.fetchone()[0]
            
            return total / days

    def get_statistics(self) -> dict:
        """获取统计数据"""
        return {
            "total_income": self.get_total_income(),
            "yearly_income": self.get_yearly_income(),
            "monthly_income": self.get_monthly_income(),
            "daily_average": self.get_daily_average()
        }

    def get_record_count(self) -> int:
        """获取记录总数"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM income_records")
            return cursor.fetchone()[0]

    # --- 高级分析方法 ---

    def get_daily_trend(self, days: int = 30) -> Tuple[List[str], List[float]]:
        """
        获取最近N天的日收入趋势
        返回: (日期列表, 金额列表)
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT strftime('%Y-%m-%d', date) as day, SUM(amount)
                FROM income_records
                WHERE date >= ? AND date <= ?
                GROUP BY day
                ORDER BY day ASC
            """, (start_date.isoformat(), end_date.isoformat()))
            rows = cursor.fetchall()
            
            data = {row[0]: row[1] for row in rows}
            
            # 补全日期
            dates = []
            values = []
            current = start_date
            while current <= end_date:
                day_str = current.strftime('%Y-%m-%d')
                dates.append(day_str)
                values.append(data.get(day_str, 0.0))
                current += timedelta(days=1)
                
            return dates, values

    def get_category_distribution(self, start_date: str = None, end_date: str = None) -> Dict[str, float]:
        """
        获取分类收入分布
        返回: {分类:总金额}
        """
        query = "SELECT category, SUM(amount) FROM income_records WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
            
        query += " GROUP BY category"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return {row[0]: row[1] for row in rows}

    def backup_db(self, target_path: str) -> bool:
        """备份数据库"""
        try:
            # 确保源文件落盘
            with self.get_connection() as conn:
                conn.execute("VACUUM")
            
            shutil.copy2(self.db_path, target_path)
            return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False

    def export_to_excel(self, target_path: str) -> bool:
        """导出数据到 Excel"""
        if not PANDAS_AVAILABLE:
            return False
            
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query("SELECT * FROM income_records ORDER BY date DESC", conn)
                
            # 重命名列
            df = df.rename(columns={
                "id": "ID",
                "amount": "金额",
                "category": "分类",
                "description": "备注",
                "date": "日期",
                "created_at": "创建时间"
            })
            
            df.to_excel(target_path, index=False, engine='openpyxl')
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False

    # --- 设置管理方法 ---

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """获取设置值"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_setting(self, key: str, value: str) -> bool:
        """保存设置值"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO app_settings (key, value)
                VALUES (?, ?)
            """, (key, str(value)))
            return cursor.rowcount > 0

    def get_monthly_budget(self) -> float:
        """获取月度预算目标"""
        val = self.get_setting("monthly_budget", "0")
        try:
            return float(val)
        except ValueError:
            return 0.0

    def set_monthly_budget(self, amount: float) -> bool:
        """设置月度预算"""
        return self.set_setting("monthly_budget", str(amount))

    def get_spending_forecast(self) -> dict:
        """
        智能预测本月支出 (AI-Lite)
        
        算法逻辑:
        1. 获取本月已过天数的日均支出 (权重：最近3天更高)
        2. 结合历史日均支出 (如果数据足够)
        3. 预测剩余天数的支出
        4. 返回: {
            'predicted_total': float, # 预测本月总支出
            'remaining_days': int,    # 剩余天数
            'daily_average': float,   # 当前日均 (加权)
            'status': str             # 'safe' | 'warning' | 'danger' (相对于预算)
        }
        """
        now = datetime.now()
        year, month = now.year, now.month
        
        # 本月总天数
        if month == 12:
            next_month = now.replace(year=year+1, month=1, day=1)
        else:
            next_month = now.replace(month=month+1, day=1)
        
        total_days = (next_month - timedelta(days=1)).day
        passed_days = now.day
        remaining_days = total_days - passed_days
        
        # 1. 获取本月实际支出 (从本月1号到当前时刻)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM income_records
                WHERE date >= ? AND date <= ?
            """, (start_of_month.isoformat(), now.isoformat()))
            real_month_spending = cursor.fetchone()[0]

        # 2. 计算日均 (加权: 本月日均 * 0.7 + 历史日均 * 0.3)
        # 如果是1号，主要依赖历史日均
        historical_daily_avg = self.get_daily_average()
        
        if passed_days > 1:
            current_daily_avg = real_month_spending / passed_days
            # 混合权重计算，随月份进行 current 权重增加
            weight_current = min(0.8, passed_days / 15.0) 
            daily_avg = (current_daily_avg * weight_current) + (historical_daily_avg * (1 - weight_current))
        else:
            daily_avg = historical_daily_avg
            
        # 3. 预测 (简单线性外推)
        predicted_remaining = daily_avg * remaining_days
        predicted_total = real_month_spending + predicted_remaining
        
        # 4. 评估状态
        budget = self.get_monthly_budget()
        status = "safe"
        if budget > 0:
            if predicted_total > budget:
                status = "danger"
            elif predicted_total > budget * 0.9:
                status = "warning"
                
        return {
            'predicted_total': predicted_total,
            'remaining_days': remaining_days,
            'daily_average': daily_avg,
            'status': status,
            'current_month_spending': real_month_spending
        }

    def vacuum_db(self) -> bool:
        """执行数据库整理 (压缩体积)"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
            return True
        except Exception as e:
            print(f"VACUUM failed: {e}")
            return False

    def checkpoint_wal(self) -> bool:
        """执行 WAL checkpoint，减少 -wal 文件大小"""
        try:
            with self.get_connection() as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            return True
        except Exception as e:
            print(f"WAL checkpoint failed: {e}")
            return False



# 全局数据库实例
_db_instance: Optional[Database] = None


def get_database() -> Database:
    """获取全局数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
