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

connected = False
current_ip = None
sock = None
targets = {}
active_module = "home"
log_history = []

# 初始化Eel
eel.init(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'function'))
# expose_methods()

    # ==== 核心网络功能 ====
@eel.expose
def start_scan():
    """启动网络扫描"""
    append_log("开始扫描网络...")
    threading.Thread(target=scan_targets).start()

def scan_targets():
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
            append_log(f"扫描错误: {str(e)}")

    targets = targets
    append_log(f"扫描完成，找到 {len(targets)} 个目标")
    eel.updateTargetList(json.dumps(targets))
    return json.dumps(targets)

@eel.expose
def toggle_connection(ip=None):
        """切换连接状态"""
        global current_ip
        if not connected:
            if ip:
                current_ip = ip
                threading.Thread(target=connect_target).start()
            else:
                append_log("请先选择目标设备")
        else:
            disconnect()

@eel.expose
def connect_target():
    """建立TCP连接"""
    global connected, sock
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((current_ip, TCP_PORT))

        # 版本校验
        version = get_remote_version()
        if version != VERSION:
            append_log("版本校验失败")
            eel.show_error("错误", f"版本不匹配 (目标机:{version} -- 控制端:{VERSION})")
            return

        connected = True
        append_log(f"成功连接到 {current_ip}")
        eel.updateConnectionStatus(True, current_ip)
    except Exception as e:
            append_log(f"连接失败: {str(e)}")

@eel.expose
def get_remote_version():
    """获取远程版本"""
    sock.send(b"/version")
    return sock.recv(1024).decode()

@eel.expose
def disconnect():
    """断开连接"""
    global connected, sock
    if sock:
        sock.close()
    connected = False
    eel.updateConnectionStatus(False)
    append_log("已断开连接")

# ==== 功能模块 ====
@eel.expose
def load_module(module_name):
    """加载功能模块"""
    active_module = module_name
    eel.update_nav_status(module_name)

def show_process_manager():
    """进程管理"""
    if connected:
        eel.show_module('process_manager')
        # 这里可以添加获取进程列表的逻辑

def show_hardware_control():
    """硬件控制"""
    if connected:
        eel.show_module('hardware_control')

def show_send_message():
    """发送消息"""
    if connected:
        eel.show_module('send_message')

def show_file_manager():
    """文件管理"""
    if connected:
        eel.show_module('file_manager')
        # 这里可以添加获取文件列表的逻辑

# ==== 命令执行 ==== #
@eel.expose
def send_command(command):
    global stop_receive
    if not command:
        return
    append_log(f"发送命令:{command}")

    protocol = f"CMD:{command}"
    try:
        sock.sendall(protocol.encode('utf-8'))
        # 启动接收线程
        stop_receive = False
        receive_thread = threading.Thread(target=receive_output)
        receive_thread.start()
    except Exception as e:
        eel.append_output(f"[ERROR] {str(e)}\n")
    finally:
        pass

# 独立接收线程函数
def receive_output():
        """ 新増：独立线程接收输出 """
        global stop_receive
        buffer = b""
        while not stop_receive:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break

                # 分离结束标记
                if b"[END]\n" in chunk:
                    data_part = chunk.split(b"[END]\n", 1)
                    buffer += data_part
                    if buffer:
                        eel.append_output(buffer.decode('gbk', errors='replace'))
                    break
                else:
                    buffer += chunk
                    # 实时显示当前数据
                    eel.append_output(buffer.decode('gbk', errors='replace'))
                    buffer = b""
            except BlockingIOError:
                time.sleep(0.1)
            except Exception as e:
                eel.append_output(f"[ERROR] {str(e)}\n")
                break
# ==== 命令执行 ==== #


def show_screen_view():
    """实时屏幕"""
    if connected:
        eel.show_module('screen_view')

 # ==== 工具方法 ====
@eel.expose
def append_log(message):
    """追加日志"""
    timestamp = time.strftime("[%H%M%S]", time.localtime())
    full_msg = f"{timestamp}|{message}"
    log_history.append(full_msg)
    print(full_msg)

@eel.expose
def get_status():
    """获取连接状态"""
    return {
        'connected': connected,
        'current_ip': current_ip,
        'version': VERSION
    }
    
@eel.expose
def get_version():
    """获取当前版本"""
    return VERSION

if __name__ == "__main__":
    # 启动Eel应用
    eel.start('index.html',mode='edge')
