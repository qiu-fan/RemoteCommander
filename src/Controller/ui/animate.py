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


