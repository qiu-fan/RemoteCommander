import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class ShortcutManagerWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("快捷键管理")
        self.geometry("400x300")

        self.create_widgets()

    def create_widgets(self):
        # 快捷键列表
        self.tree = ttk.Treeview(self, columns=("command", "action"), show="headings")
        self.tree.heading("command", text="快捷键")
        self.tree.heading("action", text="操作")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 加载快捷键
        self.load_shortcuts()

        # 操作按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="执行", command=self.execute_shortcut).pack(side=tk.LEFT)

    def load_shortcuts(self):
        shortcuts = [
            ("/exit", "Alt + F4"),
            ("/c-a", "Ctrl + A"),
            ("/c-c", "Ctrl + C"),
            ("/space", "Space"),
            ("/enter", "Enter"),
            ("/tab", "Tab"),
            ("/up", "Up Arrow"),
            ("/down", "Down Arrow"),
            ("/left", "Left Arrow"),
            ("/right", "Right Arrow"),
            ("/home", "Home"),
            ("/end", "End"),
            ("/pageup", "Page Up"),
            ("/pagedown", "Page Down"),
            ("/insert", "Insert"),
            ("/delete", "Delete"),
        ]
        for cmd, action in shortcuts:
            self.tree.insert("", tk.END, values=(cmd, action))

    def execute_shortcut(self):
        selected = self.tree.selection()
        if selected:
            cmd = self.tree.item(selected[0])['values'][0]
            try:
                self.parent.sock.sendall(cmd.encode('utf-8'))
                response = self.parent.sock.recv(1024).decode()
                self.parent.log(f"执行快捷键: {cmd} -> {response}")
            except Exception as e:
                messagebox.showerror("错误", str(e))