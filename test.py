import pytesseract
from PIL import Image
import pyautogui
import numpy as np
import re
import cv2
import time

# ---------------------  自定义打印模块  ---------------------
from datetime import datetime, timedelta


def print_self(*args, **kwargs):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] ", *args, **kwargs)


# ---------------------  OCR初始化模块  ---------------------
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 打开图像文件
# image = Image.open('C:\\Users\\w1625\\Desktop\\1.jpg')
# 进行文字识别
# text = pytesseract.image_to_string(image, lang='eng')
# # 打印识别结果
# print(text)

# ---------------------  绘制模块  ---------------------
# 设置绘制速度
pyautogui.PAUSE = 0.01
# 移动到起始位置
screen_width, screen_height = pyautogui.size()

# startX = 500
startX = int(screen_width * 0.5)
startY = int(screen_height * 0.7)
length = 20  # 单笔长度
duration = 0.02  # duration表示笔画持续时间


def drawGT():
    pyautogui.moveTo(startX, startY)
    pyautogui.mouseDown()  # 开始绘制 >
    pyautogui.dragTo(startX + length, startY + length, duration=duration)  # 斜向右下  坐标表示笔画终点
    pyautogui.dragTo(startX, startY + length + length, duration=duration)  # 斜向左下
    # 结束绘制
    pyautogui.mouseUp()


def drawLT():
    pyautogui.moveTo(startX, startY)
    pyautogui.mouseDown()  # 开始绘制 <
    pyautogui.dragTo(startX - length, startY + length, duration=duration)  # 斜向右下  坐标表示笔画终点 duration表示笔画持续时间
    pyautogui.dragTo(startX, startY + length + length, duration=duration)  # 斜向左下
    # 结束绘制
    pyautogui.mouseUp()


def drawEQUAL():
    pyautogui.moveTo(startX, startY)
    pyautogui.mouseDown()  # 开始绘制
    pyautogui.dragTo(startX + length, startY, duration=duration)  # 水平向右
    pyautogui.mouseUp()  # 结束上面的横线绘制

    # 绘制下面的横线
    pyautogui.moveTo(startX, startY + length)
    pyautogui.mouseDown()  # 开始绘制
    pyautogui.dragTo(startX + length, startY + length, duration=duration)  # 水平向右
    pyautogui.mouseUp()  # 结束下面的横线绘制


def draw(symbol):
    if symbol == '>':
        drawGT()
    elif symbol == '<':
        drawLT()
    elif symbol == '=':
        drawEQUAL()
    else:
        print_self("error OCR symbol")


#  -----------------------点击进行下一场PK模块---------------
def click_coordinates(x, y, clicks, interval=0.3):
    """
    在指定坐标(x, y)上点击指定次数，每次点击间隔一定的时间。

    :param x: x坐标
    :param y: y坐标
    :param clicks: 点击次数
    :param interval: 点击间隔时间（秒）
    """
    for _ in range(clicks):
        pyautogui.click(x, y)
        time.sleep(interval)


def get_screen_pixel_color(x, y):
    """
    获取屏幕中指定坐标(x, y)的RGB值。

    :param x: x坐标
    :param y: y坐标
    :return: RGB值
    """
    return pyautogui.pixel(x, y)


def is_color_close(color1, color2, tolerance=2):
    """
    检查两个颜色是否在指定的容差范围内相似。

    :param color1: 第一个颜色的RGB值
    :param color2: 第二个颜色的RGB值
    :param tolerance: 容差值
    :return: 布尔值
    """
    if abs(color1[0] - color2[0]) < tolerance and abs(color1[1] - color2[1]) < tolerance and abs(
            color1[2] - color2[2]) < tolerance:
        return True
    else:
        return False


#  -----------------------OCR逻辑模块---------------


