import tkinter as tk
from function.process_manager import ProcessManager  # 依赖抽象
class ProcessManagerWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.controller = ProcessManager(self)
        
        # UI组件初始化
        self.setup_ui()
        self.create_bindings()

    def setup_ui(self):
        # 进程列表显示区域
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 按钮区域
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)
        
        self.refresh_btn = tk.Button(btn_frame, text="刷新", command=self.refresh_list)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.kill_btn = tk.Button(btn_frame, text="终止进程", command=self.terminate_process)
        self.kill_btn.pack(side=tk.LEFT, padx=5)

    def create_bindings(self):
        self.bind('<Destroy>', lambda e: self.on_close())
        self.listbox.bind('<Double-1>', lambda e: self.terminate_process())

    def refresh_list(self):
        """刷新进程列表"""
        self.listbox.delete(0, tk.END)
        processes = self.controller.get_process_list()
        for proc in processes:
            self.listbox.insert(tk.END, f"{proc['pid']} - {proc['name']} - CPU:{proc['cpu']:.1f}%")

    def terminate_process(self):
        """终止选中进程"""
        selection = self.listbox.curselection()
        if selection:
            pid = int(self.listbox.get(selection[0]).split(' ')[0])
            if self.controller.terminate_process(pid):
                self.refresh_list()

    def on_close(self):
        pass