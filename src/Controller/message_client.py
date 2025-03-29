from tkinter import messagebox

def send_message(parent, format, message, byte_len=1024, function=None, show_info=True):
    protocol = f"{format}:{message}"
    try:
        parent.sock.sendall(protocol.encode('utf-8'))
        response = parent.sock.recv(byte_len).decode()
        if show_info:
            parent.log(f"{response}")
        else:
            function(response)

    except Exception as e:
        messagebox.showerror("错误", str(e))

"""这个函数是发送消息的，在指令发送中有所使用"""
