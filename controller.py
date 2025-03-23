import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk, messagebox, scrolledtext, filedialog
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


def send_message(parent, format, message, byte_len=1024, function=None, show_info=True, return_=False):
    protocol = f"{format}:{message}"
    try:
        parent.sock.sendall(protocol.encode('utf-8'))
        response = parent.sock.recv(byte_len).decode()
        if show_info:
            messagebox.showinfo("结果", response)
        else:
            function(response)
        if return_:
            return response

    except Exception as e:
        messagebox.showerror("错误", str(e))


class RemoteCommanderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"RemoteCommander GUI v{VERSION}")
        self.root.iconbitmap("./icon/icon.ico")
        self.root.geometry("1000x700")

        # 连接状态
        self.connected = False
        self.current_ip = None
        self.sock = None

        # 创建界面组件
        self.create_widgets()
        self.setup_style()

        # 取消版本校验选框
        self.var_version_check = tk.IntVar()
        # self.var_version_check.set("1")
        self.btn_version_check = tk.Checkbutton(master=self.root, text="版本校验", variable=self.var_version_check, onvalue=1, offvalue=0)
        self.btn_version_check.place(x=0, y=675)

        # 绑定快捷键
        self.root.bind("<Control-m>", self.get_mouse_position)

        # 首次扫描
        self.after_scan()

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def start_hover_animation(self, button, start_color, end_color):
        start_r, start_g, start_b = self.hex_to_rgb(start_color)
        end_r, end_g, end_b = self.hex_to_rgb(end_color)

        def set_color(value):
            r = int((1 - value) * start_r + value * end_r)
            g = int((1 - value) * start_g + value * end_g)
            b = int((1 - value) * start_b + value * end_b)
            color = f'#{r:02x}{g:02x}{b:02x}'
            button.config(bg=color)

        animate(
            widget=button,
            start=0,
            end=1,
            duration=0.3,
            bezier_params=(0.25, 0.1, 0.25, 1.0),  # 使用EASE缓动
            set_value=set_color
        )

    def create_widgets(self):
        # 侧边栏
        sidebar = tk.Frame(self.root, bg='#f0f0f0')  # 确保背景色一致
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # 按钮样式配置
        button_style = {
            'bg': '#d9d9d9', 'fg': 'black', 'relief': 'flat',
            'activebackground': '#00e0eb', 'borderwidth': 0
        }

        # 创建按钮并绑定事件
        self.btn_scan = tk.Button(sidebar, text="扫描网络", command=self.start_scan, **button_style)
        self.btn_scan.pack(side=tk.TOP, fill=tk.X, pady=2)
        self.btn_scan.bind('<Enter>', lambda e: self.start_hover_animation(e.widget, '#d9d9d9', '#0ce0eb'))
        self.btn_scan.bind('<Leave>', lambda e: self.start_hover_animation(e.widget, '#0ce0eb', '#d9d9d9'))

        # 其他按钮同理，每个按钮添加相同的绑定
        # 使用列表存储按钮控件
        buttons = [
            ("连接", self.toggle_connection),
            ("进程管理", self.show_process_manager),
            ("鼠标控制", self.show_mouse_control),
            ("键盘控制", self.show_enter_string),
            ("执行按键", self.show_shortcut_manager),
            ("文件管理", self.show_open_file),
            ("发送消息", self.show_send_message),
            ("CMD控制", self.show_cmd_control),
            ("实时屏幕", self.show_screen_view)
        ]

        self.btn_objects = []

        for text, cmd in buttons:
            btn = tk.Button(sidebar, text=text, command=cmd, **button_style)
            btn.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

            self.btn_objects.append(btn)

            btn.bind('<Enter>', lambda e: self.start_hover_animation(e.widget, '#d9d9d9', '#0ce0eb'))
            btn.bind('<Leave>', lambda e: self.start_hover_animation(e.widget, '#0ce0eb', '#d9d9d9'))

        # 主内容区域
        main_content = ttk.Frame(self.root)
        main_content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 目标列表
        self.target_tree = ttk.Treeview(main_content, columns=("ip", "hostname", "version"), show="headings")
        self.target_tree.heading("ip", text="IP地址")
        self.target_tree.heading("hostname", text="主机名")
        self.target_tree.heading("version", text="版本")
        self.target_tree.column("ip", width=120)
        self.target_tree.column("hostname", width=150)
        self.target_tree.column("version", width=80)
        self.target_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.target_tree.bind("<<TreeviewSelect>>", self.on_target_select)

        # 日志窗口
        self.log_area = scrolledtext.ScrolledText(main_content, wrap=tk.WORD)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 状态栏
        self.status = tk.StringVar()
        self.status.set("就绪")

        self.l_status = ttk.Label(main_content, textvariable=self.status)
        self.l_status.pack(side=tk.BOTTOM, fill=tk.X)


        # 进入时输出基本信息
        self.log("RemoteCommander GUI v" + VERSION)
        self.log("Author: Qiu_Fan")
        self.log("Email: 3592916761@qq.com")
        self.log("Fork: Coco")
        self.log("Email: 3881898540@qq.com")
        self.log("本程序仅供学习交流使用，禁止商业用途")

    def setup_style(self):
        style = ttk.Style()
        style.configure("TButton", padding=6)
        style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
        style.map("TButton",
                  foreground=[('pressed', '#0ce0eb'), ('active', '#0ce0eb')],
                  background=[('pressed', '#006699'), ('active', '#006699')])

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def set_status(self, message):
        self.l_status.config(text=message)

    def after_scan(self):
        self.root.after(100, self.start_scan)

    def start_scan(self):
        self.log("开始扫描网络...")
        self.btn_scan.config(state=tk.DISABLED)
        threading.Thread(target=self.scan_targets).start()

    def scan_targets(self):
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

    def update_target_list(self, targets):
        self.target_tree.delete(*self.target_tree.get_children())
        for ip, info in targets.items():
            self.target_tree.insert("", tk.END, values=(ip, info['hostname'], info['version']))
        self.btn_scan.config(state=tk.NORMAL)
        self.log(f"扫描完成，找到 {len(targets)} 个目标")

    def on_target_select(self, _):
        selected = self.target_tree.selection()
        if selected:
            item = self.target_tree.item(selected[0])
            self.current_ip = item['values'][0]

    def toggle_connection(self):
        if not self.connected:
            if self.current_ip:
                threading.Thread(target=self.connect_target).start()
        else:
            self.disconnect()

    def connect_target(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.current_ip, TCP_PORT))

            # 版本校验
            self.sock.send(b"/version")
            version = self.sock.recv(1024).decode()

            if self.var_version_check.get():
                if version != VERSION:
                    self.log(f"版本校验失败")
                    messagebox.showerror("错误", f"版本不匹配 (目标机:{version} -- 控制端:{VERSION})")
                    return

                self.log("通过版本校验")

            self.connected = True
            self.root.after(0, self.update_connection_ui)
            self.log(f"成功连接到 {self.current_ip}")

            self.status.set(f"已连接到 {self.current_ip}")
        except Exception as e:
            self.log(f"连接失败: {str(e)}")

    def update_connection_ui(self):
        self.btn_objects[0].config(text="断开")

    def disconnect(self):
        if self.sock:
            self.sock.close()
        self.connected = False
        self.btn_objects[0].config(text="连接")
        self.set_status("已断开连接")

        self.status.set("已断开")

    def show_process_manager(self):
        if self.connected:
            ProcessManagerWindow(self)

    def show_mouse_control(self):
        if self.connected:
            MouseControlWindow(self)

    def show_shortcut_manager(self):
        if self.connected:
            ShortcutManagerWindow(self)

    def show_open_file(self):
        if self.connected:
            FileManagerWindow(self)

    def show_send_message(self):
        if self.connected:
            SendMessage(self)

    def show_enter_string(self):
        if self.connected:
            EnterString(self)

    def show_cmd_control(self):
        if self.connected:
            CMDControlWindow(self)

    def show_screen_view(self):
        if self.connected:
            ScreenViewWindow(self)

    def get_mouse_position(self, _):
        x, y = pyautogui.position()
        self.log(f"当前鼠标坐标: X={x}, Y={y}")


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
            self.parent.sock.sendall(protocol.encode('utf-8'))
            response = self.parent.sock.recv(1024).decode()
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
    def __init__(self, parent, remote_resolution=(1920, 1080)):
        super().__init__(parent.root)
        self.parent = parent
        self.title("实时屏幕")
        self.geometry("800x600")

        # 状态控制变量
        self.running = False
        self.is_alive = True  # 新增窗口存活状态标记
        self.remote_w, self.remote_h = remote_resolution

        # 图像显示
        self.img_label = tk.Label(self)
        self.img_label.pack(fill=tk.BOTH, expand=True)
        self.img_label.bind("<Button-1>", self.on_click)

        # 控制按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.btn_start = ttk.Button(btn_frame, text="开始", command=self.start_stream)
        self.btn_start.pack(side=tk.LEFT)
        self.btn_stop = ttk.Button(btn_frame, text="停止", command=self.stop_stream)
        self.btn_stop.pack(side=tk.LEFT)

        # 绑定窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def safe_update_button(self, state):
        """ 线程安全的按钮状态更新 """
        if self.is_alive and self.btn_start.winfo_exists():
            self.btn_start.config(state=state)

    def start_stream(self):
        if not self.running:
            self.running = True
            self.stream_thread = threading.Thread(target=self.receive_screen)
            self.stream_thread.daemon = True  # 设为守护线程
            self.stream_thread.start()

    def stop_stream(self):
        self.running = False

    def on_close(self):
        """ 窗口关闭时的清理方法 """
        self.is_alive = False
        self.running = False
        if hasattr(self, 'stream_thread') and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=1)  # 等待线程退出
        self.destroy()

    def receive_screen(self):
        try:
            self.after(0, self.safe_update_button, tk.DISABLED)

            # 建立屏幕传输连接
            self.parent.sock.sendall("SCREEN:START".encode('utf-8'))
            response = self.parent.sock.recv(1024)
            if response.decode('utf-8') != "[OK] 开始屏幕传输":
                self.after(0, lambda: messagebox.showerror("错误", "启动失败"))
                return

            while self.running and self.is_alive:  # 双重状态检查
                # 读取图像长度头
                size_data = b''
                while len(size_data) < 4 and self.running and self.is_alive:
                    try:
                        chunk = self.parent.sock.recv(4 - len(size_data))
                        if not chunk:
                            break
                        size_data += chunk
                    except (socket.timeout, ConnectionResetError):
                        break

                if len(size_data) != 4 or not self.is_alive:
                    break

                # 读取图像数据
                img_size = int.from_bytes(size_data, 'big')
                img_data = b''
                remaining = img_size
                while remaining > 0 and self.running and self.is_alive:
                    try:
                        chunk = self.parent.sock.recv(min(4096, remaining))
                        if not chunk:
                            break
                        img_data += chunk
                        remaining -= len(chunk)
                    except (socket.timeout, ConnectionResetError):
                        break

                if not self.is_alive or len(img_data) != img_size:
                    break

                # 显示图像（主线程操作）
                self.after(0, self.update_image, img_data)

                # 发送确认信号
                try:
                    self.parent.sock.sendall(b"GO")
                except (BrokenPipeError, ConnectionResetError):
                    break

        except Exception as e:
            error_msg = f"屏幕传输错误: {str(e)}"
            self.after(0, self.parent.log, error_msg)
            self.after(0, lambda: messagebox.showerror("错误", error_msg))

        finally:
            # 清理操作
            self.after(0, self.safe_update_button, tk.NORMAL)
            try:
                if self.is_alive:
                    self.parent.sock.sendall("SCREEN:STOP".encode('utf-8'))
            except:
                pass
            self.running = False

    def update_image(self, img_data):
        """ 主线程更新图像显示 """
        if not self.is_alive:
            return

        try:
            img = Image.open(io.BytesIO(img_data))
            img_tk = ImageTk.PhotoImage(img.resize((1440, 810)))
            self.img_label.config(image=img_tk)
            self.img_label.image = img_tk
        except Exception as e:
            self.parent.log(f"图像显示错误: {str(e)}")

    def update_scaling_factors(self):
        """动态更新坐标比例"""
        if not self.is_alive:
            return

        local_w = self.img_label.winfo_width()
        local_h = self.img_label.winfo_height()
        if local_w > 0 and local_h > 0:
            self.scale_x = self.remote_w / local_w
            self.scale_y = self.remote_h / local_h

    def on_click(self, event):
        """ 点击事件处理 """
        if self.is_alive and self.running:
            self.update_scaling_factors()
            x = int(event.x * self.scale_x)
            y = int(event.y * self.scale_y)
            send_message(parent=self.parent,
                         format="MOUSE:CLICK",
                         message=f"{x}:{y}",
                         show_info=False)





if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteCommanderGUI(root)
    root.mainloop()