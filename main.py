#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF展示应用程序主入口
功能：
1. 显示PDF文档
2. 选择特定页面
3. 临时文件管理
4. 后台监听Option+Command自动遍历复制粘贴
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from ui.main_window import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("PDF页面选择器")
    app.setOrganizationName("PDF Tools")
    
    # 设置应用程序字体
    font = QFont("SF Pro Display", 12)  # macOS系统字体
    app.setFont(font)
    
    # 创建主窗口
    main_window = MainWindow()
    main_window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 