def ocr_and_process():
    # 全局重复number记录
    glob_num1 = -1
    glob_num2 = -1

    # 全局绘制计数器 超过10+次清零  然后执行点击进行下一场PK
    cnt = 0

    # 全局计时器 直接判断系统时间是否超过2s还没画图 防止卡死
    # todo 逻辑不应该以时间为准  而是用一个数字【a，b】的list或cnt  如果当前读数=a，b则加入list 或cnt++  如果list size或 cnt超过5次则强制绘画> <  并清空list等
    actual_timer = datetime.now()
    tmp_timer = actual_timer
    flag_during_game=False

    while True:

        if cnt > 10:
            cnt = cnt % 10
        #  点击进行下一场PK模块---------------  FIN

        # 获取屏幕截图
        image = pyautogui.screenshot()
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        # print_self("has shoot")
        # 提取需要识别的区域
        roi = image[580:700, 1150:1800]

        #  点击进行下一场PK模块---------------

        button_next_pixel = image[int(screen_height * 0.84167), int(screen_width * 0.5)]  # 注意：OpenCV的坐标格式是(y, x)
        rgb_value = (button_next_pixel[2], button_next_pixel[1], button_next_pixel[0])
        # print_self("val-====", rgb_value)
        if rgb_value[0] > 200 and rgb_value[1] > 200 and rgb_value[2] < 110:  # 究极debug  yellow
            flag_during_game = False

            # debug  先把鼠标移开
            pyautogui.moveTo(startX, startY)
            # 执行点击操作
            print_self("click to next PK")
            # 在0.2秒内持续点击(1500, 1500)这个坐标2次   注意
            click_coordinates(1500, 1500, 2, 0.1)
            # 在0.2秒内持续点击(2200, 1600)这个坐标2次
            click_coordinates(2200, 1600, 2, 0.1)
            # 再次在0.2秒内持续点击(1500, 1500)这个坐标2次
            click_coordinates(1500, 1500, 2, 0.1)

            continue
        #  点击进行下一场PK模块  FIN---------------

        #  优化:ready阶段的暗色数字识别到也无法绘图 所以直接识别并跳过循环步骤  特征是大量像素点的RGB<100   正常模式底色白色 RGB均接近255
        # 获取ROI最左上角的像素点
        top_left_pixel = roi[0, 0]
        # 检查RGB值是否都小于100
        if top_left_pixel[0] < 100 and top_left_pixel[1] < 100 and top_left_pixel[2] < 100:
            # print_self("ready！")
            flag_during_game = False
            continue

        #  读取当前时间模块---------------
        actual_timer = datetime.now()
        #  判断时间是否持续超过2s没有进行绘画 如果是 则直接绘>和< 并continue
        if actual_timer - tmp_timer > timedelta(seconds=2) and flag_during_game:
            time.sleep(0.5)
            draw('>')
            time.sleep(1.5)
            draw('<')
            print_self("force to continue")
            tmp_timer = actual_timer
            continue
        else:
            tmp_timer = actual_timer
        #  读取当前时间模块FIN ---------------

        # 图像预处理
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        roi_contrast = cv2.convertScaleAbs(roi_gray, alpha=2.0, beta=0)
        roi_blur = cv2.GaussianBlur(roi_contrast, (5, 5), 0)
        _, roi_thresh = cv2.threshold(roi_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # OCR识别
        custom_config = r'--oem 3 --psm 6'
        roi_text = pytesseract.image_to_string(roi_thresh, config=custom_config, lang='eng')
        #  优化  替换文本中的字母'o'或'O'为数字'0'
        roi_text = roi_text.replace('o', '0').replace('O', '0')
        # print("识别到的文本为", roi_text)

        # 提取数字并判断大小
        matches = re.findall(r'\d+', roi_text)
        if len(matches) >= 2:
            flag_during_game=True
            num1, num2 = int(matches[0]), int(matches[1])
            print_self("get number:", num1, num2)
            if glob_num1 != num1 or glob_num2 != num2:  # 说明有新题目
                glob_num1 = num1
                glob_num2 = num2
                result = '<' if glob_num1 < glob_num2 else '>' if glob_num1 > glob_num2 else '='
                # 绘制
                draw(result)
                # print_self(actual_timer, "act!!!", tmp_timer)
                # 优化 每次绘画后记录最新一次绘制时间
                tmp_timer = actual_timer
                cnt += 1
        else:
            flag_during_game = False
        # 等待一小段时间
        time.sleep(0.1)
        # debug 需要强制结束的监听器例如按回车 也可以直接判断如果数字重复则不绘制  可以趁间隙终止运行


# ---------------------  main  ---------------------
ocr_and_process()
