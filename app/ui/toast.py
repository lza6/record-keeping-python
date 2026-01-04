"""
Toast 消息通知组件
非阻塞式、美观的消息提示
"""
from PyQt6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve
from PyQt6.QtGui import QColor

from .styles import COLORS, FONTS

class Toast(QLabel):
    """
    Toast 通知组件
    """
    def __init__(self, parent, message, duration=3000, type="info"):
        super().__init__(parent)
        self.message = message
        self.duration = duration
        self.type = type
        
        self.setup_ui()
        self.show_animation()
        
    def setup_ui(self):
        """设置UI"""
        # 根据类型设置颜色
        if self.type == "success":
            color = COLORS['accent_success']
            icon = "✅"
        elif self.type == "error":
            color = COLORS['accent_danger']
            icon = "❌"
        elif self.type == "warning":
            color = COLORS['accent_warning']
            icon = "⚠️"
        else:
            color = COLORS['accent_primary']
            icon = "ℹ️"
            
        self.setText(f"{icon}  {self.message}")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {color};
                border-radius: 8px;
                padding: 12px 24px;
                font-family: {FONTS['primary']};
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        self.adjustSize()
        
        # 居中显示在父窗口下方
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = parent_rect.height() - 100
            self.move(x, y)
            
        # 设置透明度效果
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
    def show_animation(self):
        """显示动画"""
        self.show()
        
        # 1. 淡入 + 上浮
        self.anim_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_in.setDuration(300)
        self.anim_in.setStartValue(0)
        self.anim_in.setEndValue(1)
        self.anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(300)
        start_pos = self.pos()
        self.pos_anim.setStartValue(QPoint(start_pos.x(), start_pos.y() + 20))
        self.pos_anim.setEndValue(start_pos)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.anim_in.start()
        self.pos_anim.start()
        
        # 定时关闭
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close_animation)
        self.timer.start(self.duration)
        
    def close_animation(self):
        """关闭动画"""
        self.timer.stop()
        
        # 淡出
        self.anim_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_out.setDuration(300)
        self.anim_out.setStartValue(1)
        self.anim_out.setEndValue(0)
        self.anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim_out.finished.connect(self._cleanup)
        self.anim_out.start()
    
    def _cleanup(self):
        """清理资源，防止内存泄漏"""
        self.close()
        # 使用 deleteLater 确保 Qt 对象正确释放
        self.deleteLater()

# 静态帮助方法
def show_toast(parent, message, type="info", duration=3000):
    toast = Toast(parent, message, duration, type)
    toast.show()
