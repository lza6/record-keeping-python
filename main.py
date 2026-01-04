"""
收入记账助手
基于 PyQt6 的个人收入管理软件
"""
import sys
import os
import traceback
from datetime import datetime

# 确保模块路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt

from app.ui.main_window import MainWindow
from app.database import get_database

class ErrorDialog(QDialog):
    """自定义错误报告对话框"""
    def __init__(self, error_msg):
        super().__init__()
        self.setWindowTitle("程序遇到问题")
        self.setFixedSize(500, 350)
        self.setup_ui(error_msg)
        
    def setup_ui(self, error_msg):
        layout = QVBoxLayout(self)
        
        # 头部
        header_layout = QHBoxLayout()
        icon_label = QLabel("😔")
        icon_label.setStyleSheet("font-size: 40px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel("糟糕，程序发生了一个意外错误")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        layout.addWidget(QLabel("我们已记录错误详情，您可以截图或复制以下信息反馈给开发者:"))
        
        # 详情区域
        self.text_area = QTextEdit()
        self.text_area.setPlainText(error_msg)
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ccc; font-family: Consolas;")
        layout.addWidget(self.text_area)
        
        # 按钮
        btn_layout = QHBoxLayout()
        copy_btn = QPushButton("复制错误信息")
        copy_btn.clicked.connect(self.copy_error)
        btn_layout.addWidget(copy_btn)
        
        btn_layout.addStretch()
        
        quit_btn = QPushButton("退出程序")
        quit_btn.clicked.connect(self.accept)
        btn_layout.addWidget(quit_btn)
        
        layout.addLayout(btn_layout)
        
    def copy_error(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_area.toPlainText())
        QMessageBox.information(self, "复制成功", "错误详情已复制到剪贴板")

def exception_hook(exctype, value, tb):
    """全局异常捕获"""
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    print(error_msg)
    
    # 写入日志
    with open("error.log", "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] Uncaught Exception:\n")
        f.write(error_msg)
        f.write("-" * 50 + "\n")
        
    # 显示自定义错误框
    if QApplication.instance():
        dialog = ErrorDialog(error_msg)
        dialog.exec()

def shutdown_handler():
    """程序退出时的清理工作"""
    print("Shutting down...")
    try:
        db = get_database()
        print("Optimizing database...")
        db.vacuum_db()
        print("Database optimized.")
    except Exception as e:
        print(f"Cleanup failed: {e}")

def main():
    """程序入口"""
    # 注册异常钩子
    sys.excepthook = exception_hook
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 注册退出钩子
    app.aboutToQuit.connect(shutdown_handler)
    
    # 设置应用属性
    app.setApplicationName("收入记账助手 Pro")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("IncomeTracker")
    
    # 设置默认字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 启用高DPI缩放
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
