# -*- coding: utf-8 -*-
"""
键盘监听服务
处理全局快捷键监听
"""

import time
import threading
import Cocoa
import Quartz


class KeyboardService:
    """键盘监听服务类"""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.is_running = False
        self.thread = None
        
    def get_key_state(self):
        """获取当前按键状态"""
        # 获取当前按键状态
        keys = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateCombinedSessionState)
        
        # 检测 Command 键
        cmd_pressed = keys & Quartz.kCGEventFlagMaskCommand
        
        # 检测 Option 键
        option_pressed = keys & Quartz.kCGEventFlagMaskAlternate
        
        # 检测 Option 键 同时 Command 键 同时按下
        if option_pressed and cmd_pressed:
            print("🎯 Option + Command 组合键触发!")
            if self.callback:
                self.callback()
            return True
        
        return False
    
    def start_listening(self):
        """启动键盘监听"""
        if self.is_running:
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("🎧 开始全局监听 Option+Command 快捷键...")
        
    def stop_listening(self):
        """停止键盘监听"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)
        print("🛑 键盘监听已停止")
        
    def _listen_loop(self):
        """监听循环"""
        while self.is_running:
            self.get_key_state()
            time.sleep(0.1)  # 每0.1秒检查一次 