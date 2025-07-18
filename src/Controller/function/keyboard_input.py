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


