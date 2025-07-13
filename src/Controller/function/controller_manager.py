import socket
import threading
import time
import pyautogui

class ControllerManager:
    def __init__(self, log_callback, update_ui_callback):
        self.log = log_callback
        self.update_ui = update_ui_callback
        self.TCP_PORT = 9999
        self.UDP_PORT = 9998
        self.connected = False
        self.sock = None
        
    # 网络扫描
    def scan_targets(self):
        targets = {}
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(2)
            try:
                s.sendto(b"DISCOVER", ('<broadcast>', self.UDP_PORT))
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
        
        self.update_ui(targets)

    # 连接管理
    def connect_target(self, ip, version_check, VERSION):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((ip, self.TCP_PORT))

            # 版本校验
            self.sock.send(b"/version")
            version = self.sock.recv(1024).decode()

            if version_check:
                if version != VERSION:
                    self.log(f"版本校验失败")
                    return False

            self.log("通过版本校验")
            self.connected = True
            self.log(f"成功连接到 {ip}")
            return True
        except Exception as e:
            self.log(f"连接失败: {str(e)}")
            return False
            
    def disconnect(self):
        if self.sock:
            self.sock.close()
        self.connected = False
        self.log("已断开连接")
        return True
        
    # 命令发送
    def send_command(self, command):
        if not self.connected:
            return False
            
        try:
            protocol = f"CMD:{command}".encode('utf-8')
            self.sock.sendall(protocol)
            self.log(f"已发送命令: {command}")
            return True
        except Exception as e:
            self.log(f"命令发送失败: {str(e)}")
            return False
            
    # 获取鼠标位置
    def get_mouse_position(self):
        return pyautogui.position()