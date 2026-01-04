"""
自定义 UI 组件库
提供高级交互和视觉效果的通用组件
"""
from PyQt6.QtWidgets import (
    QStackedWidget, QWidget, QGraphicsOpacityEffect, 
    QLabel, QProgressBar
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QPoint, 
    QAbstractAnimation, QParallelAnimationGroup
)

from .styles import COLORS

class AnimatedStackedWidget(QStackedWidget):
    """
    带切换动画的 StackedWidget
    支持滑动和淡入淡出效果
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.m_direction = Qt.Orientation.Horizontal
        self.m_duration = 300 # 动画时长 ms
        self.m_curve = QEasingCurve.Type.OutCubic
        self.m_active = False # 是否正在动画

    def setAnimation(self, direction=Qt.Orientation.Horizontal, duration=300, curve=QEasingCurve.Type.OutCubic):
        self.m_direction = direction
        self.m_duration = duration
        self.m_curve = curve

    def slideInIdx(self, index: int):
        """切换到指定索引（带动画）"""
        if index == self.currentIndex() or self.m_active:
            return

        self.m_active = True
        
        current_idx = self.currentIndex()
        next_idx = index
        
        current_widget = self.widget(current_idx)
        next_widget = self.widget(next_idx)
        
        # 确定滑动方向 (下行是向左滑，上行是向右滑)
        offset_x = self.frameRect().width()
        offset_y = self.frameRect().height()
        
        # 默认 next 从右边进来 (offset_x, 0)
        # current 往左边出去 (-offset_x, 0)
        # 如果是往前翻页，则反过来
        is_forward = next_idx > current_idx
        
        if not is_forward:
            offset_x = -offset_x
            offset_y = -offset_y

        next_widget.setGeometry(self.rect())
        
        # 初始位置
        start_pos_current = QPoint(0, 0)
        end_pos_current = QPoint(-offset_x, 0)
        
        start_pos_next = QPoint(offset_x, 0)
        end_pos_next = QPoint(0, 0)
        
        # 设置 next widget 初始位置
        next_widget.move(start_pos_next)
        next_widget.show()
        next_widget.raise_()
        
        # 动画组 (使用下划线前缀确保引用持久)
        self._anim_group = QParallelAnimationGroup(self)
        
        anim_current = QPropertyAnimation(current_widget, b"pos")
        anim_current.setDuration(self.m_duration)
        anim_current.setStartValue(start_pos_current)
        anim_current.setEndValue(end_pos_current)
        anim_current.setEasingCurve(self.m_curve)
        
        anim_next = QPropertyAnimation(next_widget, b"pos")
        anim_next.setDuration(self.m_duration)
        anim_next.setStartValue(start_pos_next)
        anim_next.setEndValue(end_pos_next)
        anim_next.setEasingCurve(self.m_curve)
        
        self._anim_group.addAnimation(anim_current)
        self._anim_group.addAnimation(anim_next)
        
        self._anim_group.finished.connect(lambda: self._on_animation_finished(next_idx))
        
        self._anim_group.start()

    def _on_animation_finished(self, index):
        self.setCurrentIndex(index)
        self.widget(index).move(0, 0) # 确保位置归零
        self.m_active = False

class BudgetProgressBar(QProgressBar):
    """
    自定义预算进度条
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setFixedHeight(8)
        self.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {COLORS['border_muted']};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent_primary']};
                border-radius: 4px;
            }}
        """)
    
    def set_status(self, current, total):
        """设置状态，根据百分比变色"""
        if total <= 0:
            percentage = 0
            self.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background-color: {COLORS['border_muted']};
                    border-radius: 4px;
                }}
            """)
        else:
            percentage = int((current / total) * 100)
            percentage = min(percentage, 100)
            
            color = COLORS['accent_primary']
            if percentage > 90:
                color = COLORS['accent_danger']
            elif percentage > 75:
                color = COLORS['accent_warning']
                
            self.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background-color: {COLORS['border_muted']};
                    border-radius: 4px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 4px;
                }}
            """)
            
        self.setValue(percentage)
