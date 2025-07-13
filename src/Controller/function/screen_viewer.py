from message_client import send_message
import io
import socket
from PIL import Image, ImageTk


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

            # 发送继续信号
            self.parent.sock.sendall(b"GO")
    except Exception as e:
        self.parent.log(f"屏幕传输错误: {str(e)}")
        # 清空缓冲区
        while True:
            try:
                data = self.parent.sock.recv(4096)
            except socket.error as e:
                break

    finally:
        self.parent.sock.sendall("SCREEN:STOP".encode('utf-8'))
        # 清空缓冲区
        while True:
            try:
                data = self.parent.sock.recv(4096)
            except socket.error as e:
                break