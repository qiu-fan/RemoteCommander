import socket
import threading
import time
import tkinter as tk
from tkinter import (
    messagebox,
    scrolledtext,
    ttk
)

import pyautogui

from Controller.animate import animate
from function import (process_manager, mouse_control, file_manager,
                      shortcut_manager, screen_viewer, message_sender,
                      keyboard_input, cmd_control)





TCP_PORT = 9999
UDP_PORT = 9998
VERSION = "7.0.3"


class RemoteCommanderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"RemoteCommander")



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
        self.var_version_check.set("1")
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
        # 加载图标
        try:
            self.root.iconbitmap("./icon/icon.ico")
        except:
            self.log("无法加载图标")

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
            process_manager.ProcessManagerWindow(self)


    def show_mouse_control(self):
        if self.connected:
            mouse_control.MouseControlWindow(self)

    def show_shortcut_manager(self):
        if self.connected:
            shortcut_manager.ShortcutManagerWindow(self)

    def show_open_file(self):
        if self.connected:
            file_manager.FileManagerWindow(self)

    def show_send_message(self):
        if self.connected:
            message_sender.SendMessage(self)

    def show_enter_string(self):
        if self.connected:
            keyboard_input.EnterString(self)

    def show_cmd_control(self):
        if self.connected:
            cmd_control.CMDControlWindow(self)

    def show_screen_view(self):
        if self.connected:
            screen_viewer.ScreenViewWindow(self)

    def get_mouse_position(self, _):
        x, y = pyautogui.position()
        self.log(f"当前鼠标坐标: X={x}, Y={y}")



if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteCommanderGUI(root)
    root.mainloop()
