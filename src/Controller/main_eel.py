import socket
import threading
import time
import json
import eel
import os
import pyautogui
from tkinter import messagebox

TCP_PORT = 9999
UDP_PORT = 9998
VERSION = "7.0.6"

class RemoteCommander:
    def __init__(self):
        self.connected = False
        self.current_ip = None
        self.sock = None
        self.targets = {}
        self.active_module = "home"
        self.log_history = []

        # 初始化Eel
        eel.init(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'function'))
        self.expose_methods()

    def expose_methods(self):
        """暴露所有前端需要的方法"""
        eel.expose(self.get_status)
        eel.expose(self.get_version)
        eel.expose(self.append_log)
        eel.expose(self.start_scan)
        eel.expose(self.toggle_connection)
        eel.expose(self.load_module)
        
        # 功能模块
        eel.expose(self.show_process_manager)
        eel.expose(self.show_hardware_control)
        eel.expose(self.show_send_message)
        eel.expose(self.show_file_manager)
        eel.expose(self.show_cmd_control)
        eel.expose(self.show_screen_view)

    # ==== 核心网络功能 ====
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
                self.log(f"扫描错误: {str(e)}")

        self.root.after(0, self.update_target_list, targets)

        self.targets = targets
        eel.update_target_list(json.dumps(targets))
        self.append_log(f"扫描完成，找到 {len(targets)} 个目标")

    def toggle_connection(self, ip=None):
        """切换连接状态"""
        if not self.connected:
            if ip:
                self.current_ip = ip
                threading.Thread(target=self.connect_target).start()
            else:
                self.append_log("请先选择目标设备")
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

    # ==== 功能模块 ====
    def load_module(self, module_name):
        """加载功能模块"""
        self.active_module = module_name
        eel.update_nav_status(module_name)

    def show_process_manager(self):
        """进程管理"""
        if self.connected:
            eel.show_module('process_manager')
            # 这里可以添加获取进程列表的逻辑

    def show_hardware_control(self):
        """硬件控制"""
        if self.connected:
            eel.show_module('hardware_control')

    def show_send_message(self):
        """发送消息"""
        if self.connected:
            eel.show_module('send_message')

    def show_file_manager(self):
        """文件管理"""
        if self.connected:
            eel.show_module('file_manager')
            # 这里可以添加获取文件列表的逻辑

    def show_cmd_control(self):
        """CMD控制"""
        if self.connected:
            eel.show_module('cmd_control')

    def show_screen_view(self):
        """实时屏幕"""
        if self.connected:
            eel.show_module('screen_view')

    # ==== 工具方法 ====
    def append_log(self, message):
        """追加日志"""
        timestamp = time.strftime("[%H%M%S]", time.localtime())
        full_msg = f"{timestamp}|{message}"
        self.log_history.append(full_msg)
        print(full_msg)

    def get_status(self):
        """获取连接状态"""
        return {
            'connected': self.connected,
            'current_ip': self.current_ip,
            'version': VERSION
        }

    def get_version(self):
        """获取当前版本"""
        return VERSION

if __name__ == "__main__":
    commander = RemoteCommander()
    
    # 启动Eel应用
    eel.start(
        'index.html',
        mode='edge',
        port=8080,
        size=(1000, 700),
        position=(100, 100),
        disable_cache=True
    )
