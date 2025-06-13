# -*- coding: utf-8 -*-
"""
剪贴板服务
处理图片复制粘贴功能
"""

import os
import subprocess

# AppKit导入
try:
    from AppKit import NSPasteboard, NSPasteboardTypePNG, NSPasteboardTypeTIFF, NSImage
    from Foundation import NSData
    APPKIT_AVAILABLE = True
except ImportError:
    print("⚠️ AppKit不可用，将使用替代方法")
    APPKIT_AVAILABLE = False


class ClipboardService:
    """剪贴板服务类"""
    
    @staticmethod
    def copy_image_to_clipboard(image_path):
        """
        使用 AppKit 将图片复制到剪贴板
        
        参数:
            image_path (str): 图片文件路径
        
        返回:
            bool: 操作是否成功
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                print(f"❌ 错误: 文件不存在 - {image_path}")
                return False
            
            if not APPKIT_AVAILABLE:
                print("❌ AppKit不可用，无法复制到剪贴板")
                return False
            
            # 获取绝对路径
            abs_path = os.path.abspath(image_path)
            print(f"📁 复制图片: {os.path.basename(abs_path)}")
            
            # 获取剪贴板
            pb = NSPasteboard.generalPasteboard()
            pb.clearContents()
            
            # 创建NSImage对象
            img = NSImage.alloc().initWithContentsOfFile_(abs_path)
            
            if img is None:
                print(f"❌ 错误: 无法加载图片文件")
                return False
            
            print(f"📊 图片尺寸: {img.size().width} x {img.size().height}")
            
            # 方法1: 设置TIFF格式(NSImage的标准格式)
            tiff_data = img.TIFFRepresentation()
            if tiff_data:
                pb.setData_forType_(tiff_data, NSPasteboardTypeTIFF)
                print("✅ 成功设置TIFF格式")
            
            # 方法2: 尝试设置PNG格式
            try:
                # 获取图像的bitmap representation
                bitmap_rep = img.representations()[0]
                if bitmap_rep:
                    # 转换为PNG格式
                    png_data = bitmap_rep.representationUsingType_properties_(
                        4,  # NSBitmapImageFileTypePNG
                        None
                    )
                    if png_data:
                        pb.setData_forType_(png_data, NSPasteboardTypePNG)
                        print("✅ 成功设置PNG格式")
            except Exception as e:
                print(f"⚠️ PNG格式设置失败: {e}")
            
            print(f"✅ 图片已复制到剪贴板: {os.path.basename(image_path)}")
            return True
            
        except Exception as e:
            print(f"❌ 复制图片异常: {e}")
            return False
    
    @staticmethod
    def simulate_paste():
        """模拟执行 Cmd+V 粘贴操作"""
        try:
            # 使用 osascript 模拟按键
            script = '''
            tell application "System Events"
                keystroke "v" using command down
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print("📋 已执行粘贴操作 (Cmd+V)")
                return True
            else:
                print(f"❌ 粘贴操作失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ 粘贴操作超时")
            return False
        except Exception as e:
            print(f"❌ 粘贴操作异常: {e}")
            return False 