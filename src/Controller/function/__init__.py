from . import *
# 文件操作相关功能
from .file_operations import FileOperations

__all__ = [
    "cmd_control",
    "controller_manager",
    "file_explorer",
    "file_manager",
    "keyboard_input",
    "message_client",
    "message_sender",
    "mouse_control",
    "multitasking",  # 添加新模块
    "process_manager",
    "screen_viewer",
    "shortcut_manager",
    # 添加文件操作模块
    "FileOperations",
]


__version__ = "1.0.0"

print(f"Import function version: {__version__}\n")

