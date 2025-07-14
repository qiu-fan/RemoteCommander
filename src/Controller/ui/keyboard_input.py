import tkinter as tk
from function.keyboard_input import KeyboardInputController

class KeyboardInputWindow(tk.Toplevel):
    """键盘输入控制窗口类 - 仅负责UI布局与交互"""
    def __init__(self, app):
        super().__init__(app.root)
        self.title("键盘输入")
        self.geometry("400x300")
        
        # 初始化功能控制器
        self.controller = KeyboardInputController(self, app.sock)
        
        # 创建UI组件
        self._create_widgets()
        
    def _create_widgets(self):
        """创建并布局UI组件"""
        input_btn = tk.Button(
            self,
            text="开始输入",
            command=self._on_input_click
        )
        input_btn.pack(pady=20)
        
    def _on_input_click(self):
        """处理输入按钮点击事件"""
        self.controller.start_keyboard_input()
