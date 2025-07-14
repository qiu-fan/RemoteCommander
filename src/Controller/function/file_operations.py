
import os
import socket

class FileOperations:
    def __init__(self, sock):
        self.sock = sock
        self.progress_callback = None
        self.status_callback = None

    def set_callbacks(self, progress_callback, status_callback):
        self.progress_callback = progress_callback
        self.status_callback = status_callback

    def execute_protocol(self, protocol, path=None):
        try:
            self.sock.sendall(protocol.encode())
            response = self.sock.recv(4096).decode()
            if response.startswith("[ERROR]"):
                raise Exception(response.split("]", 1)[1].strip())
            return response
        except Exception as e:
            self._handle_error(f"执行协议失败: {str(e)}", path)
            return None

    def list_files(self, path):
        response = self.execute_protocol(f"FILE:LIST:{path}", path)
        if response and not response.startswith("[ERROR]"):
            return [line.split("|", 3) for line in response.split("\n") if line.count("|") == 3]
        return []

    def download_file(self, remote_path, local_path):
        protocol = f"FILE:DOWNLOAD:{remote_path}->{local_path}"
        try:
            self.sock.sendall(protocol.encode())
            with open(local_path, "wb") as f:
                while True:
                    data = self.sock.recv(4096)
                    if data.endswith(b"[END]"):
                        f.write(data[:-5])
                        break
                    f.write(data)
            return True
        except Exception as e:
            self._handle_error(f"下载失败: {str(e)}", remote_path)
            return False

    def upload_file(self, local_path, remote_name):
        try:
            with open(local_path, "rb") as f:
                file_data = f.read()
                protocol = f"FILE:UPLOAD:{remote_name}:{len(file_data)}"
                self.sock.sendall(protocol.encode())

                response = self.sock.recv(1024).decode()
                if response != "[OK] 准备接收文件":
                    raise Exception("服务器未就绪")

                self.sock.sendall(file_data)
                final_response = self.sock.recv(1024).decode()
                return "[OK]" in final_response
        except Exception as e:
            self._handle_error(f"上传失败: {str(e)}", local_path)
            return False

    def delete_item(self, path):
        return "[OK]" in self.execute_protocol(f"FILE:DELETE:{path}", path)

    def create_folder(self, path):
        return "[OK]" in self.execute_protocol(f"FILE:MKDIR:{path}", path)

    def rename_item(self, old_path, new_path):
        return "[OK]" in self.execute_protocol(f"FILE:RENAME:{old_path}->{new_path}", old_path)

    def get_disks(self):
        response = self.execute_protocol("FILE:DISK")
        if response and response.startswith("DISK|"):
            return response[5:].split("|")
        return []

    def _handle_error(self, message, path=None):
        if self.status_callback:
            self.status_callback(f"错误: {message}")
        print(f"Error in file operation ({path}): {message}")
