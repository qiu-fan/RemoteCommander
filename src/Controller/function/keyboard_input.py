import tkinter as tk
from tkinter import ttk
from message_client import send_message
from tkinter import messagebox
import socket
import threading
import tkinter as tk
from tkinter import messagebox

class KeyboardInputController:
    """键盘输入控制核心功能模块"""
    def __init__(self, master, sock):
        self.master = master
        self.sock = sock
        
    def start_keyboard_input(self):
        """启动键盘输入功能"""
        if not self.sock:
            messagebox.showerror("错误", "未连接到目标设备")
            return
            
        # 添加核心控制逻辑
        threading.Thread(target=self._input_worker, daemon=True).start()
        
    def _input_worker(self):
        """后台键盘输入工作线程"""
        try:
            while True:
                # 添加实际控制逻辑
                pass
        except Exception as e:
            messagebox.showerror("错误", f"键盘输入异常: {str(e)}")

class KeyboardController:
    def __init__(self, parent):
        self.parent = parent  # 弱引用保持者
        self.sock = parent.sock if hasattr(parent, 'sock') else None

    def send_key(self, key_code):
        """发送键盘指令"""
        try:
            protocol = f"KEYBOARD:{key_code}"
            self.sock.sendall(protocol.encode('utf-8'))
        except Exception as e:
            self.parent.append_output(f"[ERROR] {str(e)}\n")

    def send_text(self, text):
        """发送文本输入"""
        try:
            protocol = f"TEXT:{text}"
            self.sock.sendall(protocol.encode('utf-8'))
        except Exception as e:
            self.parent.append_output(f"[ERROR] {str(e)}\n")


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
