
from . import *

__all__ = ["process_manager", "file_manager", "cmd_control", "screen_viewer", 
           "shortcut_manager", "mouse_control", "keyboard_input", "message_sender", 
           "multitasking", "file_explorer"]
__version__ = "1.0.0"

print(f"Import ui version: {__version__}\n")

# 显式导出所有UI类
from .process_manager import ProcessManagerWindow
from .mouse_control import MouseControlWindow
from .keyboard_input import KeyboardInputWindow
from .shortcut_manager import ShortcutManagerWindow
from .screen_viewer import ScreenViewerWindow
from .multitasking import MultitaskingUI
from .cmd_control import CMDControlWindow
from .file_explorer import FileExplorerUI, FileManagerWindow

__all__ = [
    "ProcessManagerWindow", "MouseControlWindow", "KeyboardInputWindow",
    "ShortcutManagerWindow", "ScreenViewerWindow", "MultitaskingUI",
    "CMDControlWindow", "FileExplorerUI", "FileManagerWindow"
]
