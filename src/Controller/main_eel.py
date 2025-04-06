import socket
import threading
import time
import json
import eel
from tkinter import messagebox
import pyautogui
from animate import animate
import os

TCP_PORT = 9999
UDP_PORT = 9998
VERSION = "7.0.6"

class RemoteCommander:
    def __init__(self):
        self.connected = False
        self.current_ip = None
        self.sock = None
        self.targets = {}
        
        
        eel.init(os.path.join(os.path.dirname(os.path.abspath(__file__))))

    def expose_methods(self):
        """暴露接口给前端"""
        eel.expose(self.get_status)
        eel.expose(self.get_version)
        eel.expose(self.append_log)

    # ==== 核心功能 ====
    def start_scan(self):
        """启动网络扫描"""
        self.append_log("开始扫描网络...")
        threading.Thread(target=self.scan_targets).start()

    def scan_targets(self):
        """执行网络扫描"""
        targets = {}
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(2)
            try:
                s.sendto(b"DISCOVER", ('<broadcast>', UDP_PORT))
                start_time = time.time()

                while time.time() - start_time <= 10:
                    try:
                        data, addr = s.recvfrom(1024)
                        ver, hostname = data.decode().split('|')
                        targets[addr[0]] = {
                            'hostname': hostname,
                            'version': ver
                        }
                    except socket.timeout:
                        break
            except Exception as e:
                self.append_log(f"扫描错误: {str(e)}")

        self.targets = targets
        eel.update_target_list(json.dumps(targets))  # 推送目标列表到前端
        self.append_log(f"扫描完成，找到 {len(targets)} 个目标")

    def toggle_connection(self, ip):
        """切换连接状态"""
        if not self.connected:
            self.current_ip = ip
            threading.Thread(target=self.connect_target).start()
        else:
            self.disconnect()

    def connect_target(self):
        """建立TCP连接"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.current_ip, TCP_PORT))

            # 版本校验
            version = self.get_remote_version()
            if version != VERSION:
                self.append_log("版本校验失败")
                eel.show_error("错误", f"版本不匹配 (目标机:{version} -- 控制端:{VERSION})")
                return

            self.connected = True
            self.append_log(f"成功连接到 {self.current_ip}")
            eel.update_connection_status(True, self.current_ip)
        except Exception as e:
            self.append_log(f"连接失败: {str(e)}")

    def get_remote_version(self):
        """获取远程版本"""
        self.sock.send(b"/version")
        return self.sock.recv(1024).decode()

    def disconnect(self):
        """断开连接"""
        if self.sock:
            self.sock.close()
        self.connected = False
        eel.update_connection_status(False)
        self.append_log("已断开连接")

    # ==== 工具方法 ====
    def append_log(self, message):
        """追加日志"""
        timestamp = time.strftime("[%H%M%S]", time.localtime())
        eel.append_log(f"{timestamp}|{message}")

    def get_status(self):
        """获取连接状态"""
        return "已连接" if self.connected else "未连接"

    def get_version(self):
        """获取当前版本"""
        return VERSION

    # ==== 功能模块 ====
    def show_process_manager(self):
        if self.connected:
            # 进程管理逻辑
            pass

    # 其他功能模块类似...

if __name__ == "__main__":
    commander = RemoteCommander()
    
    # 暴露Python函数给JavaScript
    eel.expose(commander.start_scan)
    eel.expose(commander.toggle_connection)
    
    # 启动Eel应用
    eel.start(
        f'function\\index.html',
        mode='edge',
        port=8080,
        size=(1000, 700),
        position=(100, 100),
        disable_cache=True
        )