"""
主窗口
采用侧边栏导航 + 多页面布局
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QFrame, QPushButton, QButtonGroup, 
    QGraphicsDropShadowEffect, QApplication, QComboBox, QSpacerItem,
    QSizePolicy, QDoubleSpinBox, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QSize, QTimer, QEvent
from PyQt6.QtGui import QIcon, QColor, QAction, QCloseEvent, QShortcut, QKeySequence

from ..utils import get_beijing_time, format_datetime
from ..database import get_database
from .styles import ThemeManager, COLORS, FONTS, THEMES
from .dashboard import DashboardWidget
from .income_form import IncomeFormWidget
from .record_list import RecordListWidget
from .toast import show_toast
from .components import AnimatedStackedWidget
from ..workers import Worker
from PyQt6.QtCore import QThreadPool
from datetime import datetime

class Sidebar(QFrame):
    """侧边栏组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(260)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 30, 15, 20)
        self.layout.setSpacing(10)
        
        # Logo / Title
        title_box = QHBoxLayout()
        title_icon = QLabel("💰")
        title_icon.setStyleSheet("font-size: 32px;")
        title_box.addWidget(title_icon)
        
        title_text = QLabel("记账助手")
        title_text.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_box.addWidget(title_text)
        title_box.addStretch()
        
        self.layout.addLayout(title_box)
        self.layout.addSpacing(30)
        
        # Navigation Buttons
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        
        self.add_nav_btn("📊  仪表概览", 0, checked=True)
        self.add_nav_btn("📝  记一笔", 1)
        self.add_nav_btn("📋  收支明细", 2)
        self.add_nav_btn("⚙️  系统设置", 3)
        
        self.layout.addStretch()
        
        # Time Display
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: #8b949e; font-size: 13px; font-family: Consolas;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.time_label)

    def add_nav_btn(self, text, index, checked=False):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setObjectName("navBtn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(50)
        self.layout.addWidget(btn)
        self.btn_group.addButton(btn, index)

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.setup_window()
        self.setup_ui()
        self.setup_shortcuts()  # 键盘快捷键
        self.setup_tray_icon()  # 系统托盘
        self.start_clock()
        self.check_auto_backup()  # 自动备份检查
        
        # 默认应用深色主题
        self.change_theme("dark")

    def setup_shortcuts(self):
        """设置键盘快捷键"""
        # Ctrl+1: 仪表盘
        self.shortcut_dashboard = QShortcut(QKeySequence("Ctrl+1"), self)
        self.shortcut_dashboard.activated.connect(lambda: self.switch_page(0))
        
        # Ctrl+N: 新增记录
        self.shortcut_new = QShortcut(QKeySequence("Ctrl+N"), self)
        self.shortcut_new.activated.connect(lambda: self.switch_page(1))
        
        # Ctrl+L: 记录列表
        self.shortcut_list = QShortcut(QKeySequence("Ctrl+L"), self)
        self.shortcut_list.activated.connect(lambda: self.switch_page(2))

    def setup_tray_icon(self):
        """配置系统托盘"""
        self.force_quit = False # 标志位：是否强制退出
        
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("resources/icon.png")) # 假如没有图标会自动只显示占位或默认
        # 既然我们没有实际图标文件，暂时用一个 emoji 转成的 pixmap 或者系统默认
        # 这里为了稳健，如果 load 不到图标，Qt 可能会显示空白，我们尽量先不设置具体的 file path，
        # 或者后续可以生成一个。暂时用 window icon。
        self.tray_icon.setIcon(self.windowIcon()) 
        
        # 托盘菜单
        tray_menu = QMenu()
        
        action_show = QAction("打开主界面", self)
        action_show.triggered.connect(self.show_window)
        tray_menu.addAction(action_show)
        
        action_add = QAction("📝 记一笔", self)
        action_add.triggered.connect(self.quick_add_from_tray)
        tray_menu.addAction(action_add)
        
        tray_menu.addSeparator()
        
        action_quit = QAction("退出程序", self)
        action_quit.triggered.connect(self.quit_app)
        tray_menu.addAction(action_quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
        
        # 提示气泡
        self.tray_icon.setToolTip("收入记账助手 Pro")

    def show_window(self):
        self.show()
        self.setWindowState(Qt.WindowState.WindowActive)
        self.activateWindow()

    def quick_add_from_tray(self):
        self.show_window()
        self.switch_page(1) # 跳转到记一笔页面

    def quit_app(self):
        """退出应用程序"""
        # 清理系统托盘图标
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
        self.force_quit = True
        QApplication.quit()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def closeEvent(self, event: QCloseEvent):
        """重写关闭事件：最小化到托盘"""
        if self.force_quit:
            event.accept()
        else:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "记账助手运行中", 
                "程序已最小化到托盘，双击图标可重新打开。", 
                QSystemTrayIcon.MessageIcon.Information, 
                2000
            )

    def check_auto_backup(self):
        """检查是否需要自动备份"""
        last_backup = self.db.get_setting("last_backup_time")
        should_backup = False
        
        now_str = get_beijing_time().strftime("%Y-%m-%d %H:%M:%S")
        
        if not last_backup:
            should_backup = True
        else:
            try:
                last_dt = datetime.strptime(last_backup, "%Y-%m-%d %H:%M:%S")
                # 超过 24 小时
                if (datetime.now() - last_dt).total_seconds() > 86400:
                    should_backup = True
            except:
                should_backup = True
        
        if should_backup:
            print("Starting auto-backup...")
            # 自动备份到 data/backups 目录
            import os
            base_dir = os.path.dirname(self.db.db_path)
            backup_dir = os.path.join(base_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            filename = f"AutoBackup_{get_beijing_time().strftime('%Y%m%d_%H%M%S')}.db"
            target_path = os.path.join(backup_dir, filename)
            
            def do_backup():
                return self.db.backup_db(target_path)
            
            worker = Worker(do_backup)
            # 备份成功后更新时间戳
            worker.signals.result.connect(lambda s: self.on_auto_backup_finished(s, now_str))
            QThreadPool.globalInstance().start(worker)

    def on_auto_backup_finished(self, success, time_str):
        if success:
            self.db.set_setting("last_backup_time", time_str)
            print("Auto-backup successful.")
        else:
            print("Auto-backup failed.")

    def setup_window(self):
        self.setWindowTitle("💰 收入记账助手 Pro")
        self.resize(1200, 850)
        self.setMinimumSize(1000, 700)

    def setup_ui(self):
        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Sidebar
        self.sidebar = Sidebar()
        self.sidebar.btn_group.idClicked.connect(self.switch_page)
        main_layout.addWidget(self.sidebar)
        
        # 2. Main Content Area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Stacked Pages
        self.stack = AnimatedStackedWidget()
        
        # Page 0: Dashboard
        self.page_dashboard = DashboardWidget()
        self.stack.addWidget(self.page_dashboard)
        
        # Page 1: Add Income (Wrapped in a centered widget for aesthetics)
        self.page_add = QWidget()
        add_layout = QVBoxLayout(self.page_add)
        add_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.income_form = IncomeFormWidget()
        self.income_form.setFixedWidth(500) # 限制宽度，更美观
        # 连接添加成功信号到自动跳转
        self.income_form.record_added.connect(self.on_income_added)
        
        add_layout.addWidget(self.income_form)
        self.stack.addWidget(self.page_add)
        
        # Page 2: Records List
        self.page_records = QWidget()
        records_layout = QVBoxLayout(self.page_records)
        self.record_list = RecordListWidget()
        records_layout.addWidget(self.record_list)
        self.stack.addWidget(self.page_records)
        
        # Page 3: Settings
        self.page_settings = self.create_settings_page()
        self.stack.addWidget(self.page_settings)
        
        content_layout.addWidget(self.stack)
        main_layout.addWidget(content_area)

    def create_settings_page(self):
        """创建设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Title
        title = QLabel("⚙️ 系统设置")
        title.setObjectName("h1")
        layout.addWidget(title)
        layout.addSpacing(20)
        
        # Theme Settings
        theme_group = QFrame()
        theme_group.setObjectName("card")
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl = QLabel("🎨 界面主题")
        lbl.setObjectName("h2")
        theme_layout.addWidget(lbl)
        
        self.theme_combo = QComboBox()
        for key, val in THEMES.items():
            self.theme_combo.addItem(f"{val['name']} ({key})", key)
        
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # Budget Management
        budget_group = QFrame()
        budget_group.setObjectName("card")
        budget_layout = QVBoxLayout(budget_group)
        budget_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_budget = QLabel("💰 预算设置 (月度)")
        lbl_budget.setObjectName("h2")
        budget_layout.addWidget(lbl_budget)
        
        budget_input_box = QHBoxLayout()
        self.budget_spin = QDoubleSpinBox()
        self.budget_spin.setRange(0, 1000000)
        self.budget_spin.setPrefix("¥ ")
        self.budget_spin.setValue(self.db.get_monthly_budget())
        self.budget_spin.setSingleStep(100)
        
        btn_save_budget = QPushButton("保存预算")
        btn_save_budget.setObjectName("primaryBtn")
        btn_save_budget.clicked.connect(self.save_budget)
        
        budget_input_box.addWidget(self.budget_spin)
        budget_input_box.addWidget(btn_save_budget)
        budget_layout.addLayout(budget_input_box)
        
        layout.addWidget(budget_group)

        # Data Management
        data_group = QFrame()
        data_group.setObjectName("card")
        data_layout = QVBoxLayout(data_group)
        data_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_data = QLabel("💾 数据管理")
        lbl_data.setObjectName("h2")
        data_layout.addWidget(lbl_data)
        
        btn_export = QPushButton("📉 导出数据到 Excel")
        btn_export.clicked.connect(self.export_data)
        data_layout.addWidget(btn_export)
        
        btn_backup = QPushButton("📦 备份数据库")
        btn_backup.clicked.connect(self.backup_data)
        data_layout.addWidget(btn_backup)
        
        layout.addWidget(data_group)
        
        return page

    def save_budget(self):
        """保存预算"""
        val = self.budget_spin.value()
        if self.db.set_monthly_budget(val):
            show_toast(self, f"月度预算已更新为: ¥{val:,.2f}", type="success")
            # 刷新仪表盘以显示新的预算状态
            self.page_dashboard.refresh(animate=False)
        else:
            show_toast(self, "保存失败", type="error")

    def switch_page(self, index):
        """切换页面"""
        # 使用自定义的滑动切换
        self.stack.slideInIdx(index)
        
        # 刷新数据
        if index == 0:
            self.page_dashboard.refresh()
        elif index == 2:
            self.record_list.refresh()

    def start_clock(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        now = get_beijing_time()
        self.sidebar.time_label.setText(format_datetime(now, "%H:%M:%S\n%Y-%m-%d"))

    def on_income_added(self):
        """添加收入后的回调"""
        show_toast(self, "记录已添加！", type="success")
        self.sidebar.btn_group.button(0).click() # 返回仪表盘

    def on_theme_changed(self, text):
        """切换主题"""
        theme_key = self.theme_combo.currentData()
        self.change_theme(theme_key)
        
    def change_theme(self, theme_key):
        """执行换肤"""
        ThemeManager.apply_theme(QApplication.instance(), theme_key)
        show_toast(self, f"已切换主题: {THEMES[theme_key]['name']}")
        
        # 尝试刷新图表颜色 (需要重建图表或重新设置颜色，这里简单重绘)
        # 实际开发中应该让 Chart 组件监听主题变化
        self.page_dashboard.refresh(animate=False)

    def export_data(self):
        """导出包装 (异步)"""
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "导出Excel", f"Income_{get_beijing_time().strftime('%Y%m%d')}.xlsx", "Excel(*.xlsx)")
        
        if not path:
            return

        # 禁用按钮防止重复点击
        sender = self.sender()
        if sender: sender.setEnabled(False)
        show_toast(self, "正在导出...", duration=2000)

        def do_export():
            return self.db.export_to_excel(path)
            
        worker = Worker(do_export)
        worker.signals.result.connect(lambda success: self.on_export_finished(success, sender))
        QThreadPool.globalInstance().start(worker)

    def on_export_finished(self, success, btn):
        if btn: btn.setEnabled(True)
        if success:
            show_toast(self, "导出成功", type="success")
        else:
            show_toast(self, "导出失败 (请检查是否安装了 pandas/openpyxl)", type="error")

    def backup_data(self):
        """数据备份 (异步)"""
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "备份DB", f"Backup_{get_beijing_time().strftime('%Y%m%d')}.db", "DB(*.db)")
        
        if not path:
            return
            
        show_toast(self, "正在备份...", duration=2000)
        
        def do_backup():
            return self.db.backup_db(path)
            
        worker = Worker(do_backup)
        worker.signals.result.connect(lambda s: show_toast(self, "备份成功" if s else "备份失败", type="success" if s else "error"))
        QThreadPool.globalInstance().start(worker)
