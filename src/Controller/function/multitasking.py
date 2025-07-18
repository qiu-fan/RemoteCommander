import tkinter as tk
import threading
import time
from tkinter import messagebox

class MultitaskingCore:
    def __init__(self, parent):
        self.parent = parent  # 主窗口实例
        self.tasks = []
        self.running = False
        self.current_selected = None

        # 任务协议映射（保持与UI模块一致）
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

    def add_task(self, task_type, entries):
        if task_type not in self.task_protocols:
            messagebox.showerror("错误", "请选择有效的任务类型")
            return

        params = {}
        protocol = self.task_protocols[task_type]
        try:
            for i, param in enumerate(protocol["params"]):
                value = entries[i].get()
                if not value:
                    raise ValueError(f"请输入 {param}")
                params[param] = value

            if not protocol["validate"](params):
                raise ValueError("参数验证失败")

            self.tasks.append({"type": task_type, "params": params})
            return True

        except Exception as e:
            messagebox.showerror("输入错误", str(e))
            return False

    def load_selected_task(self, selection):
        if not selection:
            self.parent.inspector_status.config(text="无检查")
            self.parent.edit_frame.pack_forget()
            return

        self.current_selected = selection[0]
        task = self.tasks[self.current_selected]

        self.parent.inspector_status.config(text="")
        self.parent.edit_frame.pack(fill=tk.BOTH, expand=True)

        self.parent.edit_task_type.set(task["type"])
        self.parent.update_edit_params()

        entries = self.parent.edit_entries
        for entry, value in zip(entries, task["params"].values()):
            entry.delete(0, tk.END)
            entry.insert(0, str(value))

    def modify_task(self):
        if self.current_selected is None:
            return

        task_type = self.parent.edit_task_type.get()
        protocol = self.task_protocols.get(task_type)
        if not protocol:
            return

        params = {}
        entries = self.parent.edit_entries

        try:
            for i, param in enumerate(protocol["params"]):
                value = entries[i].get()
                if not value:
                    raise ValueError(f"请输入 {param}")
                params[param] = value

            if not protocol["validate"](params):
                raise ValueError("参数验证失败")

            self.tasks[self.current_selected] = {"type": task_type, "params": params}
            self.parent.task_list.delete(self.current_selected)
            self.parent.task_list.insert(self.current_selected, f"{task_type}: {params}")
            self.parent.task_list.selection_set(self.current_selected)

        except Exception as e:
            messagebox.showerror("修改错误", str(e))

    def delete_task(self):
        if self.current_selected is None:
            return

        self.tasks.pop(self.current_selected)
        self.parent.task_list.delete(self.current_selected)
        self.current_selected = None
        self.parent.inspector_status.config(text="未选择任务")
        self.parent.edit_frame.pack_forget()

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

            self.parent.status_bar.config(text=f"{task_type} 执行成功 ({cost:.1f}s)")
            self.parent.log(f"[任务] 执行 {task_type}: {response}")

        except Exception as e:
            self.parent.status_bar.config(text=f"{task_type} 失败: {str(e)}", bootstyle="danger")
            self.parent.log(f"[任务] 错误 {task_type}: {str(e)}")
            raise

    def run_tasks(self):
        if not self.tasks:
            messagebox.showwarning("提示", "请先添加任务")
            return

        if not messagebox.askyesno("确认", "确定要执行所有任务吗？", parent=self.parent):
            return

        def task_runner():
            try:
                total = len(self.tasks)
                for idx, task in enumerate(self.tasks, 1):
                    self.parent.status_bar.config(text=f"正在执行 ({idx}/{total}): {task['type']}", bootstyle="info")
                    self.dispatch_task(task)
                    time.sleep(0.3)

                self.parent.status_bar.config(text="所有任务执行完成", bootstyle="success")

            except Exception as e:
                self.parent.status_bar.config(text=f"执行中断: {str(e)}", bootstyle="danger")
            finally:
                self.parent.start_btn.config(state=tk.NORMAL)

        threading.Thread(target=task_runner, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = MultitaskingCore(root)
    root.mainloop()