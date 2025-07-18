class ScreenViewer:
    def __init__(self, parent):
        self.parent = parent
        # 确保parent有sock属性且不为None
        if hasattr(parent, 'sock') and parent.sock is not None:
            self.sock = parent.sock
        else:
            self.sock = None
        self.viewer_active = False
        self.quality = 85  # 默认画质质量

    def start_stream(self):
        """启动屏幕流传输"""
        try:
            # 验证sock有效性
            if not self.sock or not hasattr(self.sock, 'send'):
                raise ConnectionError("Socket连接未建立或已断开")
            
            protocol = f"SCREEN:START:{self.quality}"
            self.sock.sendall(protocol.encode('utf-8'))
            self.viewer_active = True
            threading.Thread(
                target=self._receive_frames,
                daemon=True
            ).start()
        except Exception as e:
            # 安全地记录错误并显示用户友好的提示
            self._safe_log(f"[ERROR] {str(e)}\n")
            if hasattr(self.parent, 'window') and hasattr(self.parent.window, 'show_error'):
                self.parent.window.show_error("屏幕流错误", str(e))
            else:
                messagebox.showerror("错误", str(e))  # 回退到标准对话框

    def stop_stream(self):
        """停止屏幕流传输"""
        try:
            if not self.sock:
                raise ConnectionError("Socket连接未建立")
            
            protocol = f"SCREEN:STOP"
            self.sock.sendall(protocol.encode('utf-8'))
            self.viewer_active = False
        except Exception as e:
            self._safe_log(f"[ERROR] {str(e)}\n")

    def set_quality(self, quality):
        """设置传输画质"""
        self.quality = max(10, min(95, quality))
        try:
            if not self.sock:
                raise ConnectionError("Socket连接未建立")
            
            protocol = f"SCREEN:QUALITY:{self.quality}"
            self.sock.sendall(protocol.encode('utf-8'))
        except Exception as e:
            self._safe_log(f"[ERROR] {str(e)}\n")

    # 在ScreenViewer类中添加辅助方法
    def _safe_log(self, message):
        """安全地记录日志，避免引用错误"""
        try:
            # 尝试通过组合模式访问主窗口日志
            if hasattr(self.parent, 'window') and hasattr(self.parent.window, 'log'):
                self.parent.window.log(message)
            elif hasattr(self.parent, 'log'):
                self.parent.log(message)
            else:
                print(message)  # 最终回退到控制台输出
        except Exception:
            print(message)