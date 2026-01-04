"""
PyQt6 样式定义
支持多主题切换和现代化设计
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor

# 字体设置
FONTS = {
    "primary": "Microsoft YaHei, Segoe UI, sans-serif",
    "mono": "Consolas, Monaco, monospace",
}

# 预定义主题
THEMES = {
    "dark": {
        "name": "深邃夜空",
        "colors": {
            "bg_primary": "#0d1117",
            "bg_secondary": "#161b22",
            "bg_tertiary": "#21262d",
            "card_bg": "#1c2128",
            "card_hover": "#262c36",
            "card_border": "#30363d",
            "accent_primary": "#58a6ff",
            "accent_secondary": "#1f6feb",
            "accent_success": "#3fb950",
            "accent_warning": "#d29922",
            "accent_danger": "#f85149",
            "gradient_start": "#667eea",
            "gradient_end": "#764ba2",
            "text_primary": "#f0f6fc",
            "text_secondary": "#8b949e",
            "text_muted": "#6e7681",
            "border_default": "#30363d",
            "border_muted": "#21262d",
            "input_bg": "#0d1117",
            "input_border": "#30363d",
            "input_focus": "#58a6ff",
        }
    },
    "light": {
        "name": "清新明亮",
        "colors": {
            "bg_primary": "#f6f8fa",
            "bg_secondary": "#ffffff",
            "bg_tertiary": "#eff2f5",
            "card_bg": "#ffffff",
            "card_hover": "#f3f5f8",
            "card_border": "#d0d7de",
            "accent_primary": "#0969da",
            "accent_secondary": "#218bff",
            "accent_success": "#1a7f37",
            "accent_warning": "#bf8700",
            "accent_danger": "#cf222e",
            "gradient_start": "#4facfe",
            "gradient_end": "#00f2fe",
            "text_primary": "#24292f",
            "text_secondary": "#57606a",
            "text_muted": "#8c959f",
            "border_default": "#d0d7de",
            "border_muted": "#eaeef2",
            "input_bg": "#ffffff",
            "input_border": "#d0d7de",
            "input_focus": "#0969da",
        }
    },
    "modern_fusion": {
        "name": "现代融合 (Glass)",
        "colors": {
            "bg_primary": "#121212",
            "bg_secondary": "#1e1e1e",
            "bg_tertiary": "#252526",
            "card_bg": "rgba(40, 40, 40, 0.7)", # 半透明 Glass
            "card_hover": "rgba(60, 60, 60, 0.8)",
            "card_border": "rgba(255, 255, 255, 0.1)",
            "accent_primary": "#bb86fc",
            "accent_secondary": "#3700b3",
            "accent_success": "#03dac6",
            "accent_warning": "#cf6679",
            "accent_danger": "#ffb4ab",
            "gradient_start": "#7f00ff",
            "gradient_end": "#e100ff",
            "text_primary": "#e1e1e1",
            "text_secondary": "#a0a0a0",
            "text_muted": "#606060",
            "border_default": "#333333",
            "border_muted": "#2a2a2a",
            "input_bg": "#2d2d2d",
            "input_border": "#3d3d3d",
            "input_focus": "#bb86fc",
        }
    }
}

# 默认颜色 (用于兼容旧引用)
COLORS = THEMES['dark']['colors']
CARD_COLORS = {
    "total": "#7f00ff",    # Violet
    "yearly": "#03dac6",   # Teal
    "monthly": "#bb86fc",  # Purple
    "average": "#ffb4ab",  # Red-ish
}

class ThemeManager:
    """主题管理器"""
    
    @staticmethod
    def get_style_sheet(theme_name: str = "dark") -> str:
        """生成指定主题的样式表"""
        theme = THEMES.get(theme_name, THEMES['dark'])
        c = theme['colors']
        
        is_glass = "modern_fusion" in theme_name
        card_bg_style = f"background-color: {c['card_bg']};" if not is_glass else f"background-color: {c['card_bg']}; border: 1px solid {c['card_border']};"

        return f"""
        /* 全局样式 - {theme['name']} */
        QWidget {{
            font-family: {FONTS['primary']};
            font-size: 14px;
            color: {c['text_primary']};
        }}

        QMainWindow {{
            background-color: {c['bg_primary']};
        }}

        /* 滚动条 - 更现代的细条 */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 8px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background-color: {c['border_muted']};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {c['accent_primary']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

        QScrollBar:horizontal {{
            background-color: transparent;
            height: 8px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {c['border_muted']};
            border-radius: 4px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {c['accent_primary']};
        }}

        /* 按钮通用 */
        QPushButton {{
            background-color: {c['bg_tertiary']};
            color: {c['text_primary']};
            border: 1px solid {c['border_default']};
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {c['card_hover']};
            border-color: {c['accent_primary']};
        }}
        QPushButton:pressed {{
            background-color: {c['border_muted']};
        }}
        
        /* 特殊按钮 */
        QPushButton#primaryBtn {{
            background-color: {c['accent_primary']};
            color: {c['bg_primary'] if is_glass else 'white'};
            border: none;
        }}
        QPushButton#primaryBtn:hover {{
            background-color: {c['accent_secondary']};
        }}
        
        QPushButton#dangerBtn {{
            background-color: {c['accent_danger']};
            color: {c['bg_primary'] if is_glass else 'white'};
            border: none;
        }}
        QPushButton#dangerBtn:hover {{
            background-color: #d32f2f;
        }}

        /* 侧边栏导航按钮 */
        QPushButton#navBtn {{
            background-color: transparent;
            border: none;
            text-align: left;
            padding: 12px 20px;
            border-radius: 8px;
            color: {c['text_secondary']};
            font-size: 15px;
        }}
        QPushButton#navBtn:hover {{
            background-color: {c['bg_tertiary']};
            color: {c['text_primary']};
        }}
        QPushButton#navBtn:checked {{
            background-color: {c['accent_primary']};
            color: {c['bg_primary'] if is_glass else 'white'};
            font-weight: bold;
        }}

        /* 卡片容器 */
        QFrame#card {{
            {card_bg_style}
            border-radius: 12px;
        }}
        QFrame#card:hover {{
            border-color: {c['accent_primary']};
        }}
        
        /* 侧边栏 */
        QFrame#sidebar {{
            background-color: {c['bg_secondary']};
            border-right: 1px solid {c['border_default']};
        }}
        
        /* 输入框 */
        QLineEdit, QDoubleSpinBox, QDateEdit, QComboBox, QTextEdit {{
            background-color: {c['input_bg']};
            border: 1px solid {c['input_border']};
            border-radius: 6px;
            padding: 8px;
            color: {c['text_primary']};
            selection-background-color: {c['accent_primary']};
        }}
        QLineEdit:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus {{
            border: 2px solid {c['input_focus']};
            padding: 7px; /* 补偿边框宽度变化 */
        }}
        
        /* 表格 */
        QTableWidget {{
            background-color: {c['card_bg']};
            border: none;
            gridline-color: {c['border_muted']};
            alternate-background-color: {c['bg_tertiary']};
        }}
        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {c['border_muted']};
        }}
        QTableWidget::item:selected {{
            background-color: {c['bg_tertiary']};
            color: {c['accent_primary']};
        }}
        QHeaderView::section {{
            background-color: {c['bg_tertiary']};
            color: {c['text_secondary']};
            border: none;
            padding: 8px;
            font-weight: bold;
        }}
        
        /* 标签 */
        QLabel#h1 {{
            font-size: 24px;
            font-weight: bold;
            color: {c['text_primary']};
        }}
        QLabel#h2 {{
            font-size: 18px;
            font-weight: bold;
            color: {c['text_primary']};
        }}
        QLabel#subtitle {{
            font-size: 14px;
            color: {c['text_secondary']};
        }}
        """

    @staticmethod
    def apply_theme(app: QApplication, theme_name: str):
        """应用主题"""
        app.setStyleSheet(ThemeManager.get_style_sheet(theme_name))
        
        # 更新全局 COLORS 引用
        global COLORS
        COLORS.update(THEMES[theme_name]['colors'])

class AnimationEffects:
    """常用的动画效果"""
    
    @staticmethod
    def fade_in(widget, duration=500):
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        
        op = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(op)
        
        anim = QPropertyAnimation(op, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.start()
        # 注意: 动画对象需要保持引用，否则会被垃圾回收，实际使用时建议作为 widget 属性
        widget._fade_anim = anim 

# 全局样式表 (默认深色)
GLOBAL_STYLESHEET = ThemeManager.get_style_sheet("dark")
