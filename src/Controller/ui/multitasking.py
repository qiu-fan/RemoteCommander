import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from function.multitasking import MultitaskingCore  # 导入功能模块

class MultitaskingUI(tk.Toplevel):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent  # 主窗口实例
        self.title("自动化任务管理器")
        self.geometry("800x600")
        
        # 初始化功能核心
        self.core = MultitaskingCore(parent)
        
        self.create_widgets()
        self.setup_style()

    def setup_style(self):
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6)
        self.style.configure("danger.TButton", foreground="white", background="#dc3545")
        self.style.configure("success.TButton", foreground="white", background="#28a745")

    def create_widgets(self):
        # 主布局框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧任务列表
        left_frame = ttk.Frame(main_frame, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        ttk.Label(left_frame, text="任务列表", font=("Helvetica", 10, "bold")).pack(pady=5)
        self.task_list = tk.Listbox(left_frame, width=25, height=15, font=("Helvetica", 10))
        self.task_list.pack(fill=tk.BOTH, expand=True)
        self.task_list.bind("<<ListboxSelect>>", self.load_selected_task)

        # 中间添加区域
        center_frame = ttk.Frame(main_frame)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        ttk.Label(center_frame, text="添加新任务", font=("Helvetica", 12, "bold")).pack(pady=5)

        # 任务类型选择
        type_frame = ttk.Frame(center_frame)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(type_frame, text="任务类型:").pack(side=tk.LEFT)
        self.add_task_type = ttk.Combobox(type_frame, values=list(self.core.task_protocols.keys()))  # 使用功能模块的协议
        self.add_task_type.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.add_task_type.bind("<<ComboboxSelected>>", self.update_add_params)

        # 参数输入区域
        self.add_param_frame = ttk.Frame(center_frame)
        self.add_param_frame.pack(fill=tk.BOTH, pady=10)

        # 添加按钮
        ttk.Button(center_frame, text="添加任务", command=self.add_task, bootstyle=SUCCESS).pack(pady=10)

        # ... 其他UI组件保持不变 ...

    def add_task(self):
        task_type = self.add_task_type.get()
        if task_type not in self.core.task_protocols:
            messagebox.showerror("错误", "请选择有效的任务类型")
            return

        # 使用功能模块的方法
        if self.core.add_task(task_type, self.add_entries):
            self.task_list.insert(tk.END, f"{task_type}: {self.core.tasks[-1]['params']}")
            self.clear_add_fields()