import tkinter as tk
import tkinter.ttk as ttk
from function.message_client import send_message
from .base_window import BaseWindow

class ProcessManagerWindow(BaseWindow):
    def __init__(self, parent):
        super().__init__(parent, title="进程管理", geometry="1000x400")
        self.current_page = 1
        self.filter_keyword = ""
        self.load_processes()

    def create_widgets(self):
        # 工具栏
        buttons = [
            ("刷新", self.load_processes),
            ("上一页", self.prev_page),
            ("下一页", self.next_page)
        ]
        toolbar = self.create_toolbar(buttons)

        self.page_label = ttk.Label(toolbar, text="第1页")
        self.page_label.pack(side=tk.LEFT, padx=10)

        self.filter_entry = ttk.Entry(toolbar)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="过滤", command=self.apply_filter).pack(side=tk.LEFT)

        # 进程列表
        columns = ("pid", "name", "user", "cpu", "memory")
        self.tree = self.create_treeview(columns)

        # 操作按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="终止进程", command=self.kill_process).pack(side=tk.LEFT)

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