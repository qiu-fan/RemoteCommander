import tkinter as tk
from function.mouse_control import MouseController

class MouseControlWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.title("鼠标控制")
        self.geometry("400x300")
        
        # 初始化功能控制器
        self.controller = MouseController(self, app.sock)
        
        # 创建UI组件
        self._create_widgets()
        
    def _create_widgets(self):
        """创建并布局UI组件"""
        control_btn = tk.Button(
            self,
            text="开始控制",
            command=self._on_control_click
        )
        control_btn.pack(pady=20)
        
    def _on_control_click(self):
        """处理控制按钮点击事件"""
        self.controller.start_mouse_control()

    def setup_ui(self):
        # 创建画布用于鼠标跟踪
        self.canvas = tk.Canvas(self, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 状态显示区域
        self.status_label = tk.Label(self, text="等待连接...")
        self.status_label.pack(pady=5)

    def create_bindings(self):
        self.bind('<Destroy>', lambda e: self.on_close())
        self.canvas.bind('<Motion>', self.handle_motion)
        self.canvas.bind('<ButtonPress-1>', lambda e: self.controller.click('left'))
        self.canvas.bind('<ButtonRelease-1>', self.handle_release)

    def handle_motion(self, event):
        self.controller.move_cursor(event.x, event.y)
        self.status_label.config(text=f"坐标: {event.x}, {event.y}")

    def handle_release(self, _):
        self.status_label.config(text="等待操作...")

    def on_close(self):
        pass
