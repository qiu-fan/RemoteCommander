import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import socket
import time
import threading
import pyautogui
import os

TCP_PORT = 9999
UDP_PORT = 9998
VERSION = "6.1.2"

def send_message(parent, format, message):
    protocol = f"{format}:{message}"
    try:
        parent.sock.sendall(protocol.encode('utf-8'))
        response = parent.sock.recv(1024).decode()
        messagebox.showinfo("结果", response)
    except Exception as e:
        messagebox.showerror("错误", str(e))

class BasePage(ttk.Frame):
    """功能页面基类"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.create_widgets()
        
    def create_widgets(self):
        raise NotImplementedError("子类必须实现此方法")



class ProcessManagerPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.controller = controller
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
        protocol = f"PROC:LIST:{self.filter_keyword}:{self.current_page}"
        try:
            self.controller.sock.sendall(protocol.encode('utf-8'))
            response = self.controller.sock.recv(4096).decode('utf-8')
            self.update_process_list(response)
        except Exception as e:
            messagebox.showerror("错误", str(e))

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

        self.page_label.config(text=f"第{params['PAGE']}页 共{params['TOTAL']}条")

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
            protocol = f"PROC:KILL:{pid}"
            try:
                self.controller.sock.sendall(protocol.encode('utf-8'))
                response = self.controller.sock.recv(1024).decode()
                messagebox.showinfo("结果", response)
                self.load_processes()
            except Exception as e:
                messagebox.showerror("错误", str(e))


class MouseControlPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.create_widgets()

    def create_widgets(self):
        # 坐标输入区域
        input_frame = ttk.Frame(self)
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(input_frame, text="X坐标:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_x = ttk.Entry(input_frame, width=15)
        self.entry_x.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(input_frame, text="Y坐标:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_y = ttk.Entry(input_frame, width=15)
        self.entry_y.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # 获取坐标按钮
        ttk.Button(
            input_frame, 
            text="获取当前坐标", 
            command=self.get_current_pos
        ).grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")

        # 操作按钮区域
        btn_frame = ttk.Frame(self)
        btn_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        ttk.Button(
            btn_frame, 
            text="移动鼠标", 
            command=lambda: self.send_mouse_command("MOVE")
        ).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        ttk.Button(
            btn_frame, 
            text="点击", 
            command=lambda: self.send_mouse_command("CLICK")
        ).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        ttk.Button(
            btn_frame, 
            text="移动并点击", 
            command=lambda: self.send_mouse_command("MOVE_CLICK")
        ).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def get_current_pos(self):
        """获取本机鼠标坐标（仅用于参考）"""
        x, y = pyautogui.position()
        self.entry_x.delete(0, tk.END)
        self.entry_x.insert(0, str(x))
        self.entry_y.delete(0, tk.END)
        self.entry_y.insert(0, str(y))

    def send_mouse_command(self, action):
        """发送鼠标指令到目标机器"""
        try:
            x = int(self.entry_x.get())
            y = int(self.entry_y.get())
            protocol = f"MOUSE:{action}:{x}:{y}"
            self.controller.sock.sendall(protocol.encode('utf-8'))
            response = self.controller.sock.recv(1024).decode()
            if response.startswith("[ERROR]"):
                raise Exception(response)
            messagebox.showinfo("操作成功", response)
        except ValueError:
            messagebox.showerror("输入错误", "坐标必须为整数")
        except Exception as e:
            messagebox.showerror("通信错误", str(e))


class EnterStringPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 输入区域
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="输入内容:").pack(side=tk.LEFT, padx=5)
        self.entry = ttk.Entry(input_frame)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 特殊按键面板
        key_frame = ttk.LabelFrame(main_frame, text="特殊按键")
        key_frame.pack(fill=tk.X, pady=5)

        keys = [
            ("Enter", "{enter}"), ("Tab", "{tab}"), ("Space", "{space}"),
            ("↑", "{up}"), ("↓", "{down}"), ("←", "{left}"), ("→", "{right}"),
            ("Win", "{win}"), ("Alt", "{alt}"), ("Ctrl", "{ctrl}"), ("Shift", "{shift}")
        ]
        
        row, col = 0, 0
        for text, symbol in keys:
            btn = ttk.Button(
                key_frame, 
                text=text, 
                width=6,
                command=lambda s=symbol: self.insert_symbol(s)
            )
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            col += 1
            if col > 3:  # 每行4个按钮
                col = 0
                row += 1

        # 功能按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="发送", command=self.send_code).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="组合键示例", command=self.show_shortcuts).pack(side=tk.RIGHT)

    def insert_symbol(self, symbol):
        self.entry.insert(tk.END, symbol)

    def send_code(self):
        text = self.entry.get().strip()
        if not text:
            messagebox.showwarning("输入错误", "内容不能为空")
            return
            
        try:
            protocol = f"KEYBOARD:{text}"
            self.controller.sock.sendall(protocol.encode('utf-8'))
            response = self.controller.sock.recv(1024).decode()
            messagebox.showinfo("操作结果", response)
        except Exception as e:
            messagebox.showerror("通信错误", str(e))

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


# 主界面类 --------------------------------------------------
class RemoteCommanderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"RemoteCommander GUI v{VERSION}")
        self.root.geometry("1400x600")
        
        self.connected = False
        self.current_ip = None
        self.sock = None
        self.current_page = None
        self.pages = {}

        self.create_widgets()
        self.setup_style()
        self.root.bind("<Control-m>", self.get_mouse_position)
        self.after_scan()

    def create_widgets(self):
        # 侧边栏
        sidebar = ttk.Frame(self.root)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        nav_buttons = [
            ("扫描网络", self.start_scan),
            ("连接", self.toggle_connection),
            ("进程管理", lambda: self.show_page("proc")),
            ("鼠标控制", lambda: self.show_page("mouse")),
            ("键盘控制", lambda: self.show_page("keyboard")),
            ("执行按键", lambda: self.show_page("shortcut")),
            ("文件管理", lambda: self.show_page("file")),
            ("发送消息", lambda: self.show_page("message")),
            ("CMD控制", lambda: self.show_page("cmd"))
        ]

        for text, cmd in nav_buttons:
            btn = ttk.Button(sidebar, text=text, command=cmd)
            btn.pack(side=tk.TOP, fill=tk.X, pady=2)

        # 主内容区域
        self.main_content = ttk.Frame(self.root)
        self.main_content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 目标列表
        self.target_tree = ttk.Treeview(self.main_content, columns=("ip", "hostname", "version"), show="headings")
        self.target_tree.heading("ip", text="IP地址")
        self.target_tree.heading("hostname", text="主机名")
        self.target_tree.heading("version", text="版本")
        self.target_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.target_tree.bind("<<TreeviewSelect>>", self.on_target_select)

        # 日志窗口
        self.log_area = scrolledtext.ScrolledText(self.main_content, wrap=tk.WORD)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 状态栏
        self.status = ttk.Label(self.main_content, text="就绪")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        # 初始化所有页面
        self.pages = {
            "proc": ProcessManagerPage(self.main_content, self),
            "mouse": MouseControlPage(self.main_content, self),
            "keyboard": EnterStringPage(self.main_content, self)
            # 其他页面需要类似初始化...
        }

        for page in self.pages.values():
            page.pack_forget()

    def show_page(self, page_name):
        if self.current_page:
            self.current_page.pack_forget()
            
        self.current_page = self.pages.get(page_name)
        if self.current_page:
            self.current_page.pack(fill=tk.BOTH, expand=True)
            if hasattr(self.current_page, 'load_processes'):
                self.current_page.load_processes()

    # 以下是需要补全的核心方法 --------------------------------
    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=6)
        style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def start_scan(self):
        self.log("开始扫描网络...")
        threading.Thread(target=self.scan_targets).start()

    def scan_targets(self):
        targets = {}
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(2)
            try:
                s.sendto(b"DISCOVER", ('<broadcast>', UDP_PORT))
                start_time = time.time()
                while time.time() - start_time < 3:
                    try:
                        data, addr = s.recvfrom(1024)
                        ver, hostname = data.decode().split('|')
                        targets[addr[0]] = {'hostname': hostname, 'version': ver}
                    except socket.timeout:
                        break
            except Exception as e:
                self.log(f"扫描错误: {str(e)}")
        self.root.after(0, self.update_target_list, targets)

    def update_target_list(self, targets):
        for item in self.target_tree.get_children():
            self.target_tree.delete(item)
        for ip, info in targets.items():
            self.target_tree.insert("", tk.END, values=(ip, info['hostname'], info['version']))
        self.log(f"扫描完成，找到 {len(targets)} 个目标")

    def on_target_select(self, _):
        selected = self.target_tree.selection()
        if selected:
            self.current_ip = self.target_tree.item(selected[0])['values'][0]

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
            self.sock.send(b"/version")
            version = self.sock.recv(1024).decode()
            if version != VERSION:
                messagebox.showerror("错误", f"版本不匹配 (目标机:{version} -- 控制端:{VERSION})")
                return
            self.connected = True
            self.root.after(0, self.update_connection_ui)
            self.log(f"成功连接到 {self.current_ip}")
        except Exception as e:
            self.log(f"连接失败: {str(e)}")

    def update_connection_ui(self):
        self.status.config(text=f"已连接: {self.current_ip}")

    def disconnect(self):
        if self.sock:
            self.sock.close()
        self.connected = False
        self.status.config(text="已断开连接")

    def get_mouse_position(self, _):
        x, y = pyautogui.position()
        self.log(f"当前鼠标坐标: X={x}, Y={y}")

    def after_scan(self):
        self.root.after(100, self.start_scan)

if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteCommanderGUI(root)
    root.mainloop()