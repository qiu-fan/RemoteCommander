
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from ttkbootstrap.constants import *


class FileExplorerUI:
    def __init__(self, parent, file_ops):
        self.parent = parent
        self.file_ops = file_ops
        self.root = parent  # 添加root属性作为parent的别名
        self.create_widgets()
        self.setup_style()

    def setup_style(self):
        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=25)
        self.style.configure("Path.TEntry", font=("Arial", 10))

    def create_widgets(self):
        # 主布局
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 工具栏
        self.toolbar = ttk.Frame(self.main_frame)
        self.toolbar.pack(fill=tk.X, pady=5)

        self.btn_refresh = ttk.Button(self.toolbar, text="刷新", command=self.refresh, bootstyle=INFO)
        self.btn_refresh.pack(side=tk.LEFT, padx=2)
        self.btn_download = ttk.Button(self.toolbar, text="下载 →", command=self.download_file, bootstyle=SUCCESS)
        self.btn_download.pack(side=tk.LEFT, padx=2)
        self.btn_upload = ttk.Button(self.toolbar, text="← 上传", command=self.upload_file, bootstyle=PRIMARY)
        self.btn_upload.pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="新建文件夹", command=self.create_folder, bootstyle=SECONDARY).pack(side=tk.LEFT, padx=2)
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(self.toolbar, text="删除", command=self.delete_item, bootstyle=DANGER).pack(side=tk.LEFT, padx=2)

        # 双面板布局
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # 远程文件面板
        remote_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(remote_frame, weight=1)

        # 远程路径框
        self.remote_path_frame = ttk.Frame(remote_frame)
        self.remote_path_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.remote_path_frame, text="远程路径:").pack(side=tk.LEFT)
        self.remote_path = tk.StringVar(value="/home")
        self.remote_path_entry = ttk.Entry(self.remote_path_frame, textvariable=self.remote_path, width=50, style="Path.TEntry")
        self.remote_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(self.remote_path_frame, text="跳转", command=self.change_remote_path, bootstyle=PRIMARY).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.remote_path_frame, text="复制", command=self.copy_remote_path, bootstyle=SECONDARY).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.remote_path_frame, text="上一页", command=self.remote_prev_page, bootstyle=INFO).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.remote_path_frame, text="上一层", command=self.remote_parent_dir, bootstyle=INFO).pack(side=tk.LEFT, padx=5)

        # 远程磁盘选择
        self.remote_disk_combo = ttk.Combobox(self.remote_path_frame, width=10)
        self.remote_disk_combo.pack(side=tk.LEFT, padx=5)
        self.remote_disk_combo.bind("<<ComboboxSelected>>", self.on_remote_disk_select)

        ttk.Label(remote_frame, text="远程文件系统", bootstyle=PRIMARY).pack(fill=tk.X)
        self.remote_tree = self.create_file_tree(remote_frame)
        self.remote_tree.bind("<FocusIn>", lambda e: setattr(self, "current_focus", "remote"))

        # 本地文件面板
        local_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(local_frame, weight=1)

        # 本地路径框
        self.local_path_frame = ttk.Frame(local_frame)
        self.local_path_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.local_path_frame, text="本地路径:").pack(side=tk.LEFT)
        self.local_path = tk.StringVar(value=os.path.expanduser("~"))
        self.local_path_entry = ttk.Entry(self.local_path_frame, textvariable=self.local_path, width=50, style="Path.TEntry")
        self.local_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(self.local_path_frame, text="跳转", command=self.change_local_path, bootstyle=PRIMARY).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.local_path_frame, text="复制", command=self.copy_local_path, bootstyle=SECONDARY).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.local_path_frame, text="上一页", command=self.local_prev_page, bootstyle=INFO).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.local_path_frame, text="上一层", command=self.local_parent_dir, bootstyle=INFO).pack(side=tk.LEFT, padx=5)

        # 本地磁盘选择
        self.local_disk_combo = ttk.Combobox(self.local_path_frame, width=10)
        self.local_disk_combo.pack(side=tk.LEFT, padx=5)
        self.local_disk_combo.bind("<<ComboboxSelected>>", self.on_local_disk_select)

        ttk.Label(local_frame, text="本地文件系统", bootstyle=SECONDARY).pack(fill=tk.X)
        self.local_tree = self.create_file_tree(local_frame)
        self.local_tree.bind("<FocusIn>", lambda e: setattr(self, "current_focus", "local"))

        # 进度条和状态栏
        self.progress = ttk.Progressbar(self.main_frame, bootstyle=SUCCESS, maximum=100)
        self.progress.pack(fill=tk.X, pady=5)

        self.status_bar = ttk.Label(self.main_frame, text="就绪", bootstyle=SECONDARY)
        self.status_bar.pack(fill=tk.X)

        # 右键菜单
        self.context_menu = tk.Menu(self.parent, tearoff=0)
        self.context_menu.add_command(label="打开", command=self.open_item)
        self.context_menu.add_command(label="重命名", command=self.rename_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="属性", command=self.show_properties)

        # 初始化加载
        self.current_focus = "remote"
        self.remote_path_history = []
        self.local_path_history = []

    def create_file_tree(self, parent):
        """创建文件树组件"""
        tree = ttk.Treeview(
            parent,
            columns=("name", "type", "size", "modified"),
            show="headings",
            selectmode=tk.BROWSE
        )

        # 配置列
        tree.heading("name", text="名称", anchor=tk.W)
        tree.heading("type", text="类型", anchor=tk.W)
        tree.heading("size", text="大小", anchor=tk.E)
        tree.heading("modified", text="修改时间", anchor=tk.W)

        tree.column("name", width=300, anchor=tk.W)
        tree.column("type", width=100, anchor=tk.W)
        tree.column("size", width=100, anchor=tk.E)
        tree.column("modified", width=150, anchor=tk.W)

        # 滚动条
        scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scroll.set)

        tree.pack(fill=tk.BOTH, expand=True)
        return tree

    def format_size(self, size):
        """格式化文件大小显示"""
        try:
            size = int(size)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"
        except:
            return ""

    def set_progress(self, value):
        self.progress['value'] = value

    def set_status(self, message):
        self.status_bar.config(text=message)

    def refresh(self):
        """刷新文件列表"""
        self.load_remote_files()
        self.load_local_files()
        self.set_status("文件列表已刷新")

    def show_message(self, title, message, type="info"):
        if type == "error":
            messagebox.showerror(title, message)
        elif type == "warning":
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)

    def confirm_action(self, title, message):
        return messagebox.askyesno(title, message)
