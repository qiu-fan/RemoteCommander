import socket
class ProcessManager:
    def __init__(self, parent):
        self.parent = parent
        self.sock = parent.sock if hasattr(parent, 'sock') else None

    def get_process_list(self):
        """获取远程主机进程列表"""
        try:
            self.sock.sendall(b"PROCESS:LIST")
            response = self.sock.recv(65536)  # 使用更大的缓冲区接收数据
            return self._parse_process_data(response)
        except Exception as e:
            self.parent.append_output(f"[ERROR] {str(e)}\n")
            return []

    def terminate_process(self, pid):
        """终止指定PID的进程"""
        try:
            protocol = f"PROCESS:KILL:{pid}"
            self.sock.sendall(protocol.encode('utf-8'))
            return True
        except Exception as e:
            self.parent.append_output(f"[ERROR] {str(e)}\n")
            return False

    def _parse_process_data(self, data):
        """解析进程数据"""
        try:
            if not data:
                return []
            lines = data.decode('utf-8', errors='replace').split('\n')
            processes = []
            for line in lines:
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 3:
                        processes.append({
                            'pid': int(parts[0]),
                            'name': parts[1],
                            'cpu': float(parts[2])
                        })
            return processes
        except Exception as e:
            self.parent.append_output(f"[ERROR] 解析进程数据失败: {str(e)}\n")
            return []