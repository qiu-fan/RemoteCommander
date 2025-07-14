
import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from ttkbootstrap.constants import *
import psutil
from ui.file_explorer_ui import FileExplorerUI
from function.file_operations import FileOperations

class FileManagerWindow(FileExplorerUI):
    def __init__(self, parent):
        self.parent = parent
        
        # 初始化路径相关变量
        self.remote_path = tk.StringVar(value="/home")
        self.local_path = tk.StringVar(value=os.path.expanduser("~"))
        self.current_focus = "remote"
        self.remote_path_history = []
        self.local_path_history = []
        
        # 创建文件操作实例
        self.file_ops = FileOperations(self.parent.sock)
        
        # 设置回调
        self.file_ops.set_callbacks(self.set_progress, self.set_status)
        
        # 调用父类初始化方法
        super().__init__(parent, self.file_ops)
        
        # 设置窗口标题和大小
        self.master.title("双面板文件管理器")
        self.master.geometry("1600x600")
        
        # 绑定事件
        self.bind_events()
        
        # 加载初始数据
        self.load_remote_disks()
        self.load_local_disks()
        self.load_remote_files()
        self.load_local_files()

    def bind_events(self):
        # 文件树事件绑定
        self.remote_tree.bind("<Double-1>", self.on_remote_double_click)
        self.local_tree.bind("<Double-1>", self.on_local_double_click)
        self.remote_tree.bind("<Button-3>", self.show_context_menu)
        self.local_tree.bind("<Button-3>", self.show_context_menu)
        
        # 路径输入框回车事件
        self.remote_path_entry.bind("<Return>", lambda e: self.change_remote_path())
        self.local_path_entry.bind("<Return>", lambda e: self.change_local_path())

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

    def load_remote_files(self):
        self.remote_tree.delete(*self.remote_tree.get_children())
        files = self.file_ops.list_files(self.remote_path.get())
        for name, ftype, size, mtime in files:
            self.remote_tree.insert("", tk.END, values=(name, ftype, self.format_size(size), mtime))

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
            self.show_message("错误", f"加载本地文件失败: {str(e)}")

    def show_context_menu(self, event):
        """显示右键菜单"""
        tree = event.widget
        try:
            item = tree.identify_row(event.y)
            tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

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
            self.show_message("提示", "请选择要重命名的项目")
            return

        old_name = tree.item(selected[0], "values")[0]
        new_name = simpledialog.askstring("重命名", "输入新名称:", initialvalue=old_name)

        if not new_name or new_name == old_name:
            return

        try:
            if is_remote:
                old_path = os.path.join(current_path, old_name)
                new_path = os.path.join(current_path, new_name)
                if self.file_ops.rename_item(old_path, new_path):
                    self.refresh()
                    self.show_message("成功", "重命名完成")
            else:
                old_path = os.path.join(current_path, old_name)
                new_path = os.path.join(current_path, new_name)
                os.rename(old_path, new_path)
                self.refresh()
                self.show_message("成功", "重命名完成")
        except Exception as e:
            self.show_message(f"错误", f"重命名失败: {str(e)}", type="error")

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
                self.show_message("提示", "请在远程系统上打开文件")
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
        self.show_message("属性", message)

    def download_file(self):
        """下载选中的远程文件"""
        selected = self.remote_tree.selection()
        if not selected:
            self.show_message("提示", "请选择要下载的文件")
            return

        remote_item = self.remote_tree.item(selected[0])
        name, ftype, *_ = remote_item["values"]

        if ftype == "文件夹":
            self.show_message("提示", "暂不支持文件夹下载")
            return

        local_path = filedialog.asksaveasfilename(
            initialdir=self.local_path.get(),
            initialfile=name
        )
        if not local_path:
            return

        try:
            if self.file_ops.download_file(os.path.join(self.remote_path.get(), name), local_path):
                self.show_message("成功", "文件下载完成")
                self.load_local_files()
        except Exception as e:
            self.show_message("错误", f"下载失败: {str(e)}", type="error")

    def upload_file(self):
        """上传本地选中的文件"""
        selected = self.local_tree.selection()
        if not selected:
            self.show_message("提示", "请选择要上传的文件")
            return

        local_item = self.local_tree.item(selected[0])
        name, ftype, *_ = local_item["values"]

        if ftype == "文件夹":
            self.show_message("提示", "暂不支持文件夹上传")
            return

        local_path = os.path.join(self.local_path.get(), name)

        try:
            if self.file_ops.upload_file(local_path, name):
                self.show_message("成功", "文件上传完成")
                self.load_remote_files()
        except Exception as e:
            self.show_message("错误", f"上传失败: {str(e)}", type="error")

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
            self.show_message("提示", "请选择要删除的项目")
            return

        name, ftype, *_ = tree.item(selected[0], "values")

        if not self.confirm_action("确认", f"确定要删除 {name} 吗？"):
            return

        try:
            if is_remote:
                path = os.path.join(current_path, name)
                if self.file_ops.delete_item(path):
                    self.refresh()
                    self.show_message("成功", "删除完成")
            else:
                path = os.path.join(current_path, name)
                if ftype == "文件夹":
                    os.rmdir(path)
                else:
                    os.remove(path)
                self.refresh()
                self.show_message("成功", "删除完成")
        except Exception as e:
            self.show_message("错误", f"删除失败: {str(e)}", type="error")

    def create_folder(self):
        """新建文件夹"""
        folder_name = simpledialog.askstring("新建文件夹", "请输入文件夹名称:")
        if not folder_name:
            return

        if self.current_focus == "remote":
            path = os.path.join(self.remote_path.get(), folder_name)
            if self.file_ops.create_folder(path):
                self.load_remote_files()
                self.show_message("成功", "文件夹创建成功")
        else:
            path = os.path.join(self.local_path.get(), folder_name)
            try:
                os.mkdir(path)
                self.load_local_files()
                self.show_message("成功", "文件夹创建成功")
            except Exception as e:
                self.show_message("错误", f"创建失败: {str(e)}", type="error")

    def change_remote_path(self):
        """跳转到远程路径"""
        path = self.remote_path.get()
        try:
            if not os.path.exists(path):
                raise Exception("路径不存在")

            self.file_ops.execute_protocol(f"FILE:LIST:{path}", path)
            self.remote_path.set(path)
            self.remote_path_history.append(path)
            self.load_remote_files()
        except Exception as e:
            self.show_message("错误", f"跳转失败: {str(e)}", type="error")

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
            self.show_message("错误", f"跳转失败: {str(e)}", type="error")

    def copy_remote_path(self):
        """复制远程路径"""
        self.master.clipboard_clear()
        self.master.clipboard_append(self.remote_path.get())
        self.show_message("成功", "路径已复制到剪贴板")

    def copy_local_path(self):
        """复制本地路径"""
        self.master.clipboard_clear()
        self.master.clipboard_append(self.local_path.get())
        self.show_message("成功", "路径已复制到剪贴板")

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
        """加载远程磁盘"""
        disks = self.file_ops.get_disks()
        if disks:
            self.remote_disk_combo['values'] = disks
            if disks:
                self.remote_disk_combo.set(disks[0])

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


    # 创建Tk实例并设置为主窗口
    root = tk.Tk()
    # 将root作为parent传递给FileManagerWindow
    app = FileManagerWindow(root)
    root.mainloop()