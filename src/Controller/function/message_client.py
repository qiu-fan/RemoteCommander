from tkinter import messagebox

def send_message(parent, format, message, byte_len=1024, function=None, show_info=True):
    if parent.sock:
        try:
            parent.sock.send(f"{format}:{message}".encode())
            if show_info:
                parent.log(f"发送{format}指令成功")
        except Exception as e:
            parent.log(f"发送{format}指令失败: {str(e)}")
    else:
        parent.log("未连接")

"""这个函数是发送消息的，在指令发送中有所使用"""
