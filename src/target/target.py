import socket
import pyautogui
import io
from tkinter import messagebox
import shutil
import time
import subprocess
from threading import Thread
import os
import psutil
import traceback
import sys
import requests
import zipfile
from bs4 import BeautifulSoup
import json
import re
import hashlib

# 配置信息
HOST = '0.0.0.0'
TCP_PORT = 9999
UDP_PORT = 9998
VERSION = "9.0.0"

DOWNLOAD_DIR = "D:\\dol"
CHUNK_SIZE = 8192  # 新增分块大小配置

# 版本更新地址
GITHUB_API = "https://api.github.com/repos/qiu-fan/RemoteCommander/releases/latest"
CURRENT_VERSION = VERSION

# 确保下载目录存在
try:
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
except Exception as e:
    print(e)
    DOWNLOAD_DIR = "C:\\dol"

# 指令映射表
shortcutKey = {
    "/exit": (pyautogui.hotkey, ('alt', 'f4')),
    "/c-a": (pyautogui.hotkey, ('ctrl', 'a')),
    "/c-c": (pyautogui.hotkey, ('ctrl', 'c')),
    "/space": (pyautogui.press, ('space',)),
    "/enter": (pyautogui.press, ('enter',)),
    "/tab": (pyautogui.press, ('tab',)),
    "/up": (pyautogui.press, ('up',)),
    "/down": (pyautogui.press, ('down',)),
    "/left": (pyautogui.press, ('left',)),
    "/right": (pyautogui.press, ('right',)),
    "/home": (pyautogui.press, ('home',)),
    "/end": (pyautogui.press, ('end',)),
    "/pageup": (pyautogui.press, ('pageup',)),
    "/pagedown": (pyautogui.press, ('pagedown',)),
    "/insert": (pyautogui.press, ('insert',)),
    "/delete": (pyautogui.press, ('delete',)),
}

