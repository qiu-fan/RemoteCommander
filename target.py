import socket
import pyautogui
import psutil
from threading import Thread
import os
import io
from PIL import Image
from tkinter import messagebox
import shutil
import time
import subprocess

# 配置信息
HOST = '0.0.0.0'
TCP_PORT = 9999
UDP_PORT = 9998
VERSION = "7.0.1"
SAFE_PROCESS = {"system", "svchost.exe", "bash", "csrss.exe", "System"}
DOWNLOAD_DIR = "D:\\dol"
SAFE_PATHS = ["C:\\Windows", "C:\\Program Files"]  # 受保护路径

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
        if target.lower() in SAFE_PROCESS:
            return f"禁止操作系统关键进程: {target}"

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
        return "权限不足"
    except Exception as e:
        return f"操作失败: {str(e)}"


def handle_connection(conn, addr):
    """ 处理TCP连接请求 """
    try:
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
                        ack = conn.recv(10).strip().decode("utf-8")  # 扩大接收缓冲区
                        if ack == "SCREEN:STOP":
                            img_data = None
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
                text = data[9:]
                try:
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

                    if keys:
                        pyautogui.hotkey(*keys)

                    conn.sendall("[OK] 输入执行成功".encode('utf-8'))
                except Exception as e:
                    return f"[ERROR] {str(e)}"
                continue

            # 文件传输协议
            if data.startswith("FILE:"):
                _, action, *args = data.split(':')
                if action == "RECEIVE":
                    filename, filesize = args
                    filesize = int(filesize)
                    filepath = os.path.join(DOWNLOAD_DIR, filename)
                    conn.sendall("[OK] 准备接收文件".encode('utf-8'))
                    with open(filepath, 'wb') as f:
                        remaining = filesize
                        while remaining > 0:
                            chunk = conn.recv(min(4096, remaining))
                            if not chunk:
                                break
                            f.write(chunk)
                            remaining -= len(chunk)
                    conn.sendall("[OK] 文件接收完成".encode('utf-8'))
                continue

            # 进程管理协议
            if data.startswith("PROC:"):
                parts = data.split(':', 3)
                if len(parts) < 3:
                    conn.sendall("协议格式错误".encode('utf-8'))
                    continue

                action = parts[1]
                if action == "LIST":
                    keyword = parts[2] if parts[2] else None
                    try:
                        page = int(parts[3]) if len(parts) > 3 else 1
                    except:
                        page = 1

                    result = list_processes(keyword, page)
                    response = f"PAGE:{result['page']}|TOTAL:{result['total']}|DATA:" + \
                               "\n".join(f"{p['pid']}|{p['name']}|{p['user']}|{p['cpu']}%|{p['memory']}MB"
                                         for p in result['data'])
                    conn.sendall(response.encode('utf-8'))
                elif action == "KILL":
                    target = parts[2] if len(parts) > 2 else ""
                    result = kill_process(target)
                    conn.sendall(f"KILL_RESULT:{result}".encode('utf-8'))
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

                    # 安全检查
                    if any(p in SAFE_PATHS for p in [source, target]):
                        conn.sendall("[ERROR] 禁止操作系统目录".encode('utf-8'))
                        continue

                    if not os.path.exists(source):
                        conn.sendall("[ERROR] 源路径不存在".encode('utf-8'))
                        continue

                    # 创建目标目录
                    target_dir = os.path.dirname(target)
                    os.makedirs(target_dir, exist_ok=True)

                    # 执行移动操作
                    shutil.move(source, target)

                    # 验证结果
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
                _, *args = data.split(':')
                try:
                    pyautogui.typewrite(args[0])
                    conn.sendall("[OK] 键盘已输入".encode('utf-8'))
                except Exception as e:
                    conn.sendall(f"[ERROR] {str(e)}".encode('utf-8'))
                continue
            # 未知指令
            conn.sendall("[ERROR] 未知指令".encode('utf-8'))




    except Exception as e:
        print(f"处理连接异常: {str(e)}")
    finally:
        conn.close()


def target_main():
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


if __name__ == "__main__":
    pyautogui.FAILSAFE = False
    print("[OK] 启动控制端")
    target_main()
