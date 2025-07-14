import tkinter as tk
from function.screen_viewer import ScreenViewer  # 依赖抽象
class ScreenViewerWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.controller = ScreenViewer(self)  # 组合代替继承
        
        # UI组件初始化
        self.setup_ui()
        self.create_bindings()

    def setup_ui(self):
        # 显示画布
        self.canvas = tk.Canvas(self, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 控制面板
        control_frame = tk.Frame(self)
        control_frame.pack(pady=5)
        
        self.quality_var = tk.IntVar(value=85)
        tk.Label(control_frame, text="画质:").pack(side=tk.LEFT)
        tk.Scale(
            control_frame,
            variable=self.quality_var,
            from_=10,
            to=95,
            orient=tk.HORIZONTAL,
            command=lambda v: self.controller.set_quality(int(v))
        ).pack(side=tk.LEFT, padx=5)
        
        self.start_btn = tk.Button(control_frame, text="启动", command=self.toggle_stream)
        self.start_btn.pack(side=tk.LEFT, padx=5)

    def create_bindings(self):
        self.bind('<Destroy>', lambda e: self.on_close())
        self.bind('<Configure>', self.handle_resize)

    def toggle_stream(self):
        """切换屏幕流状态"""
        if not self.controller.viewer_active:
            self.controller.start_stream()
            self.start_btn.config(text="停止")
        else:
            self.controller.stop_stream()
            self.start_btn.config(text="启动")

    def update_display(self, frame_data):
        """更新显示画面"""
        try:
            from PIL import Image, ImageTk
            import io
            
            # 解码JPEG数据
            image = Image.open(io.BytesIO(frame_data))
            # 调整大小适应窗口
            width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
            image = image.resize((width, height))
            # 更新显示
            photo = ImageTk.PhotoImage(image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self._current_photo = photo  # 保持引用防止被GC
        except Exception as e:
            self.controller.stop_stream()
            self.start_btn.config(text="启动")

    def handle_resize(self, _):
        """处理窗口尺寸变化"""
        pass

    def on_close(self):
        self.controller.stop_stream()
