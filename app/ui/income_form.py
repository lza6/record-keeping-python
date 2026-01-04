"""
收入录入表单组件
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QComboBox, QDateEdit, QPushButton,
    QTextEdit, QFrame, QMessageBox, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor
from datetime import datetime

from ..models import IncomeRecord, INCOME_CATEGORIES
from ..database import get_database
from ..utils import get_beijing_time, BEIJING_TZ
from .styles import COLORS


class SmartCategorizer:
    """智能分类器"""
    
    # 关键词映射 (简单规则引擎)
    RULES = {
        "工资": "工资薪金", "薪水": "工资薪金", "奖金": "奖金补贴", "加班": "奖金补贴",
        "股票": "投资收益", "基金": "投资收益", "理财": "投资收益", "股息": "投资收益",
        "兼职": "兼职收入", "外快": "兼职收入", "副业": "兼职收入",
        "红包": "人情往来", "礼金": "人情往来",
        "退税": "其他收入", "报销": "其他收入"
    }
    
    @staticmethod
    def suggest_category(text: str) -> str:
        text = text.lower()
        for keyword, category in SmartCategorizer.RULES.items():
            if keyword in text:
                return category
        return None


class IncomeFormWidget(QWidget):
    """收入录入表单"""
    
    # 信号：记录添加成功
    record_added = pyqtSignal()
    # 信号：记录更新成功
    record_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.editing_record = None  # 正在编辑的记录
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 表单容器
        form_container = QFrame()
        form_container.setObjectName("card")  # 使用全局样式定义的 card 样式
        
        # 添加阴影 (保持不变，通用阴影)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        form_container.setGraphicsEffect(shadow)
        
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(20)
        
        # 标题
        title = QLabel("➕  新增收入")
        title.setObjectName("h2")
        form_layout.addWidget(title)
        self.form_title = title
        
        # 金额输入
        amount_layout = QVBoxLayout()
        amount_label = QLabel("💵 金额")
        amount_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold;")
        amount_layout.addWidget(amount_label)
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 999999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setPrefix("¥ ")
        self.amount_input.setSingleStep(100)
        self.amount_input.setMinimumHeight(45)
        amount_layout.addWidget(self.amount_input)
        form_layout.addLayout(amount_layout)
        
        # 分类选择
        category_layout = QVBoxLayout()
        category_label = QLabel("📂 分类")
        category_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold;")
        category_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(INCOME_CATEGORIES)
        self.category_combo.setMinimumHeight(45)
        category_layout.addWidget(self.category_combo)
        form_layout.addLayout(category_layout)
        
        # 日期选择
        date_layout = QVBoxLayout()
        date_label = QLabel("📅 日期")
        date_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold;")
        date_layout.addWidget(date_label)
        
        date_input_layout = QHBoxLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setMinimumHeight(45)
        date_input_layout.addWidget(self.date_edit)
        
        # 快捷按钮
        btn_yesterday = QPushButton("昨天")
        btn_yesterday.setFixedWidth(60)
        btn_yesterday.setFixedHeight(40)
        btn_yesterday.clicked.connect(lambda: self.date_edit.setDate(QDate.currentDate().addDays(-1)))
        date_input_layout.addWidget(btn_yesterday)
        
        btn_today = QPushButton("今天")
        btn_today.setFixedWidth(60)
        btn_today.setFixedHeight(40)
        btn_today.clicked.connect(lambda: self.date_edit.setDate(QDate.currentDate()))
        date_input_layout.addWidget(btn_today)
        
        date_layout.addLayout(date_input_layout)
        form_layout.addLayout(date_layout)
        
        # 备注输入 (包含智能分类监听)
        desc_layout = QVBoxLayout()
        desc_label = QLabel("📝 备注 (选填)")
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold;")
        desc_layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("例如：加班费、股票理财收益...")
        self.desc_input.setMaximumHeight(80)
        self.desc_input.textChanged.connect(self.on_desc_changed) # 监听
        desc_layout.addWidget(self.desc_input)
        form_layout.addLayout(desc_layout)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        # 取消按钮（编辑模式下显示）
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("secondaryBtn")
        self.cancel_btn.setMinimumHeight(45)
        self.cancel_btn.clicked.connect(self.cancel_edit)
        self.cancel_btn.setVisible(False)
        btn_layout.addWidget(self.cancel_btn)
        
        # 提交按钮
        self.submit_btn = QPushButton("✓ 保存记录")
        self.submit_btn.setObjectName("primaryBtn")
        self.submit_btn.setMinimumHeight(45)
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.clicked.connect(self.submit)
        btn_layout.addWidget(self.submit_btn)
        
        form_layout.addLayout(btn_layout)
        
        layout.addWidget(form_container)
        layout.addStretch()

    def on_desc_changed(self):
        """当备注改变时，尝试智能分类"""
        # 仅在非编辑模式，或者用户未手动修改过分类时生效 (简化处理：总是尝试，除非用户刚选过？)
        # 这里简单策略：只在文本输入时触发，如果是编辑已有记录，也会触发，但这可能符合预期
        text = self.desc_input.toPlainText()
        suggestion = SmartCategorizer.suggest_category(text)
        if suggestion:
            index = self.category_combo.findText(suggestion)
            if index >= 0 and self.category_combo.currentIndex() != index:
                # 提示用户或直接切换？直接切换更流畅，但最好有个视觉反馈
                self.category_combo.setCurrentIndex(index)
                # 可选：闪烁一下分类框 (这里暂略)

    def submit(self):
        """提交表单"""
        amount = self.amount_input.value()
        
        # 验证反馈
        if amount <= 0:
            self.amount_input.setStyleSheet(f"border: 2px solid {COLORS['accent_danger']};")
            # 震动效果可以使用动画，这里简单弹窗
            QMessageBox.warning(self, "输入错误", "请输入有效的金额！")
            return
        else:
            # 恢复样式
            self.amount_input.setStyleSheet("")
            
        category = self.category_combo.currentText()
        description = self.desc_input.toPlainText().strip()
        
        # 获取选择的日期并转换为带时区的datetime
        qdate = self.date_edit.date()
        record_date = datetime(
            qdate.year(), qdate.month(), qdate.day(),
            tzinfo=BEIJING_TZ
        )
        
        db = get_database()
        
        if self.editing_record:
            # 更新模式
            self.editing_record.amount = amount
            self.editing_record.category = category
            self.editing_record.description = description
            self.editing_record.date = record_date
            
            if db.update_income(self.editing_record):
                self.reset_form()
                self.record_updated.emit()
            else:
                QMessageBox.critical(self, "错误", "更新记录失败！")
        else:
            # 添加模式
            record = IncomeRecord(
                id=None,
                amount=amount,
                category=category,
                description=description,
                date=record_date,
                created_at=get_beijing_time()
            )
            
            try:
                db.add_income(record)
                self.reset_form()
                self.record_added.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加记录失败：{str(e)}")
                
    def reset_form(self):
        """重置表单"""
        # 阻断信号防止重置时触发智能分类
        self.desc_input.blockSignals(True)
        
        self.amount_input.setValue(0)
        self.amount_input.setStyleSheet("") # 清除错误样式
        self.category_combo.setCurrentIndex(0)
        self.date_edit.setDate(QDate.currentDate())
        self.desc_input.clear()
        
        self.desc_input.blockSignals(False)
        
        # 退出编辑模式
        self.editing_record = None
        self.form_title.setText("➕ 新增收入")
        self.submit_btn.setText("✓ 保存记录")
        self.cancel_btn.setVisible(False)
        
    def edit_record(self, record: IncomeRecord):
        """进入编辑模式"""
        self.editing_record = record
        
        self.desc_input.blockSignals(True) # 防止填充时触发
        
        # 填充表单
        self.amount_input.setValue(record.amount)
        
        # 设置分类
        index = self.category_combo.findText(record.category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
            
        # 设置日期
        self.date_edit.setDate(QDate(
            record.date.year,
            record.date.month,
            record.date.day
        ))
        
        self.desc_input.setText(record.description)
        self.desc_input.blockSignals(False)
        
        # 更新UI
        self.form_title.setText("✏️ 编辑收入")
        self.submit_btn.setText("✓ 保存更改")
        self.cancel_btn.setVisible(True)
        
    def cancel_edit(self):
        """取消编辑"""
        self.reset_form()
