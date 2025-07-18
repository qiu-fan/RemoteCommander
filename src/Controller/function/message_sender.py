from message_client import send_message
# 发送消息的函数
def send_alert(self):
    message = self.entry_msg.get()
    if not message:
        self.show_error("请输入提示消息")
        return

    send_message(self.parent, "ALERT", message)

    self.parent.log(f"发送消息成功:{message}")