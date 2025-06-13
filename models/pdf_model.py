# -*- coding: utf-8 -*-
"""
PDF数据模型
"""

from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon
import fitz
import os
import tempfile
import datetime
from pathlib import Path


class PDFPageItem(QListWidgetItem):
    """PDF页面项"""
    def __init__(self, page_num, pixmap):
        super().__init__()
        self.page_num = page_num
        self.pixmap = pixmap
        self.setText(f"第 {page_num + 1} 页")


class PDFLoader(QThread):
    """PDF加载线程"""
    page_loaded = pyqtSignal(int, QPixmap)
    loading_finished = pyqtSignal()
    loading_progress = pyqtSignal(int, int)
    
    def __init__(self, pdf_path):
        super().__init__()
        self.pdf_path = pdf_path
        self.doc = None
        
    def run(self):
        try:
            self.doc = fitz.open(self.pdf_path)
            total_pages = len(self.doc)
            
            for page_num in range(total_pages):
                page = self.doc[page_num]
                # 渲染页面为图片，设置适当的缩放比例
                mat = fitz.Matrix(1.5, 1.5)  # 缩放比例
                pix = page.get_pixmap(matrix=mat)
                
                # 转换为QPixmap
                img_data = pix.tobytes("png")
                qimg = QImage()
                qimg.loadFromData(img_data)
                pixmap = QPixmap.fromImage(qimg)
                
                self.page_loaded.emit(page_num, pixmap)
                self.loading_progress.emit(page_num + 1, total_pages)
                
            self.loading_finished.emit()
            
        except Exception as e:
            print(f"加载PDF错误: {e}")


class PDFDocument:
    """PDF文档模型"""
    
    def __init__(self):
        self.pdf_path = None
        self.doc = None
        self.selected_pages = []
        self.temp_files = []
        self.temp_dir = None
        
        # 缩放相关
        self.current_zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 5.0
        
    def load_document(self, pdf_path):
        """加载PDF文档"""
        self.pdf_path = pdf_path
        if self.doc:
            self.doc.close()
        self.doc = fitz.open(pdf_path)
        
    def get_page_count(self):
        """获取页面数量"""
        return len(self.doc) if self.doc else 0
        
    def parse_page_range(self, range_str):
        """解析页码范围字符串"""
        pages = []
        parts = range_str.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = part.split('-', 1)
                start = int(start.strip())
                end = int(end.strip())
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(part))
                
        return sorted(list(set(pages)))  # 去重并排序
        
    def pdf_page_to_image(self, page_num, output_path=None, dpi=300):
        """
        将PDF的指定页面转换为图片
        
        参数:
            page_num (int): 页码 (从0开始，内部使用)
            output_path (str): 输出图片路径，如果为None则自动生成
            dpi (int): 分辨率，默认300
        
        返回:
            str: 保存的图片路径
        """
        try:
            if not self.doc:
                raise ValueError("PDF文档未加载")
            
            # 检查页码范围
            if page_num < 0 or page_num >= len(self.doc):
                raise ValueError(f"页码 {page_num} 超出范围 (0-{len(self.doc)-1})")
            
            # 获取指定页面
            page = self.doc[page_num]
            
            # 计算缩放比例 (DPI转换)
            zoom = dpi / 72.0  # 72是默认DPI
            mat = fitz.Matrix(zoom, zoom)
            
            # 渲染页面为图片
            pix = page.get_pixmap(matrix=mat)
            
            # 生成输出路径
            if output_path is None:
                if self.temp_dir:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    pdf_name = Path(self.pdf_path).stem if self.pdf_path else "pdf"
                    output_path = os.path.join(self.temp_dir, f"{pdf_name}_第{page_num+1}页_{timestamp}.png")
                else:
                    raise ValueError("临时目录未创建")
            
            # 保存图片
            pix.save(output_path)
            
            return output_path
            
        except Exception as e:
            print(f"❌ 转换页面 {page_num+1} 失败: {e}")
            return None
            
    def create_temp_directory(self):
        """创建临时目录"""
        try:
            self.temp_dir = tempfile.mkdtemp(prefix="pdf_viewer_")
            print(f"📁 临时目录已创建: {self.temp_dir}")
        except Exception as e:
            print(f"❌ 创建临时目录失败: {e}")
            self.temp_dir = None
            
    def cleanup(self):
        """清理资源"""
        if self.doc:
            self.doc.close()
            
        # 清理临时文件
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
                
        # 删除临时目录
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                os.rmdir(self.temp_dir)
                print(f"📁 临时目录已删除: {self.temp_dir}")
            except:
                print(f"⚠️ 无法删除临时目录: {self.temp_dir}") 