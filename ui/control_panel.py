# -*- coding: utf-8 -*-
"""
控制面板UI组件
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QLineEdit, QTextEdit, QListWidget, 
                            QListWidgetItem, QGroupBox, QProgressBar, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal
import os


class ControlPanel(QWidget):
    """左侧控制面板"""
    
    # 信号定义
    open_pdf_requested = pyqtSignal()
    select_pages_requested = pyqtSignal()
    save_images_requested = pyqtSignal()
    clear_selection_requested = pyqtSignal()
    refresh_temp_files_requested = pyqtSignal()
    clear_temp_files_requested = pyqtSignal()
    delete_selected_files_requested = pyqtSignal(list)  # 删除选中的文件
    open_temp_folder_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setMaximumWidth(400)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)
        
        self.open_button = QPushButton("选择PDF文件")
        self.open_button.clicked.connect(self.open_pdf_requested.emit)
        file_layout.addWidget(self.open_button)
        
        self.file_label = QLabel("未选择文件")
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        file_layout.addWidget(self.progress_bar)
        
        layout.addWidget(file_group)
        
        # 页面选择区域
        selection_group = QGroupBox("页面选择")
        selection_layout = QVBoxLayout(selection_group)
        
        # 页码输入
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("页码范围:"))
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("例如: 1,3,5-7,10")
        input_layout.addWidget(self.page_input)
        selection_layout.addLayout(input_layout)
        
        # 选择按钮
        select_layout = QHBoxLayout()
        self.select_button = QPushButton("选择页面")
        self.select_button.clicked.connect(self.select_pages_requested.emit)
        self.select_button.setEnabled(False)
        select_layout.addWidget(self.select_button)
        
        self.clear_button = QPushButton("清除选择")
        self.clear_button.clicked.connect(self.clear_selection_requested.emit)
        select_layout.addWidget(self.clear_button)
        selection_layout.addLayout(select_layout)
        
        # 选中页面显示
        self.selected_label = QLabel("已选择: 0 页")
        selection_layout.addWidget(self.selected_label)
        
        self.selected_list = QTextEdit()
        self.selected_list.setMaximumHeight(100)
        self.selected_list.setReadOnly(True)
        selection_layout.addWidget(self.selected_list)
        
        layout.addWidget(selection_group)
        
        # 临时文件管理区域
        temp_group = QGroupBox("临时文件管理")
        temp_layout = QVBoxLayout(temp_group)
        
        # 添加时间间隔控制
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("复制间隔:"))
        
        self.interval_input = QLineEdit()
        self.interval_input.setText("4")  # 默认4秒
        self.interval_input.setFixedWidth(60)
        self.interval_input.setPlaceholderText("4.0")
        interval_layout.addWidget(self.interval_input)
        
        interval_layout.addWidget(QLabel("秒"))
        
        # 添加一些常用的时间预设按钮
        quick_interval_layout = QHBoxLayout()
        quick_times = [("1s", 1), ("3s", 3), ("6s", 6)]
        
        for text, time_val in quick_times:
            btn = QPushButton(text)
            btn.setFixedSize(30, 25)
            btn.setStyleSheet("font-size: 10px; padding: 2px;")
            btn.clicked.connect(lambda checked, t=time_val: self.set_interval(t))
            quick_interval_layout.addWidget(btn)
        
        interval_layout.addLayout(quick_interval_layout)
        interval_layout.addStretch()
        
        temp_layout.addLayout(interval_layout)
        
        self.save_images_button = QPushButton("保存选中页面为图片")
        self.save_images_button.clicked.connect(self.save_images_requested.emit)
        self.save_images_button.setEnabled(False)
        temp_layout.addWidget(self.save_images_button)
        
        # 临时文件列表
        self.temp_files_list = QListWidget()
        self.temp_files_list.setMaximumHeight(100)
        self.temp_files_list.setSelectionMode(QListWidget.ExtendedSelection)  # 支持多选
        self.temp_files_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.temp_files_list.customContextMenuRequested.connect(self.show_context_menu)
        temp_layout.addWidget(self.temp_files_list)
        
        self.temp_files_label = QLabel("临时文件: 0 个")
        temp_layout.addWidget(self.temp_files_label)
        
        # 临时文件管理按钮
        temp_buttons_layout = QHBoxLayout()
        
        self.refresh_temp_button = QPushButton("刷新")
        self.refresh_temp_button.clicked.connect(self.refresh_temp_files_requested.emit)
        temp_buttons_layout.addWidget(self.refresh_temp_button)
        
        self.delete_selected_button = QPushButton("删除选中")
        self.delete_selected_button.clicked.connect(self.delete_selected_files)
        temp_buttons_layout.addWidget(self.delete_selected_button)
        
        self.clear_temp_button = QPushButton("清空全部")
        self.clear_temp_button.clicked.connect(self.clear_temp_files_requested.emit)
        temp_buttons_layout.addWidget(self.clear_temp_button)
        
        temp_layout.addLayout(temp_buttons_layout)
        
        # 第二行按钮
        temp_buttons_layout2 = QHBoxLayout()
        
        self.open_folder_button = QPushButton("打开文件夹")
        self.open_folder_button.clicked.connect(self.open_temp_folder_requested.emit)
        temp_buttons_layout2.addWidget(self.open_folder_button)
        
        temp_buttons_layout2.addStretch()
        temp_layout.addLayout(temp_buttons_layout2)
        
        layout.addWidget(temp_group)
        layout.addStretch()
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        if self.temp_files_list.itemAt(position) is None:
            return
            
        context_menu = QMenu(self)
        
        # 删除选中文件
        delete_action = QAction("删除选中文件", self)
        delete_action.triggered.connect(self.delete_selected_files)
        context_menu.addAction(delete_action)
        
        # 打开文件位置
        open_location_action = QAction("打开文件位置", self)
        open_location_action.triggered.connect(self.open_temp_folder_requested.emit)
        context_menu.addAction(open_location_action)
        
        context_menu.exec_(self.temp_files_list.mapToGlobal(position))
    
    def delete_selected_files(self):
        """删除选中的文件"""
        selected_items = self.temp_files_list.selectedItems()
        if not selected_items:
            return
            
        # 获取选中文件的路径
        selected_files = []
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            if file_path:
                selected_files.append(file_path)
        
        if selected_files:
            self.delete_selected_files_requested.emit(selected_files)
        
    def get_copy_interval(self):
        """获取复制间隔时间"""
        try:
            interval_text = self.interval_input.text().strip()
            if not interval_text:
                return 4
            interval = float(interval_text)
            # 限制范围在0.5-60秒之间
            if interval < 0.5:
                interval = 0.5
            elif interval > 60:
                interval = 60
            return interval
        except ValueError:
            return 4
            
    def set_interval(self, interval):
        """设置复制间隔时间"""
        self.interval_input.setText(str(interval))
        
    def set_file_info(self, filename):
        """设置文件信息"""
        self.file_label.setText(f"文件: {filename}")
        
    def show_progress(self, show):
        """显示/隐藏进度条"""
        self.progress_bar.setVisible(show)
        if show:
            self.progress_bar.setValue(0)
            
    def update_progress(self, current, total):
        """更新进度"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        
    def enable_select_button(self, enabled):
        """启用/禁用选择按钮"""
        self.select_button.setEnabled(enabled)
        
    def get_page_range(self):
        """获取页码范围"""
        return self.page_input.text().strip()
        
    def clear_page_input(self):
        """清空页码输入"""
        self.page_input.clear()
        
    def update_selection_info(self, count, page_list):
        """更新选择信息"""
        self.selected_label.setText(f"已选择: {count} 页")
        self.selected_list.setText(page_list)
        self.save_images_button.setEnabled(count > 0)
        
    def update_temp_files(self, temp_files):
        """更新临时文件列表"""
        self.temp_files_list.clear()
        
        if temp_files:
            for file_path in temp_files:
                file_name = os.path.basename(file_path)
                item = QListWidgetItem(file_name)
                item.setData(Qt.UserRole, file_path)
                
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    item.setText(f"❌ {file_name} (已删除)")
                    item.setEnabled(False)
                
                self.temp_files_list.addItem(item)
            
            self.temp_files_label.setText(f"临时文件: {len(temp_files)} 个")
        else:
            self.temp_files_label.setText("临时文件: 0 个") 