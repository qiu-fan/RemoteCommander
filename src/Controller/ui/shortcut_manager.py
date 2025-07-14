import tkinter as tk

class ShortcutManagerWindow(tk.Toplevel):
    """快捷键管理窗口类 - 仅负责UI布局与交互"""
    def __init__(self, app):
        super().__init__(app.root)
        self.title("快捷键管理")
        self.geometry("400x300")
        
        # 创建UI组件
        self._create_widgets()
        
    def _create_widgets(self):
        """创建并布局UI组件"""
        close_btn = tk.Button(
            self,
            text="关闭",
            command=self.destroy
        )
        close_btn.pack(pady=20)
