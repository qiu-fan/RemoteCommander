import tkinter as tk
import threading
import time


def send_command(self, command=None):
    if not command:
        return
    self.parent.log(f"发送命令:{command}")

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

def on_close(self):
    """ 新增：窗口关闭时停止接收线程 """
    self.stop_receive = True
    if self.receive_thread and self.receive_thread.is_alive():
        self.receive_thread.join()
    self.destroy()