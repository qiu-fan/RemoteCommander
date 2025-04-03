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
import traceback


# ================= 增强配置管理 =================
class ProtectionConfig:
    PROCESS_NAME = r"C:/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
    CHECK_INTERVAL = random.randint(8, 15)  # 更动态的检查间隔
    OBF_KEY = random.SystemRandom().randint(0x01, 0xFFFF)  # 扩大密钥范围
    DEBUG_MODE = False  # 生产环境应关闭
    MUTEX_NAME = hashlib.sha256(os.urandom(32)).hexdigest()[:32]  # 随机互斥体名称
    DECOY_PROCESSES = ["svchost.exe", "explorer.exe"]  # 伪装进程白名单

# ================= 核心功能模块 =================
class StringObfuscator:
    def __init__(self):
        self.key = ProtectionConfig.OBF_KEY
    
    def encrypt(self, s):
        return bytes([ord(c) ^ self.key for c in s]).decode('latin-1')
    
    def decrypt(self, s):
        return bytes([ord(c) ^ self.key for c in s]).decode('utf-8')

class AntiDebugger:
    @staticmethod
    def check_debuggers():
        """综合反调试检测"""
        checks = [
            ctypes.windll.kernel32.IsDebuggerPresent(),
            psutil.Process().parent().name().lower() in ['ollydbg.exe', 'idaq.exe'],
            ctypes.windll.kernel32.CheckRemoteDebuggerPresent(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(ctypes.c_bool()))
        ]
        if any(checks):
            sys.exit(random.randint(100, 200))
    
    @staticmethod
    def time_drift_check(threshold=2):
        """时间差反调试"""
        start = time.perf_counter()
        [x**x for x in range(1000)]
        elapsed = time.perf_counter() - start
        if elapsed > threshold:
            sys.exit(0xDEAD)

class AdvancedObfuscator(StringObfuscator):
    def __init__(self):
        super().__init__()
        self.dynamic_key = (int(time.time()) & 0xFF) ^ self.key
    
    def polymorphic_encrypt(self, s):
        return bytes([
            (ord(c) + random.randint(0,255)) % 256 ^ self.dynamic_key 
            for c in s
        ]).decode('latin-1')
    
    def code_flow_obfuscation(self):
        """控制流混淆"""
        junk_ops = [
            lambda: hashlib.sha256(os.urandom(256)).hexdigest(),
            lambda: ctypes.windll.user32.MessageBoxW(0, "", "", 0) if random.random() < 0.1 else None,
            lambda: [winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Junk{random.randint(1,100)}") for _ in range(3)]
        ]
        random.choice(junk_ops)()

class HookDetector:
    @staticmethod
    def check_hooks():
        critical_apis = {
            "CreateProcessW": "kernel32.dll",
            "WriteProcessMemory": "kernel32.dll",
            "LoadLibraryA": "kernel32.dll"
        }
        for func, dll in critical_apis.items():
            module = ctypes.windll.kernel32.GetModuleHandleW(dll)
            addr = ctypes.windll.kernel32.GetProcAddress(module, func)
            if ctypes.c_ubyte.from_address(addr).value == 0xE9:  # JMP指令检测
                ctypes.windll.kernel32.TerminateProcess(-1, 0)

def create_mutex():
    """创建互斥体防止多实例"""
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, ProtectionConfig.MUTEX_NAME)
    if ctypes.GetLastError() == 183:
        sys.exit()

def require_admin():
    """增强权限请求逻辑"""
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            if ProtectionConfig.DEBUG_MODE:
                print("[INFO] 尝试以管理员权限运行...")
                result = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1
                )
                if result <= 32:  # ShellExecute失败代码判断
                    return False
            return False  # 当前实例仍为非管理员
        return True
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
    vm_indicators = [
        any(x in (os.getenv("PROCESSOR_IDENTIFIER") or "").upper() 
            for x in ["VIRTUAL", "VMWARE", "KVM"]),
        psutil.virtual_memory().total < 2*1024**3,
        len(psutil.net_connections()) < 3
    ]
    if any(vm_indicators):
        sys.exit(random.randint(1000, 9999))
    """增强型反沙箱检测"""
    vm_indicators = [
        any(x in (os.getenv("PROCESSOR_IDENTIFIER") or "").upper() 
            for x in ["VIRTUAL", "VMWARE", "KVM"]),
        psutil.virtual_memory().total < 2*1024**3,
        len(psutil.net_connections()) < 3
    ]
    if any(vm_indicators):
        sys.exit(random.randint(1000, 9999))

def inject_guardian():
    """增强进程守护"""
    def guardian():
        try:
            # 前置路径校验
            if not os.path.exists(ProtectionConfig.PROCESS_NAME):
                raise FileNotFoundError(f"目标程序不存在: {ProtectionConfig.PROCESS_NAME}")
                
            max_retries = 5
            while max_retries > 0:
                try:
                    target_procs = [p for p in psutil.process_iter(['name']) 
                                if p.info['name'] == os.path.basename(ProtectionConfig.PROCESS_NAME)]
                    
                    if not target_procs:
                        startup_info = subprocess.STARTUPINFO()
                        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        subprocess.Popen(
                            [sys.executable, ProtectionConfig.PROCESS_NAME],
                            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
                            startupinfo=startup_info
                        )
                        max_retries = max(5, max_retries*2)  # 动态调整重试次数
                    else:
                        # 监控进程状态
                        for p in target_procs:
                            if p.status() == psutil.STATUS_ZOMBIE:
                                p.terminate()
                    
                except Exception as e:
                    max_retries -= 1
                    if max_retries <= 0:
                        break
                    time.sleep(random.uniform(1, 3))
                
                time.sleep(ProtectionConfig.CHECK_INTERVAL + random.randint(-3,3))  # 随机间隔
        except Exception as e:
            if ProtectionConfig.DEBUG_MODE:
                print(f"[守护进程] {str(e)}")
            sys.exit(1)
    t = Thread(target=guardian, daemon=True)
    t.start()

def protect_memory():
    """安全内存保护"""
    try:
        # 使用有效内存缓冲区替代危险操作
        buf = (ctypes.c_byte * 1024)()
        ctypes.windll.kernel32.VirtualProtect(
            ctypes.byref(buf),
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
    try:
        #create_mutex()
        #is_admin = require_admin()
        #anti_sandbox()
        #AntiDebugger.check_debuggers()
        #HookDetector.check_hooks()
        #hide_console()
        inject_guardian()  # 启用进程守护
        #protect_memory()
    except Exception as e:
        # 异常日志记录
        with open("crash.log", "a") as f:
            f.write(f"[{time.ctime()}] CRASH: {str(e)}\n")
        raise

if __name__ == "__main__":
    # 调试模式配置
    if ProtectionConfig.DEBUG_MODE:
        ProtectionConfig.CHECK_INTERVAL = 60  # 延长检测间隔
        
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
    
    with open("crash.log", "a") as f:
            f.write(f"{time.ctime()} 崩溃原因:\n{traceback.format_exc()}\n")
            os.system("pause") # 保持窗口查看错误
    
