# 桌面中国象棋模仿操作脚本 - 吃子检测增强版  但是吃子模仿不太稳定 可以精调
# 需要安装的库: pip install opencv-python pillow pyautogui numpy tkinter keyboard

import cv2
import numpy as np
import pyautogui
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
import time
import keyboard

class ChineseChessMimic:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("中国象棋模仿操作 - 吃子增强版")
        self.root.geometry("400x850")
        
        # 区域坐标
        self.ai_board_region = None
        self.real_board_region = None
        
        # 主被动棋盘状态管理
        self.active_board_region = None  # 当前主动棋盘区域
        self.passive_board_region = None  # 当前被动棋盘区域
        self.active_board_name = None     # 主动棋盘名称 ("AI" 或 "REAL")
        self.passive_board_name = None    # 被动棋盘名称 ("AI" 或 "REAL")
        
        # 监控状态
        self.monitoring = False
        self.monitor_thread = None
        
        # 移动历史记录，用于防重复
        self.move_history = []
        
        # 棋盘网格信息 - 用于吃子检测
        self.board_grid = None
        self.grid_initialized = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        tk.Label(self.root, text="中国象棋模仿操作工具", font=("Arial", 14)).pack(pady=10)
        
        # 框选AI棋盘按钮
        tk.Button(self.root, text="1. 框选AI棋盘区域", 
                 command=self.select_ai_board, 
                 bg="lightblue", width=20, height=2).pack(pady=5)
        
        # 框选实际棋盘按钮
        tk.Button(self.root, text="2. 框选实际棋盘区域", 
                 command=self.select_real_board, 
                 bg="lightgreen", width=20, height=2).pack(pady=5)
        
        # 开始监控按钮
        self.start_btn = tk.Button(self.root, text="3. 开始监控并模仿", 
                                  command=self.toggle_monitoring, 
                                  bg="orange", width=20, height=2)
        self.start_btn.pack(pady=5)
        
        # 状态显示
        self.status_label = tk.Label(self.root, text="请先框选AI棋盘和实际棋盘区域", 
                                   fg="red")
        self.status_label.pack(pady=10)
        
        # 设置说明
        instructions = """使用说明:
1. 点击"框选AI棋盘区域"，在屏幕上拖拽框选AI棋盘
2. 点击"框选实际棋盘区域"，框选你要操作的实际棋盘
3. 点击"开始监控"，程序将自动检测AI移动并模仿
4. 按ESC键可以随时停止监控

主被动棋盘轮换:
- 自动检测哪个棋盘发生变化
- 变化的棋盘成为主动棋盘
- 映射动作到被动棋盘后角色互换
- 支持无限轮换操作

吃子检测增强:
- 自动识别棋盘网格结构
- 检测棋子消失位置（起始点）
- 严格按照像素变化检测吃子目标
- 移除基于棋理的推测，提高准确性
- 增强的移动验证机制"""
        
        tk.Label(self.root, text=instructions, justify=tk.LEFT, 
                wraplength=350).pack(pady=10)
        
    def select_region(self, title):
        """选择屏幕区域"""
        self.root.withdraw()  # 隐藏主窗口
        time.sleep(0.5)  # 等待窗口隐藏
        
        # 创建全屏截图
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        # 创建选择窗口
        clone = screenshot_cv.copy()
        
        # 全局变量用于存储选择区域
        refPt = []
        selecting = False
        
        def select_area(event, x, y, flags, param):
            nonlocal refPt, selecting, clone
            
            if event == cv2.EVENT_LBUTTONDOWN:
                refPt = [(x, y)]
                selecting = True
                
            elif event == cv2.EVENT_MOUSEMOVE and selecting:
                temp_img = clone.copy()
                cv2.rectangle(temp_img, refPt[0], (x, y), (0, 255, 0), 2)
                cv2.imshow(title, temp_img)
                
            elif event == cv2.EVENT_LBUTTONUP:
                refPt.append((x, y))
                selecting = False
                cv2.rectangle(clone, refPt[0], refPt[1], (0, 255, 0), 2)
                cv2.imshow(title, clone)
        
        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        cv2.imshow(title, clone)
        cv2.setMouseCallback(title, select_area)
        
        print(f"请在屏幕上拖拽选择{title}，按空格键确认，按ESC取消")
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' ') and len(refPt) == 2:  # 空格键确认
                break
            elif key == 27:  # ESC取消
                refPt = []
                break
                
        cv2.destroyAllWindows()
        self.root.deiconify()  # 显示主窗口
        
        if len(refPt) == 2:
            # 确保坐标顺序正确
            x1, y1 = refPt[0]
            x2, y2 = refPt[1]
            return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        return None
    
    def select_ai_board(self):
        """选择AI棋盘区域"""
        region = self.select_region("选择AI棋盘区域")
        if region:
            self.ai_board_region = region
            self.status_label.config(text=f"AI棋盘区域已选择: {region}")
            self.grid_initialized = False  # 重置网格初始化状态
            self.initialize_board_roles()  # 初始化主被动角色
            self.check_ready()
    
    def select_real_board(self):
        """选择实际棋盘区域"""
        region = self.select_region("选择实际棋盘区域")
        if region:
            self.real_board_region = region
            self.status_label.config(text=f"实际棋盘区域已选择: {region}")
            self.initialize_board_roles()  # 初始化主被动角色
            self.check_ready()
    
    def initialize_board_roles(self):
        """初始化主被动棋盘角色"""
        if self.ai_board_region and self.real_board_region:
            # 初始状态：AI棋盘为主动，实际棋盘为被动
            self.active_board_region = self.ai_board_region
            self.passive_board_region = self.real_board_region
            self.active_board_name = "AI"
            self.passive_board_name = "REAL"
            print(f"初始化主被动角色: {self.active_board_name} -> {self.passive_board_name}")
    
    def swap_board_roles(self):
        """交换主被动棋盘角色"""
        # 交换区域
        self.active_board_region, self.passive_board_region = self.passive_board_region, self.active_board_region
        # 交换名称
        self.active_board_name, self.passive_board_name = self.passive_board_name, self.active_board_name
        # 重置网格初始化状态（因为棋盘大小可能不同）
        self.grid_initialized = False
        print(f"主被动角色已交换: {self.active_board_name} -> {self.passive_board_name}")
    
    def check_ready(self):
        """检查是否准备就绪"""
        if self.ai_board_region and self.real_board_region:
            if self.active_board_name and self.passive_board_name:
                self.status_label.config(text=f"准备就绪！主动: {self.active_board_name}, 被动: {self.passive_board_name}", fg="green")
            else:
                self.status_label.config(text="准备就绪！可以开始监控", fg="green")
    
    def capture_region(self, region):
        """截取指定区域"""
        x1, y1, x2, y2 = region
        screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
        return np.array(screenshot)
    
    def initialize_board_grid(self, board_img):
        """初始化棋盘网格信息 - 用于吃子检测"""
        if self.grid_initialized:
            return
            
        print("正在初始化棋盘网格...")
        
        # 标准中国象棋棋盘：9x10格子
        board_height, board_width = board_img.shape[:2]
        
        # 计算网格间距（留出边距）
        margin_x = board_width * 0.08  # 左右边距
        margin_y = board_height * 0.05  # 上下边距
        
        grid_width = (board_width - 2 * margin_x) / 8  # 9条竖线，8个间距
        grid_height = (board_height - 2 * margin_y) / 9  # 10条横线，9个间距
        
        # 生成所有网格交点坐标
        self.board_grid = []
        for row in range(10):  # 10行
            grid_row = []
            for col in range(9):  # 9列
                x = margin_x + col * grid_width
                y = margin_y + row * grid_height
                grid_row.append((int(x), int(y)))
            self.board_grid.append(grid_row)
        
        self.grid_initialized = True
        print(f"棋盘网格初始化完成：{len(self.board_grid)}行 x {len(self.board_grid[0])}列")
    
    def find_nearest_grid_point(self, pos):
        """找到最近的网格交点"""
        if not self.grid_initialized or not self.board_grid:
            return pos
            
        x, y = pos
        min_distance = float('inf')
        nearest_point = pos
        nearest_grid = (0, 0)
        
        for row_idx, row in enumerate(self.board_grid):
            for col_idx, (gx, gy) in enumerate(row):
                distance = np.sqrt((x - gx)**2 + (y - gy)**2)
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = (gx, gy)
                    nearest_grid = (row_idx, col_idx)
        
        return nearest_point, nearest_grid
    
    def detect_piece_positions(self, board_img):
        """检测当前棋盘上所有棋子的位置"""
        if not self.grid_initialized:
            self.initialize_board_grid(board_img)
            return []
        
        # 转换为灰度图
        gray = cv2.cvtColor(board_img, cv2.COLOR_RGB2GRAY)
        
        # 使用边缘检测找棋子
        edges = cv2.Canny(gray, 50, 150)
        
        # 形态学操作
        kernel = np.ones((3,3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # 寻找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        piece_positions = []
        board_area = board_img.shape[0] * board_img.shape[1]
        min_area = board_area / 1000  # 最小棋子面积
        max_area = board_area / 80    # 最大棋子面积
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area <= area <= max_area:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    # 找到最近的网格点
                    grid_pos, grid_coord = self.find_nearest_grid_point((cx, cy))
                    if np.sqrt((cx - grid_pos[0])**2 + (cy - grid_pos[1])**2) < 30:  # 距离阈值
                        piece_positions.append(grid_coord)
        
        return piece_positions
    
    def detect_move_with_capturing(self, prev_img, curr_img):
        """增强的移动检测 - 支持吃子"""
        if prev_img is None:
            return None
        
        # 初始化网格
        if not self.grid_initialized:
            self.initialize_board_grid(prev_img)
        
        # 转换为灰度图
        prev_gray = cv2.cvtColor(prev_img, cv2.COLOR_RGB2GRAY)
        curr_gray = cv2.cvtColor(curr_img, cv2.COLOR_RGB2GRAY)
        
        # 计算差异
        diff = cv2.absdiff(prev_gray, curr_gray)
        
        # 二值化处理
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        
        # 形态学操作
        kernel = np.ones((3,3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # 寻找轮廓
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 获取截图尺寸
        board_width = prev_img.shape[1]
        board_height = prev_img.shape[0]
        
        # 面积过滤
        min_area = (board_width * board_height) / 500
        max_area = (board_width * board_height) / 6
        
        candidates = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area <= area <= max_area:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    candidates.append((cx, cy, area))
        
        print(f"检测到 {len(candidates)} 个候选变化点")
        
        if len(candidates) == 0:
            return None
        
        # 分析每个候选点的变化特征
        analyzed_candidates = []
        for cx, cy, area in candidates:
            brightness_change, intensity, change_type = self.analyze_position_change(
                (cx, cy), prev_gray, curr_gray)
            analyzed_candidates.append((cx, cy, area, brightness_change, intensity, change_type))
        
        # 情况1：检测到多个变化点，正常移动
        if len(analyzed_candidates) >= 2:
            return self.handle_normal_move(analyzed_candidates)
        
        # 情况2：只检测到一个变化点，可能是吃子
        elif len(analyzed_candidates) == 1:
            return self.handle_capturing_move(analyzed_candidates[0], prev_img, curr_img)
        
        return None
    
    def analyze_position_change(self, pos, prev_gray, curr_gray):
        """分析位置的像素变化特征"""
        x, y = int(pos[0]), int(pos[1])
        radius = 15
        x1, y1 = max(0, x-radius), max(0, y-radius)
        x2, y2 = min(prev_gray.shape[1], x+radius), min(prev_gray.shape[0], y+radius)
        
        prev_region = prev_gray[y1:y2, x1:x2]
        curr_region = curr_gray[y1:y2, x1:x2]
        
        if prev_region.size == 0 or curr_region.size == 0:
            return 0, 0, 'unknown'
        
        # 计算平均亮度变化
        brightness_change = np.mean(curr_region.astype(float)) - np.mean(prev_region.astype(float))
        
        # 计算变化强度
        intensity = np.std(prev_region.astype(float) - curr_region.astype(float))
        
        # 判断变化类型
        if brightness_change > 8 and intensity > 15:
            change_type = 'piece_left'  # 棋子离开
        elif brightness_change < -8 and intensity > 15:
            change_type = 'piece_arrived'  # 棋子到达
        elif intensity > 20:
            change_type = 'piece_changed'  # 棋子变化（可能是吃子）
        else:
            change_type = 'minor_change'  # 轻微变化
        
        return brightness_change, intensity, change_type
    
    def handle_normal_move(self, candidates):
        """处理正常移动（非吃子）"""
        # 按强度排序，取最强的两个
        candidates.sort(key=lambda x: x[4], reverse=True)  # 按intensity排序
        
        pos1 = (candidates[0][0], candidates[0][1])
        pos2 = (candidates[1][0], candidates[1][1])
        type1 = candidates[0][5]
        type2 = candidates[1][5]
        
        # 验证移动距离
        distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
        board_width = 800  # 估算值
        min_distance = board_width / 30
        max_distance = board_width * 0.9
        
        if not (min_distance < distance < max_distance):
            print(f"移动距离不合理: {distance:.1f}")
            return None
        
        # 根据变化类型判断起始和结束位置
        if type1 == 'piece_left' and type2 == 'piece_arrived':
            from_pos, to_pos = pos1, pos2
        elif type2 == 'piece_left' and type1 == 'piece_arrived':
            from_pos, to_pos = pos2, pos1
        else:
            # 如果类型不明确，使用亮度变化判断
            brightness1 = candidates[0][3]
            brightness2 = candidates[1][3]
            if brightness1 > brightness2:
                from_pos, to_pos = pos1, pos2
            else:
                from_pos, to_pos = pos2, pos1
        
        print(f"检测到正常移动: {from_pos} -> {to_pos}")
        return (from_pos, to_pos)
    
    def handle_capturing_move(self, candidate, prev_img, curr_img):
        """处理吃子移动 - 严格按照像素变化检测，增强大距离处理"""
        cx, cy, area, brightness_change, intensity, change_type = candidate
        from_pos = (cx, cy)
        
        print(f"检测到可能的吃子，起始位置: {from_pos}")
        print(f"变化类型: {change_type}, 亮度变化: {brightness_change:.2f}")
        
        if change_type != 'piece_left':
            print("变化特征不符合棋子离开，跳过")
            return None
        
        # 策略1：标准像素变化检测
        to_pos = self.find_capturing_target_strict(prev_img, curr_img, from_pos)
        
        if to_pos:
            print(f"检测到吃子移动: {from_pos} -> {to_pos}")
            return (from_pos, to_pos)
        
        # 策略2：大距离移动的特殊检测
        to_pos = self.detect_long_distance_capture(prev_img, curr_img, from_pos)
        
        if to_pos:
            print(f"检测到大距离吃子移动: {from_pos} -> {to_pos}")
            return (from_pos, to_pos)
        
        print("无法通过像素变化确定吃子目标位置")
        return None
    
    def find_capturing_target_strict(self, prev_img, curr_img, from_pos):
        """严格按照像素变化寻找吃子的目标位置 - 增强大距离检测"""
        if not self.grid_initialized:
            return None
        
        # 转换为灰度图
        prev_gray = cv2.cvtColor(prev_img, cv2.COLOR_RGB2GRAY)
        curr_gray = cv2.cvtColor(curr_img, cv2.COLOR_RGB2GRAY)
        
        # 计算差异
        diff = cv2.absdiff(prev_gray, curr_gray)
        
        # 使用更低的阈值检测所有变化（提高敏感度）
        _, thresh = cv2.absdiff(prev_gray, curr_gray)
        
        # 形态学操作，连接相近的变化区域
        kernel = np.ones((3,3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # 寻找所有变化区域
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 分析每个变化区域
        change_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 30:  # 降低面积阈值，捕获更多变化
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    change_regions.append((cx, cy, area))
        
        print(f"检测到 {len(change_regions)} 个变化区域")
        
        # 策略1：基于变化区域检测
        if change_regions:
            best_target = self.find_target_from_regions(change_regions, from_pos, prev_gray, curr_gray)
            if best_target:
                return best_target
        
        # 策略2：全局网格扫描（用于大距离移动）
        best_target = self.scan_all_grid_points(from_pos, prev_gray, curr_gray)
        
        return best_target
    
    def find_target_from_regions(self, change_regions, from_pos, prev_gray, curr_gray):
        """从变化区域中找到最佳目标"""
        best_target = None
        max_score = 0
        
        for cx, cy, area in change_regions:
            # 跳过起始位置附近
            if np.sqrt((cx - from_pos[0])**2 + (cy - from_pos[1])**2) < 30:
                continue
            
            # 找到最近的网格点
            nearest_grid, grid_coord = self.find_nearest_grid_point((cx, cy))
            
            # 计算变化强度
            change_score = self.calculate_grid_change_strict(prev_gray, curr_gray, nearest_grid)
            
            # 距离加权评分（大距离移动给予更高权重）
            distance = np.sqrt((cx - from_pos[0])**2 + (cy - from_pos[1])**2)
            distance_bonus = min(distance / 100.0, 2.0)  # 距离越远，权重越高，但不超过2倍
            
            final_score = change_score * distance_bonus
            
            if final_score > max_score and change_score > 2:  # 降低基础阈值
                max_score = final_score
                best_target = nearest_grid
        
        if best_target:
            print(f"从变化区域找到目标，评分: {max_score:.2f}")
        
        return best_target
    
    def scan_all_grid_points(self, from_pos, prev_gray, curr_gray):
        """全局扫描所有网格点（用于大距离移动）"""
        best_target = None
        max_change_score = 0
        
        # 计算棋盘尺寸
        board_width = prev_gray.shape[1]
        board_height = prev_gray.shape[0]
        
        # 遍历所有网格点
        for row_idx, row in enumerate(self.board_grid):
            for col_idx, (gx, gy) in enumerate(row):
                # 跳过起始位置
                if np.sqrt((gx - from_pos[0])**2 + (gy - from_pos[1])**2) < 25:
                    continue
                
                # 计算这个网格点的变化强度
                change_score = self.calculate_grid_change_strict(prev_gray, curr_gray, (gx, gy))
                
                # 距离加权（大距离移动给予更高权重）
                distance = np.sqrt((gx - from_pos[0])**2 + (gy - from_pos[1])**2)
                
                # 大距离移动的特殊处理
                if distance > board_width * 0.3:  # 超过棋盘宽度的30%
                    # 对于大距离移动，降低变化阈值，提高敏感度
                    if change_score > max_change_score and change_score > 1.5:  # 更低的阈值
                        max_change_score = change_score
                        best_target = (gx, gy)
                else:
                    # 正常距离移动
                    if change_score > max_change_score and change_score > 3:
                        max_change_score = change_score
                        best_target = (gx, gy)
        
        if best_target:
            print(f"全局扫描找到目标，变化评分: {max_change_score:.2f}")
        else:
            print("全局扫描未找到足够明显的变化目标")
        
        return best_target
    
    def calculate_grid_change_strict(self, prev_gray, curr_gray, grid_pos):
        """严格计算网格点附近的变化程度 - 增强大距离敏感度"""
        x, y = int(grid_pos[0]), int(grid_pos[1])
        radius = 18  # 进一步增大检测半径
        x1, y1 = max(0, x-radius), max(0, y-radius)
        x2, y2 = min(prev_gray.shape[1], x+radius), min(prev_gray.shape[0], y+radius)
        
        prev_region = prev_gray[y1:y2, x1:x2]
        curr_region = curr_gray[y1:y2, x1:x2]
        
        if prev_region.size == 0 or curr_region.size == 0:
            return 0
        
        # 计算多种变化指标
        diff = cv2.absdiff(prev_region, curr_region)
        
        # 平均变化强度
        mean_change = np.mean(diff)
        
        # 变化的标准差（表示变化的剧烈程度）
        std_change = np.std(diff)
        
        # 变化区域的面积比例（使用更低的阈值）
        change_pixels = np.sum(diff > 8)  # 降低阈值，捕获更多变化
        total_pixels = diff.size
        change_ratio = change_pixels / total_pixels if total_pixels > 0 else 0
        
        # 最大变化值（用于检测强烈变化）
        max_change = np.max(diff)
        
        # 边缘变化检测（棋子边缘的变化）
        edges_prev = cv2.Canny(prev_region, 50, 150)
        edges_curr = cv2.Canny(curr_region, 50, 150)
        edge_diff = cv2.absdiff(edges_prev, edges_curr)
        edge_change = np.mean(edge_diff)
        
        # 综合评分（增强对大距离变化的敏感度）
        change_score = (
            mean_change * 1.0 +           # 基础变化
            std_change * 0.4 +            # 变化剧烈程度
            change_ratio * 60 +           # 变化区域比例
            max_change * 0.1 +            # 最大变化
            edge_change * 0.3             # 边缘变化
        )
        
        return change_score
    
    def convert_coordinates_simple(self, active_pos, active_region, passive_region):
        """坐标转换 - 从主动棋盘到被动棋盘"""
        active_x, active_y = active_pos
        active_x1, active_y1, active_x2, active_y2 = active_region
        passive_x1, passive_y1, passive_x2, passive_y2 = passive_region
        
        # 计算在主动棋盘区域内的相对位置
        active_width = active_x2 - active_x1
        active_height = active_y2 - active_y1
        rel_x = active_x / active_width
        rel_y = active_y / active_height
        
        # 映射到被动棋盘区域
        passive_width = passive_x2 - passive_x1
        passive_height = passive_y2 - passive_y1
        passive_x = passive_x1 + rel_x * passive_width
        passive_y = passive_y1 + rel_y * passive_height
        
        return (int(passive_x), int(passive_y))
    
    def is_duplicate_move(self, from_pos, to_pos):
        """检查是否是重复移动"""
        current_time = time.time()
        
        # 清理旧记录
        self.move_history = [move for move in self.move_history 
                           if current_time - move[2] < 5.0]
        
        # 检查重复
        for prev_from, prev_to, prev_time in self.move_history:
            from_dist = np.sqrt((from_pos[0] - prev_from[0])**2 + (from_pos[1] - prev_from[1])**2)
            to_dist = np.sqrt((to_pos[0] - prev_to[0])**2 + (to_pos[1] - prev_to[1])**2)
            
            if from_dist < 25 and to_dist < 25 and (current_time - prev_time) < 3.0:
                return True
        
        return False
    
    def perform_move_simple(self, from_pos, to_pos):
        """简化的移动执行"""
        print(f"=== 执行移动 ===")
        print(f"起始位置: {from_pos}")
        print(f"目标位置: {to_pos}")
        
        try:
            # 记录移动
            self.move_history.append((from_pos, to_pos, time.time()))
            
            # 直接点击起始位置
            print(f"点击起始位置: {from_pos}")
            pyautogui.click(from_pos[0], from_pos[1])
            time.sleep(0.15)
            
            # 直接点击目标位置
            print(f"点击目标位置: {to_pos}")
            pyautogui.click(to_pos[0], to_pos[1])
            time.sleep(0.15)
            
            print(f"=== 移动完成 ===")
            return True
            
        except Exception as e:
            print(f"执行移动时出现错误: {e}")
            return False
    
    def monitor_loop(self):
        """监控循环 - 支持主被动棋盘轮换"""
        print("开始监控棋盘变化...")
        frame_count = 0
        stable_frames = 0
        
        # 分别跟踪两个棋盘的上一帧
        prev_ai_board = None
        prev_real_board = None
        
        while self.monitoring:
            try:
                frame_count += 1
                
                # 同时截取两个棋盘
                current_ai_board = self.capture_region(self.ai_board_region)
                current_real_board = self.capture_region(self.real_board_region)
                
                # 检测哪个棋盘发生了变化
                ai_changed = False
                real_changed = False
                
                # 检查AI棋盘是否变化
                if prev_ai_board is not None:
                    ai_move = self.detect_move_with_capturing(prev_ai_board, current_ai_board)
                    if ai_move:
                        ai_changed = True
                        print(f"检测到AI棋盘变化")
                
                # 检查实际棋盘是否变化
                if prev_real_board is not None:
                    real_move = self.detect_move_with_capturing(prev_real_board, current_real_board)
                    if real_move:
                        real_changed = True
                        print(f"检测到实际棋盘变化")
                
                # 如果检测到变化，处理移动并轮换角色
                if ai_changed or real_changed:
                    stable_frames = 0
                    
                    # 确定哪个棋盘发生了变化
                    if ai_changed:
                        changed_board = current_ai_board
                        changed_region = self.ai_board_region
                        changed_name = "AI"
                        changed_move = ai_move
                    else:
                        changed_board = current_real_board
                        changed_region = self.real_board_region
                        changed_name = "REAL"
                        changed_move = real_move
                    
                    # 如果变化的棋盘不是当前主动棋盘，需要轮换角色
                    if changed_name != self.active_board_name:
                        print(f"检测到被动棋盘变化，开始轮换角色")
                        # 将变化的棋盘设为主动棋盘
                        self.active_board_region = changed_region
                        self.passive_board_region = self.ai_board_region if changed_name == "REAL" else self.real_board_region
                        self.active_board_name = changed_name
                        self.passive_board_name = "REAL" if changed_name == "AI" else "AI"
                        self.grid_initialized = False
                        print(f"角色已轮换: {self.active_board_name} -> {self.passive_board_name}")
                        continue
                    
                    # 处理主动棋盘的移动
                    if changed_move:
                        active_from, active_to = changed_move
                        
                        # 检查重复
                        if self.is_duplicate_move(active_from, active_to):
                            print(f"跳过重复移动: {active_from} -> {active_to}")
                            continue
                        
                        print(f"检测到{self.active_board_name}棋盘移动: {active_from} -> {active_to}")
                        
                        # 转换坐标到被动棋盘
                        passive_from = self.convert_coordinates_simple(active_from, self.active_board_region, self.passive_board_region)
                        passive_to = self.convert_coordinates_simple(active_to, self.active_board_region, self.passive_board_region)
                        
                        # 执行移动
                        success = self.perform_move_simple(passive_from, passive_to)
                        
                        if success:
                            self.status_label.config(text=f"✓ {self.active_board_name}->{self.passive_board_name}: {passive_from} -> {passive_to}", fg="green")
                        else:
                            self.status_label.config(text=f"✗ 移动失败: {passive_from} -> {passive_to}", fg="red")
                        
                        # 移动完成后轮换角色
                        self.swap_board_roles()
                        
                        # 移动后等待稳定
                        time.sleep(0.8)
                        
                else:
                    stable_frames += 1
                    if stable_frames % 50 == 0:
                        print(f"第 {frame_count} 帧: 棋盘稳定，继续监控... (主动: {self.active_board_name})")
                
                # 更新两个棋盘的上一帧
                prev_ai_board = current_ai_board.copy()
                prev_real_board = current_real_board.copy()
                
                # 检查ESC键
                if keyboard.is_pressed('esc'):
                    self.stop_monitoring()
                    break
                    
                time.sleep(0.1)  # 监控间隔
                
            except Exception as e:
                print(f"监控出错: {e}")
                time.sleep(0.5)
    
    def toggle_monitoring(self):
        """切换监控状态"""
        if not self.ai_board_region or not self.real_board_region:
            messagebox.showerror("错误", "请先选择AI棋盘和实际棋盘区域")
            return
            
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self.start_btn.config(text="停止监控", bg="red")
        self.status_label.config(text="正在监控中... (按ESC停止)", fg="blue")
        
        # 清空历史
        self.move_history = []
        self.grid_initialized = False
        
        # 确保主被动角色已初始化
        if not self.active_board_region or not self.passive_board_region:
            self.initialize_board_roles()
        
        print(f"开始监控，当前主动棋盘: {self.active_board_name}")
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        self.start_btn.config(text="3. 开始监控并模仿", bg="orange")
        self.status_label.config(text="监控已停止", fg="red")
    
    def detect_long_distance_capture(self, prev_img, curr_img, from_pos):
        """专门检测大距离吃子移动"""
        if not self.grid_initialized:
            return None
        
        # 转换为灰度图
        prev_gray = cv2.cvtColor(prev_img, cv2.COLOR_RGB2GRAY)
        curr_gray = cv2.cvtColor(curr_img, cv2.COLOR_RGB2GRAY)
        
        # 计算差异
        diff = cv2.absdiff(prev_gray, curr_gray)
        
        # 使用高斯模糊减少噪声
        diff_blur = cv2.GaussianBlur(diff, (5, 5), 0)
        
        # 寻找变化最明显的区域
        best_target = None
        max_score = 0
        
        # 遍历所有网格点
        for row_idx, row in enumerate(self.board_grid):
            for col_idx, (gx, gy) in enumerate(row):
                # 跳过起始位置
                if np.sqrt((gx - from_pos[0])**2 + (gy - from_pos[1])**2) < 30:
                    continue
                
                # 计算距离
                distance = np.sqrt((gx - from_pos[0])**2 + (gy - from_pos[1])**2)
                
                # 只考虑大距离移动（超过棋盘宽度的25%）
                if distance < prev_img.shape[1] * 0.25:
                    continue
                
                # 计算变化强度（使用更大的检测区域）
                change_score = self.calculate_long_distance_change(prev_gray, curr_gray, (gx, gy))
                
                # 距离加权（距离越远权重越高）
                distance_weight = min(distance / 150.0, 3.0)
                final_score = change_score * distance_weight
                
                if final_score > max_score and change_score > 1.0:  # 更低的阈值
                    max_score = final_score
                    best_target = (gx, gy)
        
        if best_target:
            print(f"大距离检测找到目标，评分: {max_score:.2f}")
        
        return best_target
    
    def calculate_long_distance_change(self, prev_gray, curr_gray, grid_pos):
        """计算大距离移动的变化强度"""
        x, y = int(grid_pos[0]), int(grid_pos[1])
        radius = 25  # 更大的检测半径
        x1, y1 = max(0, x-radius), max(0, y-radius)
        x2, y2 = min(prev_gray.shape[1], x+radius), min(prev_gray.shape[0], y+radius)
        
        prev_region = prev_gray[y1:y2, x1:x2]
        curr_region = curr_gray[y1:y2, x1:x2]
        
        if prev_region.size == 0 or curr_region.size == 0:
            return 0
        
        # 计算差异
        diff = cv2.absdiff(prev_region, curr_region)
        
        # 使用更敏感的变化检测
        # 1. 平均变化
        mean_change = np.mean(diff)
        
        # 2. 变化的标准差
        std_change = np.std(diff)
        
        # 3. 变化像素比例（使用更低的阈值）
        change_pixels = np.sum(diff > 5)  # 更低的阈值
        total_pixels = diff.size
        change_ratio = change_pixels / total_pixels if total_pixels > 0 else 0
        
        # 4. 局部最大值检测
        local_max = np.max(diff)
        
        # 5. 梯度变化检测
        grad_x_prev = cv2.Sobel(prev_region, cv2.CV_64F, 1, 0, ksize=3)
        grad_y_prev = cv2.Sobel(prev_region, cv2.CV_64F, 0, 1, ksize=3)
        grad_x_curr = cv2.Sobel(curr_region, cv2.CV_64F, 1, 0, ksize=3)
        grad_y_curr = cv2.Sobel(curr_region, cv2.CV_64F, 0, 1, ksize=3)
        
        grad_diff = np.sqrt((grad_x_curr - grad_x_prev)**2 + (grad_y_curr - grad_y_prev)**2)
        grad_change = np.mean(grad_diff)
        
        # 综合评分（针对大距离移动优化）
        change_score = (
            mean_change * 1.2 +           # 基础变化
            std_change * 0.5 +            # 变化剧烈程度
            change_ratio * 80 +           # 变化区域比例（更高权重）
            local_max * 0.05 +            # 局部最大值
            grad_change * 0.4             # 梯度变化
        )
        
        return change_score
    
    def run(self):
        """运行程序"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop_monitoring()

if __name__ == "__main__":
    # pyautogui设置
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    
    app = ChineseChessMimic()
    app.run()
