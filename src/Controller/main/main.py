import socket
import threading
import time
import tkinter as tk
from tkinter import (
    messagebox,
    scrolledtext
)

import ttkbootstrap as ttk

import pyautogui
import sys
from pathlib import Path

# 添加项目根目录（RemoteCommander）到Python路径
current_dir = Path(__file__).resolve()
project_root = current_dir.parent.parent.parent  # 指向RemoteCommander目录
sys.path.append(str(project_root))

from controller.ui import cmd_control, mouse_control, keyboard_input, message_sender, process_manager, screen_viewer, shortcut_manager, file_explorer
from controller.function.controller_manager import ControllerManager  # 新增导入

TCP_PORT = 9999
UDP_PORT = 9998
VERSION = "9.0.0"
THEME = "morph"


class RemoteCommanderGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"RemoteCommander v{VERSION}")

        try:
            self.root.iconbitmap("./icon/icon.ico")
        except Exception as e:
            print(e)
        self.root.geometry("1000x700")

        # 连接状态
        self.connected = False
        self.current_ip = None
        self.sock = None

        # 创建功能管理器
        self.controller = ControllerManager(  # 新增初始化
            log_callback=self.log,
            update_ui_callback=self.update_target_list
        )

        # 创建界面组件
        self.create_widgets()
        self.setup_style()

    def create_widgets(self):
        # 侧边栏
        sidebar = tk.Frame(self.root, bg='#f0f0f0')
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # 创建按钮并绑定事件
        self.btn_scan = ttk.Button(sidebar, text="扫描网络", command=self.start_scan)
        self.btn_scan.grid(row=0, column=0, sticky="ew", pady=2)
        self.btn_scan.bind('<Enter>', lambda e: e.widget.after(50, lambda: e.widget.config(style="Hover.TButton")))
        self.btn_scan.bind('<Leave>', lambda e: e.widget.after(50, lambda: e.widget.config(style="TButton")))

        # 其他按钮同理，每个按钮添加相同的绑定
        buttons = [
            ("连接", self.toggle_connection),
            ("进程管理", self.show_process_manager),
            ("鼠标控制", self.show_mouse_control),
            ("键盘控制", self.show_enter_string),
            ("执行按键", self.show_shortcut_manager),
            ("文件管理", self.show_open_file),
            ("发送消息", self.show_send_message),
            ("CMD控制", self.show_cmd_control),
            ("实时屏幕", self.show_screen_view),
            ("自动任务", self.show_auto_task),
            ("文件浏览器", self.show_file_explorer),
        ]

        self.btn_objects = []

# 导入UI窗口类
from ui.cmd_control import CMDControlWindow
from ui.mouse_control import MouseControlWindow
from ui.keyboard_input import EnterString
from ui.message_sender import SendMessage
from ui.process_manager import ProcessManagerWindow
from ui.screen_viewer import ScreenViewWindow
from ui.shortcut_manager import ShortcutManagerWindow
from ui.file_explorer import FileManagerWindow

for i, (text, cmd) in enumerate(buttons):
    btn = ttk.Button(sidebar, text=text, command=cmd)
    btn.grid(row=i+1, column=0, sticky="ew", padx=5, pady=5)

    self.btn_objects.append(btn)

    btn.bind('<Enter>', lambda e: e.widget.after(50, lambda: e.widget.config(style="Hover.TButton")))
    btn.bind('<Leave>', lambda e: e.widget.after(50, lambda: e.widget.config(style="TButton")))

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

    self.var_version_check = tk.IntVar()
    self.var_version_check.set(1)
    ttk.Checkbutton(master=self.root, text="版本检查", variable=self.var_version_check).place(x=10, y=680)

    # 进入时输出基本信息
    self.log("RemoteCommander GUI v" + VERSION)
    self.log("Author: Qiu_Fan")
    self.log("Email: 3592916761@qq.com")
    self.log("Fork: Coco")
    self.log("Email: 3881898540@qq.com")
    self.log("本程序仅供学习交流使用，禁止商业用途\n\n")

def setup_style(self):
    style = ttk.Style()
    style.configure("TButton", padding=6, background='#4BB1EA', foreground='black')
    style.configure("Hover.TButton", background='#00e0eb')
    style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
    style.map("TButton",
                foreground=[('pressed', '#0ce0eb'), ('active', '#0ce0eb')],
                background=[('pressed', '#006699'), ('active', '#006699')])

def log(self, message):
    self.log_area.insert(tk.END, f"{time.strftime('[%H%M%S]', time.localtime())}[Info]|{message} \n")
    self.log_area.see(tk.END)


def set_status(self, message):
    self.l_status.config(text=message)

def after_scan(self):
    self.root.after(100, self.start_scan)

def start_scan(self):
    self.log("开始扫描网络...")
    self.btn_scan.config(state=tk.DISABLED)
    threading.Thread(target=self.controller.scan_targets).start()  # 修改为调用功能管理器

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
    success = self.controller.connect_target(  # 修改为调用功能管理器
        ip=self.current_ip,
        version_check=self.var_version_check.get(),
        VERSION=VERSION
    )
    
    if success:
        self.connected = True
        self.root.after(0, self.update_connection_ui)
        self.status.set(f"已连接到 {self.current_ip}")

def update_connection_ui(self):
    self.btn_objects[0].config(text="断开")

def disconnect(self):
    if self.controller.disconnect():  # 修改为调用功能管理器
        self.connected = False
        self.btn_objects[0].config(text="连接")
        self.set_status("已断开连接")
        self.status.set("已断开")