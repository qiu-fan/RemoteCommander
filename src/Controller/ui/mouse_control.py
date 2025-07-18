import socket
import threading
import tkinter as tk
import ttkbootstrap as ttk
import pyautogui
from .base_window import BaseWindow
from tkinter import messagebox
from function.mouse_control import *

class MouseController:
    """鼠标控制核心功能模块，实现与UI的完全解耦"""
    def __init__(self, master, sock):
        self.master = master
        self.sock = sock
        
    def start_mouse_control(self):
        """启动鼠标控制功能"""
        if not self.sock:
            messagebox.showerror("错误", "未连接到目标设备")
            return
            
        # 添加核心控制逻辑
        threading.Thread(target=self._mouse_worker, daemon=True).start()
        
    def _mouse_worker(self):
        """后台鼠标控制工作线程"""
        try:
            while True:
                # 添加实际控制逻辑
                pass
        except Exception as e:
            messagebox.showerror("错误", f"鼠标控制异常: {str(e)}")

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
        ttk.Button(self, text="移动鼠标", command=lambda: send_mouse_command(self, "MOVE")).grid(row=3, column=0, padx=5,
                                                                                                pady=5)
        ttk.Button(self, text="点击", command=lambda: send_mouse_command(self, "CLICK")).grid(row=3, column=1, padx=5,
                                                                                             pady=5)
        ttk.Button(self, text="移动并点击", command=lambda: send_mouse_command(self, "MOVE_CLICK")).grid(row=4, column=0,
                                                                                                        columnspan=2,
                                                                                                        pady=5)

    def get_current_pos(self):
        x, y = pyautogui.position()
        self.entry_x.delete(0, tk.END)
        self.entry_x.insert(0, str(x))
        self.entry_y.delete(0, tk.END)
        self.entry_y.insert(0, str(y))

