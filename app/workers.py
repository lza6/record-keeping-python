"""
异步任务处理模块
用于将耗时操作移动到后台线程，确保 UI 流畅不卡顿
"""
import sys
import traceback
from PyQt6.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal

class WorkerSignals(QObject):
    """
    Worker 信号定义
    """
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QRunnable):
    """
    通用后台工作线程
    
    :param fn: 要执行的回调函数
    :param args: 传递给回调的参数
    :param kwargs: 传递给回调的关键字参数
    """
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        """
        线程执行入口
        """
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
