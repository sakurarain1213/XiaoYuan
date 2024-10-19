from PIL import ImageGrab
from pynput import mouse

def on_move(x, y):
    # 处理鼠标移动事件，输出当前坐标

    print(f"Mouse moved to ({x}, {y}).")

def on_click(x, y, button, pressed):
    # 当鼠标点击事件发生时，输出点击的信息
    color = get_pixel_color(x, y)
    if not pressed:
        print(f"Mouse clicked at ({x}, {y}) with {button},Color: RGB{color}")
        return False

def on_scroll(x, y, dx, dy):
    # 当鼠标滚轮事件发生时，输出滚轮的信息
    print(f"Mouse scrolled at ({x}, {y}) with delta ({dx}, {dy})")


def get_pixel_color(x, y):
    # 捕获鼠标位置的像素颜色
    pixel_color = ImageGrab.grab(bbox=(x, y, x+1, y+1)).getpixel((0, 0))
    return pixel_color


# 设置鼠标监听器
with mouse.Listener(
        on_move=on_move,
        on_click=on_click,
        on_scroll=on_scroll) as listener:
    listener.join()