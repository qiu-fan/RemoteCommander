import tkinter as tk
from tkinter import ttk

class BaseWindow(tk.Toplevel):
    def __init__(self, parent, title="", geometry=""):
        super().__init__(parent.root)
        self.parent = parent
        self.title(title)
        self.geometry(geometry)
        self.create_widgets()

    def create_widgets(self):
        # 由子类实现具体布局
        pass

    def create_toolbar(self, buttons):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        for btn_text, command in buttons:
            ttk.Button(toolbar, text=btn_text, command=command).pack(
                side=tk.LEFT, padx=2
            )
        return toolbar

    def create_treeview(self, columns):
        tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return tree

    def show_error(self, message):
        from tkinter import messagebox
        messagebox.showerror("错误", message)

    def show_info(self, message):
        from tkinter import messagebox
        messagebox.showinfo("提示", message)