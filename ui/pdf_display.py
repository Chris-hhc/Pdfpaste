# -*- coding: utf-8 -*-
"""
PDF显示区域UI组件
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QIcon
from models.pdf_model import PDFPageItem
import fitz


class PDFDisplay(QWidget):
    """PDF显示区域"""
    
    # 信号定义
    page_selection_changed = pyqtSignal(list)  # 选中页面列表
    
    def __init__(self):
        super().__init__()
        
        # 缩放相关变量
        self.current_zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 5.0
        
        # PDF文档引用
        self.pdf_document = None
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题和控制栏
        control_layout = QHBoxLayout()
        
        title_label = QLabel("PDF页面预览")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-right: 20px;")
        control_layout.addWidget(title_label)
        
        # 缩放控制 - 第一组：基本控制
        zoom_basic_layout = QHBoxLayout()
        zoom_basic_layout.addWidget(QLabel("缩放:"))
        
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedSize(35, 30)
        self.zoom_out_btn.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_basic_layout.addWidget(self.zoom_out_btn)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(60)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setStyleSheet("font-weight: bold; border: 1px solid #ddd; padding: 5px; background: white; border-radius: 3px;")
        zoom_basic_layout.addWidget(self.zoom_label)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(35, 30)
        self.zoom_in_btn.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_basic_layout.addWidget(self.zoom_in_btn)
        
        self.reset_zoom_btn = QPushButton("重置")
        self.reset_zoom_btn.setFixedWidth(50)
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        zoom_basic_layout.addWidget(self.reset_zoom_btn)
        
        control_layout.addLayout(zoom_basic_layout)
        
        # 添加分隔符
        separator = QLabel("|")
        separator.setStyleSheet("color: #ccc; margin: 0 15px; font-size: 16px;")
        control_layout.addWidget(separator)
        
        # 缩放控制 - 第二组：快捷按钮
        zoom_preset_layout = QHBoxLayout()
        zoom_preset_layout.addWidget(QLabel("快捷:"))
        
        # 常用缩放比例按钮
        preset_buttons = [
            ("50%", 0.5),
            ("100%", 1.0),
            ("150%", 1.5),
            ("200%", 2.0),
            ("300%", 3.0),
            ("400%", 4.0)
        ]
        
        for text, zoom_value in preset_buttons:
            btn = QPushButton(text)
            btn.setFixedWidth(50)
            btn.setStyleSheet("font-size: 12px; padding: 5px;")
            btn.clicked.connect(lambda checked, z=zoom_value: self.set_zoom(z))
            zoom_preset_layout.addWidget(btn)
        
        control_layout.addLayout(zoom_preset_layout)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # 页面列表
        self.page_list = QListWidget()
        self.page_list.setViewMode(QListWidget.IconMode)
        self.page_list.setIconSize(QSize(200, 250))
        self.page_list.setResizeMode(QListWidget.Adjust)
        self.page_list.setSelectionMode(QListWidget.MultiSelection)
        self.page_list.itemSelectionChanged.connect(self.on_page_selection_changed)
        
        # 设置页面列表的样式
        self.page_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
            QListWidget::item {
                border: 2px solid transparent;
                border-radius: 5px;
                margin: 5px;
                padding: 5px;
            }
            QListWidget::item:selected {
                border: 2px solid #007AFF;
                background-color: #E3F2FD;
            }
            QListWidget::item:hover {
                border: 2px solid #87CEEB;
                background-color: #F0F8FF;
            }
        """)
        
        layout.addWidget(self.page_list)
        
    def add_page(self, page_num, pixmap):
        """添加页面"""
        item = PDFPageItem(page_num, pixmap)
        # 使用当前缩放比例
        scaled_pixmap = pixmap.scaled(
            self.page_list.iconSize(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        item.setIcon(QIcon(scaled_pixmap))
        self.page_list.addItem(item)
        
    def clear_pages(self):
        """清除所有页面"""
        self.page_list.clear()
        
    def get_page_count(self):
        """获取页面数量"""
        return self.page_list.count()
        
    def select_pages(self, page_indices):
        """选择指定页面"""
        self.page_list.clearSelection()
        
        for i in range(self.page_list.count()):
            item = self.page_list.item(i)
            if isinstance(item, PDFPageItem) and item.page_num in page_indices:
                item.setSelected(True)
                
    def clear_selection(self):
        """清除选择"""
        self.page_list.clearSelection()
        
    def on_page_selection_changed(self):
        """页面选择改变"""
        selected_items = self.page_list.selectedItems()
        selected_pages = [item.page_num for item in selected_items 
                         if isinstance(item, PDFPageItem)]
        self.page_selection_changed.emit(selected_pages)
        
    def zoom_in(self):
        """放大预览"""
        if self.current_zoom < self.max_zoom:
            # 根据当前缩放比例调整步长
            if self.current_zoom < 1.0:
                step = 0.1  # 小于100%时，步长为10%
            elif self.current_zoom < 2.0:
                step = 0.2  # 100%-200%时，步长为20%
            else:
                step = 0.5  # 大于200%时，步长为50%
            
            self.current_zoom = min(self.current_zoom + step, self.max_zoom)
            self.update_zoom()
            
    def zoom_out(self):
        """缩小预览"""
        if self.current_zoom > self.min_zoom:
            # 根据当前缩放比例调整步长
            if self.current_zoom <= 1.0:
                step = 0.1  # 小于等于100%时，步长为10%
            elif self.current_zoom <= 2.0:
                step = 0.2  # 100%-200%时，步长为20%
            else:
                step = 0.5  # 大于200%时，步长为50%
            
            self.current_zoom = max(self.current_zoom - step, self.min_zoom)
            self.update_zoom()
            
    def reset_zoom(self):
        """重置缩放"""
        self.current_zoom = 1.0
        self.update_zoom()
        
    def set_zoom(self, zoom_level):
        """设置缩放比例"""
        self.current_zoom = zoom_level
        self.update_zoom()
        
    def update_zoom(self):
        """更新缩放显示"""
        # 更新缩放标签
        zoom_percent = int(self.current_zoom * 100)
        self.zoom_label.setText(f"{zoom_percent}%")
        
        # 更新图标大小
        base_width = 200
        base_height = 250
        new_width = int(base_width * self.current_zoom)
        new_height = int(base_height * self.current_zoom)
        self.page_list.setIconSize(QSize(new_width, new_height))
        
        # 重新加载当前页面
        if self.pdf_document and self.pdf_document.doc:
            self.reload_current_pages()
            
    def reload_current_pages(self):
        """重新加载当前显示的页面"""
        if not self.pdf_document or not self.pdf_document.doc:
            return
            
        # 保存当前选中的页面
        selected_pages = [item.page_num for item in self.page_list.selectedItems() 
                         if isinstance(item, PDFPageItem)]
        
        # 清除当前显示
        self.page_list.clear()
        
        # 重新加载所有页面
        for page_num in range(len(self.pdf_document.doc)):
            page = self.pdf_document.doc[page_num]
            # 使用当前缩放比例渲染页面
            mat = fitz.Matrix(1.5 * self.current_zoom, 1.5 * self.current_zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # 转换为QPixmap
            img_data = pix.tobytes("png")
            from PyQt5.QtGui import QImage
            qimg = QImage()
            qimg.loadFromData(img_data)
            pixmap = QPixmap.fromImage(qimg)
            
            # 创建列表项
            item = PDFPageItem(page_num, pixmap)
            scaled_pixmap = pixmap.scaled(
                self.page_list.iconSize(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            item.setIcon(QIcon(scaled_pixmap))
            self.page_list.addItem(item)
            
            # 恢复选中状态
            if page_num in selected_pages:
                item.setSelected(True)
        
    def set_pdf_document(self, pdf_document):
        """设置PDF文档引用"""
        self.pdf_document = pdf_document 