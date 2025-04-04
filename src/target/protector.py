import os
import time
import psutil
import subprocess
from threading import Thread

class ProcessGuardian:
    def __init__(self, target_paths=None):
        """
        进程守护库
        :param target_paths: 要守护的进程路径字典 
           示例：{"C:/path/to/exe1.exe": True, "C:/path/to/exe2.exe": False}
        """
        self.running = False
        self.check_interval = 15
        self.thread = None
        self.targets = target_paths or {}

    def start(self):
        """启动守护线程"""
        if not self.running:
            self.running = True
            self.thread = Thread(target=self._guard_loop)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        """停止守护线程"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def add_process(self, exe_path, enabled=True):
        """添加要守护的进程"""
        self.targets[exe_path] = enabled

    def remove_process(self, exe_path):
        """移除守护进程"""
        if exe_path in self.targets:
            del self.targets[exe_path]

    def _guard_loop(self):
        """守护主循环"""
        while self.running:
            for exe_path, enabled in self.targets.items():
                if enabled and not self._is_process_running(exe_path):
                    self._start_process(exe_path)
            time.sleep(self.check_interval)

    def _is_process_running(self, exe_path):
        """检查进程是否在运行"""
        exe_name = os.path.basename(exe_path).lower()
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                if proc.info['name'].lower() == exe_name or \
                   proc.info['exe'] and proc.info['exe'].lower() == exe_path.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def _start_process(self, exe_path):
        """静默启动进程"""
        try:
            subprocess.Popen(exe_path)
            return True
        except Exception:
            return False