"""
图表组件
使用 PyQt6-Charts 实现高级数据可视化
"""
try:
    from PyQt6.QtCharts import (
        QChart, QChartView, QLineSeries, QPieSeries, 
        QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis,
        QPieSlice, QSplineSeries, QAreaSeries
    )
    from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient
    from PyQt6.QtCore import Qt
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    from PyQt6.QtWidgets import QLabel
    from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from .styles import COLORS, FONTS

if CHARTS_AVAILABLE:
    class BaseChartWidget(QChartView):
        """图表基类"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.setStyleSheet("background: transparent;")
            
            self.chart = QChart()
            self.chart.setBackgroundVisible(False)
            self.chart.layout().setContentsMargins(0, 0, 0, 0) # 减少边距
            self.setChart(self.chart)
            
            # 通用图表设置
            self.chart.legend().setVisible(True)
            self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
            self.chart.legend().setLabelColor(QColor(COLORS['text_secondary']))
            
            # 汉字字体支持
            font = QFont(FONTS['primary'], 9)
            self.chart.setTitleFont(QFont(FONTS['primary'], 12, QFont.Weight.Bold))
            self.chart.legend().setFont(font)
            
        def set_title(self, title: str):
            self.chart.setTitle(title)
            self.chart.setTitleBrush(QColor(COLORS['text_primary']))

    class AreaTrendChart(BaseChartWidget):
        """收入趋势面积图 (Area Chart)"""
        def __init__(self, parent=None):
            super().__init__(parent)
            
            # 创建曲线系列
            self.upper_series = QSplineSeries()
            self.upper_series.setName("每日收入")
            
            # 设置线条样式
            pen = QPen(QColor(COLORS['accent_primary']))
            pen.setWidth(2)
            self.upper_series.setPen(pen)
            
            # 创建面积系列 (使用 upper_series 作为上边界)
            self.area_series = QAreaSeries(self.upper_series)
            self.area_series.setName("收入趋势")
            
            # 设置渐变填充
            gradient = QLinearGradient(0, 0, 0, 1)
            gradient.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
            gradient.setColorAt(0.0, QColor(COLORS['accent_primary']))
            gradient.setColorAt(1.0, QColor(COLORS['accent_secondary'])) # 或者是更淡的颜色
            
            # 如果是 Glass 风格，透明度可以更低
            # 注意: 这里简单处理，AreaSeries 的 brush 默认是不透明的
            c_start = QColor(COLORS['gradient_start'])
            c_start.setAlpha(150)
            c_end = QColor(COLORS['gradient_end'])
            c_end.setAlpha(30)
            
            gradient_fill = QLinearGradient(0, 0, 0, 1)
            gradient_fill.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
            gradient_fill.setColorAt(0.0, c_start)
            gradient_fill.setColorAt(1.0, c_end)
            
            self.area_series.setBrush(gradient_fill)
            
            # 去掉面积图的边框
            self.area_series.setPen(QPen(Qt.PenStyle.NoPen))
            
            self.chart.addSeries(self.area_series)
            self.chart.addSeries(self.upper_series) # 叠加线条以确保清晰
            
            # 坐标轴
            self.axis_x = QBarCategoryAxis()
            self.axis_x.setLabelsColor(QColor(COLORS['text_secondary']))
            self.axis_x.setGridLineColor(QColor(COLORS['border_muted']))
            self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
            self.upper_series.attachAxis(self.axis_x)
            self.area_series.attachAxis(self.axis_x)
            
            self.axis_y = QValueAxis()
            self.axis_y.setLabelsColor(QColor(COLORS['text_secondary']))
            self.axis_y.setGridLineColor(QColor(COLORS['border_muted']))
            self.axis_y.setLabelFormat("%.0f")
            self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)
            self.upper_series.attachAxis(self.axis_y)
            self.area_series.attachAxis(self.axis_y)
            
            # 隐藏图例 (如果不需要显示具体 series name)
            self.chart.legend().hide()
            
        def update_data(self, dates: list, values: list):
            """更新数据"""
            self.upper_series.clear()
            self.axis_x.clear()
            
            # 限制数据点数量，避免过密
            if len(dates) > 30:
                step = len(dates) // 30 + 1
                display_dates = dates[::step]
                display_values = values[::step]
            else:
                display_dates = dates
                display_values = values
                
            self.axis_x.append(display_dates)
            
            max_val = 0
            for i, val in enumerate(display_values):
                self.upper_series.append(i, val)
                if val > max_val:
                    max_val = val
                    
            # 动态调整 Y 轴
            top_margin = max_val * 0.2 if max_val > 0 else 100
            self.axis_y.setRange(0, max_val + top_margin)


    class CategoryPieChart(BaseChartWidget):
        """分类占比图 (环形图)"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.series = QPieSeries()
            self.series.setHoleSize(0.45) # 稍微加大空心
            self.series.setPieSize(0.75) # 调整大小
            
            self.chart.addSeries(self.series)
            
        def update_data(self, data: dict):
            """
            更新数据
            data: {category: amount}
            """
            self.series.clear()
            
            # 预定义颜色列表
            colors = [
                COLORS['accent_primary'], COLORS['accent_secondary'], 
                COLORS['accent_success'], COLORS['accent_warning'], 
                COLORS['accent_danger'], COLORS['gradient_start'],
                COLORS['gradient_end']
            ]
            
            sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
            
            # 只显示前 6 项 + 其他
            if len(sorted_data) > 6:
                others = sum(v for k, v in sorted_data[6:])
                sorted_data = sorted_data[:6]
                sorted_data.append(("其他", others))
            
            for i, (cat, val) in enumerate(sorted_data):
                if val <= 0: continue
                
                slice = self.series.append(cat, val)
                slice.setLabel(f"{cat} {val:.0f}")
                
                # 颜色循环
                color_hex = colors[i % len(colors)]
                color = QColor(color_hex)
                slice.setBrush(color)
                slice.setPen(QPen(QColor(COLORS['bg_primary']), 2)) # 分割线颜色与背景一致
                
                # 特效: 只要 label 可见
                slice.setLabelVisible(True)
                
                # 点击效果
                slice.setExploded(False)
                slice.clicked.connect(lambda: self.handle_slice_click(slice))
                
        def handle_slice_click(self, slice):
            """处理点击扇区"""
            is_exploded = slice.isExploded()
            # 重置所有
            for s in self.series.slices():
                s.setExploded(False)
            # 切换当前
            slice.setExploded(not is_exploded)

else:
    # 替代类，当图表库不可用时
    class BaseChartWidget(QWidget): pass
    
    class AreaTrendChart(QLabel):
        def __init__(self, parent=None):
            super().__init__("图表组件无法加载\n(PyQt6-Charts 未安装)", parent)
            self.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setStyleSheet(f"color: {COLORS['text_muted']};")
        def update_data(self, *args): pass
        
    class CategoryPieChart(QLabel):
        def __init__(self, parent=None):
            super().__init__("图表组件无法加载\n(PyQt6-Charts 未安装)", parent)
            self.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setStyleSheet(f"color: {COLORS['text_muted']};")
        def update_data(self, *args): pass

class ChartContainer(QFrame):
    """图表容器卡片"""
    def __init__(self, title, chart_widget, parent=None):
        super().__init__(parent)
        self.setObjectName("card") # 复用全局 card 样式
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        header = QLabel(title)
        header.setStyleSheet(f"""
            font-size: 15px; 
            font-weight: bold; 
            color: {COLORS['text_secondary']};
            padding-left: 10px;
        """)
        layout.addWidget(header)
        
        layout.addWidget(chart_widget)

