"""
日历筛选组件
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor
from datetime import datetime

from ..utils import (
    get_beijing_time, get_week_range, get_month_range, 
    get_year_range, get_recent_days_range, BEIJING_TZ
)
from .styles import COLORS


class QuickFilterButton(QPushButton):
    """快捷筛选按钮"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumHeight(36)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: 8px;
                padding: 8px 16px;
                color: {COLORS['text_secondary']};
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['card_hover']};
                color: {COLORS['text_primary']};
            }}
            QPushButton:checked {{
                background-color: {COLORS['accent_secondary']};
                border-color: {COLORS['accent_primary']};
                color: {COLORS['text_primary']};
            }}
        """)


class CalendarFilterWidget(QWidget):
    """日历筛选组件"""
    
    # 信号：筛选条件变化
    filter_changed = pyqtSignal(object, object)  # start_date, end_date
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 筛选容器
        filter_container = QFrame()
        filter_container.setObjectName("filterContainer")
        filter_container.setStyleSheet(f"""
            QFrame#filterContainer {{
                background-color: {COLORS['card_bg']};
                border: 1px solid {COLORS['border_default']};
                border-radius: 16px;
            }}
        """)
        
        # 添加阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        filter_container.setGraphicsEffect(shadow)
        
        filter_layout = QVBoxLayout(filter_container)
        filter_layout.setContentsMargins(20, 20, 20, 20)
        filter_layout.setSpacing(16)
        
        # 标题
        title = QLabel("🔍 日期筛选")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        filter_layout.addWidget(title)
        
        # 快捷筛选按钮
        quick_label = QLabel("快捷选择")
        quick_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        filter_layout.addWidget(quick_label)
        
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(8)
        
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        
        self.btn_all = QuickFilterButton("全部")
        self.btn_today = QuickFilterButton("今日")
        self.btn_week = QuickFilterButton("本周")
        self.btn_month = QuickFilterButton("本月")
        self.btn_year = QuickFilterButton("本年")
        
        buttons = [self.btn_all, self.btn_today, self.btn_week, self.btn_month, self.btn_year]
        for i, btn in enumerate(buttons):
            self.btn_group.addButton(btn, i)
            quick_layout.addWidget(btn)
            
        self.btn_all.setChecked(True)
        
        filter_layout.addLayout(quick_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS['border_default']};")
        line.setMaximumHeight(1)
        filter_layout.addWidget(line)
        
        # 自定义日期范围
        custom_label = QLabel("自定义范围")
        custom_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        filter_layout.addWidget(custom_label)
        
        # 开始日期
        start_layout = QHBoxLayout()
        start_label = QLabel("开始日期")
        start_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        start_label.setFixedWidth(70)
        start_layout.addWidget(start_label)
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QDate(2020, 1, 1))
        self.start_date.setMinimumHeight(40)
        start_layout.addWidget(self.start_date)
        filter_layout.addLayout(start_layout)
        
        # 结束日期
        end_layout = QHBoxLayout()
        end_label = QLabel("结束日期")
        end_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        end_label.setFixedWidth(70)
        end_layout.addWidget(end_label)
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setMinimumHeight(40)
        end_layout.addWidget(self.end_date)
        filter_layout.addLayout(end_layout)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setObjectName("secondaryBtn")
        self.reset_btn.setMinimumHeight(40)
        self.reset_btn.clicked.connect(self.reset_filter)
        btn_layout.addWidget(self.reset_btn)
        
        self.apply_btn = QPushButton("应用筛选")
        self.apply_btn.setObjectName("primaryBtn")
        self.apply_btn.setMinimumHeight(40)
        self.apply_btn.clicked.connect(self.apply_custom_filter)
        btn_layout.addWidget(self.apply_btn)
        
        filter_layout.addLayout(btn_layout)
        
        layout.addWidget(filter_container)
        
        # 连接快捷按钮信号
        self.btn_group.buttonClicked.connect(self.on_quick_filter)
        
    def on_quick_filter(self, button):
        """快捷筛选按钮点击"""
        btn_id = self.btn_group.id(button)
        
        if btn_id == 0:  # 全部
            self.filter_changed.emit(None, None)
        elif btn_id == 1:  # 今日
            today = get_beijing_time().replace(hour=0, minute=0, second=0, microsecond=0)
            end = today.replace(hour=23, minute=59, second=59)
            self.filter_changed.emit(today, end)
        elif btn_id == 2:  # 本周
            start, end = get_week_range()
            self.filter_changed.emit(start, end)
        elif btn_id == 3:  # 本月
            start, end = get_month_range()
            self.filter_changed.emit(start, end)
        elif btn_id == 4:  # 本年
            start, end = get_year_range()
            self.filter_changed.emit(start, end)
            
    def apply_custom_filter(self):
        """应用自定义筛选"""
        # 取消快捷按钮选中状态
        checked_btn = self.btn_group.checkedButton()
        if checked_btn:
            self.btn_group.setExclusive(False)
            checked_btn.setChecked(False)
            self.btn_group.setExclusive(True)
        
        start_qdate = self.start_date.date()
        end_qdate = self.end_date.date()
        
        start = datetime(
            start_qdate.year(), start_qdate.month(), start_qdate.day(),
            tzinfo=BEIJING_TZ
        )
        end = datetime(
            end_qdate.year(), end_qdate.month(), end_qdate.day(),
            23, 59, 59,
            tzinfo=BEIJING_TZ
        )
        
        self.filter_changed.emit(start, end)
        
    def reset_filter(self):
        """重置筛选"""
        self.btn_all.setChecked(True)
        self.start_date.setDate(QDate(2020, 1, 1))
        self.end_date.setDate(QDate.currentDate())
        self.filter_changed.emit(None, None)
