"""
收入记录列表组件
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QFrame,
    QMessageBox, QGraphicsDropShadowEffect, QAbstractItemView,
    QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction, QCursor
from datetime import datetime
from typing import Optional, List

from ..models import IncomeRecord
from ..database import get_database
from ..utils import format_currency, format_date
from .styles import COLORS


class RecordListWidget(QWidget):
    """收入记录列表"""
    
    # 信号：请求编辑记录
    edit_requested = pyqtSignal(IncomeRecord)
    # 信号：记录已删除
    record_deleted = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filter_start = None
        self.current_filter_end = None
        self.records: List[IncomeRecord] = []
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 列表容器
        list_container = QFrame()
        list_container.setObjectName("listContainer")
        list_container.setStyleSheet(f"""
            QFrame#listContainer {{
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
        list_container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(list_container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(16)
        
        # 头部
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 收入记录")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 记录数量标签
        self.count_label = QLabel("共 0 条记录")
        self.count_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px;")
        header_layout.addWidget(self.count_label)
        
        container_layout.addLayout(header_layout)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["日期", "金额", "分类", "备注", "操作"])
        
        # 表格样式
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                border: none;
                gridline-color: {COLORS['border_muted']};
            }}
            QTableWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {COLORS['border_muted']};
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['accent_secondary']};
            }}
            QTableWidget::item:hover {{
                background-color: {COLORS['card_hover']};
            }}
        """)
        
        # 表格设置
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        
        # 设置表头
        header = self.table.horizontalHeader()
        header.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_secondary']};
                font-weight: bold;
                padding: 12px;
                border: none;
                border-bottom: 2px solid {COLORS['border_default']};
            }}
        """)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 110)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(4, 100)
        
        # 右键菜单
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        container_layout.addWidget(self.table)
        layout.addWidget(list_container)
        
    def refresh(self, start_date: Optional[datetime] = None, 
                end_date: Optional[datetime] = None):
        """刷新记录列表"""
        self.current_filter_start = start_date
        self.current_filter_end = end_date
        
        db = get_database()
        self.records = db.get_incomes(start_date=start_date, end_date=end_date)
        
        # 批量更新：禁用 UI 更新以提高性能
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(self.records))
        
        for row, record in enumerate(self.records):
            # 日期
            date_item = QTableWidgetItem(format_date(record.date))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, date_item)
            
            # 金额
            amount_item = QTableWidgetItem(format_currency(record.amount))
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            amount_item.setForeground(QColor(COLORS['accent_success']))
            self.table.setItem(row, 1, amount_item)
            
            # 分类
            category_item = QTableWidgetItem(record.category)
            category_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, category_item)
            
            # 备注
            desc_item = QTableWidgetItem(record.description or "-")
            desc_item.setForeground(QColor(COLORS['text_secondary']))
            self.table.setItem(row, 3, desc_item)
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(5, 5, 5, 5)
            btn_layout.setSpacing(5)
            
            edit_btn = QPushButton("编辑")
            edit_btn.setMinimumHeight(30)
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent_secondary']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 5px 10px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_primary']};
                }}
            """)
            edit_btn.clicked.connect(lambda checked, r=record: self.edit_record(r))
            btn_layout.addWidget(edit_btn)
            
            del_btn = QPushButton("删除")
            del_btn.setMinimumHeight(30)
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent_danger']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 5px 10px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: #da3633;
                }}
            """)
            del_btn.clicked.connect(lambda checked, r=record: self.delete_record(r))
            btn_layout.addWidget(del_btn)
            
            self.table.setCellWidget(row, 4, btn_widget)
            
            # 设置行高
            self.table.setRowHeight(row, 55)
            
        self.count_label.setText(f"共 {len(self.records)} 条记录")
        
        # 恢复 UI 更新
        self.table.setUpdatesEnabled(True)
        
    def show_context_menu(self, position):
        """显示右键菜单"""
        row = self.table.rowAt(position.y())
        if row < 0 or row >= len(self.records):
            return
            
        record = self.records[row]
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['card_bg']};
                border: 1px solid {COLORS['border_default']};
                border-radius: 8px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['card_hover']};
            }}
        """)
        
        edit_action = QAction("✏️ 编辑", self)
        edit_action.triggered.connect(lambda: self.edit_record(record))
        menu.addAction(edit_action)
        
        delete_action = QAction("🗑️ 删除", self)
        delete_action.triggered.connect(lambda: self.delete_record(record))
        menu.addAction(delete_action)
        
        menu.exec(QCursor.pos())
        
    def edit_record(self, record: IncomeRecord):
        """编辑记录"""
        self.edit_requested.emit(record)
        
    def delete_record(self, record: IncomeRecord):
        """删除记录"""
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除这条记录吗？\n\n日期：{format_date(record.date)}\n金额：{format_currency(record.amount)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db = get_database()
            if db.delete_income(record.id):
                self.record_deleted.emit()
            else:
                QMessageBox.critical(self, "错误", "删除记录失败！")
                
    def apply_filter(self, start_date: Optional[datetime], end_date: Optional[datetime]):
        """应用筛选"""
        self.refresh(start_date, end_date)