def check_update():
    """检查更新"""
    try:
        headers = {'Accept': 'application/vnd.github.v3+json'}
        with requests.Session() as session:
            response = session.get(GITHUB_API, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                latest_version = data['tag_name'].lstrip('v')
                return latest_version
            return None
    except Exception:
        return None

def download_and_update(latest_version):
    """下载并更新"""
    try:
        temp_dir = os.path.join(DOWNLOAD_DIR, f"update_temp_{latest_version}")
        os.makedirs(temp_dir, exist_ok=True)

        with requests.Session() as session:
            response = session.get(GITHUB_API, timeout=15)
            if response.status_code != 200:
                return False

            release_data = response.json()
            if not release_data.get('assets'):
                return False

            download_url = release_data['assets'][0]['browser_download_url']
            zip_path = os.path.join(temp_dir, f"update_{latest_version}.zip")

            print(f"[Info] 正在下载更新: {download_url}到 {zip_path}")
            # 使用流式下载避免内存占用过大

            with session.get(download_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            current_dir = os.path.dirname(os.path.abspath(__file__))
            for item in os.listdir(temp_dir):
                s = os.path.join(temp_dir, item)
                d = os.path.join(current_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

            shutil.rmtree(temp_dir)
            create_cleanup_script()
            return True
    except Exception:
        return False

def create_cleanup_script():
    """创建清理脚本"""
    current_path = os.path.abspath(__file__)
    script_content = f"""
@echo off
setlocal
:: 等待3秒确保文件释放
timeout /t 3 /nobreak >nul
:: 使用PowerShell进行强制删除
powershell.exe -Command "Try {{
    Remove-Item '{current_path}' -Force -Recurse
    Remove-Item '%~f0' -Force
    Start-Process '{sys.executable}' '{current_path}'
}} Catch {{}}"
"""
    with open("cleanup.bat", "w") as f:
        f.write(script_content)

def udp_broadcast_listener():
    """ UDP广播响应服务 """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('', UDP_PORT))
        while True:
            data, addr = s.recvfrom(1024)
            if data.decode() == "DISCOVER":
                response = f"{VERSION}|{socket.gethostname()}".encode('utf-8')
                s.sendto(response, addr)


def list_processes(filter_keyword=None, page=1, page_size=20):
    """ 获取进程列表，支持分页和过滤 """
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info']):
        try:
            p_info = proc.info
            process_data = {
                'pid': p_info['pid'],
                'name': p_info['name'],
                'user': p_info['username'],
                'cpu': round(p_info['cpu_percent'], 1),
                'memory': round(p_info['memory_info'].rss / (1024 * 1024), 1)
            }
            if not filter_keyword or filter_keyword.lower() in process_data['name'].lower():
                processes.append(process_data)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # 分页处理
    total = len(processes)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        'total': total,
        'page': page,
        'data': processes[start:end]
    }


def kill_process(target):
    """ 终止指定进程 """
    try:
        if not target:
            return "需要指定进程名或PID"

        target = target.strip()

        # 保护进程太安全不想要
        # if target.lower() in SAFE_PROCESS:
        #     return f"禁止操作系统关键进程: {target}"

        if target.isdigit():
            pid = int(target)
            p = psutil.Process(pid)
            p.terminate()
            return f"已终止PID: {pid}"
        else:
            count = 0
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == target.lower():
                    try:
                        proc.terminate()
                        count += 1
                    except Exception:
                        continue
            return f"已终止 {count} 个 {target} 进程" if count else "未找到匹配进程"
    except psutil.NoSuchProcess:
        return "进程不存在"
    except psutil.AccessDenied:
        # noinspection PyUnboundLocalVariable
        process = subprocess.Popen(
                        f"taskkill /F /pid {pid}",
                        shell=True,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        bufsize=1,
                        encoding='gbk',
                        errors='replace'
                    )
        return f"权限不足\n已尝试使用taskkill清除:\n{process.stdout.read()}"
    except Exception as e:
        return f"操作失败: {str(e)}"
    
def get_valid_drives():
    """安全获取可用磁盘列表"""
    try:
        from ctypes import windll
        drives = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if bitmask & 1:
                drives.append(f"{letter}:\\")
            bitmask >>= 1
        return [d for d in drives if os.path.exists(d)]
    except Exception as e:
        print(f"获取磁盘列表失败: {str(e)}")
        return []

# noinspection PyUnusedLocal
def handle_connection(conn: socket.socket, addr):
    conn.settimeout(60)

    try:
        """
        想加一个INFO指令获取一堆信息，在A显示更多关于B的信息
        看到加上
        """

        # 主循环
        while True:
            data = conn.recv(1024).decode('utf-8').strip()
            print(data)
            if not data:
                break

            # 版本检查
            if data == "/version":
                conn.sendall(VERSION.encode('utf-8'))
                continue

            # 屏幕传输协议
            if data == "SCREEN:START":
                conn.sendall("[OK] 开始屏幕传输".encode('utf-8'))
                while True:
                    try:
                        # 捕获屏幕并压缩为JPEG
                        img = pyautogui.screenshot()
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='JPEG', quality=30)  # 调整quality控制画质
                        img_data = img_byte_arr.getvalue()

                        # 发送数据长度（4字节）和数据内容
                        conn.sendall(len(img_data).to_bytes(4, 'big'))
                        conn.sendall(img_data)
                        # 接收控制端信号（支持STOP指令）
                        ack = conn.recv(1024).strip().decode("utf-8")  # 扩大接收缓冲区
                        print(ack)
                        if ack == "SCREEN:STOP":
                            img_data = b''
                            break
                        elif ack != "GO":
                            break

                    except:
                        break
                    continue

            # 处理CMD命令
            if data.startswith("CMD:"):
                command = data[4:]
                try:
                    process = subprocess.Popen(
                        command,
                        shell=True,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        bufsize=1,
                        encoding='gbk',
                        errors='replace'
                    )
                    start_time = time.time()
                    timeout = 15

                    while True:
                        # 检查总超时
                        if time.time() - start_time > timeout:
                            process.kill()
                            conn.sendall("\n错误：命令执行超时".encode('gbk') + b"[END]\n")
                            break

                        # 读取一行输出并实时发送（强制刷新缓冲区）
                        line = process.stdout.readline()
                        if line:
                            conn.sendall(line.encode('gbk'))
                            conn.sendall(b"")  # 强制刷新网络缓冲区
                        else:
                            # 检查进程是否结束
                            if process.poll() is not None:
                                conn.sendall(b"[END]\n")
                                break
                            time.sleep(0.05)
                except Exception as e:
                    conn.sendall(f"错误：{str(e)}".encode('gbk') + b"[END]\n")
                continue

            # 处理键盘输入
            if data.startswith("KEYBOARD:"):
                parts = data.split(':', 2)
                if len(parts) < 3:
                    # 支持直接发送特殊键格式如"KEYBOARD:{enter}"
                    if data.endswith('}') and '{' in data:
                        key_part = data[data.find('{')+1:data.rfind('}')]
                        parts = [parts[0], key_part, ""]
                    else:
                        conn.sendall("[ERROR] 键盘协议格式错误".encode('utf-8'))
                        continue
                try:
                    text = parts[2]
                    keys = []
                    current_key = []
                    in_special = False

                    for char in text:
                        if char == '{':
                            in_special = True
                            current_key = []
                        elif char == '}' and in_special:
                            in_special = False
                            key_name = ''.join(current_key).lower()
                            keys.append(key_name)
                        elif in_special:
                            current_key.append(char)
                        else:
                            pyautogui.write(char)

                    # 支持连续按键操作
                    for key in keys:
                        pyautogui.press(key)

                    conn.sendall("[OK] 输入执行成功".encode('utf-8'))
                except Exception as e:
                    conn.sendall(f"[ERROR] {str(e)}".encode('utf-8'))
                continue

            # 文件管理协议
            if data.startswith("FILE:"):
                parts = data.split(':', 3)
                action = parts[1]
                if action == "LIST":
                    path = parts[2] if len(parts) >= 3 else "/"
                    path = path.replace("/", os.sep)
                    if re.match(r"^[A-Za-z]:\\$", path):
                        path = path[:-1] + "\\"
                    files = []
                    try:
                        for item in os.listdir(path):
                            full_path = os.path.join(path, item)
                            ftype = "文件夹" if os.path.isdir(full_path) else "文件"
                            try:
                                mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(full_path)))
                            except:
                                mtime = "未知时间"
                            size = os.path.getsize(full_path) if ftype == "文件" else 0
                            files.append(f"{item}|{ftype}|{size}|{mtime}")
                        conn.sendall(("\n".join(files)).encode('utf-8'))
                    except Exception as e:
                        conn.sendall(f"[ERROR] {str(e)}".encode('utf-8'))



                elif action == "DOWNLOAD":
                    filepath = ':'.join(parts[2:])  # 合并路径部分
                    filepath = filepath.replace("/", os.sep)
                    if not os.path.exists(filepath) or not os.path.isfile(filepath):
                        conn.sendall("[ERROR] 文件不存在".encode('utf-8'))
                        continue

                    try:
                        with open(filepath, "rb") as f:
                            file_data = f.read()

                        conn.sendall(f"{len(file_data)}".encode('utf-8'))
                        response = conn.recv(1024).decode('utf-8')
                        # if response == "[OK] 准备接收文件":
                        conn.sendall(file_data)
                            
                    except Exception as e:
                        conn.sendall(f"[ERROR] {str(e)}".encode('utf-8'))

                elif action == "UPLOAD":

                    if len(parts) < 4:  # 确保协议包含足够参数

                        conn.sendall("[ERROR] 上传协议格式错误".encode('utf-8'))

                        continue

                    filename = parts[2]

                    try:

                        filesize = int(parts[3])

                    except ValueError:

                        conn.sendall("[ERROR] 文件大小格式错误".encode('utf-8'))

                        continue

                    # 确保下载目录存在

                    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

                    filepath = os.path.join(DOWNLOAD_DIR, filename)

                    conn.sendall("[OK] 准备接收文件".encode('utf-8'))

                    try:

                        received = 0

                        with open(filepath, 'wb') as f:

                            while received < filesize:

                                chunk = conn.recv(min(4096, filesize - received))

                                if not chunk:
                                    break

                                f.write(chunk)

                                received += len(chunk)

                        if received == filesize:

                            conn.sendall(f"[OK] 文件接收完成 {filesize}字节".encode('utf-8'))

                        else:

                            conn.sendall(f"[ERROR] 文件不完整 收到{received}/{filesize}".encode('utf-8'))

                    except Exception as e:

                        conn.sendall(f"[ERROR] {str(e)}".encode('utf-8'))


                elif action == "DELETE":
                    filepath = ':'.join(parts[2:])  # 合并路径部分
                    filepath = filepath.replace("/", os.sep)
                    try:
                        os.remove(filepath)
                        conn.sendall("[OK] 文件删除成功".encode('utf-8'))
                    except Exception as e:
                        conn.sendall(f"[ERROR] \n"
                                     f"Print:\n"
                                     f"{str(e)}".encode('utf-8'))
                        
                elif action == "GET_FILE_TREE":
                    if parts[2] != ["Root"]:
                        path = ':'.join(parts[2:])  # 合并路径部分
                        path = path.replace("/", os.sep)
                    else:
                        path = "Root"
                    try:
                        if path == "Root":
                            valid_disks = []
                            for drive in get_valid_drives():  # 使用专用方法获取可用磁盘
                                try:
                                    # 验证磁盘可访问性
                                    os.listdir(drive)
                                    valid_disks.append({
                                        "name": f"磁盘 {drive[0]}",
                                        "path": drive,
                                        "isDir": True
                                    })
                                except Exception as e:
                                    conn.sendall(f"磁盘{drive}不可访问: {str(e)}".encode('utf-8'))
                                    continue
                            conn.sendall(json.dumps({"path": "Root", "children": valid_disks}).encode('utf-8'))
                            conn.sendall(b"[END]")  # 添加结束标识

                        # 添加路径规范化
                        elif path != "Root":
                            norm_path = os.path.normpath(path)
                            if not os.path.exists(norm_path):
                                conn.sendall(json.dumps({"path": path, "children": [], "error": "路径不存在"}).encode('utf-8'))
                                conn.sendall(b"[END]")  # 错误情况也添加结束标识
                            else:
                                children = []
                                for entry in os.listdir(norm_path):
                                    full_path = os.path.join(norm_path, entry)
                                    if os.path.exists(full_path):
                                        children.append({
                                            "name": entry,
                                            "path": full_path,
                                            "isDir": os.path.isdir(full_path)
                                        })
                                conn.sendall(json.dumps({"path": norm_path, "children": children}).encode('utf-8'))
                                conn.sendall(b"[END]")  # 正常情况添加结束标识
                                        
                    except Exception as e:
                        conn.sendall(json.dumps({"path": path, "children": [], "error": str(e)}).encode('utf-8'))
                        conn.sendall(b"[END]")  # 异常情况添加结束标识


                elif action == "DISK":
                    try:
                        drives = []
                        for disk in psutil.disk_partitions():
                            if disk.mountpoint:
                                drives.append(disk.mountpoint)
                        conn.sendall(("DISK|" + "|".join(drives)).encode('utf-8'))
                    except Exception as e:
                        conn.sendall(f"[ERROR] {str(e)}".encode('utf-8'))

                continue

            # 鼠标控制协议
            if data.startswith("MOUSE:"):
                _, action, *args = data.split(':')
                try:
                    x, y = map(int, args)
                    if action == "MOVE":
                        pyautogui.moveTo(x, y)
                        conn.sendall("[OK] 鼠标已移动".encode('utf-8'))
                    elif action == "CLICK":
                        pyautogui.click(x, y)
                        conn.sendall("[OK] 鼠标已点击".encode('utf-8'))
                    elif action == "MOVE_CLICK":
                        pyautogui.moveTo(x, y)
                        pyautogui.click()
                        conn.sendall("[OK] 鼠标已移动并点击".encode('utf-8'))
                    else:
                        conn.sendall("[ERROR] 无效鼠标指令".encode('utf-8'))
                except Exception as e:
                    conn.sendall(f"[ERROR] {str(e)}".encode('utf-8'))
                continue

            # 打开文件
            if data.startswith("OPENFILE:"):
                filepath = data.split(':', 1)[1]
                try:
                    if os.path.exists(filepath):
                        os.startfile(filepath)
                        conn.sendall("[OK] 文件已打开".encode('utf-8'))
                    else:
                        conn.sendall("[ERROR] 文件不存在".encode('utf-8'))
                except Exception as e:
                    conn.sendall(f"[ERROR] {str(e)}".encode('utf-8'))
                continue

            # 弹出提示
            if data.startswith("ALERT:"):
                message = data.split(':', 1)[1]
                # 使用线程避免阻塞
                Thread(target=lambda: messagebox.showinfo("提示", message)).start()
                conn.sendall("[OK] 提示已显示".encode('utf-8'))
                continue

            if data.startswith("MOVEFILE:"):
                try:
                    _, paths = data.split(':', 1)
                    source, target = paths.split('->', 1)
                    target_dir = os.path.dirname(target)
                    os.makedirs(target_dir, exist_ok=True)
                    shutil.move(source, target)
                    if os.path.exists(target):
                        conn.sendall(f"[OK] 移动完成: {target}".encode('utf-8'))
                    else:
                        conn.sendall("[ERROR] 移动操作失败".encode('utf-8'))
                except Exception as e:
                    conn.sendall(f"[ERROR] 移动失败: {str(e)}".encode('utf-8'))
                continue

            # 预设快捷键指令
            if data in shortcutKey:
                func, args = shortcutKey[data]
                try:
                    if isinstance(args, tuple):
                        func(*args)
                    else:
                        func(args)
                    conn.sendall(f"[SUCCESS] {data}".encode('utf-8'))
                except Exception as e:
                    conn.sendall(f"[ERROR] {str(e)}".encode('utf-8'))
                continue

            # 控制键盘输入字符串
            if data.startswith("KEYBOARD:"):
                parts = data.split(':', 2)
                if len(parts) < 3:
                    conn.sendall("[ERROR] 键盘协议格式错误".encode('utf-8'))
                    continue
                
                try:
                    pyautogui.typewrite(parts[2])
                    conn.sendall("[OK] 键盘已输入".encode('utf-8'))
                except Exception as e:
                    conn.sendall(f"[ERROR] {str(e)}".encode('utf-8'))
                continue

            # 未知指令
            conn.sendall("[ERROR] 未知指令".encode('utf-8'))



    except Exception as e:
        print(f"处理连接异常: {str(e)}")
        with open("crash.log", "a") as f:
            f.write(f"{time.ctime()} 崩溃原因:\n{traceback.format_exc()}\n")
        # 关闭当前连接并重新开始
        conn.close()
        return
    finally:
        # 修改递归调用方式
        # 将递归调用改为循环结构
        # 创建新的连接处理循环
        while True:
            try:
                new_data = conn.recv(1024).decode('utf-8').strip()
                if not new_data:
                    break
                # 处理新数据
                # 这里添加处理新数据的逻辑
            except:
                break
        conn.close()


