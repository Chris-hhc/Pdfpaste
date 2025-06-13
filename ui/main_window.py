# -*- coding: utf-8 -*-
"""
主窗口UI
"""

import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QSplitter, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import QShortcut

from .control_panel import ControlPanel
from .pdf_display import PDFDisplay
from models.pdf_model import PDFDocument, PDFLoader
from services.keyboard_service import KeyboardService
from services.auto_copy_service import AutoCopyService


class MainWindow(QMainWindow):
    """PDF查看器主窗口"""
    
    # 自定义信号
    command_r_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # 初始化数据模型
        self.pdf_document = PDFDocument()
        self.pdf_document.create_temp_directory()
        
        # 初始化服务
        self.keyboard_service = KeyboardService(callback=self.on_global_shortcut)
        self.auto_copy_service = AutoCopyService(
            temp_dir_getter=lambda: self.pdf_document.temp_dir,
            interval_getter=self.get_copy_interval
        )
        
        # PDF加载器
        self.pdf_loader = None
        
        self.init_ui()
        self.setup_shortcuts()
        self.setup_connections()
        
        # 启动键盘监听
        self.keyboard_service.start_listening()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("PDF页面选择器")
        self.setGeometry(100, 100, 1400, 800)
        
        # 设置主题样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLabel {
                color: #333;
            }
        """)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 创建UI组件
        self.control_panel = ControlPanel()
        self.pdf_display = PDFDisplay()
        
        splitter.addWidget(self.control_panel)
        splitter.addWidget(self.pdf_display)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
    def setup_shortcuts(self):
        """设置窗口内快捷键"""
        # 打开文件 - Command+O (窗口内)
        open_shortcut = QShortcut(QKeySequence("Meta+O"), self)
        open_shortcut.activated.connect(self.open_pdf)
        
        # 选择页面 - Command+S (窗口内)
        select_shortcut = QShortcut(QKeySequence("Meta+S"), self)
        select_shortcut.activated.connect(self.select_pages)
        
    def setup_connections(self):
        """设置信号连接"""
        # 控制面板信号连接
        self.control_panel.open_pdf_requested.connect(self.open_pdf)
        self.control_panel.select_pages_requested.connect(self.select_pages)
        self.control_panel.save_images_requested.connect(self.save_selected_pages_as_images)
        self.control_panel.clear_selection_requested.connect(self.clear_selection)
        self.control_panel.refresh_temp_files_requested.connect(self.refresh_temp_files)
        self.control_panel.clear_temp_files_requested.connect(self.clear_temp_files)
        self.control_panel.delete_selected_files_requested.connect(self.delete_selected_files)
        self.control_panel.open_temp_folder_requested.connect(self.open_temp_folder)
        
        # PDF显示区域信号连接
        self.pdf_display.page_selection_changed.connect(self.on_page_selection_changed)
        
        # 全局快捷键信号连接
        self.command_r_signal.connect(self.auto_copy_service.start_auto_copy_paste)
        
    def on_global_shortcut(self):
        """全局快捷键回调"""
        # 使用Qt的信号槽机制在主线程中执行
        self.command_r_signal.emit()
        
    def get_copy_interval(self):
        """获取复制间隔时间"""
        return self.control_panel.get_copy_interval()
        
    def open_pdf(self):
        """打开PDF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PDF文件", "", "PDF文件 (*.pdf)")
        
        if file_path:
            self.pdf_document.load_document(file_path)
            self.control_panel.set_file_info(os.path.basename(file_path))
            self.load_pdf()
            
    def load_pdf(self):
        """加载PDF文件"""
        if not self.pdf_document.pdf_path:
            return
            
        # 设置PDF显示组件的文档引用
        self.pdf_display.set_pdf_document(self.pdf_document)
            
        # 清除之前的数据
        self.pdf_display.clear_pages()
        self.pdf_document.selected_pages.clear()
        
        # 显示进度条
        self.control_panel.show_progress(True)
        
        # 启动加载线程
        self.pdf_loader = PDFLoader(self.pdf_document.pdf_path)
        self.pdf_loader.page_loaded.connect(self.pdf_display.add_page)
        self.pdf_loader.loading_finished.connect(self.on_loading_finished)
        self.pdf_loader.loading_progress.connect(self.control_panel.update_progress)
        self.pdf_loader.start()
        
    @pyqtSlot()
    def on_loading_finished(self):
        """所有页面加载完成"""
        self.control_panel.show_progress(False)
        self.control_panel.enable_select_button(True)
        
        QMessageBox.information(self, "加载完成", 
                              f"PDF加载完成，共 {self.pdf_display.get_page_count()} 页")
        
    def select_pages(self):
        """根据输入选择页面"""
        if not self.pdf_document.doc:
            QMessageBox.warning(self, "警告", "请先打开PDF文件")
            return
            
        page_range = self.control_panel.get_page_range()
        if not page_range:
            QMessageBox.warning(self, "警告", "请输入页码范围")
            return
            
        try:
            pages = self.pdf_document.parse_page_range(page_range)
            total_pages = self.pdf_document.get_page_count()
            
            # 验证页码
            valid_pages = []
            for page in pages:
                if 1 <= page <= total_pages:
                    valid_pages.append(page - 1)  # 转换为0索引
                else:
                    QMessageBox.warning(self, "警告", f"页码 {page} 超出范围 (1-{total_pages})")
                    return
                    
            # 选择页面
            self.pdf_display.select_pages(valid_pages)
                    
        except ValueError as e:
            QMessageBox.warning(self, "错误", f"页码格式错误: {e}")
            
    def on_page_selection_changed(self, selected_pages):
        """页面选择改变"""
        self.pdf_document.selected_pages = selected_pages
        
        count = len(selected_pages)
        page_numbers = [str(page + 1) for page in sorted(selected_pages)]
        
        self.control_panel.update_selection_info(count, ", ".join(page_numbers))
        
    def clear_selection(self):
        """清除页面选择"""
        self.pdf_display.clear_selection()
        self.control_panel.clear_page_input()
        
    def save_selected_pages_as_images(self):
        """保存选中页面为图片文件"""
        if not self.pdf_document.selected_pages:
            QMessageBox.warning(self, "警告", "请先选择页面")
            return
            
        if not self.pdf_document.doc:
            QMessageBox.warning(self, "警告", "PDF文档未加载")
            return
        
        if not self.pdf_document.temp_dir:
            QMessageBox.warning(self, "警告", "临时目录未创建")
            return
        
        try:
            saved_files = []
            failed_count = 0
            
            for page_num in sorted(self.pdf_document.selected_pages):
                output_path = self.pdf_document.pdf_page_to_image(page_num, dpi=300)
                if output_path:
                    saved_files.append(output_path)
                    self.pdf_document.temp_files.append(output_path)
                else:
                    failed_count += 1
            
            # 更新临时文件列表显示
            self.control_panel.update_temp_files(self.pdf_document.temp_files)
            
            # 显示结果
            success_count = len(saved_files)
            total_count = len(self.pdf_document.selected_pages)
            
            if success_count > 0:
                QMessageBox.information(self, "保存完成", 
                                      f"成功保存 {success_count}/{total_count} 页为图片\n"
                                      f"保存位置: {self.pdf_document.temp_dir}")
            else:
                QMessageBox.warning(self, "保存失败", "所有页面保存失败")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存过程中发生错误: {e}")
    
    def refresh_temp_files(self):
        """刷新临时文件列表"""
        if not self.pdf_document.temp_dir:
            QMessageBox.information(self, "提示", "暂无临时目录")
            return
            
        # 重新扫描临时目录
        self.pdf_document.refresh_temp_files()
        
        # 更新显示
        self.control_panel.update_temp_files(self.pdf_document.temp_files)
        
        QMessageBox.information(self, "刷新完成", 
                              f"已刷新临时文件列表，共 {len(self.pdf_document.temp_files)} 个文件")
    
    def delete_selected_files(self, selected_files):
        """删除选中的临时文件"""
        if not selected_files:
            QMessageBox.information(self, "提示", "请先选择要删除的文件")
            return
            
        reply = QMessageBox.question(self, "确认删除", 
                                   f"确定要删除选中的 {len(selected_files)} 个文件吗？\n"
                                   "此操作不可撤销！",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            deleted_count = self.pdf_document.delete_selected_files(selected_files)
            
            # 更新显示
            self.control_panel.update_temp_files(self.pdf_document.temp_files)
            
            QMessageBox.information(self, "删除完成", 
                                  f"已删除 {deleted_count} 个文件")
    
    def clear_temp_files(self):
        """清理所有临时文件"""
        if not self.pdf_document.temp_files:
            QMessageBox.information(self, "提示", "暂无临时文件需要清理")
            return
            
        reply = QMessageBox.question(self, "确认清空", 
                                   f"确定要删除所有 {len(self.pdf_document.temp_files)} 个临时文件吗？\n"
                                   "此操作不可撤销！",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            deleted_count = self.pdf_document.clear_temp_files()
            
            # 更新显示
            self.control_panel.update_temp_files(self.pdf_document.temp_files)
            
            QMessageBox.information(self, "清空完成", 
                                  f"已删除 {deleted_count} 个临时文件")
    
    def open_temp_folder(self):
        """打开临时文件夹"""
        if not self.pdf_document.temp_dir or not os.path.exists(self.pdf_document.temp_dir):
            QMessageBox.warning(self, "警告", "临时目录不存在")
            return
            
        try:
            # macOS 使用 open 命令打开文件夹
            import subprocess
            subprocess.run(["open", self.pdf_document.temp_dir])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件夹: {e}")
            
    def closeEvent(self, event):
        """程序关闭时清理资源"""
        # 停止自动遍历
        if self.auto_copy_service.is_processing():
            self.auto_copy_service.stop_auto_copy_paste()
        
        # 停止键盘监听
        self.keyboard_service.stop_listening()
        
        # 询问是否删除临时文件
        if self.pdf_document.temp_files:
            reply = QMessageBox.question(self, "退出程序", 
                                       f"程序即将退出，是否删除 {len(self.pdf_document.temp_files)} 个临时文件？",
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                self.pdf_document.cleanup()
        
        event.accept() 