# -*- coding: utf-8 -*-
"""
自动复制粘贴服务
处理批量图片的自动复制粘贴功能
"""

import os
from PyQt5.QtCore import QTimer
from services.clipboard_service import ClipboardService


class AutoCopyService:
    """自动复制粘贴服务类"""
    
    def __init__(self, temp_dir_getter, interval_getter):
        self.temp_dir_getter = temp_dir_getter  # 获取临时目录的函数
        self.interval_getter = interval_getter  # 获取时间间隔的函数
        
        # 自动遍历相关
        self.auto_copy_timer = QTimer()
        self.auto_copy_timer.timeout.connect(self.process_next_image)
        self.current_image_index = 0
        self.images_to_process = []
        self.is_auto_processing = False
        
    def get_temp_image_files(self):
        """获取临时目录中的所有图片文件"""
        temp_dir = self.temp_dir_getter()
        if not temp_dir or not os.path.exists(temp_dir):
            return []
        
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
        image_files = []
        
        try:
            for file in os.listdir(temp_dir):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    full_path = os.path.join(temp_dir, file)
                    if os.path.exists(full_path):
                        image_files.append(full_path)
            
            # 按文件名排序
            image_files.sort()
            return image_files
            
        except Exception as e:
            print(f"❌ 获取图片文件失败: {e}")
            return []
    
    def start_auto_copy_paste(self):
        """开始自动遍历复制粘贴 (后台运行)"""
        if self.is_auto_processing:
            print("⚠️ 自动遍历正在进行中，请等待完成")
            return
        
        # 获取所有图片文件
        self.images_to_process = self.get_temp_image_files()
        
        if not self.images_to_process:
            print("⚠️ 临时目录中没有找到图片文件")
            return
        
        # 开始处理
        self.current_image_index = 0
        self.is_auto_processing = True
        
        # 立即处理第一张图片
        self.process_next_image()
        
        print(f"🚀 开始后台自动遍历 {len(self.images_to_process)} 张图片")
    
    def process_next_image(self):
        """处理下一张图片"""
        if not self.is_auto_processing or self.current_image_index >= len(self.images_to_process):
            self.stop_auto_copy_paste()
            return
        
        current_image = self.images_to_process[self.current_image_index]
        
        print(f"\n🖼️  处理第 {self.current_image_index + 1}/{len(self.images_to_process)} 张图片")
        
        # 复制到剪贴板
        if ClipboardService.copy_image_to_clipboard(current_image):
            # 等待一小段时间确保复制完成
            QTimer.singleShot(500, ClipboardService.simulate_paste)
        else:
            print(f"❌ 复制失败，跳过: {os.path.basename(current_image)}")
        
        # 准备下一张图片
        self.current_image_index += 1
        
        # 如果还有图片，设置定时器处理下一张
        if self.current_image_index < len(self.images_to_process):
            # 获取用户设置的时间间隔
            interval = self.get_copy_interval()
            self.auto_copy_timer.start(int(interval * 1000))  # 转换为毫秒并转为整数
        else:
            # 所有图片处理完成
            QTimer.singleShot(1000, self.stop_auto_copy_paste)
    
    def get_copy_interval(self):
        """获取复制间隔时间"""
        try:
            interval = self.interval_getter()
            
            # 限制范围：最小0.5秒，最大60秒
            if interval < 0.5:
                interval = 0.5
                print("⚠️ 时间间隔不能小于0.5秒，已自动调整")
            elif interval > 60:
                interval = 60
                print("⚠️ 时间间隔不能大于60秒，已自动调整")
            
            return interval
            
        except (ValueError, TypeError):
            print("⚠️ 时间间隔格式错误，使用默认值4秒")
            return 4
    
    def stop_auto_copy_paste(self):
        """停止自动遍历复制粘贴"""
        if not self.is_auto_processing:
            return
        
        self.auto_copy_timer.stop()
        self.is_auto_processing = False
        
        if self.current_image_index >= len(self.images_to_process):
            print(f"✅ 自动遍历完成！已处理 {len(self.images_to_process)} 张图片")
        else:
            print(f"🛑 自动遍历已停止 (处理了 {self.current_image_index}/{len(self.images_to_process)} 张)")
            
    def is_processing(self):
        """检查是否正在处理"""
        return self.is_auto_processing 