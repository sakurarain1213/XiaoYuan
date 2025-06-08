# 独立脚本 可单独运行  用于某平台的自动关注
import sys
import time
from datetime import datetime

# 第三方库导入
import pyautogui
import tkinter as tk

# ---------------------  自定义打印模块  ---------------------
def print_self(*args, **kwargs):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] ", *args, **kwargs)


# 设置绘制速度
pyautogui.PAUSE = 0.01
# 获取屏幕尺寸
screen_width, screen_height = pyautogui.size()

def click_with_coordinates(x, y, clicks=1, interval=0.1):
    """
    在指定坐标点击并打印坐标信息
    """
    print_self(f"点击: x={x}, y={y}")
    for _ in range(clicks):
        pyautogui.click(x, y)
        time.sleep(interval)

def show_control_window():
    """
    显示控制窗口，包含开始和退出按钮
    """
    root = tk.Tk()
    root.title("脚本控制")
    
    # 设置窗口位置（左上角）和大小
    window_width = 300
    window_height = 300
    root.geometry(f"{window_width}x{window_height}+10+10")
    
    # 设置窗口置顶
    root.attributes('-topmost', True)
    
    # 创建按钮
    start_button = tk.Button(root, text="开始运行", width=15, height=2)
    exit_button = tk.Button(root, text="退出脚本", width=15, height=2)
    
    # 放置按钮
    start_button.pack(pady=20)
    exit_button.pack(pady=20)
    
    # 设置退出按钮事件
    def on_exit():
        print_self("用户点击退出按钮，脚本终止")
        root.destroy()
        sys.exit()
    
    exit_button.config(command=on_exit)
    
    # 设置开始按钮事件
    def on_start():
        start_button.config(state='disabled')  # 禁用开始按钮
        root.after(1000, main_sequence)  # 1秒后开始主循环
    
    start_button.config(command=on_start)
    
    # 运行窗口
    root.mainloop()

def show_decision_dialog():
    """
    显示决策对话框，返回是否关注
    """
    root = tk.Tk()
    root.title("是否关注")
    
    # 计算窗口位置使其水平居中
    window_width = 200
    window_height = 250
    x_position = (screen_width - window_width) // 2
    y_position = 50  # 固定在顶部50像素处
    
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
    
    result = [False]  # 使用列表存储结果，以便在回调函数中修改
    
    def on_yes():
        result[0] = True
        root.quit()  # 使用quit()而不是destroy()
        root.destroy()
    
    def on_no():
        result[0] = False
        root.quit()  # 使用quit()而不是destroy()
        root.destroy()
    
    # 创建按钮
    yes_button = tk.Button(root, text="关注", command=on_yes, width=10, height=2)
    no_button = tk.Button(root, text="不关注", command=on_no, width=10, height=2)
    
    # 放置按钮
    yes_button.pack(pady=20)
    no_button.pack(pady=20)
    
    # 设置窗口置顶
    root.attributes('-topmost', True)
    
    # 运行对话框
    root.mainloop()
    
    return result[0]

def main_sequence():
    # 定义坐标（根据实际获取的坐标设置）
    start_button = (1197, 1437)  # 开始按钮
    avatar_button = (1059, 268)  # 头像坐标
    follow_button = (1319, 1682)  # 关注按钮
    exit_button = (1029, 148)  # 退出按钮

    print_self("脚本开始运行...")
    
    while True:
        try:
            # 点击开始
            print("[开始]")
            click_with_coordinates(*start_button)
            
            # 等待10秒
            print_self("等待8秒...")
            time.sleep(8)
            
            # 点击头像
            print("[头像]")
            click_with_coordinates(*avatar_button)
            
            # 显示决策对话框
            print_self("请选择是否关注...")
            should_follow = show_decision_dialog()
            print_self(f"决策结果: {'关注' if should_follow else '不关注'}")
            
            # 等待1秒让决策对话框完全关闭
            time.sleep(1)
            
            # 根据选择执行操作
            if should_follow:
                print_self("执行关注操作")
                click_with_coordinates(*follow_button)
                # 等待1秒让关注操作完成
                time.sleep(1)
            
            # 点击退出两次
            print("[退出*2]")
            click_with_coordinates(*exit_button, clicks=2)
            
            # 等待1秒后继续下一轮
            time.sleep(1)
            
        except Exception as e:
            print_self(f"发生错误: {e}")
            time.sleep(1)

if __name__ == "__main__":
    print_self("脚本启动")
    print_self(f"屏幕分辨率: {screen_width}x{screen_height}")
    
    # 显示控制窗口
    show_control_window()
