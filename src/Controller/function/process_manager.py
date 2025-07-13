from message_client import send_message

def load_processes(self):
    send_message(self.parent, "PROC:LIST", f"{self.filter_keyword}:{self.current_page}",
                                byte_len=4096, function=self.update_process_list, show_info=False)

def update_process_list(self, response):
    if "|DATA:" not in response:
        self.show_error("无效响应格式")
        return

    header, data = response.split("|DATA:", 1)
    params = {k: v for k, v in [p.split(':') for p in header.split('|') if ':' in p]}

    self.tree.delete(*self.tree.get_children())
    for line in data.split('\n'):
        print(line)
        if line.count('|') == 4:
            pid, name, user, cpu, mem = line.split('|')
            self.tree.insert("", tk.END, values=(pid, name, user, cpu, mem))

    self.page_label.config(text=f"第{params['PAGE']}页 已装载{params['TOTAL']}条")