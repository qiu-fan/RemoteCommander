import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import socket
import threading
import psutil
import time
from .base_window import BaseWindow

class FileManagerWindow(BaseWindow):
    def __init__(self, parent):
        super().__init__(parent, title="双面板文件管理器", geometry="1600x600")
        # 初始化路径
        self.remote_path = tk.StringVar(value="/")
        self.local_path = tk.StringVar(value=os.path.expanduser("~"))
        self.current_focus = "remote"  # 跟踪当前焦点面板
        self.remote_path_history = []  # 远程路径历史
        self.local_path_history = []   # 本地路径历史

        self.setup_style()

    def setup_style(self):
        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=25)
        self.style.configure("Path.TEntry", font=("Arial", 10))

    def create_widgets(self):
        # 主布局
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=5)

        self.btn_refresh = ttk.Button(toolbar, text="刷新", command=self.refresh, bootstyle=INFO)
        self.btn_refresh.pack(side=tk.LEFT, padx=2)
        self.btn_download = ttk.Button(toolbar, text="下载 →", command=self.download_file, bootstyle=SUCCESS)
        self.btn_download.pack(side=tk.LEFT, padx=2)
        self.btn_upload = ttk.Button(toolbar, text="← 上传", command=self.upload_file, bootstyle=PRIMARY)
        self.btn_upload.pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="新建文件夹", command=self.create_folder, bootstyle=SECONDARY).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(toolbar, text="删除", command=self.delete_item, bootstyle=DANGER).pack(side=tk.LEFT, padx=2)

        # 双面板布局
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # 远程文件面板
        remote_frame = ttk.Frame(paned_window)
        paned_window.add(remote_frame, weight=1)

        # 远程路径框
        remote_path_frame = ttk.Frame(remote_frame)
        remote_path_frame.pack(fill=tk.X, pady=5)
        ttk.Label(remote_path_frame, text="远程路径:").pack(side=tk.LEFT)
        self.remote_path_entry = ttk.Entry(remote_path_frame, textvariable=self.remote_path, width=50, style="Path.TEntry")
        self.remote_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(remote_path_frame, text="跳转", command=self.change_remote_path, bootstyle=PRIMARY).pack(side=tk.LEFT, padx=5)
        ttk.Button(remote_path_frame, text="复制", command=self.copy_remote_path, bootstyle=SECONDARY).pack(side=tk.LEFT, padx=5)
        ttk.Button(remote_path_frame, text="上一页", command=self.remote_prev_page, bootstyle=INFO).pack(side=tk.LEFT, padx=5)
        ttk.Button(remote_path_frame, text="上一层", command=self.remote_parent_dir, bootstyle=INFO).pack(side=tk.LEFT, padx=5)

        # 远程磁盘选择
        self.remote_disk_combo = ttk.Combobox(remote_path_frame, width=10)
        self.remote_disk_combo.pack(side=tk.LEFT, padx=5)
        self.remote_disk_combo.bind("<<ComboboxSelected>>", self.on_remote_disk_select)
        self.load_remote_disks()

        ttk.Label(remote_frame, text="远程文件系统", bootstyle=PRIMARY).pack(fill=tk.X)
        self.remote_tree = self.create_file_tree(remote_frame)
        self.remote_tree.bind("<FocusIn>", lambda e: setattr(self, "current_focus", "remote"))

        # 本地文件面板
        local_frame = ttk.Frame(paned_window)
        paned_window.add(local_frame, weight=1)

        # 本地路径框
        local_path_frame = ttk.Frame(local_frame)
        local_path_frame.pack(fill=tk.X, pady=5)
        ttk.Label(local_path_frame, text="本地路径:").pack(side=tk.LEFT)
        self.local_path_entry = ttk.Entry(local_path_frame, textvariable=self.local_path, width=50, style="Path.TEntry")
        self.local_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(local_path_frame, text="跳转", command=self.change_local_path, bootstyle=PRIMARY).pack(side=tk.LEFT, padx=5)
        ttk.Button(local_path_frame, text="复制", command=self.copy_local_path, bootstyle=SECONDARY).pack(side=tk.LEFT, padx=5)
        ttk.Button(local_path_frame, text="上一页", command=self.local_prev_page, bootstyle=INFO).pack(side=tk.LEFT, padx=5)
        ttk.Button(local_path_frame, text="上一层", command=self.local_parent_dir, bootstyle=INFO).pack(side=tk.LEFT, padx=5)

        # 本地磁盘选择
        self.local_disk_combo = ttk.Combobox(local_path_frame, width=10)
        self.local_disk_combo.pack(side=tk.LEFT, padx=5)
        self.local_disk_combo.bind("<<ComboboxSelected>>", self.on_local_disk_select)
        self.load_local_disks()

        ttk.Label(local_frame, text="本地文件系统", bootstyle=SECONDARY).pack(fill=tk.X)
        self.local_tree = self.create_file_tree(local_frame)
        self.local_tree.bind("<FocusIn>", lambda e: setattr(self, "current_focus", "local"))

        # 进度条和状态栏
        self.progress = ttk.Progressbar(main_frame, bootstyle=SUCCESS, maximum=100)
        self.progress.pack(fill=tk.X, pady=5)

        self.status_bar = ttk.Label(main_frame, text="就绪", bootstyle=SECONDARY)
        self.status_bar.pack(fill=tk.X)

        # 右键菜单
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="打开", command=self.open_item)
        self.context_menu.add_command(label="重命名", command=self.rename_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="属性", command=self.show_properties)

        # 事件绑定
        self.remote_tree.bind("<Double-1>", self.on_remote_double_click)
        self.local_tree.bind("<Double-1>", self.on_local_double_click)
        self.remote_tree.bind("<Button-3>", self.show_context_menu)
        self.local_tree.bind("<Button-3>", self.show_context_menu)

        # 初始化加载
        self.load_remote_files()
        self.load_local_files()

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
        tree.heading("size", text="大小", anchor=tk.W)
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

    def load_remote_files(self):
        self.remote_tree.delete(*self.remote_tree.get_children())
        try:
            self.parent.sock.sendall(f"FILE:LIST:{self.remote_path.get()}".encode())
            response = self.parent.sock.recv(4096).decode()

            if response.startswith("[ERROR]"):
                raise Exception(response.split("]", 1)[1].strip())

            for line in response.split("\n"):
                if line and line.count("|") == 3:  # 校验数据有效性
                    name, ftype, size, mtime = line.split("|", 3)
                    self.remote_tree.insert("", tk.END, values=(name, ftype, self.format_size(size), mtime))

        except Exception as e:
            messagebox.showerror("错误", f"加载远程文件失败: {str(e)}")

    def load_local_files(self):
        """加载本地文件列表"""
        self.local_tree.delete(*self.local_tree.get_children())
        try:
            path = self.local_path.get()
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                ftype = "文件夹" if os.path.isdir(full_path) else "文件"
                size = os.path.getsize(full_path) if ftype == "文件" else ""
                mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(full_path)))

                self.local_tree.insert("", tk.END, values=(
                    item,
                    ftype,
                    self.format_size(size),
                    mtime
                ))
        except Exception as e:
            messagebox.showerror("错误", f"加载本地文件失败: {str(e)}")

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

    # noinspection PyUnusedLocal
    def on_remote_double_click(self, event):
        item = self.remote_tree.selection()[0]
        name, ftype, *_ = self.remote_tree.item(item, "values")
        if ftype == "文件夹":
            new_path = os.path.join(self.remote_path.get(), name)
            self.remote_path.set(new_path)
            self.remote_path_history.append(new_path)
            self.load_remote_files()

    # noinspection PyUnusedLocal
    def on_local_double_click(self, event):
        item = self.local_tree.selection()[0]
        name, ftype, *_ = self.local_tree.item(item, "values")
        if ftype == "文件夹":
            new_path = os.path.join(self.local_path.get(), name)
            self.local_path.set(new_path)
            self.local_path_history.append(new_path)
            self.load_local_files()

    def show_context_menu(self, event):
        """显示右键菜单"""
        tree = event.widget
        try:
            item = tree.identify_row(event.y)
            tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
        except:
            pass

    def rename_item(self):
        """重命名选中的文件/文件夹"""
        if self.current_focus == "remote":
            tree = self.remote_tree
            current_path = self.remote_path.get()
            is_remote = True
        else:
            tree = self.local_tree
            current_path = self.local_path.get()
            is_remote = False

        selected = tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要重命名的项目")
            return

        old_name = tree.item(selected[0], "values")[0]
        new_name = simpledialog.askstring("重命名", "输入新名称:", initialvalue=old_name)

        if not new_name or new_name == old_name:
            return

        try:
            if is_remote:
                # 远程重命名协议
                old_path = os.path.join(current_path, old_name)
                new_path = os.path.join(current_path, new_name)
                protocol = f"FILE:RENAME:{old_path}->{new_path}"
                self.parent.sock.sendall(protocol.encode())
                response = self.parent.sock.recv(1024).decode()
                if "[OK]" not in response:
                    raise Exception(response)
            else:
                # 本地重命名
                old_path = os.path.join(current_path, old_name)
                new_path = os.path.join(current_path, new_name)
                os.rename(old_path, new_path)

            self.refresh()
            messagebox.showinfo("成功", "重命名完成")
        except Exception as e:
            messagebox.showerror("错误", f"重命名失败: {str(e)}")

    def open_item(self):
        """打开选中的文件/文件夹"""
        if self.current_focus == "remote":
            tree = self.remote_tree
            current_path = self.remote_path.get()
            is_remote = True
        else:
            tree = self.local_tree
            current_path = self.local_path.get()
            is_remote = False

        selected = tree.selection()
        if not selected:
            return

        name, ftype, *_ = tree.item(selected[0], "values")

        if ftype == "文件夹":
            if is_remote:
                self.remote_path.set(os.path.join(current_path, name))
                self.remote_path_history.append(os.path.join(current_path, name))
                self.load_remote_files()
            else:
                self.local_path.set(os.path.join(current_path, name))
                self.local_path_history.append(os.path.join(current_path, name))
                self.load_local_files()
        else:
            if is_remote:
                messagebox.showinfo("提示", "请在远程系统上打开文件")
            else:
                os.startfile(os.path.join(current_path, name))

    def show_properties(self):
        """显示文件属性"""
        if self.current_focus == "remote":
            tree = self.remote_tree
            current_path = self.remote_path.get()
            is_remote = True
        else:
            tree = self.local_tree
            current_path = self.local_path.get()
            is_remote = False

        selected = tree.selection()
        if not selected:
            return

        name, ftype, size, mtime = tree.item(selected[0], "values")

        if is_remote:
            path = f"远程路径: {os.path.join(current_path, name)}"
        else:
            path = f"本地路径: {os.path.join(current_path, name)}"

        message = f"{path}\n类型: {ftype}\n大小: {size}\n修改时间: {mtime}"
        messagebox.showinfo("属性", message)

    def download_file(self):
        """下载选中的远程文件"""
        selected = self.remote_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要下载的文件")
            return

        remote_item = self.remote_tree.item(selected[0])
        name, ftype, *_ = remote_item["values"]

        if ftype == "文件夹":
            messagebox.showwarning("提示", "暂不支持文件夹下载")
            return

        # 选择本地保存路径
        local_path = filedialog.asksaveasfilename(
            initialdir=self.local_path.get(),
            initialfile=name
        )
        if not local_path:
            return

        try:
            # 发送下载协议
            remote_path = os.path.join(self.remote_path.get(), name)
            protocol = f"FILE:DOWNLOAD:{remote_path}->{local_path}"
            self.parent.sock.sendall(protocol.encode())

            # 接收文件内容
            with open(local_path, "wb") as f:
                while True:
                    data = self.parent.sock.recv(4096)
                    if data.endswith(b"[END]"):
                        f.write(data[:-5])
                        break
                    f.write(data)

            messagebox.showinfo("成功", "文件下载完成")
            self.load_local_files()
        except Exception as e:
            messagebox.showerror("错误", f"下载失败: {str(e)}")

    def upload_file(self):
        """上传本地选中的文件"""
        selected = self.local_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要上传的文件")
            return

        local_item = self.local_tree.item(selected[0])
        name, ftype, *_ = local_item["values"]

        if ftype == "文件夹":
            messagebox.showwarning("提示", "暂不支持文件夹上传")
            return

        # 获取本地文件路径
        local_path = os.path.join(self.local_path.get(), name)

        try:
            # 发送文件传输协议
            with open(local_path, "rb") as f:
                file_data = f.read()
                protocol = f"FILE:UPLOAD:{name}:{len(file_data)}"
                self.parent.sock.sendall(protocol.encode())

                # 等待准备响应
                response = self.parent.sock.recv(1024).decode()
                if response != "[OK] 准备接收文件":
                    raise Exception("服务器未就绪")

                # 发送文件内容
                self.parent.sock.sendall(file_data)

                # 获取最终响应
                final_response = self.parent.sock.recv(1024).decode()
                if "[OK]" in final_response:
                    messagebox.showinfo("成功", "文件上传完成")
                    self.load_remote_files()
                else:
                    raise Exception(final_response)
        except Exception as e:
            messagebox.showerror("错误", f"上传失败: {str(e)}")

    def refresh(self):
        """刷新文件列表"""
        self.load_remote_files()
        self.load_local_files()
        self.status_bar.config(text="文件列表已刷新")

    def delete_item(self):
        """删除选中的项目"""
        if self.current_focus == "remote":
            tree = self.remote_tree
            current_path = self.remote_path.get()
            is_remote = True
        else:
            tree = self.local_tree
            current_path = self.local_path.get()
            is_remote = False

        selected = tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要删除的项目")
            return

        name, ftype, *_ = tree.item(selected[0], "values")

        if not messagebox.askyesno("确认", f"确定要删除 {name} 吗？"):
            return

        try:
            if is_remote:
                # 远程删除协议
                path = os.path.join(current_path, name)
                protocol = f"FILE:DELETE:{path}"
                self.parent.sock.sendall(protocol.encode())
                response = self.parent.sock.recv(1024).decode()
                if "[OK]" not in response:
                    raise Exception(response)
            else:
                # 本地删除
                path = os.path.join(current_path, name)
                if ftype == "文件夹":
                    os.rmdir(path)
                else:
                    os.remove(path)

            self.refresh()
            messagebox.showinfo("成功", "删除完成")
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}")

    def create_folder(self):
        """新建文件夹"""
        folder_name = simpledialog.askstring("新建文件夹", "请输入文件夹名称:")
        if not folder_name:
            return

        if self.current_focus == "remote":
            # 远程创建文件夹
            path = os.path.join(self.remote_path.get(), folder_name)
            protocol = f"FILE:MKDIR:{path}"
            try:
                self.parent.sock.sendall(protocol.encode())
                response = self.parent.sock.recv(1024).decode()
                if "[OK]" not in response:
                    raise Exception(response)
                self.load_remote_files()
                messagebox.showinfo("成功", "文件夹创建成功")
            except Exception as e:
                messagebox.showerror("错误", f"创建失败: {str(e)}")
        else:
            # 本地创建文件夹
            path = os.path.join(self.local_path.get(), folder_name)
            try:
                os.mkdir(path)
                self.load_local_files()
                messagebox.showinfo("成功", "文件夹创建成功")
            except Exception as e:
                messagebox.showerror("错误", f"创建失败: {str(e)}")

    def change_remote_path(self):
        """跳转到远程路径"""
        path = self.remote_path.get()
        try:
            # 确保路径存在
            if not os.path.exists(path):
                raise Exception("路径不存在")

            self.parent.sock.sendall(f"FILE:LIST:{path}".encode())
            response = self.parent.sock.recv(4096).decode()
            if response.startswith("[ERROR]"):
                raise Exception(response.split("]", 1)[1].strip())
            self.remote_path.set(path)
            self.remote_path_history.append(path)
            self.load_remote_files()
        except Exception as e:
            messagebox.showerror("错误", f"跳转失败: {str(e)}")

    def change_local_path(self):
        """跳转到本地路径"""
        path = self.local_path.get()
        try:
            if not os.path.exists(path):
                raise Exception("路径不存在")
            self.local_path.set(path)
            self.local_path_history.append(path)
            self.load_local_files()
        except Exception as e:
            messagebox.showerror("错误", f"跳转失败: {str(e)}")

    def copy_remote_path(self):
        """复制远程路径"""
        self.clipboard_clear()
        self.clipboard_append(self.remote_path.get())
        messagebox.showinfo("成功", "路径已复制到剪贴板")

    def copy_local_path(self):
        """复制本地路径"""
        self.clipboard_clear()
        self.clipboard_append(self.local_path.get())
        messagebox.showinfo("成功", "路径已复制到剪贴板")

    def load_local_disks(self):
        """加载本地磁盘"""
        disks = []
        for disk in psutil.disk_partitions():
            if disk.mountpoint:
                disks.append(disk.mountpoint)
        self.local_disk_combo['values'] = disks
        if disks:
            self.local_disk_combo.set(disks[0])

    def load_remote_disks(self):
        try:
            self.parent.sock.sendall("FILE:DISK".encode())
            response = self.parent.sock.recv(1024).decode()
            if response.startswith("DISK|"):
                disks = response[5:].split("|")
                self.remote_disk_combo['values'] = disks
                if disks:
                    self.remote_disk_combo.set(disks[0])
        except Exception as e:
            messagebox.showerror("错误", f"加载远程磁盘失败: {str(e)}")

    def on_local_disk_select(self, event):
        """本地磁盘选择事件"""
        disk = self.local_disk_combo.get()
        if disk:
            self.local_path.set(disk)
            self.load_local_files()

    def on_remote_disk_select(self, event):
        """远程磁盘选择事件"""
        disk = self.remote_disk_combo.get()
        if disk:
            self.remote_path.set(disk)
            self.load_remote_files()

    def remote_prev_page(self):
        """远程文件管理器的上一页"""
        if len(self.remote_path_history) > 1:
            self.remote_path_history.pop()
            if self.remote_path_history:
                path = self.remote_path_history[-1]
                self.remote_path.set(path)
                self.load_remote_files()

    def local_prev_page(self):
        """本地文件管理器的上一页"""
        if len(self.local_path_history) > 1:
            self.local_path_history.pop()
            if self.local_path_history:
                path = self.local_path_history[-1]
                self.local_path.set(path)
                self.load_local_files()

    def remote_parent_dir(self):
        """远程文件管理器的上一层"""
        path = self.remote_path.get()
        parent_path = os.path.dirname(path)
        if parent_path:
            self.remote_path.set(parent_path)
            self.load_remote_files()

    def local_parent_dir(self):
        """本地文件管理器的上一层"""
        path = self.local_path.get()
        parent_path = os.path.dirname(path)
        if parent_path:
            self.local_path.set(parent_path)
            self.load_local_files()


if __name__ == "__main__":
    class MockParent:
        def __init__(self):
            class MockSocket:
                def sendall(self, *args): pass

                def recv(self, *args): return b"[OK] Test Response"

            self.sock = MockSocket()


    root = tk.Tk()
    FileManagerWindow(MockParent())
    root.mainloop()