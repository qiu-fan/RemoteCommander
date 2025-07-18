import time
import tkinter as tk

def bezier_x(t, p1x, p2x):
    """计算三次贝塞尔曲线的x坐标。"""
    return 3 * p1x * t * (1 - t)**2 + 3 * p2x * t**2 * (1 - t) + t**3

def bezier_y(t, p1y, p2y):
    """计算三次贝塞尔曲线的y坐标。"""
    return 3 * p1y * t * (1 - t)**2 + 3 * p2y * t**2 * (1 - t) + t**3

def solve_bezier_t(t_input, p1x, p2x, epsilon=1e-6, max_iterations=50):
    """使用二分法求解贝塞尔曲线参数t，使得x(t) = t_input。"""
    if t_input <= 0.0:
        return 0.0
    if t_input >= 1.0:
        return 1.0

    low, high = 0.0, 1.0
    t_param = (low + high) / 2

    for _ in range(max_iterations):
        x = bezier_x(t_param, p1x, p2x)
        if abs(x - t_input) < epsilon:
            break
        if x < t_input:
            low = t_param
        else:
            high = t_param
        t_param = (low + high) / 2
    return t_param

def cubic_bezier_easing(t_input, p1x, p1y, p2x, p2y):
    """根据贝塞尔曲线参数计算缓动进度。"""
    t_param = solve_bezier_t(t_input, p1x, p2x)
    return bezier_y(t_param, p1y, p2y)

def animate(widget, start, end, duration, bezier_params, set_value, on_complete=None):
    """
    执行动画效果。
    
    :param widget: Tkinter控件
    :param start: 起始值
    :param end: 结束值
    :param duration: 动画持续时间（秒）
    :param bezier_params: 三次贝塞尔曲线参数 (p1x, p1y, p2x, p2y)
    :param set_value: 回调函数，用于设置属性值
    :param on_complete: 动画完成后的回调函数
    """
    p1x, p1y, p2x, p2y = bezier_params
    start_time = time.time()

    def update():
        current_time = time.time() - start_time
        t = current_time / duration
        if t >= 1.0:
            set_value(end)
            if on_complete:
                on_complete()
            return
        progress = cubic_bezier_easing(t, p1x, p1y, p2x, p2y)
        current_val = start + (end - start) * progress
        if current_val >= end:
            if on_complete:
                on_complete()
                set_value(current_val)
                return
        widget.after(16, update)

    update()

# 预定义的缓动曲线参数
EASE_IN = (0.42, 0, 1.0, 1.0)          # 缓慢开始
EASE_OUT = (0, 0, 0.08, 1.0)            # 缓慢结束
EASE_IN_OUT = (0.42, 0, 0.58, 1.0)      # 缓慢开始和结束
LINEAR = (0, 0, 1.0, 1.0)               # 线性变化
EASE = (0.25, 0.1, 0.25, 1.0)           # 默认缓动效果

# 示例使用
if __name__ == "__main__":
    root = tk.Tk()
    root.title("")
    root.geometry("1000x200")

    canvas = tk.Canvas(root, width=1000, height=200)
    canvas.pack()

    # 创建一个矩形作为动画对象
    rect = canvas.create_rectangle(50, 75, 100, 125, fill="blue")

    def update_position(progress):
        """更新矩形水平位置。"""
        x = 50 + progress * 500  # 从50移动到250
        canvas.coords(rect, x, 75, x + 50, 125)

    # 启动动画：从0到1的进度，持续2秒，应用ease-out效果
    def ex_animate(root):
        animate(
            widget=root,
            start=0,
            end=1,
            duration=0.5,
            bezier_params=EASE_IN_OUT,
            set_value=update_position,
            on_complete=lambda: print("动画完成!")
        )

    btn_replay = tk.Button(text="重播", command=ex_animate(root))
    btn_replay.pack(side=tk.TOP, fill=tk.X, pady=2)
   
    root.mainloop()


