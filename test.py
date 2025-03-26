import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from animate import animate
import socket
import time
import threading
import pyautogui
import os
import io

TCP_PORT = 9999
UDP_PORT = 9998
VERSION = "7.0.1"


def send_message(parent, format, message, byte_len=1024, function=None, show_info=True):
    protocol = f"{format}:{message}"
    try:
        parent.sock.sendall(protocol.encode('utf-8'))
        response = parent.sock.recv(byte_len).decode()
        if show_info:
            messagebox.showinfo("结果", response)
        else:
            function(response)

    except Exception as e:
        messagebox.showerror("错误", str(e))

class RemoteCommanderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"RemoteCommander GUI v{VERSION}")
        self.setGeometry(100, 100, 1000, 700)
        
        # 初始化核心状态
        self.connected = False
        self.current_ip = None
        self.sock = None
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.settimeout(1)
        
        # 创建主界面
        self.init_ui()
        
        # 版本校验复选框
        self.version_check = QCheckBox("版本校验", self)
        self.version_check.move(10, 650)
        
        # 初始化首次扫描
        QTimer.singleShot(100, self.start_scan)

    def init_ui(self):
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # 侧边栏
        sidebar = QWidget()
        sidebar.setFixedWidth(150)
        sidebar_layout = QVBoxLayout(sidebar)
        
        # 功能按钮
        self.btn_scan = QPushButton("扫描网络")
        self.btn_scan.clicked.connect(self.start_scan)
        sidebar_layout.addWidget(self.btn_scan)
        
        buttons = [
            ("连接", self.toggle_connection),
            ("进程管理", self.show_process_manager),
            ("鼠标控制", self.show_mouse_control),
            ("键盘输入", self.show_keyboard_input),
            ("文件管理", self.show_file_manager),
            ("CMD控制", self.show_cmd_control),
            ("屏幕查看", self.show_screen_view),
            ("消息通知", self.show_message_dialog),
            ("快捷键", self.show_shortcut_manager)
        ]
        
        for text, handler in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #d9d9d9;
                    border: none;
                    padding: 8px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #0ce0eb;
                }
                QPushButton:disabled {
                    background-color: #aaaaaa;
                    color: #666666;
                }
            """)
            btn.setEnabled(False) if text != "扫描网络" else None
            sidebar_layout.addWidget(btn)
        
        main_layout.addWidget(sidebar)

        # 主内容区
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 目标列表
        self.target_tree = QTreeWidget()
        self.target_tree.setHeaderLabels(["IP地址", "主机名", "版本"])
        self.target_tree.setColumnWidth(0, 120)
        self.target_tree.itemDoubleClicked.connect(self.on_item_double_click)
        content_layout.addWidget(self.target_tree)
        
        # 日志区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        content_layout.addWidget(self.log_area)
        
        # 状态栏
        self.status_bar = self.statusBar()
        main_layout.addWidget(content_widget)

    # 核心功能方法
    def toggle_connection(self):
        if self.connected:
            self.disconnect()
        else:
            selected = self.target_tree.currentItem()
            if selected:
                self.connect_to_host(selected.text(0))

    def connect_to_host(self, ip):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, TCP_PORT))
            self.connected = True
            self.current_ip = ip
            self.update_ui_state()
            self.log(f"成功连接到 {ip}")
        except Exception as e:
            messagebox.showerror("连接错误", str(e))

    def disconnect(self):
        if self.sock:
            self.sock.close()
        self.connected = False
        self.current_ip = None
        self.update_ui_state()
        self.log("连接已断开")

    def update_ui_state(self):
        for btn in self.findChildren(QPushButton):
            if btn.text() != "扫描网络":
                btn.setEnabled(self.connected)

    # 功能窗口控制
    def show_process_manager(self):
        ProcessManagerWindow(self).show()

    def show_mouse_control(self):
        MouseControlWindow(self).show()

    def show_keyboard_input(self):
        EnterString(self).show()

    def show_file_manager(self):
        FileManagerWindow(self).show()

    def show_cmd_control(self):
        CMDControlWindow(self).show()

    def show_screen_view(self):
        ScreenViewWindow(self).show()

    def show_message_dialog(self):
        SendMessage(self).show()

    def show_shortcut_manager(self):
        ShortcutManagerWindow(self).show()
    
    def start_scan(self):
        """网络扫描核心方法"""
        self.log("开始扫描网络...")
        self.btn_scan.setEnabled(False)
        self.scan_thread = self.NetworkScanner()
        self.scan_thread.finished.connect(self.update_target_list)
        self.scan_thread.start()
    
    def log(self, message):
        """统一日志记录方法"""
        timestamp = QDateTime.currentDateTime().toString("[yyyy-MM-dd hh:mm:ss]")
        self.log_area.append(f"{timestamp} {message}")
        self.log_area.ensureCursorVisible()  # 自动滚动到最新内容

    def update_target_list(self, targets):
        """更新目标列表"""
        self.target_tree.clear()
        for ip, info in targets.items():
            item = QTreeWidgetItem(self.target_tree, [ip, info['hostname'], info['version']])
            item.setToolTip(0, f"最后响应: {info['response_time']}ms")
        self.btn_scan.setEnabled(True)
        self.log(f"扫描完成，发现 {len(targets)} 个在线主机")

    def on_item_double_click(self, item):
        """双击连接功能"""
        if not self.connected:
            self.connect_to_host(item.text(0))

    class NetworkScanner(QThread):
        """网络扫描线程"""
        finished = pyqtSignal(dict)
        
        def __init__(self):
            super().__init__()
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.settimeout(0.5)

        def run(self):
            """实际扫描逻辑"""
            targets = {}
            base_ip = "192.168.1."
            
            for i in range(1, 255):
                ip = base_ip + str(i)
                try:
                    start_time = time.time()
                    self.udp_socket.sendto(b"DISCOVER", (ip, UDP_PORT))
                    data, _ = self.udp_socket.recvfrom(1024)
                    response_time = round((time.time() - start_time)*1000, 2)
                    
                    if data.startswith(b"ACK"):
                        info = data.decode().split('|')
                        targets[ip] = {
                            'hostname': info[1],
                            'version': info[2],
                            'response_time': response_time
                        }
                except socket.timeout:
                    continue
                except Exception as e:
                    continue
            
            self.finished.emit(targets)


class ProcessManagerWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("进程管理")
        self.geometry("1000x400")

        self.current_page = 1
        self.filter_keyword = ""

        self.create_widgets()
        self.load_processes()

    def create_widgets(self):
        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="刷新", command=self.load_processes).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="上一页", command=self.prev_page).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="下一页", command=self.next_page).pack(side=tk.LEFT)

        self.page_label = ttk.Label(toolbar, text="第1页")
        self.page_label.pack(side=tk.LEFT, padx=10)

        self.filter_entry = ttk.Entry(toolbar)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="过滤", command=self.apply_filter).pack(side=tk.LEFT)

        # 进程列表
        columns = ("pid", "name", "user", "cpu", "memory")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("pid", text="PID")
        self.tree.heading("name", text="进程名")
        self.tree.heading("user", text="用户")
        self.tree.heading("cpu", text="CPU%")
        self.tree.heading("memory", text="内存(MB)")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 操作按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="终止进程", command=self.kill_process).pack(side=tk.LEFT)

    def load_processes(self):
        send_message(self.parent, "PROC:LIST", f"{self.filter_keyword}:{self.current_page}",
                     byte_len=4096, function=self.update_process_list, show_info=False)

    def update_process_list(self, response):
        if "|DATA:" not in response:
            messagebox.showerror("错误", "无效响应格式")
            return

        header, data = response.split("|DATA:", 1)
        params = {k: v for k, v in [p.split(':') for p in header.split('|') if ':' in p]}

        self.tree.delete(*self.tree.get_children())
        for line in data.split('\n'):
            if line.count('|') == 4:
                pid, name, user, cpu, mem = line.split('|')
                self.tree.insert("", tk.END, values=(pid, name, user, cpu, mem))

        self.page_label.config(text=f"第{params['PAGE']}页 已装载{params['TOTAL']}条")

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_processes()

    def next_page(self):
        self.current_page += 1
        self.load_processes()

    def apply_filter(self):
        self.filter_keyword = self.filter_entry.get()
        self.current_page = 1
        self.load_processes()

    def kill_process(self):
        selected = self.tree.selection()
        if selected:
            pid = self.tree.item(selected[0])['values'][0]
            send_message(self.parent, format="PROC:KILL", message=pid)


class MouseControlWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("鼠标控制")
        self.geometry("400x250")

        self.create_widgets()

    def create_widgets(self):
        # 坐标输入
        ttk.Label(self, text="X坐标:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_x = ttk.Entry(self)
        self.entry_x.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self, text="Y坐标:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_y = ttk.Entry(self)
        self.entry_y.grid(row=1, column=1, padx=5, pady=5)

        # 获取当前鼠标坐标
        ttk.Button(self, text="获取当前坐标", command=self.get_current_pos).grid(row=2, column=0, columnspan=2, pady=5)

        # 操作按钮
        ttk.Button(self, text="移动鼠标", command=lambda: self.send_mouse_command("MOVE")).grid(row=3, column=0, padx=5,
                                                                                                pady=5)
        ttk.Button(self, text="点击", command=lambda: self.send_mouse_command("CLICK")).grid(row=3, column=1, padx=5,
                                                                                             pady=5)
        ttk.Button(self, text="移动并点击", command=lambda: self.send_mouse_command("MOVE_CLICK")).grid(row=4, column=0,
                                                                                                        columnspan=2,
                                                                                                        pady=5)

    def get_current_pos(self):
        x, y = pyautogui.position()
        self.entry_x.delete(0, tk.END)
        self.entry_x.insert(0, str(x))
        self.entry_y.delete(0, tk.END)
        self.entry_y.insert(0, str(y))

    def send_mouse_command(self, action):
        try:
            x = int(self.entry_x.get())
            y = int(self.entry_y.get())
            protocol = f"MOUSE:{action}:{x}:{y}"
            response = send_message(self.parent, propagate)
            if response.startswith("[ERROR]"):
                raise Exception(response)
            self.parent.log(response)
        except Exception as e:
            messagebox.showerror("错误", str(e))


class EnterString(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("高级键盘输入")
        self.geometry("995x250")
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 输入区域
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X)

        ttk.Label(input_frame, text="输入内容:").pack(side=tk.LEFT)
        self.entry = ttk.Entry(input_frame, width=35)
        self.entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 特殊按键面板
        key_frame = ttk.LabelFrame(main_frame, text="特殊按键")
        key_frame.pack(fill=tk.X, pady=5)

        keys = [
            ("Enter", "{enter}"), ("Tab", "{tab}"), ("Space", "{space}"),
            ("↑", "{up}"), ("↓", "{down}"), ("←", "{left}"), ("→", "{right}"),
            ("Win", "{win}"), ("Alt", "{alt}"), ("Ctrl", "{ctrl}"), ("Shift", "{shift}")
        ]
        for text, symbol in keys:
            btn = ttk.Button(key_frame, text=text, width=6,
                             command=lambda s=symbol: self.insert_symbol(s))
            btn.pack(side=tk.LEFT, padx=2)

        # 功能按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="发送", command=self.send_code).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="组合键示例", command=self.show_shortcuts).pack(side=tk.RIGHT)

    def insert_symbol(self, symbol):
        self.entry.insert(tk.END, symbol)

    def send_code(self):
        text = self.entry.get()
        if not text:
            return

        send_message(self.parent, "KEYBOARD", text)

        self.parent.log(f"执行高级键盘操作成功{text}")

    def clear(self):
        self.entry.delete(0, tk.END)

    def show_shortcuts(self):
        examples = [
            "组合键示例:",
            "{ctrl}{alt}{delete} - Ctrl+Alt+Del",
            "{win}{r} - 打开运行窗口",
            "{ctrl}{shift}{esc} - 打开任务管理器"
        ]
        messagebox.showinfo("组合键帮助", "\n".join(examples))


class ShortcutManagerWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("快捷键管理")
        self.geometry("400x300")

        self.create_widgets()

    def create_widgets(self):
        # 快捷键列表
        self.tree = ttk.Treeview(self, columns=("command", "action"), show="headings")
        self.tree.heading("command", text="快捷键")
        self.tree.heading("action", text="操作")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 加载快捷键
        self.load_shortcuts()

        # 操作按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="执行", command=self.execute_shortcut).pack(side=tk.LEFT)

    def load_shortcuts(self):
        shortcuts = [
            ("/exit", "Alt + F4"),
            ("/c-a", "Ctrl + A"),
            ("/c-c", "Ctrl + C"),
            ("/space", "Space"),
            ("/enter", "Enter"),
            ("/tab", "Tab"),
            ("/up", "Up Arrow"),
            ("/down", "Down Arrow"),
            ("/left", "Left Arrow"),
            ("/right", "Right Arrow"),
            ("/home", "Home"),
            ("/end", "End"),
            ("/pageup", "Page Up"),
            ("/pagedown", "Page Down"),
            ("/insert", "Insert"),
            ("/delete", "Delete"),
        ]
        for cmd, action in shortcuts:
            self.tree.insert("", tk.END, values=(cmd, action))

    def execute_shortcut(self):
        selected = self.tree.selection()
        if selected:
            cmd = self.tree.item(selected[0])['values'][0]
            try:
                self.parent.sock.sendall(cmd.encode('utf-8'))
                response = self.parent.sock.recv(1024).decode()
                self.parent.log(f"执行快捷键: {cmd} -> {response}")
            except Exception as e:
                messagebox.showerror("错误", str(e))


class FileManagerWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("文件管理系统")
        self.geometry("825x450")  # 调整窗口尺寸

        # 创建主容器
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧操作区域
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew")

        # 右侧按钮区域
        right_frame = ttk.Frame(main_frame, width=100)
        right_frame.grid(row=0, column=1, sticky="ns", padx=10)

        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # 文件操作区域 ------------------------------------------------------
        # 打开文件分组框
        open_frame = ttk.LabelFrame(left_frame, text=" 文件操作 ")
        open_frame.pack(fill=tk.X, pady=5)

        ttk.Label(open_frame, text="打开路径：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.open_entry = ttk.Entry(open_frame, width=35)
        self.open_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(open_frame, text="浏览", command=self.select_open_file, width=6).grid(row=0, column=2)

        # 移动文件分组框
        move_frame = ttk.LabelFrame(left_frame, text=" 移动操作 ")
        move_frame.pack(fill=tk.X, pady=5)

        ttk.Label(move_frame, text="源路径：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.source_entry = ttk.Entry(move_frame, width=35)
        self.source_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(move_frame, text="浏览", command=self.select_source_file, width=6).grid(row=0, column=2)

        ttk.Label(move_frame, text="目标路径：").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.target_entry = ttk.Entry(move_frame, width=35)
        self.target_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(move_frame, text="浏览", command=self.select_target_path, width=6).grid(row=1, column=2)

        # 文件传输区域 ------------------------------------------------------
        transfer_frame = ttk.LabelFrame(left_frame, text=" 文件传输 ")
        transfer_frame.pack(fill=tk.X, pady=5)

        ttk.Label(transfer_frame, text="传输文件：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.transfer_entry = ttk.Entry(transfer_frame, width=35)
        self.transfer_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(transfer_frame, text="浏览", command=self.select_transfer_file, width=6).grid(row=0, column=2)

        self.progress = ttk.Progressbar(transfer_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.grid(row=1, column=0, columnspan=3, pady=10, padx=5)

        # 操作按钮区域 ------------------------------------------------------
        action_style = ttk.Style()
        action_style.configure("Action.TButton", width=12, padding=6)

        ttk.Button(right_frame, text="执行打开", command=self.send_open_file,
                   style="Action.TButton").pack(pady=8)
        ttk.Button(right_frame, text="执行移动", command=self.move_file,
                   style="Action.TButton").pack(pady=8)
        ttk.Button(right_frame, text="发送文件", command=self.send_file,
                   style="Action.TButton").pack(pady=8)
        ttk.Button(right_frame, text="关闭窗口", command=self.on_close,
                   style="Action.TButton").pack(pady=8)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # 文件选择方法组 ------------------------------------------------------
    def select_open_file(self):
        self._select_file(self.open_entry)

    def select_source_file(self):
        self._select_file(self.source_entry)

    def select_target_path(self):
        path = filedialog.askdirectory()
        if path:
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, path)

    def select_transfer_file(self):
        self._select_file(self.transfer_entry)

    def _select_file(self, entry_widget):
        filepath = filedialog.askopenfilename()
        if filepath:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filepath)

    # 核心功能方法 ------------------------------------------------------
    def send_open_file(self):
        filepath = self.open_entry.get()
        if not filepath:
            messagebox.showerror("错误", "请选择要打开的文件")
            return

        protocol = f"OPENFILE:{filepath}"
        self._send_protocol(protocol)

    def move_file(self):
        source = self.source_entry.get()
        target = self.target_entry.get()
        if not source or not target:
            messagebox.showerror("错误", "请填写完整的路径信息")
            return

        protocol = f"MOVEFILE:{source}->{target}"
        self._send_protocol(protocol)

    def send_file(self):
        filepath = self.transfer_entry.get()
        self.parent.log("文件传输开始")
        if not filepath:
            messagebox.showerror("错误", "请选择要传输的文件")
            return

        try:
            with open(filepath, 'rb') as f:
                filesize = len(f.read())
                filename = os.path.basename(filepath)
                protocol = f"FILE:RECEIVE:{filename}:{filesize}"

                # 发送文件头信息
                self._send_protocol(protocol, expect_response="[OK] 准备接收文件")

                # 重置进度条
                self.progress['maximum'] = filesize
                self.progress['value'] = 0

                # 发送文件内容
                with open(filepath, 'rb') as f_:
                    while True:
                        chunk = f_.read(4096)
                        if not chunk:
                            break
                        self.parent.sock.sendall(chunk)
                        self.progress['value'] += len(chunk)
                        self.update_idletasks()

                # 获取最终响应
                self.parent.sock.recv(1024).decode()
                self.parent.log("文件传输完成")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    # 通用方法 ------------------------------------------------------
    def _send_protocol(self, protocol, expect_response=None):
        try:
            self.parent.sock.sendall(protocol.encode('utf-8'))
            response = self.parent.sock.recv(1024).decode()

            if expect_response and response != expect_response:
                raise Exception(f"服务器响应异常: {response}")

        except Exception as e:
            messagebox.showerror("通信错误", str(e))

    def on_close(self):
        self.destroy()


class SendMessage(tk.Toplevel):
    def __init__(self, parent):
        self.parent = parent

        super().__init__(parent.root)

        self.title("发送消息")
        self.geometry("450x100")

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=10)
        ttk.Label(self, text="输入内容:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_msg = ttk.Entry(self, width=30)
        self.entry_msg.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="发送", command=self.send_alert).pack(side=tk.LEFT, padx=5)

    # 发送消息的函数
    def send_alert(self):
        message = self.entry_msg.get()
        if not message:
            messagebox.showerror("错误", "请输入提示消息")
            return

        send_message(self.parent, "ALERT", message)

        self.parent.log(f"发送消息成功:{message}")


class CMDControlWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("CMD控制台")
        self.geometry("700x600")
        self.create_widgets()
        self.command_history = []
        self.history_index = -1
        self.receive_thread = None
        self.stop_receive = False

    def create_widgets(self):
        # 输出区域
        self.output_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled')
        self.output_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 输入区域
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.cmd_entry = ttk.Entry(input_frame)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.cmd_entry.bind("<Return>", self.send_command)
        self.cmd_entry.bind("<Up>", self.history_prev)
        self.cmd_entry.bind("<Down>", self.history_next)

        ttk.Button(input_frame, text="发送", command=self.send_command).pack(side=tk.LEFT)
        ttk.Button(input_frame, text="清屏", command=self.clear_output).pack(side=tk.LEFT)

    def send_command(self):
        command = self.cmd_entry.get().strip()
        if not command:
            return
        self.parent.log(f"发送命令:{command}")

        self.command_history.append(command)
        self.history_index = len(self.command_history)

        self.append_output(f"Controller >> {command}\n")

        protocol = f"CMD:{command}"
        try:
            self.parent.sock.sendall(protocol.encode('utf-8'))
            # 启动接收线程
            self.stop_receive = False
            self.receive_thread = threading.Thread(target=self.receive_output)
            self.receive_thread.start()
        except Exception as e:
            self.append_output(f"[ERROR] {str(e)}\n")
        finally:
            self.cmd_entry.delete(0, tk.END)

    def receive_output(self):
        """ 新増：独立线程接收输出 """
        buffer = b""
        while not self.stop_receive:
            try:
                chunk = self.parent.sock.recv(4096)
                if not chunk:
                    break

                # 分离结束标记
                if b"[END]\n" in chunk:
                    data_part, end_part = chunk.split(b"[END]\n", 1)
                    buffer += data_part
                    if buffer:
                        self.append_output(buffer.decode('gbk', errors='replace'))
                    break
                else:
                    buffer += chunk
                    # 实时显示当前数据
                    self.append_output(buffer.decode('gbk', errors='replace'))
                    buffer = b""
            except BlockingIOError:
                time.sleep(0.1)
            except Exception as e:
                self.append_output(f"[ERROR] {str(e)}\n")
                break

    def append_output(self, text):
        self.output_area.after(0, self._update_output, text)

    def _update_output(self, text):
        """ 实际更新UI的方法 """
        self.output_area.configure(state='normal')
        self.output_area.insert(tk.END, text)
        self.output_area.configure(state='disabled')
        self.output_area.see(tk.END)

    def clear_output(self):
        self.output_area.configure(state='normal')
        self.output_area.delete(1.0, tk.END)
        self.output_area.configure(state='disabled')

    def history_prev(self, _):
        if self.command_history:
            self.history_index = max(0, self.history_index - 1)
            self.cmd_entry.delete(0, tk.END)
            self.cmd_entry.insert(0, self.command_history[self.history_index])

    def history_next(self, _):
        if self.command_history:
            self.history_index = min(len(self.command_history), self.history_index + 1)
            if self.history_index < len(self.command_history):
                self.cmd_entry.delete(0, tk.END)
                self.cmd_entry.insert(0, self.command_history[self.history_index])

    def on_close(self):
        """ 新增：窗口关闭时停止接收线程 """
        self.stop_receive = True
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join()
        self.destroy()


class ScreenViewWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("实时屏幕")
        self.geometry("800x600")
        self.running = False
        self.img_label = tk.Label(self)
        self.img_label.pack(fill=tk.BOTH, expand=True)

        # 控制按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.btn_start = ttk.Button(btn_frame, text="开始", command=self.start_stream)
        self.btn_start.pack(side=tk.LEFT)
        self.btn_stop = ttk.Button(btn_frame, text="停止", command=self.stop_stream)
        self.btn_stop.pack(side=tk.LEFT)

    def start_stream(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.receive_screen).start()

    def stop_stream(self):
        self.running = False

    def send_mouse_command(action, x, y):
        protocol = f"MOUSE:{action}:{x}:{y}"

    def send_keyboard_command(text):
        send_message(self.parent, "KEYBOARD", text)

    def receive_screen(self):
        try:
            self.parent.sock.sendall("SCREEN:START".encode('utf-8'))
            response = self.parent.sock.recv(1024)
            if response.decode('utf-8') != "[OK] 开始屏幕传输":
                raise Exception(f"启动失败({response.decode('utf-8')})")

            while self.running:
                # 读取图像长度（确保完整接收4字节）
                size_data = b''
                while len(size_data) < 4 and self.running:
                    chunk = self.parent.sock.recv(4 - len(size_data))
                    if not chunk:
                        break
                    size_data += chunk
                if len(size_data) != 4:
                    break
                size = int.from_bytes(size_data, 'big')

                # 读取图像数据（确保完整接收）
                img_data = b''
                remaining = size
                while remaining > 0 and self.running:
                    chunk = self.parent.sock.recv(4096)
                    if not chunk:
                        break
                    img_data += chunk
                    remaining -= len(chunk)

                if not self.running or len(img_data) != size:
                    break

                # 显示图像
                img = Image.open(io.BytesIO(img_data))
                img_tk = ImageTk.PhotoImage(img.resize((1440, 810)))
                self.img_label.config(image=img_tk)
                self.img_label.image = img_tk

                # 发送继续信号
                self.parent.sock.sendall(b"GO")
        except Exception as e:
            self.btn_start.config(state=tk.DISABLED)
            self.parent.log(f"屏幕传输错误: {str(e)}")
            # 清空缓冲区
            while True:
                try:
                    data = self.parent.sock.recv(4096)
                except socket.error as e:
                    self.btn_start.config(state=tk.NORMAL)
                    break

        finally:
            self.btn_start.config(state=tk.DISABLED)
            self.parent.sock.sendall("SCREEN:STOP".encode('utf-8'))
            # 清空缓冲区
            while True:
                try:
                    data = self.parent.sock.recv(4096)
                except socket.error as e:
                    self.btn_start.config(state=tk.NORMAL)
                    break



if __name__ == "__main__":
    app = QApplication([])
    window = RemoteCommanderGUI()
    window.show()
    app.exec_()