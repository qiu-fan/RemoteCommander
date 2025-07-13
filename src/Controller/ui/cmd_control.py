import tkinter as tk
from tkinter import ttk
from src.controller.function.message_client import send_message  # 修复导入路径
import threading
import time
from tkinter import scrolledtext

class CMDControlWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("CMD控制台")
        self.geometry("700x600")
        self.create_widgets()
        self.command_history = []
        self.history_index = -1
        self.receive_thread = None
        self.stop_receive = False

    def create_widgets(self):
        # 输出区域
        self.output_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled')
        self.output_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 输入区域
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.cmd_entry = ttk.Entry(input_frame)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.cmd_entry.bind("<Return>", self.send_command)
        self.cmd_entry.bind("<Up>", self.history_prev)
        self.cmd_entry.bind("<Down>", self.history_next)

        ttk.Button(input_frame, text="发送", command=self.send_command).pack(side=tk.LEFT)
        ttk.Button(input_frame, text="清屏", command=self.clear_output).pack(side=tk.LEFT)

    def send_command(self):
        command = self.cmd_entry.get().strip()
        if not command:
            return
        self.parent.log(f"发送命令:{command}")

        self.command_history.append(command)
        self.history_index = len(self.command_history)

        self.append_output(f"Controller >> {command}\n")

        protocol = f"CMD:{command}"
        try:
            self.parent.sock.sendall(protocol.encode('utf-8'))
            # 启动接收线程
            self.stop_receive = False
            self.receive_thread = threading.Thread(target=self.receive_output)
            self.receive_thread.start()
        except Exception as e:
            self.append_output(f"[ERROR] {str(e)}\n")
        finally:
            self.cmd_entry.delete(0, tk.END)

    def receive_output(self):
        """ 新増：独立线程接收输出 """
        buffer = b""
        while not self.stop_receive:
            try:
                chunk = self.parent.sock.recv(4096)
                if not chunk:
                    break

                # 分离结束标记
                if b"[END]\n" in chunk:
                    data_part, end_part = chunk.split(b"[END]\n", 1)
                    buffer += data_part
                    if buffer:
                        self.append_output(buffer.decode('gbk', errors='replace'))
                    break
                else:
                    buffer += chunk
                    # 实时显示当前数据
                    self.append_output(buffer.decode('gbk', errors='replace'))
                    buffer = b""
            except BlockingIOError:
                time.sleep(0.1)
            except Exception as e:
                self.append_output(f"[ERROR] {str(e)}\n")
                break

    def append_output(self, text):
        self.output_area.after(0, self._update_output, text)

    def _update_output(self, text):
        """ 实际更新UI的方法 """
        self.output_area.configure(state='normal')
        self.output_area.insert(tk.END, text)
        self.output_area.configure(state='disabled')
        self.output_area.see(tk.END)

    def clear_output(self):
        self.output_area.configure(state='normal')
        self.output_area.delete(1.0, tk.END)
        self.output_area.configure(state='disabled')

    def history_prev(self, _):
        if self.command_history:
            self.history_index = max(0, self.history_index - 1)
            self.cmd_entry.delete(0, tk.END)
            self.cmd_entry.insert(0, self.command_history[self.history_index])

    def history_next(self, _):
        if self.command_history:
            self.history_index = min(len(self.command_history), self.history_index + 1)
            if self.history_index < len(self.command_history):
                self.cmd_entry.delete(0, tk.END)
                self.cmd_entry.insert(0, self.command_history[self.history_index])

    def on_close(self):
        """ 新增：窗口关闭时停止接收线程 """
        self.stop_receive = True
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join()
        self.destroy()