def target_main():
    # 自动更新检查
    print("[Info] 正在检查更新...")
    latest_version = check_update()
    if latest_version and latest_version > VERSION:
        print(f"[Info] 检测到新版本: {latest_version}")
        if download_and_update(latest_version):
            os.system("start cleanup.bat")
            sys.exit(0)
    else:
        print("[Info] 已是最新版本或检查更新失败，云端最新版：", latest_version, "本地版本：", VERSION)

    # 启动UDP监听线程
    Thread(target=udp_broadcast_listener, daemon=True).start()

    # TCP主服务
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, TCP_PORT))
        s.listen()
        while True:
            conn, addr = s.accept()
            Thread(target=handle_connection, args=(conn, addr)).start()

# 根据得到的消息合成出路径
# def merge_path(message):
#     _, action, *args = message.split(':')
#     if len(args[0]) == 1:
#         # 把盘符和冒号连起来
#         filepath = args[0] + ":"
#         for f in args[1:]:
#             filepath += f
#         print(f"merge_path: {filepath}")
#         filepath = filepath.replace("/", os.sep)
#         return filepath
#
#     return "ERROR"

def merge_path(message):
    """根据协议消息合成路径"""
    parts = message.split(':', 3)
    if len(parts) < 3:
        return None
    
    action = parts[1]
    if action == "LIST" or action == "UPLOAD" or action == "DOWNLOAD":
        path = ':'.join(parts[2:])  # 合并路径部分
        path = path.replace("/", os.sep)
        return path

    return None





if __name__ == "__main__":
    try:
        pyautogui.FAILSAFE = False
        print("__启动控制端__")
        target_main()
    except Exception:
        traceback.print_exc()
        target_main()
