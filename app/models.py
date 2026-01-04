"""
数据模型定义
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class IncomeRecord:
    """收入记录数据模型"""
    id: Optional[int]  # 主键，新记录时为 None
    amount: float  # 金额
    category: str  # 分类
    description: str  # 备注
    date: datetime  # 记录日期
    created_at: datetime  # 创建时间

    def __post_init__(self):
        """数据验证"""
        if self.amount < 0:
            raise ValueError("金额不能为负数")

    @classmethod
    def from_db_row(cls, row: tuple) -> "IncomeRecord":
        """从数据库行创建记录对象"""
        return cls(
            id=row[0],
            amount=row[1],
            category=row[2],
            description=row[3],
            date=datetime.fromisoformat(row[4]),
            created_at=datetime.fromisoformat(row[5])
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "date": self.date.isoformat(),
            "created_at": self.created_at.isoformat()
        }


# 预定义收入分类
INCOME_CATEGORIES = [
    "💼 工资",
    "🎁 奖金",
    "📈 投资收益",
    "🏠 租金收入",
    "💻 兼职收入",
    "🛒 销售收入",
    "🎯 其他收入"
]
