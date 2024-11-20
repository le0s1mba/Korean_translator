import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
import pyperclip
import urllib.request
import urllib.parse
import json
import threading
import winreg
import sys
import os
import win32gui
import win32con
from tkinter.scrolledtext import ScrolledText
import pystray
from PIL import Image, ImageDraw

class TranslatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("한영 번역기")
        self.root.withdraw()
        self.popup = None
        self.is_translating = False
        keyboard.add_hotkey('ctrl+`', self.show_popup)
        self.root.update()
        
    def translate_text(self, text):
        text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=ko&tl=en&dt=t&q={text}"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        
        raw_data = response.read().decode('utf-8')
        data = json.loads(raw_data)
        
        translated_text = ''
        for sentence in data[0]:
            if sentence[0]:
                translated_text += sentence[0]
                
        return translated_text
        
    def show_popup(self):
        if self.popup is None or not tk.Toplevel.winfo_exists(self.popup):
            self.popup = tk.Toplevel(self.root)
            self.popup.title("입력창")
            
            screen_width = self.popup.winfo_screenwidth()
            screen_height = self.popup.winfo_screenheight()
            x = (screen_width/2) - (400/2)
            y = (screen_height/2) - (300/2)
            self.popup.geometry(f'400x300+{int(x)}+{int(y)}')
            
            self.text_input = ScrolledText(self.popup, height=10)
            self.text_input.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
            
            self.status_label = ttk.Label(self.popup, text="")
            self.status_label.pack(pady=5)
            
            self.char_count = tk.Label(self.popup, text="글자 수: 0")
            self.char_count.pack(pady=5)
            
            self.text_input.bind('<KeyRelease>', self.update_char_count)
            self.popup.bind('<Return>', self.handle_return)
            self.popup.bind('<Shift-Return>', lambda e: self.text_input.insert(tk.INSERT, '\n'))
            
            self.text_input.focus()
    
    def handle_return(self, event):
        if not event.state & 0x1:  # Shift key is not pressed
            self.handle_translation()
            return 'break'
    
    def update_char_count(self, event=None):
        text = self.text_input.get('1.0', tk.END).strip()
        count = len(text)
        self.char_count.config(text=f"글자 수: {count}")
    
    def translation_thread(self, text):
        try:
            translated_text = self.translate_text(text)
            self.status_label.config(text="")
            pyperclip.copy(translated_text)
            self.popup.destroy()
            keyboard.write(translated_text)
        except Exception as e:
            messagebox.showerror("오류", f"번역 중 오류가 발생했습니다: {str(e)}")
        finally:
            self.is_translating = False
            
    def handle_translation(self):
        if self.is_translating:
            return
            
        korean_text = self.text_input.get('1.0', tk.END).strip()
        if korean_text:
            self.is_translating = True
            self.status_label.config(text="번역 중...")
            thread = threading.Thread(target=self.translation_thread, args=(korean_text,))
            thread.daemon = True
            thread.start()

    def run(self):
        self.root.mainloop()

def create_tray_icon(app):
    icon = Image.new('RGB', (64, 64), color='white')
    dc = ImageDraw.Draw(icon)
    dc.text((10, 10), "번역", fill='black')
    
    def quit_app(icon, item):
        icon.stop()
        os._exit(0)
    
    tray_icon = pystray.Icon(
        "translator",
        icon,
        "한영 번역기",
        menu=pystray.Menu(
            pystray.MenuItem("종료", quit_app)
        )
    )
    return tray_icon

def main():
    app = TranslatorApp()
    tray_icon = create_tray_icon(app)
    
    def run_tray():
        tray_icon.run()
    
    tray_thread = threading.Thread(target=run_tray)
    tray_thread.daemon = True
    tray_thread.start()
    
    app.run()

if __name__ == "__main__":
    main()