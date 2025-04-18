# src/Controller/function/multitasking.py
import tkinter as tk
import threading
import time
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class Multitasking(tk.Toplevel):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent  # 主窗口实例
        self.title("自动化任务管理器")
        self.geometry("800x600")

        # 初始化任务存储列表
        self.tasks = []
        self.running = False
        self.current_selected = None

        # 任务协议映射
        self.task_protocols = {
            "发送消息": {
                "params": ["消息内容"],
                "protocol": lambda p: f"ALERT:{p['消息内容']}",
                "validate": lambda p: len(p["消息内容"]) <= 140
            },
            "等待时间": {
                "params": ["秒数"],
                "protocol": lambda p: f"CMD:timeout /t {p['秒数']} /nobreak",
                "validate": lambda p: p["秒数"].isdigit()
            },
            "移动鼠标": {
                "params": ["X坐标", "Y坐标"],
                "protocol": lambda p: f"MOUSE:MOVE:{p['X坐标']}:{p['Y坐标']}",
                "validate": lambda p: p["X坐标"].isdigit() and p["Y坐标"].isdigit()
            },
            "点击鼠标": {
                "params": ["X坐标", "Y坐标"],
                "protocol": lambda p: f"MOUSE:CLICK:{p['X坐标']}:{p['Y坐标']}",
                "validate": lambda p: p["X坐标"].isdigit() and p["Y坐标"].isdigit()
            },
            "输入文本": {
                "params": ["文本内容"],
                "protocol": lambda p: f"KEYBOARD:{p['文本内容']}",
                "validate": lambda p: len(p["文本内容"]) > 0
            },
            "执行cmd命令": {
                "params": ["命令"],
                "protocol": lambda p: f"CMD:{p['命令']}",
                "validate": lambda p: len(p["命令"]) > 0
            },
            "打开文件": {
                "params": ["文件路径"],
                "protocol": lambda p: f"OPENFILE:{p['文件路径']}",
                "validate": lambda p: len(p["文件路径"]) > 0
            },
            "移动文件": {
                "params": ["源文件路径", "目标文件路径"],
                "protocol": lambda p: f"MOVEFILE:{p['源文件路径']}->{p['目标文件路径']}",
                "validate": lambda p: p["源文件路径"] != p["目标文件路径"]
            },
            "复制文件": {
                "params": ["源文件路径", "目标文件路径"],
                "protocol": lambda p: f"FILE:COPY:{p['源文件路径']}->{p['目标文件路径']}",
                "validate": lambda p: p["源文件路径"] != p["目标文件路径"]
            },
            "删除文件": {
                "params": ["文件路径"],
                "protocol": lambda p: f"FILE:DELETE:{p['文件路径']}",
                "validate": lambda p: len(p["文件路径"]) > 0
            },
            "执行按键": {
                "params": ["按键名称"],
                "protocol": lambda p: f"PRESS:{p['按键名称']}",
                "validate": lambda p: len(p["按键名称"]) > 0
            },
            "关闭进程": {
                "params": ["进程PID"],
                "protocol": lambda p: f"PROC:KILL:{p['进程PID']}",
                "validate": lambda p: p["进程PID"].isdigit()
            }

        }

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
        left_frame.pack(side=LEFT, fill=Y, padx=5)

        ttk.Label(left_frame, text="任务列表", font=("Helvetica", 10, "bold")).pack(pady=5)
        self.task_list = tk.Listbox(left_frame, width=25, height=15, font=("Helvetica", 10))
        self.task_list.pack(fill=BOTH, expand=True)
        self.task_list.bind("<<ListboxSelect>>", self.load_selected_task)

        # 中间添加区域
        center_frame = ttk.Frame(main_frame)
        center_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=10)

        ttk.Label(center_frame, text="添加新任务", font=("Helvetica", 12, "bold")).pack(pady=5)

        # 任务类型选择
        type_frame = ttk.Frame(center_frame)
        type_frame.pack(fill=X, pady=5)
        ttk.Label(type_frame, text="任务类型:").pack(side=LEFT)
        self.add_task_type = ttk.Combobox(type_frame, values=list(self.task_protocols.keys()))
        self.add_task_type.pack(side=RIGHT, fill=X, expand=True)
        self.add_task_type.bind("<<ComboboxSelected>>", self.update_add_params)

        # 参数输入区域
        self.add_param_frame = ttk.Frame(center_frame)
        self.add_param_frame.pack(fill=BOTH, pady=10)

        # 添加按钮
        ttk.Button(center_frame, text="添加任务", command=self.add_task, bootstyle=SUCCESS).pack(pady=10)


        # 右侧检查器
        right_frame = ttk.Frame(main_frame, width=250)
        right_frame.pack(side=RIGHT, fill=Y, padx=5)

        ttk.Label(right_frame, text="检查器", font=("Helvetica", 12, "bold")).pack(pady=5)
        self.inspector_status = ttk.Label(right_frame, text="无检查项目", bootstyle=SECONDARY)
        self.inspector_status.pack(pady=5)

        self.edit_frame = ttk.Frame(right_frame)

        # 任务类型显示
        type_info = ttk.Frame(self.edit_frame)
        type_info.pack(fill=X, pady=5)
        # ttk.Label(type_info, text="任务类型:").pack(side=LEFT)
        self.edit_task_type = ttk.Combobox(type_info, state="readonly")
        self.edit_task_type.pack(side=RIGHT, fill=X, expand=True)
        self.edit_task_type.bind("<<ComboboxSelected>>", self.update_edit_params)

        # 参数编辑区域
        self.edit_param_frame = ttk.Frame(self.edit_frame)
        self.edit_param_frame.pack(fill=BOTH, pady=10)

        # 操作按钮
        btn_frame = ttk.Frame(self.edit_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="保存修改", command=self.modify_task, bootstyle=INFO, width=10).pack(side=LEFT,
                                                                                                        padx=5)
        ttk.Button(btn_frame, text="删除任务", command=self.delete_task, bootstyle=DANGER, width=10).pack(side=RIGHT,
                                                                                                          padx=5)

        # 状态栏和控制按钮
        control_frame = ttk.Frame(self)
        control_frame.pack(side=BOTTOM, fill=X, padx=10, pady=10)

        self.status_bar = ttk.Label(control_frame, text="就绪", bootstyle=SECONDARY)
        self.status_bar.pack(side=LEFT)

        self.start_btn = ttk.Button(control_frame, text="开始执行", command=self.run_tasks, bootstyle=PRIMARY)
        self.start_btn.pack(side=RIGHT)

        # 初始化参数
        self.update_add_params()
        self.update_edit_params()

    def create_param_fields(self, parent, params, is_edit=False):
        for widget in parent.winfo_children():
            widget.destroy()

        entries = []
        for param in params:
            frame = ttk.Frame(parent)
            frame.pack(fill=X, pady=2)
            ttk.Label(frame, text=f"{param}:").pack(side=LEFT)
            entry = ttk.Entry(frame)
            entry.pack(side=RIGHT, fill=X, expand=True)
            entries.append(entry)

            if is_edit:
                entry.insert(0, "")
        return entries

    def update_add_params(self, event=None):
        task_type = self.add_task_type.get()
        if task_type in self.task_protocols:
            params = self.task_protocols[task_type]["params"]
            self.add_entries = self.create_param_fields(self.add_param_frame, params)

    def update_edit_params(self, event=None):
        task_type = self.edit_task_type.get()
        if task_type in self.task_protocols:
            params = self.task_protocols[task_type]["params"]
            self.edit_entries = self.create_param_fields(self.edit_param_frame, params, is_edit=True)

    def add_task(self):
        task_type = self.add_task_type.get()
        if task_type not in self.task_protocols:
            messagebox.showerror("错误", "请选择有效的任务类型")
            return

        params = {}
        protocol = self.task_protocols[task_type]
        entries = self.add_entries

        try:
            for i, param in enumerate(protocol["params"]):
                value = entries[i].get()
                if not value:
                    raise ValueError(f"请输入 {param}")
                params[param] = value

            if not protocol["validate"](params):
                raise ValueError("参数验证失败")

            self.tasks.append({"type": task_type, "params": params})
            self.task_list.insert(END, f"{task_type}: {params}")
            self.clear_add_fields()

        except Exception as e:
            messagebox.showerror("输入错误", str(e))

    def clear_add_fields(self):
        self.add_task_type.set("")
        for entry in self.add_entries:
            entry.delete(0, END)

    def load_selected_task(self, event):
        selection = self.task_list.curselection()
        if not selection:
            self.inspector_status.config(text="无检查")
            self.edit_frame.pack_forget()
            return

        self.current_selected = selection[0]
        task = self.tasks[self.current_selected]

        self.inspector_status.config(text="")
        self.edit_frame.pack(fill=BOTH, expand=True)

        self.edit_task_type.set(task["type"])
        self.update_edit_params()

        entries = self.edit_entries
        for entry, value in zip(entries, task["params"].values()):
            entry.delete(0, END)
            entry.insert(0, str(value))

    def modify_task(self):
        if self.current_selected is None:
            return

        task_type = self.edit_task_type.get()
        protocol = self.task_protocols.get(task_type)
        if not protocol:
            return

        params = {}
        entries = self.edit_entries

        try:
            for i, param in enumerate(protocol["params"]):
                value = entries[i].get()
                if not value:
                    raise ValueError(f"请输入 {param}")
                params[param] = value

            if not protocol["validate"](params):
                raise ValueError("参数验证失败")

            self.tasks[self.current_selected] = {"type": task_type, "params": params}
            self.task_list.delete(self.current_selected)
            self.task_list.insert(self.current_selected, f"{task_type}: {params}")
            self.task_list.selection_set(self.current_selected)

        except Exception as e:
            messagebox.showerror("修改错误", str(e))

    def delete_task(self):
        if self.current_selected is None:
            return

        # if messagebox.askyesno("确认", "确定要删除这个任务吗？", parent=self):
        self.tasks.pop(self.current_selected)
        self.task_list.delete(self.current_selected)
        self.current_selected = None
        self.inspector_status.config(text="未选择任务")
        self.edit_frame.pack_forget()

    def send_command(self, command):
        try:
            if not self.parent.connected:
                raise ConnectionError("未连接到目标机")

            self.parent.sock.sendall(command.encode("utf-8"))
            response = self.parent.sock.recv(4096).decode("utf-8")

            if response.startswith("[ERROR]"):
                error_msg = response.split("]", 1)[1].strip()
                raise RuntimeError(error_msg)

            return response

        except Exception as e:
            self.parent.log(f"指令执行失败: {str(e)}")
            raise

    def dispatch_task(self, task):
        try:
            task_type = task["type"]
            protocol = self.task_protocols[task_type]
            command = protocol["protocol"](task["params"])

            start_time = time.time()
            response = self.send_command(command)
            cost = time.time() - start_time

            self.status_bar.config(text=f"{task_type} 执行成功 ({cost:.1f}s)")
            self.parent.log(f"[任务] 执行 {task_type}: {response}")

        except Exception as e:
            self.status_bar.config(text=f"{task_type} 失败: {str(e)}", bootstyle=DANGER)
            self.parent.log(f"[任务] 错误 {task_type}: {str(e)}")
            raise

    def run_tasks(self):
        if not self.tasks:
            messagebox.showwarning("提示", "请先添加任务")
            return

        if not messagebox.askyesno("确认", "确定要执行所有任务吗？", parent=self):
            return

        def task_runner():
            self.start_btn.config(state=DISABLED)
            try:
                total = len(self.tasks)
                for idx, task in enumerate(self.tasks, 1):
                    self.status_bar.config(text=f"正在执行 ({idx}/{total}): {task['type']}", bootstyle=INFO)
                    self.dispatch_task(task)
                    time.sleep(0.3)

                self.status_bar.config(text=f"所有任务执行完成", bootstyle=SUCCESS)

            except Exception as e:
                self.status_bar.config(text=f"执行中断: {str(e)}", bootstyle=DANGER)
            finally:
                self.start_btn.config(state=NORMAL)

        threading.Thread(target=task_runner, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = Multitasking(root)
    root.mainloop()