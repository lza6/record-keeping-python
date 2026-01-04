"""
仪表盘组件
显示收入统计数据
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QColor, QFont
from datetime import datetime

from ..database import get_database
from ..utils import format_currency
from .styles import COLORS, CARD_COLORS, FONTS
from .charts import AreaTrendChart, CategoryPieChart, ChartContainer


class AnimatedLabel(QLabel):
    """支持数值动画的标签"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        
    def get_value(self):
        return self._value
    
    def set_value(self, value):
        self._value = value
        self.setText(format_currency(value))
    
    value = pyqtProperty(float, get_value, set_value)
    
    def animate_to(self, target_value: float, duration: int = 500):
        """动画过渡到目标值"""
        # 如果差异太小，不动画
        if abs(target_value - self._value) < 0.01:
            self.set_value(target_value)
            return

        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(duration)
        self.animation.setStartValue(self._value)
        self.animation.setEndValue(target_value)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()


class StatCard(QFrame):
    """统计卡片组件"""
    
    def __init__(self, title: str, icon: str, accent_color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card") # 使用全局 card 样式
        self.accent_color = accent_color
        self.setup_ui(title, icon)
        self.apply_styles()
        
    def setup_ui(self, title: str, icon: str):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # 标题行
        header_layout = QHBoxLayout()
        
        # 图标
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 24))
        header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 标题
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle") # 需要在 style 中定义或这里直接设置
        title_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        layout.addWidget(title_label)
        
        # 数值
        self.value_label = AnimatedLabel()
        self.value_label.setObjectName("cardValue")
        self.value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {self.accent_color};
            font-family: {FONTS['mono']};
        """)
        self.value_label.setText("¥0.00")
        layout.addWidget(self.value_label)
        
        # 副标题
        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        layout.addWidget(self.subtitle_label)
        
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(150)
        
    def apply_styles(self):
        """应用样式"""
        # 主要是边框颜色的特别设置
        self.setStyleSheet(f"""
            QFrame#card {{
                border-left: 4px solid {self.accent_color};
            }}
            QFrame#card:hover {{
                border-color: {self.accent_color};
            }}
        """)
        
    def set_value(self, value: float, animate: bool = True):
        """设置数值"""
        if animate:
            self.value_label.animate_to(value)
        else:
            self.value_label.set_value(value)
            
    def set_subtitle(self, text: str):
        """设置副标题"""
        self.subtitle_label.setText(text)


from .components import BudgetProgressBar

class DashboardWidget(QWidget):
    """仪表盘组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("📊 收入统计概览")
        title.setObjectName("h1") # 使用全局 h1
        layout.addWidget(title)
        
        # --- 统计卡片区域 (Grid Layout) ---
        cards_layout = QGridLayout()
        cards_layout.setSpacing(16)
        
        # 总收入卡片
        self.total_card = StatCard("累计总收入", "💰", CARD_COLORS['total'])
        cards_layout.addWidget(self.total_card, 0, 0)
        
        # 年收入卡片
        self.yearly_card = StatCard("本年收入", "📆", CARD_COLORS['yearly'])
        cards_layout.addWidget(self.yearly_card, 0, 1)
        
        # 近30天收入卡片
        self.monthly_card = StatCard("近30天收入", "🗓️", CARD_COLORS['monthly'])
        cards_layout.addWidget(self.monthly_card, 1, 0)
        
        # 日均收入卡片
        self.average_card = StatCard("日均收入", "📈", CARD_COLORS['average'])
        cards_layout.addWidget(self.average_card, 1, 1)
        
        layout.addLayout(cards_layout)
        
        # --- 预算进度条 ---
        budget_frame = QFrame()
        budget_frame.setObjectName("card") # 复用卡片背景
        budget_layout = QVBoxLayout(budget_frame)
        budget_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header Row
        budget_header_box = QHBoxLayout()
        self.budget_label_header = QLabel("月度预算执行情况")
        self.budget_label_header.setStyleSheet(f"font-weight: bold; color: {COLORS['text_primary']}")
        budget_header_box.addWidget(self.budget_label_header)
        
        budget_header_box.addStretch()
        
        # Forecast Label (AI Prediction)
        self.forecast_label = QLabel("智能预测: 分析中...")
        self.forecast_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        budget_header_box.addWidget(self.forecast_label)
        
        budget_layout.addLayout(budget_header_box)
        
        self.budget_bar = BudgetProgressBar()
        budget_layout.addWidget(self.budget_bar)
        
        self.budget_status_label = QLabel("0 / 0 (0%)")
        self.budget_status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.budget_status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        budget_layout.addWidget(self.budget_status_label)
        
        layout.addWidget(budget_frame)

        # --- 图表区域 ---
        charts_header = QLabel("📈 数据可视化分析")
        charts_header.setObjectName("h2")
        layout.addWidget(charts_header)
        
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(16)
        
        # 趋势图 (Area Chart)
        self.trend_chart = AreaTrendChart()
        self.trend_container = ChartContainer("近30天收入趋势", self.trend_chart)
        charts_layout.addWidget(self.trend_container, stretch=2)
        
        # 饼图
        self.pie_chart = CategoryPieChart()
        self.pie_container = ChartContainer("收入来源分布", self.pie_chart)
        charts_layout.addWidget(self.pie_container, stretch=1)
        
        layout.addLayout(charts_layout)
        
        layout.addStretch()
        
    def update_theme(self):
        """更新主题样式"""
        # 更新卡片样式 (需要卡片支持重绘)
        self.total_card.apply_styles()
        self.yearly_card.apply_styles()
        self.monthly_card.apply_styles()
        self.average_card.apply_styles()
        
    def refresh(self, animate: bool = True):
        """刷新统计数据"""
        db = get_database()
        stats = db.get_statistics()
        
        # 更新卡片数值
        self.total_card.set_value(stats['total_income'], animate)
        self.total_card.set_subtitle(f"共 {db.get_record_count()} 条记录")
        
        self.yearly_card.set_value(stats['yearly_income'], animate)
        self.yearly_card.set_subtitle(f"{datetime.now().year} 年")
        
        self.monthly_card.set_value(stats['monthly_income'], animate)
        self.monthly_card.set_subtitle("最近 30 天")
        
        self.average_card.set_value(stats['daily_average'], animate)
        self.average_card.set_subtitle("基于有记录的天数")
        
        # 更新预算条 & 智能预测
        forecast = db.get_spending_forecast()
        current_spending = forecast['current_month_spending']
        budget = db.get_monthly_budget()
        
        if budget > 0:
            self.budget_bar.setVisible(True)
            self.budget_status_label.setVisible(True)
            self.budget_label_header.setVisible(True)
            self.forecast_label.setVisible(True)
            
            self.budget_bar.set_status(current_spending, budget)
            percent = (current_spending / budget) * 100
            self.budget_status_label.setText(f"{format_currency(current_spending)} / {format_currency(budget)} ({percent:.1f}%)")
            
            # 更新预测文本
            pred_total = forecast['predicted_total']
            status = forecast['status']
            remaining = forecast['remaining_days']
            
            if status == "danger":
                status_icon = "⚠️"
                color = COLORS['accent_danger']
                msg = "可能超支"
                tip = f"建议日均控制在 {format_currency((budget - current_spending)/remaining) if remaining > 0 else 0} 以内"
            elif status == "warning":
                status_icon = "🔔"
                color = COLORS['accent_warning']
                msg = "需注意"
                tip = "接近预算上限"
            else:
                status_icon = "✅"
                color = COLORS['accent_success']
                msg = "预算充足"
                tip = "继续保持"
                
            self.forecast_label.setText(f"{status_icon} 智能预测本月: {format_currency(pred_total)} ({msg})  |  {tip}")
            self.forecast_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
            
        else:
            # 如果没有设置预算，隐藏预算条和预测
            self.budget_bar.setVisible(False)
            self.budget_status_label.setVisible(False)
            self.budget_label_header.setVisible(False)
            self.forecast_label.setVisible(False)

        # 更新图表数据
        try:
            # 趋势图数据
            dates, values = db.get_daily_trend(30)
            self.trend_chart.update_data(dates, values)
            
            # 分类饼图数据
            cat_data = db.get_category_distribution()
            self.pie_chart.update_data(cat_data)
        except Exception as e:
            print(f"Chart update failed: {e}")
