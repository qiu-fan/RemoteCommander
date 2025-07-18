import tkinter as tk
from function.message_sender import *
from tkinter import ttk
from .base_window import BaseWindow


class SendMessage(BaseWindow):
    def __init__(self, parent):
        super().__init__(parent, title="发送消息", geometry="450x100")
        self.parent = parent

    def create_widgets(self):
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=10)
        ttk.Label(self, text="输入内容:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_msg = ttk.Entry(self, width=30)
        self.entry_msg.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="发送", command=send_alert).pack(side=tk.LEFT, padx=5)
