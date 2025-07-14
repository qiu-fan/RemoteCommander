import socket
import threading
class ScreenViewer:
    def __init__(self, parent):
        self.parent = parent
        self.sock = parent.sock if hasattr(parent, 'sock') else None
        self.viewer_active = False
        self.quality = 85  # 默认画质质量

    def start_stream(self):
        """启动屏幕流传输"""
        try:
            protocol = f"SCREEN:START:{self.quality}"
            self.sock.sendall(protocol.encode('utf-8'))
            self.viewer_active = True
            threading.Thread(
                target=self._receive_frames,
                daemon=True
            ).start()
        except Exception as e:
            self.parent.append_output(f"[ERROR] {str(e)}\n")
            self.viewer_active = False

    def stop_stream(self):
        """停止屏幕流传输"""
        try:
            self.sock.sendall(b"SCREEN:STOP")
            self.viewer_active = False
        except Exception as e:
            self.parent.append_output(f"[ERROR] {str(e)}\n")

    def set_quality(self, quality):
        """设置传输画质"""
        self.quality = max(10, min(95, quality))
        try:
            protocol = f"SCREEN:QUALITY:{self.quality}"
            self.sock.sendall(protocol.encode('utf-8'))
        except Exception as e:
            self.parent.append_output(f"[ERROR] {str(e)}\n")

    def _receive_frames(self):
        """接收并处理屏幕帧"""
        while self.viewer_active:
            try:
                size_data = self.sock.recv(4)
                if not size_data:
                    break
                
                # 解析帧大小
                import struct
                frame_size = struct.unpack('>I', size_data)[0]
                
                # 接收完整帧数据
                frame_data = b""
                while len(frame_data) < frame_size:
                    chunk = self.sock.recv(frame_size - len(frame_data))
                    if not chunk:
                        break
                    frame_data += chunk
                
                if len(frame_data) == frame_size:
                    # 在UI线程更新显示
                    self.parent.update_display(frame_data)
            except Exception as e:
                self.parent.append_output(f"[ERROR] {str(e)}\n")
                self.viewer_active = False
                break