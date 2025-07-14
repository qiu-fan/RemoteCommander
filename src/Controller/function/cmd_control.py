import socket
import threading
class CMDController:
    def __init__(self, parent):
        self.parent = parent  # 弱引用保持者
        self.sock = parent.sock if hasattr(parent, 'sock') else None
        self.command_history = []
        self.history_index = 0
        self.stop_receive = True
        self.receive_thread = None

    def send_command(self, command=None):
        if not command:
            return
        self.parent.log(f"发送命令:{command}")
        
        protocol = f"CMD:{command}"
        try:
            self.sock.sendall(protocol.encode('utf-8'))
            self.stop_receive = False
            self.receive_thread = threading.Thread(
                target=self.receive_output,
                daemon=True
            )
            self.receive_thread.start()
        except Exception as e:
            self.append_output(f"[ERROR] {str(e)}\n")
        finally:
            self.cmd_entry.delete(0, tk.END)

    def receive_output(self):
        buffer = b""
        while not self.stop_receive:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break

                if b"[END]\n" in chunk:
                    data_part, _ = chunk.split(b"[END]\n", 1)
                    buffer += data_part
                    if buffer:
                        self.append_output(buffer.decode('gbk', errors='replace'))
                    break
                else:
                    buffer += chunk
                    self.append_output(buffer.decode('gbk', errors='replace'))
                    buffer = b""
            except BlockingIOError:
                time.sleep(0.1)
            except Exception as e:
                self.append_output(f"[ERROR] {str(e)}\n")
                break

    def on_close(self):
        self.stop_receive = True
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join()