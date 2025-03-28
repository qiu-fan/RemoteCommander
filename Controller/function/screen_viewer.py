import tkinter as tk
from tkinter import ttk
from Controller.message_client import send_message
import threading
import io
import socket
from PIL import Image, ImageTk

class ScreenViewWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("实时屏幕")
        self.geometry("800x600")
        self.running = False
        self.img_label = tk.Label(self)
        self.img_label.pack(fill=tk.BOTH, expand=True)

        # 控制按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.btn_start = ttk.Button(btn_frame, text="开始", command=self.start_stream)
        self.btn_start.pack(side=tk.LEFT)
        self.btn_stop = ttk.Button(btn_frame, text="停止", command=self.stop_stream)
        self.btn_stop.pack(side=tk.LEFT)

    def start_stream(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.receive_screen).start()

    def stop_stream(self):
        self.running = False

    def send_mouse_command(action, x, y):
        protocol = f"MOUSE:{action}:{x}:{y}"

    def send_keyboard_command(self, text):
        send_message(self.parent, "KEYBOARD", text)

    def receive_screen(self):
        try:
            self.parent.sock.sendall("SCREEN:START".encode('utf-8'))
            response = self.parent.sock.recv(1024)
            if response.decode('utf-8') != "[OK] 开始屏幕传输":
                raise Exception(f"启动失败({response.decode('utf-8')})")

            while self.running:
                # 读取图像长度（确保完整接收4字节）
                size_data = b''
                while len(size_data) < 4 and self.running:
                    chunk = self.parent.sock.recv(4 - len(size_data))
                    if not chunk:
                        break
                    size_data += chunk
                if len(size_data) != 4:
                    break
                size = int.from_bytes(size_data, 'big')

                # 读取图像数据（确保完整接收）
                img_data = b''
                remaining = size
                while remaining > 0 and self.running:
                    chunk = self.parent.sock.recv(4096)
                    if not chunk:
                        break
                    img_data += chunk
                    remaining -= len(chunk)

                if not self.running or len(img_data) != size:
                    break

                # 显示图像
                img = Image.open(io.BytesIO(img_data))
                img_tk = ImageTk.PhotoImage(img.resize((1440, 810)))
                self.img_label.config(image=img_tk)
                self.img_label.image = img_tk

                # 发送继续信号
                self.parent.sock.sendall(b"GO")
        except Exception as e:
            self.btn_start.config(state=tk.DISABLED)
            self.parent.log(f"屏幕传输错误: {str(e)}")
            # 清空缓冲区
            while True:
                try:
                    data = self.parent.sock.recv(4096)
                except socket.error as e:
                    self.btn_start.config(state=tk.NORMAL)
                    break

        finally:
            self.btn_start.config(state=tk.DISABLED)
            self.parent.sock.sendall("SCREEN:STOP".encode('utf-8'))
            # 清空缓冲区
            while True:
                try:
                    data = self.parent.sock.recv(4096)
                except socket.error as e:
                    self.btn_start.config(state=tk.NORMAL)
                    break