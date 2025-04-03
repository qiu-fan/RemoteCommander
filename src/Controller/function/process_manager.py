import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from function.message_client import send_message

class ProcessManagerWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("进程管理")
        self.geometry("1000x400")

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
        send_message(self.parent, "PROC:LIST", f"{self.filter_keyword}:{self.current_page}",
                     byte_len=4096, function=self.update_process_list, show_info=False)

    def update_process_list(self, response):
        if "|DATA:" not in response:
            messagebox.showerror("错误", "无效响应格式")
            return

        header, data = response.split("|DATA:", 1)
        params = {k: v for k, v in [p.split(':') for p in header.split('|') if ':' in p]}

        self.tree.delete(*self.tree.get_children())
        for line in data.split('\n'):
            print(line)
            if line.count('|') == 4:
                pid, name, user, cpu, mem = line.split('|')
                self.tree.insert("", tk.END, values=(pid, name, user, cpu, mem))

        self.page_label.config(text=f"第{params['PAGE']}页 已装载{params['TOTAL']}条")

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