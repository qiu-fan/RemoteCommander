from ..main import RemoteCommanderGUI
import tkinter as tk
from file_manager import FileManagerWindow
from tkinter import messagebox
import os
from tkinter import ttk

class DeploymentGUI(object):
    def __init__(self, parent: RemoteCommanderGUI):
        self.parent = parent
        self.parent.root.geometry("500x500")

        # 扫描开机自启文件夹,并显示当前部署状态
        self.scan_auto_boot_folder()

        # 创建部署按钮
        btn_frame = tk.Frame(self.parent.root)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(btn_frame, text="部署", command=self.deploy).pack(side=tk.LEFT, padx=5)

        # 部署源文件输入框
        tk.Label(btn_frame, text="部署源文件:").pack(side=tk.LEFT, padx=5)
        self.deploy_path = tk.Entry(btn_frame, width=20)
        self.deploy_path.pack(side=tk.LEFT, padx=5)

        # 文件传输进度条
        self.progress = ttk.Progressbar(self.parent.root, mode='determinate')
        self.progress.pack(side=tk.BOTTOM, fill=tk.X)


    def send_file(self, filepath):
        filepath = filepath
        self.parent.log("文件传输开始")
        if not filepath:
            messagebox.showerror("错误", "请选择要传输的文件")
            return

        try:
            with open(filepath, 'rb') as f:
                filesize = len(f.read())
                filename = os.path.basename(filepath)
                protocol = f"FILE:RECEIVE:{filename}:{filesize}"

                # 发送文件头信息
                self._send_protocol(protocol, expect_response="[OK] 准备接收文件")

                # 重置进度条
                self.progress['maximum'] = filesize
                self.progress['value'] = 0

                # 发送文件内容
                with open(filepath, 'rb') as f_:
                    while True:
                        chunk = f_.read(4096)
                        if not chunk:
                            break
                        self.parent.sock.sendall(chunk)
                        self.progress['value'] += len(chunk)
                        self.update_idletasks()

                # 获取最终响应
                self.parent.sock.recv(1024).decode()
                self.parent.log("文件传输完成")
        except Exception as e:
            messagebox.showerror("错误", str(e))


    def deploy(self):
        # 添加到开机自启文件夹
        FileManagerWindow(self.parent).send_file()


    def scan_auto_boot_folder(self):
        pass







