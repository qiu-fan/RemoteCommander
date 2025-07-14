# RemoteCommander V9.0.0 🚀

[![Version](https://img.shields.io/badge/Release-v9.0.0-blue.svg)]()
[![License](https://img.shields.io/badge/License-GPL3.0-green.svg)]()

跨平台远程控制解决方案（控制器/被控端），提供安全的设备管理能力。**请严格遵守法律法规，仅用于授权环境！**


## ✨ 核心功能

### 控制矩阵
| **模块**       | **能力**                              | **协议**  |
|----------------|--------------------------------------|-----------|
| 设备发现       | UDP广播扫描局域网存活主机              | UDP 9998  |
| 会话管理       | 安全TCP连接/版本校验/心跳检测           | TCP 9999  |
| 远程控制       | 鼠标轨迹/键盘输入/剪贴板操作            | TCP       |
| 进程管理       | 进程列表查看/强制终止/启动新进程         | TCP       |
| 文件系统       | 文件上传下载/目录浏览/跨设备转移         | TCP       |
| 系统命令       | CMD命令执行与实时回显                   | TCP       |
| 屏幕流         | JPEG实时传输（可调画质）                | TCP       |

### 安全设计
- 🔒 双因素版本校验（控制端v9.0.0 ↔ 被控端v9.0.0）
- 🛡️ 系统进程保护（自动拦截危险操作）
- 📁 安全目录限制（禁止访问系统关键路径）
- 🔑 传输校验机制（CRC32校验文件完整性）

## 🛠️ 快速部署

### 环境要求
- Python 3.8+ 
- Windows 10/11 或 Linux（实验性支持）
- 开放端口：9999(TCP)/9998(UDP)

```bash
# 安装全量依赖
pip install pyautogui psutil pillow tkinter numpy
```

### 启动被控端（后台服务）
```bash
# Windows
python src/target/main.py --daemon

# Linux 
nohup python3 src/target/main.py > /dev/null 2>&1 &
```

### 启动控制端（GUI界面）
```bash
python src/Controller/main.py
```

## 📚 开发指南

### 项目结构
```
RemoteCommander/
├── src/                          # 项目源码
  ├── Controller/                 # 控制端实现
  │   ├── function/               # 功能模块
  │   │   ├── mouse_control.py    # 鼠标控制
  │   │   ├── file_manager.py     # 文件管理
  |   |   ...                      # 更多功能模块
  │   └── main.py                 # 主界面
  ├── target/
  │   └── main.py                 # 控制端
  └── test/
      └── test.py                 # 测试
```

### 扩展开发
```python
# 添加新指令示例
def handle_custom_command(data):
    if data == "/custom":
        return execute_custom_action()
        
# 在handle_connection中注册
if data.startswith("/custom"):
    handle_custom_command(data)
```

## ⚠️ 安全警告

- 1.禁止修改被控端安全策略
- 2.生产环境务必修改默认端口
- 3.文件传输目录默认：D:\dol（自动创建）

## 👥 贡献者
- **架构设计**: Qiu_Fan[[✉️](mailto:3592916761@qq.com)]
- **部分功能开发**: Coco[[📧](mailto:3881898540@qq.com)]

[![Stars](https://img.shields.io/github/stars/qiu-fan/RemoteCommander.svg)](https://github.com/qiu-fan/RemoteCommander)
[![Forks](https://img.shields.io/github/forks/qiu-fan/RemoteCommander.svg)](https://github.com/qiu-fan/RemoteCommander)