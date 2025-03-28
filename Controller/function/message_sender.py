import tkinter as tk
from tkinter import messagebox
from Controller.message_client import send_message
from tkinter import ttk



class SendMessage(tk.Toplevel):
    def __init__(self, parent):
        self.parent = parent

        super().__init__(parent.root)

        self.title("发送消息")
        self.geometry("450x100")

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=10)
        ttk.Label(self, text="输入内容:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_msg = ttk.Entry(self, width=30)
        self.entry_msg.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="发送", command=self.send_alert).pack(side=tk.LEFT, padx=5)

    # 发送消息的函数
    def send_alert(self):
        message = self.entry_msg.get()
        if not message:
            messagebox.showerror("错误", "请输入提示消息")
            return

        send_message(self.parent, "ALERT", message)

        self.parent.log(f"发送消息成功:{message}")